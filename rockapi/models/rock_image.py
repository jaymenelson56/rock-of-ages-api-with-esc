from django.db import models
from .rock import Rock


class RockImage(models.Model):
    # Links this image to a specific rock
    # If the rock gets deleted, all its images get deleted too (CASCADE)
    rock = models.ForeignKey(Rock, on_delete=models.CASCADE, related_name='images')
    
    # The S3 URL where the full-size original image is stored
    original_url = models.URLField(max_length=500)
    
    # The S3 URL where the thumbnail is stored
    # null=True, blank=True means this can be empty initially (while Lambda is processing)
    thumbnail_small_url = models.URLField(max_length=500, null=True, blank=True)
    thumbnail_medium_url = models.URLField(max_length=500, null=True, blank=True)
    thumbnail_large_url = models.URLField(max_length=500, null=True, blank=True)
    
    # Automatically records when the image was uploaded
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Size of the file in bytes (optional, can be set later)
    file_size = models.IntegerField(null=True, blank=True)
    
    # Track if thumbnails are ready
    # Default is 'processing' - Lambda will eventually update this to 'ready'
    status = models.CharField(max_length=20, default='processing')
    
    class Meta:
        # When we query images, show newest first
        ordering = ['-uploaded_at']