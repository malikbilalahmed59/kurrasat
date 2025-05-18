from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = settings.AWS_S3_FILE_OVERWRITE
    default_acl = settings.AWS_DEFAULT_ACL


class CSVStorage(S3Boto3Storage):
    location = 'csv'
    file_overwrite = settings.AWS_S3_FILE_OVERWRITE
    default_acl = settings.AWS_DEFAULT_ACL


class RfpDocumentStorage(S3Boto3Storage):
    location = 'rfp_documents'
    file_overwrite = False
    default_acl = settings.AWS_DEFAULT_ACL


class ImprovedRfpStorage(S3Boto3Storage):
    location = 'improved_rfps'
    file_overwrite = False
    default_acl = settings.AWS_DEFAULT_ACL


class OriginalRfpStorage(S3Boto3Storage):
    location = 'original_rfps'
    file_overwrite = False
    default_acl = settings.AWS_DEFAULT_ACL