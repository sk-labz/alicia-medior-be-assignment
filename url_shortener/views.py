from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404, HttpResponseNotFound, HttpResponseServerError
from django.db import transaction
import logging

from .models import URLMapping
from .serializers import URLShortenSerializer, URLShortenResponseSerializer


logger = logging.getLogger(__name__)


@api_view(['POST'])
def shorten_url(request):
    try:
        serializer = URLShortenSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid URL shortening request: {serializer.errors}")
            return Response(
                {
                    'error': 'Validation failed',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        original_url = validated_data['url']
        
        # Check if URL already exists
        existing_mapping = URLMapping.objects.filter(
            original_url=original_url
        ).first()
        
        if existing_mapping:
            logger.info(f"Returning existing mapping for URL: {original_url}")
            response_serializer = URLShortenResponseSerializer(
                existing_mapping, 
                context={'request': request}
            )
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        # Create new URL mapping
        with transaction.atomic():
            short_code = URLMapping.generate_short_code()
            
            url_mapping = URLMapping.objects.create(
                original_url=original_url,
                short_code=short_code
            )
            
            logger.info(f"Created new URL mapping: {short_code} -> {original_url}")
            
            response_serializer = URLShortenResponseSerializer(
                url_mapping,
                context={'request': request}
            )
            
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
    
    except Exception as e:
        logger.error(f"Unexpected error in shorten_url: {str(e)}")
        return Response(
            {
                'error': 'Internal server error',
                'details': {'message': 'An unexpected error occurred'}
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def redirect_url(request, short_code):
    try:
        url_mapping = get_object_or_404(URLMapping, short_code=short_code)
        
        logger.info(f"Redirecting {short_code} to {url_mapping.original_url}")
        
        return redirect(url_mapping.original_url)
        
    except Http404:
        logger.warning(f"Short code not found: {short_code}")
        return HttpResponseNotFound(f"Short URL '{short_code}' not found")
    
    except Exception as e:
        logger.error(f"Unexpected error in redirect_url: {str(e)}")
        return HttpResponseServerError("An unexpected error occurred")
