"""
URL configuration for orders app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.create_order, name='create_order'),
    path('orders/<uuid:order_id>/', views.get_order_status, name='get_order_status'),
]

