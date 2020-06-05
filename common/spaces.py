"""Digital Ocean Spaces interaction"""
import boto3
from django.conf import settings


class SpacesBucket():
    """Interact with Spaces buckets"""
    def __init__(self, space_name="lutris"):
        session = boto3.session.Session()
        self._client = session.client(
            's3',
            region_name='nyc3',
            endpoint_url='https://nyc3.digitaloceanspaces.com',
            aws_access_key_id=settings.SPACES_ACCESS_KEY_ID,
            aws_secret_access_key=settings.SPACES_ACCESS_KEY_SECRET)
        self.space_name = space_name

    def create(self, name="new-space-name"):
        """Create a new Space"""
        self._client.create_bucket(Bucket=name)

    def list_spaces(self):
        """List all buckets on your account"""
        response = self._client.list_buckets()
        return [space['Name'] for space in response['Buckets']]

    def upload(self, local_path, dest_path, public=False):
        """Upload a file to Spaces"""
        self._client.upload_file(local_path, self.space_name, dest_path)
        if public:
            self._client.put_object_acl(
                ACL="public-read",
                Bucket=self.space_name,
                Key=dest_path
            )
