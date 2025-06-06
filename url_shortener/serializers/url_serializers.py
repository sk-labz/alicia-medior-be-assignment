from rest_framework import serializers
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import re
from ..models import URLMapping



class URLShortenSerializer(serializers.Serializer):
    url = serializers.URLField(
        max_length=2048,
        help_text="The URL to be shortened",
        error_messages={
            'invalid': 'Please provide a valid URL (including http:// or https://)',
            'max_length': 'URL is too long (maximum 2048 characters)'
        }
    )
    
    def validate_url(self, value):
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError(
                "URL must start with http:// or https://"
            )
        
        validator = URLValidator()
        try:
            validator(value)
        except ValidationError:
            raise serializers.ValidationError("Invalid URL format")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'localhost',
            r'127\.0\.0\.1',
            r'192\.168\.',
            r'10\.',
            r'172\.(1[6-9]|2[0-9]|3[0-1])\.',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise serializers.ValidationError(
                    "Cannot shorten local or private network URLs"
                )
        
        return value

class URLShortenResponseSerializer(serializers.ModelSerializer):
    short_url = serializers.SerializerMethodField()
    
    class Meta:
        model = URLMapping
        fields = ['short_code', 'short_url', 'original_url', 'created_at']
        read_only_fields = ['short_code', 'created_at']
    
    def get_short_url(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/short/{obj.short_code}/')
        return f'/short/{obj.short_code}/'
