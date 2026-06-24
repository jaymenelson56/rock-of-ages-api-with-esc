from django.http import HttpResponseServerError
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rockapi.models import Rock, RockImage
from rockapi.services.s3_service import S3Service


class RockImageView(ViewSet):
    """Rock Image view set for handling image uploads to S3"""

    @action(detail=False, methods=['post'], url_path='upload-url')
    def get_upload_url(self, request):
        """
        Generate a presigned URL for uploading an image
        
        The frontend calls this endpoint first to get permission to upload.
        
        Expected request body:
        {
            "rock_id": 1,
            "file_name": "my-rock.jpg",
            "file_type": "image/jpeg"
        }
        
        Returns a presigned URL that the frontend uses to upload directly to S3
        """
        try:
            # Extract data from request
            rock_id = request.data.get('rock_id')
            file_name = request.data.get('file_name')
            file_type = request.data.get('file_type')
            
            # Validate that all required fields are present
            if not all([rock_id, file_name, file_type]):
                return Response(
                    {'message': 'rock_id, file_name, and file_type are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify the rock exists and the user owns it
            try:
                rock = Rock.objects.get(pk=rock_id)
                if rock.user.id != request.auth.user.id:
                    return Response(
                        {'message': 'You do not own that rock'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Rock.DoesNotExist:
                return Response(
                    {'message': 'Rock not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Use S3Service to generate the presigned URL
            s3_service = S3Service()
            upload_data = s3_service.generate_presigned_upload_url(
                file_name, file_type, rock_id
            )
            
            # Create a RockImage database record
            # This starts as a placeholder - the image isn't uploaded yet
            # We store the S3 path where the image WILL be uploaded
            rock_image = RockImage()
            rock_image.rock = rock
            rock_image.original_url = f"https://{upload_data['bucket']}.s3.amazonaws.com/{upload_data['file_key']}"
            rock_image.status = 'processing'  # Will be updated when thumbnails are ready
            rock_image.save()
            
            # Return the presigned URL and metadata to the frontend
            return Response({
                'presigned_url': upload_data['presigned_url'],
                'file_key': upload_data['file_key'],
                'image_id': rock_image.id,
                'expires_in': upload_data['expires_in']
            }, status=status.HTTP_201_CREATED)
            
        except Exception as ex:
            return Response(
                {'message': str(ex)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    @action(detail=True, methods=['get'], url_path='download-url')
    def get_download_url(self, request, pk=None):
        """
        Generate a presigned GET URL for a thumbnail image.

        Query params:
            size: small | medium | large (default: medium)

        Returns a short-lived URL the client can use to fetch the image directly from S3.
        """
        try:
            rock_image = RockImage.objects.get(pk=pk)

            size = request.query_params.get('size', 'medium')
            url_map = {
                'small': rock_image.thumbnail_small_url,
                'medium': rock_image.thumbnail_medium_url,
                'large': rock_image.thumbnail_large_url,
            }

            if size not in url_map:
                return Response(
                    {'message': 'size must be small, medium, or large'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            stored_url = url_map[size]
            if not stored_url:
                return Response(
                    {'message': f'{size} thumbnail is not ready yet'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Extract the S3 key from the stored URL
            # URL format: https://<bucket>.s3.amazonaws.com/<file_key>
            file_key = stored_url.split('.amazonaws.com/', 1)[-1]

            s3_service = S3Service()
            presigned_url = s3_service.generate_presigned_download_url(file_key)

            return Response({'presigned_url': presigned_url}, status=status.HTTP_200_OK)

        except RockImage.DoesNotExist:
            return Response(
                {'message': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as ex:
            return Response(
                {'message': str(ex)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    @action(detail=True, methods=['post'], url_path='confirm-upload')
    def confirm_upload(self, request, pk=None):
        """
        Confirm that an upload was successful
        
        The frontend calls this after successfully uploading to S3.
        Optional - mainly used to update metadata like file size.
        
        Expected request body:
        {
            "file_size": 2048000
        }
        """
        try:
            rock_image = RockImage.objects.get(pk=pk)
            
            # Verify the user owns this rock
            if rock_image.rock.user.id != request.auth.user.id:
                return Response(
                    {'message': 'You do not own that rock'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Update with any additional metadata from frontend
            file_size = request.data.get('file_size')
            if file_size:
                rock_image.file_size = file_size
                rock_image.save()
            
            serializer = RockImageSerializer(rock_image)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except RockImage.DoesNotExist:
            return Response(
                {'message': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as ex:
            return Response(
                {'message': str(ex)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, pk=None):
        """
        Get a single image by ID
        
        The frontend calls this to check if thumbnails are ready.
        Used for polling after upload.
        """
        try:
            rock_image = RockImage.objects.get(pk=pk)
            serializer = RockImageSerializer(rock_image)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except RockImage.DoesNotExist:
            return Response(
                {'message': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def list(self, request):
        """
        Get all images, optionally filtered by rock_id
        
        Examples:
        GET /rock-images              -> All images for authenticated user's rocks
        GET /rock-images?rock_id=5    -> All images for rock #5
        """
        rock_id = request.query_params.get('rock_id')
        
        try:
            if rock_id:
                # Get images for a specific rock
                images = RockImage.objects.filter(rock_id=rock_id)
            else:
                # Get all images for user's rocks
                images = RockImage.objects.filter(rock__user=request.auth.user)
            
            serializer = RockImageSerializer(images, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Exception as ex:
            return HttpResponseServerError(ex)

    def destroy(self, request, pk=None):
        """
        Delete an image
        
        Only deletes the database record - you'd need to separately
        delete the actual files from S3 (Lambda or manual cleanup)
        """
        try:
            rock_image = RockImage.objects.get(pk=pk)
            
            # Verify the user owns this rock
            if rock_image.rock.user.id != request.auth.user.id:
                return Response(
                    {'message': 'You do not own that rock'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            rock_image.delete()
            return Response(None, status=status.HTTP_204_NO_CONTENT)
            
        except RockImage.DoesNotExist:
            return Response(
                {'message': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as ex:
            return Response(
                {'message': str(ex)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RockImageSerializer(serializers.ModelSerializer):
    """JSON serializer for RockImage"""
    
    class Meta:
        model = RockImage
        fields = ('id', 'rock', 'original_url', 'thumbnail_small_url', 
                  'thumbnail_medium_url', 'thumbnail_large_url', 
                  'uploaded_at', 'file_size', 'status')
        read_only_fields = ('id', 'uploaded_at')