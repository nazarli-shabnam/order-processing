from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user_id', 'status', 'total_amount', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_id', 'user_id', 'user_email']
    inlines = [OrderItemInline]
    readonly_fields = ['order_id', 'created_at', 'updated_at']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_id', 'quantity', 'price']
    list_filter = ['order__status']

