from django.contrib import admin
from .models import POSCategory, POSProduct, POSSale, POSSaleItem


class POSSaleItemInline(admin.TabularInline):
    model = POSSaleItem
    extra = 0
    readonly_fields = ('product_name', 'sku', 'unit_price', 'quantity', 'total_price')


@admin.register(POSCategory)
class POSCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'display_order', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('display_order', 'name')


@admin.register(POSProduct)
class POSProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'price', 'cost_price', 'stock_quantity', 'low_stock_threshold', 'is_active', 'updated_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'sku', 'barcode')
    list_editable = ('price', 'stock_quantity', 'is_active')


@admin.register(POSSale)
class POSSaleAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'total_amount', 'payment_method', 'cashier', 'customer_name', 'status', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('receipt_number', 'customer_name', 'cashier__username')
    readonly_fields = ('receipt_number', 'subtotal', 'discount', 'tax', 'total_amount', 'amount_received', 'change_returned', 'created_at')
    inlines = [POSSaleItemInline]
