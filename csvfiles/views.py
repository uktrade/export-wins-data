from urllib.parse import urlparse

import boto3
import itertools

from django.conf import settings
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db import models
from django.db.models import Func, F, Max
from django.db.models.functions import Lower
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.utils.functional import cached_property
from django.views.generic import TemplateView

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from alice.authenticators import (
    IsAdminServer,
    IsMIServer,
    IsMIUser,
    IsDataTeamServer
)
from alice.middleware import alice_exempt

from csvfiles.constants import FILE_TYPES
from csvfiles.models import File as CSVFile, File
from csvfiles.serializers import (
    FileSerializer,
    ExportWinsFileSerializer,
    FileWithRegionSerializer,
    FileWithSectorSerializer
)
from mi.models import FinancialYear


class Month(Func):
    function = 'EXTRACT'
    template = '%(function)s(MONTH from %(expressions)s)'
    output_field = models.IntegerField()


class CSVBaseView(APIView):
    file_type = None
    metadata_keys = list()
    serializer_class = FileSerializer

    @classmethod
    def as_view(cls, **initkwargs):
        # ensure file type is correct and crash early if not
        if 'file_type' in initkwargs and not FILE_TYPES.has_constant(initkwargs['file_type']):
            raise ValueError('file_type is not valid')
        return super().as_view(**initkwargs)

    @property
    def file_type_choice(self):
        return FILE_TYPES.for_constant(self.file_type)

    @cached_property
    def last_fy(self):
        today = now()
        if today.month < 4:
            return FinancialYear.objects.get(id=today.year - 2)
        else:
            return FinancialYear.objects.get(id=today.year - 1)

    @cached_property
    def current_fy(self):
        today = now()
        if today.month < 4:
            return FinancialYear.objects.get(id=today.year - 1)
        else:
            return FinancialYear.objects.get(id=today.year)

    def latest_file(self, file_type=None):
        if not file_type:
            file_type = self.file_type_choice

        try:
            return CSVFile.objects.filter(report_start_date__gte=self.last_fy.start,
                                          file_type=file_type.value,
                                          is_active=True).latest('created')
        except CSVFile.DoesNotExist:
            return None

    def files_list(self, file_type=None):
        if not file_type:
            file_type = self.file_type_choice

        fy_start_date = self.last_fy.start

        if file_type.constant == 'EXPORT_WINS':  # get latest file per FY
            try:
                return CSVFile.objects.filter(
                    file_type=file_type.value, is_active=True
                ).annotate(year=Func(F('report_end_date'), function='get_financial_year')
                           ).order_by('year', '-report_end_date').distinct('year')
            except CSVFile.DoesNotExist:
                return None

        # get latest one for each month available for current FY
        if file_type.constant in (
                'FDI_MONTHLY',
                'SERVICE_DELIVERIES_MONTHLY',
                'KANTAR_MONTHLY',
                'MARKETING_COMPANIES_CONTACTS_COUNTRY_TIERS_MONTHLY'
        ):
            try:
                return CSVFile.objects.filter(
                    report_start_date__gte=fy_start_date, file_type=file_type.value, is_active=True
                ).annotate(month=Month('report_end_date')
                           ).order_by('month', '-created').distinct('month')
            except CSVFile.DoesNotExist:
                return None

        # get latest one available for current FY
        if file_type.constant in (
                'FDI_DAILY',
                'SERVICE_DELIVERIES_DAILY',
                'MARKETING_COMPANIES_CONTACTS_COUNTRY_TIERS_DAILY'
        ):
            return self.latest_file(file_type)

        # metadata based, latest file available
        if file_type.constant in ('CONTACTS_REGION', 'COMPANIES_REGION'):
            try:
                return CSVFile.objects.filter(
                    file_type=file_type.value, is_active=True
                ).annotate(region=KeyTextTransform('region', 'metadata'),
                           region_lower=Lower(
                               KeyTextTransform('region', 'metadata'))
                           ).order_by('region_lower', '-report_end_date'
                                      ).distinct('region_lower')
            except CSVFile.DoesNotExist:
                return None

        if file_type.constant in ('CONTACTS_SECTOR', 'COMPANIES_SECTOR'):
            try:
                return CSVFile.objects.filter(
                    file_type=file_type.value, is_active=True
                ).annotate(sector=KeyTextTransform('sector', 'metadata'),
                           sector_lower=Lower(
                               KeyTextTransform('sector', 'metadata'))
                           ).order_by('sector_lower', '-report_end_date').distinct('sector_lower')
            except CSVFile.DoesNotExist:
                return None

        return None


