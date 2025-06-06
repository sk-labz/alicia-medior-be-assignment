from rest_framework import serializers
from ..models import URLMapping

class URLStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = URLMapping
        fields = [
            'short_code', 
            'original_url', 
            'created_at', 
            'last_accessed', 
            'access_count'
        ]
        read_only_fields = fields
