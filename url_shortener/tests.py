from django.test import TestCase
from rest_framework.test import APITestCase
from .models import URLMapping
from .serializers import URLShortenSerializer


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
