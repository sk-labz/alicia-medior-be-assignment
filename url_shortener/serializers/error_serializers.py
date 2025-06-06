
from rest_framework import serializers

class ErrorSerializer(serializers.Serializer):
    error = serializers.CharField()
    details = serializers.DictField()