from operator import itemgetter
from urllib.parse import urlparse

import boto3

from django.conf import settings
from django.utils.timezone import now

from rest_framework import status
from rest_framework.exceptions import NotFound, ParseError
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from alice.authenticators import (
    IsAdminServer,
    IsMIServer,
    IsMIUser,
    IsDataTeamServer
)

from .constants import FILE_TYPES
from .models import File as CSVFile
from users.models import User


class AllCSVFilesView(CSVBaseView):
    """
    Get returns all active CSV files for all file types from the database
    ExportWins
    FDI:
        FDI Monthly
        FDI Daily
    Service Delivery:
        SDI Monthly
        SDI Daily
    Companies
        By UK Region
        By Sector Team
    Contacts
        By UK Region
        By Sector Team
    """
    permission_classes = (IsMIServer, IsMIUser)

    def get(self, request):
        results = []
        for super_type in FILE_TYPES.subsets:
            for sub_type in FILE_TYPES[super_type]:
                files = self.files_list(sub_type.value)
                results = [
                    {
                        'id': csv_file.id,
                        'name': csv_file.name,
                        'report_date': csv_file.report_date,
                        'user_email': csv_file.user.email,
                        'created': csv_file.created
                    }
                    for csv_file in files
                ]
        return Response(sorted(results, key=itemgetter('created'), reverse=True), status=status.HTTP_200_OK)


class CSVBaseView(APIView):
    file_type = None

    @classmethod
    def as_view(cls, **initkwargs):
        # ensure file type is correct and crash early if not
        if not FILE_TYPES.has_constant(initkwargs['file_type']):
            raise ValueError('file_type is not valid')
        return super().as_view(**initkwargs)

    @property
    def file_type_choice(self):
        return FILE_TYPES.for_constant(self.file_type)

    def files_list(self, file_type=None):
        if not file_type:
            file_type = self.file_type_choice.value

        if file_type == 'EXPORT_WINS':  # get latest file per FY
            CSVFile.objects.filter(
                file_type=self.file_type_choice.value, is_active=True)
            pass
        elif file_type == 'FDI_MONTHLY':    # get latest one for each month available for current FY
            pass
        elif file_type == 'FDI_DAILY':  # get latest file
            pass
        elif file_type == 'COMPANIES':  # get a file per region
            pass


class CSVFileView(CSVBaseView):
    """
    Helps storing file details of a file that was uploaded into S3
    Post creates a new entry
    """
    permission_classes = (IsAdminUser, IsAdminServer)

    def post(self, request):
        path = request.data.get('path', None)
        if not path:
            raise ParseError(detail='Mandatory field, path missing')

        name = request.data.get('name', self.file_type_choice.display)
        report_date = request.data.get('report_date', now())

        user = User.objects.get(email=request.user.email)
        CSVFile.objects.create(
            name=name,
            s3_path=path,
            user=user,
            file_type=self.file_type_choice.value,
            report_date=report_date,
        )
        return Response({}, status=status.HTTP_201_CREATED)


class ExportWinsCSVFileView(CSVBaseView):

    permission_classes = (IsAdminUser, IsAdminServer)


class DataTeamCSVFileView(CSVBaseView):

    permission_classes = (IsDataTeamServer,)


class CSVFilesListView(CSVBaseView):
    """
    Get returns all active entries from the database
    """
    permission_classes = (IsMIServer, IsMIUser)

    def get(self, request):
        files = self.files_list()
        results = [
            {
                'id': csv_file.id,
                'name': csv_file.name,
                'report_date': csv_file.report_date,
                'user_email': csv_file.user.email,
                'created': csv_file.created
            }
            for csv_file in files
        ]
        return Response(sorted(results, key=itemgetter('created'), reverse=True), status=status.HTTP_200_OK)


class LatestCSVFileView(CSVBaseView):
    """
    Returns last uploaded file into S3
    """
    permission_classes = (IsMIServer, IsMIUser)

    def get(self, request):
        latest_csv_file = CSVFile.objects.filter(
            file_type=self.file_type_choice.value, is_active=True).latest('created')
        results = {
            'id': latest_csv_file.id,
            'created': latest_csv_file.created
        }
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
