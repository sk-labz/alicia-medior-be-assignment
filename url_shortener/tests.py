from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import URLMapping
from .serializers import URLShortenSerializer
import json


class URLMappingModelTests(TestCase):
    def setUp(self):
        self.test_url = "https://www.example.com/very/long/url"
        
    def test_url_mapping_creation(self):
        mapping = URLMapping.objects.create(
            original_url=self.test_url,
            short_code="test123"
        )
        
        self.assertEqual(mapping.original_url, self.test_url)
        self.assertEqual(mapping.short_code, "test123")
        self.assertIsNotNone(mapping.created_at)
    
    def test_generate_short_code_unique(self):
        code1 = URLMapping.generate_short_code()
        code2 = URLMapping.generate_short_code()
        
        self.assertNotEqual(code1, code2)
        self.assertEqual(len(code1), 6)
        self.assertTrue(code1.isalnum())
    
    def test_string_representation(self):
        mapping = URLMapping.objects.create(
            original_url=self.test_url,
            short_code="test123"
        )
        
        expected = f"test123 -> {self.test_url[:50]}..."
        self.assertEqual(str(mapping), expected)


class URLShortenSerializerTests(TestCase):
    def test_valid_url_serialization(self):
        data = {"url": "https://www.example.com"}
        serializer = URLShortenSerializer(data=data)
        
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['url'], data['url'])
    
    def test_invalid_url_format(self):
        data = {"url": "not-a-valid-url"}
        serializer = URLShortenSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('url', serializer.errors)
    
    def test_url_without_scheme(self):
        data = {"url": "www.example.com"}
        serializer = URLShortenSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('url', serializer.errors)

    def test_localhost_url_rejection(self):
        data = {"url": "http://localhost:8000"}
        serializer = URLShortenSerializer(data=data)
        
        self.assertFalse(serializer.is_valid())
        self.assertIn('url', serializer.errors)
    

class URLShortenerAPITests(APITestCase):
    def setUp(self):
        self.client = Client()
        self.shorten_url = reverse('shorten_url')
        self.test_url = "https://www.example.com/test"
    
    def test_shorten_url_success(self):
        data = {"url": self.test_url}
        response = self.client.post(
            self.shorten_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertIn('short_code', response_data)
        self.assertIn('short_url', response_data)
        self.assertEqual(response_data['original_url'], self.test_url)
    
    def test_shorten_url_duplicate(self):
        # Create first mapping
        data = {"url": self.test_url}
        response1 = self.client.post(
            self.shorten_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Try to create same URL again
        response2 = self.client.post(
            self.shorten_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.json()['short_code'], response2.json()['short_code'])
    
    def test_shorten_invalid_url(self):
        data = {"url": "not-a-valid-url"}
        response = self.client.post(
            self.shorten_url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.json())


    def test_redirect_url_success(self):
        # Create a URL mapping first
        mapping = URLMapping.objects.create(
            original_url=self.test_url,
            short_code="test123"
        )
        

        # Test redirection
        redirect_url = reverse('redirect_url', kwargs={'short_code': 'test123'})
        response = self.client.get(redirect_url)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.test_url)
    

    def test_redirect_nonexistent_code(self):
        redirect_url = reverse('redirect_url', kwargs={'short_code': 'nonexistent'})
        response = self.client.get(redirect_url)
        
        self.assertEqual(response.status_code, 404)

    def test_url_stats_success(self):
        # Create a URL mapping first
        mapping = URLMapping.objects.create(
            original_url=self.test_url,
            short_code="test123",
            access_count=5
        )
        
        # Test stats endpoint
        stats_url = reverse('url_stats', kwargs={'short_code': 'test123'})
        response = self.client.get(stats_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['short_code'], 'test123')
        self.assertEqual(response_data['original_url'], self.test_url)
        self.assertEqual(response_data['access_count'], 5)
    
    def test_url_stats_nonexistent(self):
        stats_url = reverse('url_stats', kwargs={'short_code': 'nonexistent'})
        response = self.client.get(stats_url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_health_check(self):
        health_url = reverse('health_check')
        response = self.client.get(health_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['status'], 'healthy')
        self.assertIn('timestamp', response_data)
        self.assertIn('version', response_data)
    