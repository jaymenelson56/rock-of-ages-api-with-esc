import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import uuid


class S3Service:
    """
    Service class for interacting with AWS S3
    Handles presigned URL generation for secure uploads
    boto3 automatically picks up credentials from the ECS task role
    """
    
    def __init__(self):
        """
        Initialize the S3 client
        boto3 automatically picks up credentials from the ECS task role
        We only need to specify the region
        """
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            endpoint_url=f"https://s3.{settings.AWS_REGION}.amazonaws.com"
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def generate_presigned_upload_url(self, file_name, file_type, rock_id):
        """
        Generate a presigned URL for uploading a file to S3
        
        This URL allows the frontend to upload directly to S3 without
        sending the file through Django, which is faster and more efficient.
        
        Args:
            file_name: Original filename (e.g., "my-rock.jpg")
            file_type: MIME type (e.g., "image/jpeg")
            rock_id: ID of the rock this image belongs to
            
        Returns:
            dict: {
                'presigned_url': The URL to PUT the file to,
                'file_key': The S3 object key where file will be stored,
                'bucket': The bucket name,
                'expires_in': How long the URL is valid (seconds)
            }
        """
        try:
            # Extract file extension from filename
            # "my-rock.jpg" -> "jpg"
            file_extension = file_name.split('.')[-1]
            
            # Generate a unique filename to prevent collisions
            # uuid.uuid4() creates a random unique ID like "a3f5b2c1-..."
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Create the S3 key (path) where file will be stored
            # Example: "rocks/5/original/a3f5b2c1-xxxx-xxxx.jpg"
            # This organizes files by rock_id and type (original vs thumbnails)
            file_key = f"rocks/{rock_id}/original/{unique_filename}"
            
            # Generate the presigned URL
            # This creates a temporary URL that allows PUT requests
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',  # The S3 operation to allow (upload)
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key,
                    'ContentType': file_type,  # Ensures correct MIME type
                },
                ExpiresIn=3600  # URL expires in 1 hour (3600 seconds)
            )
            
            # Return all the information the frontend needs
            return {
                'presigned_url': presigned_url,
                'file_key': file_key,
                'bucket': self.bucket_name,
                'expires_in': 3600
            }
            
        except ClientError as e:
            # ClientError is thrown by boto3 for AWS-specific errors
            # (like invalid credentials, bucket doesn't exist, etc.)
            raise Exception(f"Error generating presigned URL: {str(e)}")

    def generate_presigned_download_url(self, file_key, expires_in=3600):
        """
        Generate a presigned URL for downloading a file from S3
        
        This is optional - you'd use this if your S3 bucket is private.
        If your bucket is public, you can just use the regular S3 URL.
        
        Args:
            file_key: The S3 object key (e.g., "rocks/5/thumbnails/medium/abc.jpg")
            expires_in: How long the URL should be valid (seconds)
            
        Returns:
            str: Presigned download URL
        """
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',  # The S3 operation to allow (download)
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key,
                },
                ExpiresIn=expires_in
            )
            return presigned_url
            
        except ClientError as e:
            raise Exception(f"Error generating presigned download URL: {str(e)}")