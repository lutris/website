"""Digital Ocean Spaces interaction"""
import boto3
from django.conf import settings


class SpacesBucket():
    """Interact with Spaces buckets"""
    def __init__(self):
        session = boto3.session.Session()
        self._client = session.client('s3',
                                      region_name='nyc3',
                                      endpoint_url='https://nyc3.digitaloceanspaces.com',
                                      aws_access_key_id=settings.SPACES_ACCESS_KEY_ID,
                                      aws_secret_access_key=settings.SPACES_ACCESS_KEY_SECRET)

    def create(self, name="new-space-name"):
        """Create a new Space"""
        self._client.create_bucket(Bucket=name)

    def list(self):
        """List all buckets on your account"""
        response = self._client.list_buckets()
        spaces = [space['Name'] for space in response['Buckets']]
        print("Spaces List: %s" % spaces)
