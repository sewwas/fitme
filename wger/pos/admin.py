from django.contrib import admin
from .models import POSCategory, POSProduct, POSSale, POSSaleItem, POSInventoryAudit, POSCashDrawerAudit


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
    list_display = ('name', 'sku', 'category', 'price', 'cost_price', 'stock_quantity', 'low_stock_threshold', 'has_audit_discrepancy', 'last_audited_at', 'is_active', 'updated_at')
    list_filter = ('category', 'is_active', 'has_audit_discrepancy')
    search_fields = ('name', 'sku')
    list_editable = ('price', 'stock_quantity', 'is_active')


@admin.register(POSSale)
class POSSaleAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'total_amount', 'payment_method', 'cashier', 'customer_name', 'status', 'created_at')
    list_filter = ('payment_method', 'status', 'created_at')
    search_fields = ('receipt_number', 'customer_name', 'cashier__username')
    readonly_fields = ('receipt_number', 'subtotal', 'discount', 'tax', 'total_amount', 'amount_received', 'change_returned', 'created_at')
    inlines = [POSSaleItemInline]


@admin.register(POSInventoryAudit)
class POSInventoryAuditAdmin(admin.ModelAdmin):
    list_display = ('product', 'auditor', 'expected_quantity', 'counted_quantity', 'discrepancy', 'variance_value', 'reason', 'action_taken', 'audit_date')
    list_filter = ('reason', 'action_taken', 'audit_date')
    search_fields = ('product__name', 'product__sku', 'auditor__username', 'notes')
    readonly_fields = ('audit_date',)


@admin.register(POSCashDrawerAudit)
class POSCashDrawerAuditAdmin(admin.ModelAdmin):
    list_display = ('audit_date', 'cashier', 'opening_float', 'cash_sales_total', 'expected_cash', 'counted_cash', 'discrepancy', 'status')
    list_filter = ('status', 'audit_date')
    search_fields = ('cashier__username', 'notes')
    readonly_fields = ('audit_date',)
