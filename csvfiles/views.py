from operator import itemgetter
from urllib.parse import urlparse

import boto3

from django.conf import settings
from django.utils.timezone import now

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

from csvfiles.constants import FILE_TYPES
from csvfiles.models import File as CSVFile
from csvfiles.serializers import FileSerializer, ExportWinsFileSerializer


class CSVBaseView(APIView):
    file_type = None
    metadata_keys = list()
    serializer_class = FileSerializer

    @classmethod
    def as_view(cls, **initkwargs):
        # ensure file type is correct and crash early if not
        if not FILE_TYPES.has_constant(initkwargs['file_type']):
            raise ValueError('file_type is not valid')
        return super().as_view(**initkwargs)

    @property
    def file_type_choice(self):
        return FILE_TYPES.for_constant(self.file_type)


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
        return {
            'user': self.request.user.id,
        }

    def default_data(self):
        """
        :return: data that the user is allowed to override
        """
        return {
            'file_type': self.file_type,
            'name': self.file_type_choice.display,
            'report_date': now()
        }

    def get_metadata(self, data):
        metadata = {}
        for key in self.metadata_keys:
            metadata[key] = data.get(key)
        return metadata

    def submitted_data(self):
        """
        :return: data that may be provided by request
        """
        return {
            's3_path': self.request.data.get('path'),
            'metadata': self.get_metadata(self.request.data)
        }

    def get_merged_data(self):
        return {
            **self.default_data(),
            **self.submitted_data(),
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


class CSVFilesListView(CSVBaseView):
    """
    Get returns all active entries from the database
    """
    permission_classes = (IsMIServer, IsMIUser)

    def get(self, request):
        files = CSVFile.objects.filter(
            file_type=self.file_type_choice.value, is_active=True)
        results = self.serializer_class(instance=files, many=True).data
        return Response(sorted(results, key=itemgetter('created'), reverse=True), status=status.HTTP_200_OK)


class LatestCSVFileView(CSVBaseView):
    """
    Returns last uploaded file into S3
    """
    permission_classes = (IsMIServer, IsMIUser)

    def get(self, request):
        latest_csv_file = CSVFile.objects.filter(
            file_type=FILE_TYPES.EXPORT_WINS, is_active=True).latest('created')
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