class CSVFileView(CSVBaseView):
    """
    Helps storing file details of a file that was uploaded into S3
    Post creates a new entry
    """
    permission_classes = (IsAdminUser, IsAdminServer)

    def immutable_data(self):
        """
        :return: data that can't be overridden by request.data
        """
        user = self.request.user
        if user.is_authenticated:
            return {
                'user': self.request.user.id,
            }
        return {}

    def default_data(self):
        """
        :return: data that the user is allowed to override
        """
        return {
            'file_type': self.file_type,
            'name': self.file_type_choice.display,
            'report_start_date': now(),
            'report_end_date': now(),
        }

    def get_merged_data(self):
        return {
            **self.default_data(),
            **self.request.data.dict(),
            **self.immutable_data()
        }

    def post(self, request):
        serializer = self.serializer_class(data=self.get_merged_data())

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response({}, status=status.HTTP_201_CREATED)


class ExportWinsCSVFileView(CSVFileView):

    permission_classes = (IsAdminUser, IsAdminServer)
    serializer_class = ExportWinsFileSerializer


class DataTeamCSVFileView(CSVFileView):

    permission_classes = (IsDataTeamServer,)


class CSVFileWithRegionView(CSVFileView):

    permission_classes = (IsDataTeamServer,)
    serializer_class = FileWithRegionSerializer


class CSVFileWithSectorView(CSVFileView):

    permission_classes = (IsDataTeamServer,)
    serializer_class = FileWithSectorSerializer


class CSVFilesListView(CSVBaseView):
    """
    Get returns all active entries from the database
    """
    permission_classes = (IsMIServer, IsMIUser)

    def get(self, request):
        list_files = self.files_list()

        if not list_files:
            raise NotFound()

        results = self.serializer_class(
            instance=list_files, many=True).data

        return Response(results, status=status.HTTP_200_OK)


class LatestCSVFileView(CSVBaseView):
    """
    Returns last uploaded file into S3
    """
    permission_classes = (IsMIServer, IsMIUser)

    def get(self, request):
        latest_csv_file = self.latest_file()
        results = self.serializer_class(instance=latest_csv_file).data

        return Response(results, status=status.HTTP_200_OK)


class GenerateOTUForCSVFileView(CSVBaseView):
    """
    This view generates a One Time URL for given file ID
    that was already uploaded into S3.
    """
    permission_classes = (IsMIServer, IsMIUser)

    def _generate_one_time_url(self, s3_path):
        """
        Generates presigned download url for a given full S3 path
        usual S3 file format is: s3://bucket_name/full/path
        """
        parsed = urlparse(s3_path)
        bucket = parsed.netloc
        file_key = parsed.path[1:]  # remove leading /

        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_KEY_CSV_READ_ONLY_ACCESS,
            aws_secret_access_key=settings.AWS_SECRET_CSV_READ_ONLY_ACCESS,
            region_name=settings.AWS_REGION_CSV,
        )
        return s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': bucket,
                'Key': file_key
            },
            # preserve it for 2 minutes
            ExpiresIn=120
        )

    def get(self, request, file_id):
        try:
            latest_csv_file = CSVFile.objects.get(id=file_id)
            results = {
                'id': latest_csv_file.id,
                'one_time_url': self._generate_one_time_url(latest_csv_file.s3_path)
            }

            return Response(results, status=status.HTTP_200_OK)
        except CSVFile.DoesNotExist:
            raise NotFound(detail='Invalid file ID')


