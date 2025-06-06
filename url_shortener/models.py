from django.db import models
from django.core.validators import URLValidator
from django.db.models import F
from django.utils import timezone
import string
import random


class URLMapping(models.Model):
    original_url = models.URLField(
        max_length=2048, 
        validators=[URLValidator()],
        help_text="The original long URL to be shortened"
    )
    
    short_code = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text="The unique short code for the URL"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    access_count = models.PositiveIntegerField(default=0)
    
    
    creator_ip = models.GenericIPAddressField(null=True, blank=True)
    

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['short_code']),
            models.Index(fields=['created_at']),
            models.Index(fields=['access_count']),
        ]
    
    def __str__(self):
        return f"{self.short_code} -> {self.original_url[:50]}..."
    
    def increment_access_count(self):
        URLMapping.objects.filter(pk=self.pk).update(
            access_count=F('access_count') + 1,
            last_accessed=timezone.now()
        )
        self.refresh_from_db()
    
    @staticmethod
    def generate_short_code(length=6):
        chars = string.ascii_letters + string.digits
        
        max_attempts = 100
        for _ in range(max_attempts):
            code = ''.join(random.choices(chars, k=length))
            if not URLMapping.objects.filter(short_code=code).exists():
                return code
        
        return URLMapping.generate_short_code(length + 1)
