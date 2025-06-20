from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404, HttpResponseNotFound, HttpResponseServerError
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.db import transaction
import logging
from django.utils import timezone

from .models import URLMapping
from .serializers import URLShortenSerializer, URLShortenResponseSerializer, URLStatsSerializer


logger = logging.getLogger(__name__)


class URLShortenerRateThrottle(AnonRateThrottle):
    scope = 'url_shortener'


class URLAccessRateThrottle(AnonRateThrottle):
    scope = 'url_access'


@api_view(['POST'])
@throttle_classes([URLShortenerRateThrottle])
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


@cache_page(60 * 15)  # Cache for 15 minutes
@vary_on_headers('User-Agent')
def redirect_url(request, short_code):
    try:
        url_mapping = get_object_or_404(URLMapping, short_code=short_code)
        
        # Increment access count
        url_mapping.increment_access_count()
        
        logger.info(f"Redirecting {short_code} to {url_mapping.original_url}")
        
        return redirect(url_mapping.original_url)
        
    except Http404:
        logger.warning(f"Short code not found: {short_code}")
        return HttpResponseNotFound(f"Short URL '{short_code}' not found")
    
    except Exception as e:
        logger.error(f"Unexpected error in redirect_url: {str(e)}")
        return HttpResponseServerError("An unexpected error occurred")


@api_view(['GET'])
@cache_page(60 * 5)  # Cache stats for 5 minutes
def url_stats(request, short_code):
    try:
        url_mapping = get_object_or_404(URLMapping, short_code=short_code)
        
        serializer = URLStatsSerializer(url_mapping)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Http404:
        logger.warning(f"Stats requested for non-existent short code: {short_code}")
        return Response(
            {
                'error': 'Short URL not found',
                'details': {'short_code': f"'{short_code}' does not exist"}
            },
            status=status.HTTP_404_NOT_FOUND
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in url_stats: {str(e)}")
        return Response(
            {
                'error': 'Internal server error',
                'details': {'message': 'An unexpected error occurred'}
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def health_check(request):
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0'
    })


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