class AllCSVFilesView(CSVBaseView):
    """
    Get returns all active CSV files for all file types from the database
    """

    permission_classes = (IsMIServer, IsMIUser)

    def get(self, request):
        ew_files = self.files_list(FILE_TYPES.EXPORT_WINS)
        fdi_monthly_files = self.files_list(FILE_TYPES.FDI_MONTHLY)
        fdi_daily_file = self.latest_file(FILE_TYPES.FDI_DAILY)
        sdi_monthly_files = self.files_list(
            FILE_TYPES.SERVICE_DELIVERIES_MONTHLY)
        sdi_daily_file = self.latest_file(FILE_TYPES.SERVICE_DELIVERIES_DAILY)
        cont_region_files = self.files_list(FILE_TYPES.CONTACTS_REGION)
        comp_region_files = self.files_list(FILE_TYPES.COMPANIES_REGION)
        cont_sector_files = self.files_list(FILE_TYPES.CONTACTS_SECTOR)
        comp_sector_files = self.files_list(FILE_TYPES.COMPANIES_SECTOR)
        kantar_monthly_files = self.files_list(FILE_TYPES.KANTAR_MONTHLY)
        results = {}

        if ew_files:
            current_ew_files = [x for x in ew_files if x.year == self.current_fy.description]
            results['export'] = {}
            if current_ew_files:
                current_ew = current_ew_files[0]
                results['export']['current'] = {
                    'id': current_ew.id,
                    'name': current_ew.name,
                    'report_start_date': current_ew.report_start_date,
                    'report_end_date': current_ew.report_end_date,
                    'created': current_ew.created,
                    'financial_year': current_ew.year,
                }

            prev_ew_files = [x for x in ew_files if x.year != self.current_fy.description]
            results['export']['previous'] = [
                {
                    'id': x.id,
                    'name': x.name,
                    'report_start_date': x.report_start_date,
                    'report_end_date': x.report_end_date,
                    'created': x.created,
                    'financial_year': x.year,
                } for x in prev_ew_files
            ]

        if fdi_monthly_files or fdi_daily_file:
            results['fdi'] = {}

        if fdi_monthly_files:
            results['fdi']['months'] = [
                {
                    'id': x.id,
                    'name': x.name,
                    'report_start_date': x.report_start_date,
                    'report_end_date': x.report_end_date,
                    'created': x.created,
                } for x in fdi_monthly_files
            ]

        if fdi_daily_file:
            results['fdi']['latest'] = {
                'id': fdi_daily_file.id,
                'name': fdi_daily_file.name,
                'report_start_date': fdi_daily_file.report_start_date,
                'report_end_date': fdi_daily_file.report_end_date,
                'created': fdi_daily_file.created,
            }

        if sdi_monthly_files or sdi_daily_file:
            results['sdi'] = {}

        if sdi_monthly_files:
            results['sdi']['months'] = [
                {
                    'id': x.id,
                    'name': x.name,
                    'report_start_date': x.report_start_date,
                    'report_end_date': x.report_end_date,
                    'created': x.created,
                } for x in sdi_monthly_files
            ]

        if sdi_daily_file:
            results['sdi']['latest'] = {
                'id': sdi_daily_file.id,
                'name': sdi_daily_file.name,
                'report_start_date': sdi_daily_file.report_start_date,
                'report_end_date': sdi_daily_file.report_end_date,
                'created': sdi_daily_file.created,
            }

        if cont_region_files or cont_sector_files:
            results['contacts'] = {}

        if cont_region_files:
            results['contacts']['regions'] = [
                {
                    'id': x.id,
                    'name': x.name,
                    'report_start_date': x.report_start_date,
                    'report_end_date': x.report_end_date,
                    'created': x.created,
                    'region': x.region,
                } for x in cont_region_files
            ]

        if cont_sector_files:
            results['contacts']['sectors'] = [
                {
                    'id': x.id,
                    'name': x.name,
                    'report_start_date': x.report_start_date,
                    'report_end_date': x.report_end_date,
                    'created': x.created,
                    'sector': x.sector,
                } for x in cont_sector_files
            ]

        if comp_region_files or comp_sector_files:
            results['companies'] = {}

        if comp_region_files:
            results['companies']['regions'] = [
                {
                    'id': x.id,
                    'name': x.name,
                    'report_start_date': x.report_start_date,
                    'report_end_date': x.report_end_date,
                    'created': x.created,
                    'region': x.region,
                } for x in comp_region_files
            ]

        if comp_sector_files:
            results['companies']['sectors'] = [
                {
                    'id': x.id,
                    'name': x.name,
                    'report_start_date': x.report_start_date,
                    'report_end_date': x.report_end_date,
                    'created': x.created,
                    'sector': x.sector,
                } for x in comp_sector_files
            ]

        if kantar_monthly_files:
            results['kantar'] = {}
            results['kantar']['months'] = [
                {
                    'id': x.id,
                    'name': x.name,
                    'report_start_date': x.report_start_date,
                    'report_end_date': x.report_end_date,
                    'created': x.created,
                } for x in kantar_monthly_files
            ]

        return Response(results, status=status.HTTP_200_OK)


@method_decorator(alice_exempt, name='dispatch')
class PingdomCustomCheckView(TemplateView):
    """
    A view which will respond with a NOT OK status if
    the latest csv uploaded by the data science team is
    > 25 hours.
    """

    template_name = 'pingdom.xml'
    content_type = 'text/xml; charset=utf-8'
    error_after_seconds = 25 * 60 * 60  # 25 hours (25 * 60 mins * 60 seconds)

    file_types_filter = [x for x in FILE_TYPES.subsets if x != 'EW']

    @cached_property
    def _get_filtered_filetypes(self):
        """
        return file_type ids that are delivered by the data science team
        """
        return [y[0] for y in itertools.chain.from_iterable(getattr(FILE_TYPES, x) for x in self.file_types_filter)]

    def get_context_data(self, **kwargs):
        files_type_and_created = File.objects.filter(
            file_type__in=self._get_filtered_filetypes
        ).aggregate(
            Max('created')
        )
        status = 'NOT OK'
        latest_iso = None
        if files_type_and_created:
            latest = files_type_and_created['created__max']
            if latest:
                latest_iso = latest.isoformat()
                delta = now() - latest
                if delta.total_seconds() < self.error_after_seconds:
                    status = 'OK'

        return {
            'status': status,
            'response_time': 1,
            'last_uploaded': latest_iso
        }
