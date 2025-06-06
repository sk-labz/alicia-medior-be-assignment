from django.urls import path
from . import views

urlpatterns = [
    path('shorten/', views.shorten_url, name='shorten_url'),
    path('short/<str:short_code>/', views.redirect_url, name='redirect_url'),
]