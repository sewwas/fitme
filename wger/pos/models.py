from decimal import Decimal
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class POSCategory(models.Model):
    """Product categories for gym drinks, supplements, snacks, and gear."""
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    icon = models.CharField(max_length=50, default='fa-wine-bottle', help_text="FontAwesome 5 icon class")
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'POS Category'
        verbose_name_plural = 'POS Categories'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class POSProduct(models.Model):
    """Sellable item: gym drink, protein scoop, pre-workout, bar, or gear."""
    category = models.ForeignKey(POSCategory, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=120)
    sku = models.CharField(max_length=40, unique=True, db_index=True, help_text="Stock Keeping Unit / Short Code")
    barcode = models.CharField(max_length=60, blank=True, db_index=True, help_text="UPC/EAN barcode for laser scanner")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Retail Price in LKR")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Cost Price in LKR")
    stock_quantity = models.IntegerField(default=0, help_text="Current units in stock at front desk")
    low_stock_threshold = models.IntegerField(default=5, help_text="Triggers warning badge when stock reaches this level")
    unit = models.CharField(max_length=30, default='unit', help_text="e.g. bottle, scoop, can, bar, piece")
    image_url = models.URLField(max_length=500, blank=True, null=True, help_text="Product picture URL")
    is_active = models.BooleanField(default=True, help_text="Visible in POS catalog")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'POS Product'
        verbose_name_plural = 'POS Products'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} (LKR {self.price:,.2f}) [{self.sku}]"

    @property
    def is_out_of_stock(self):
        return self.stock_quantity <= 0

    @property
    def is_low_stock(self):
        return 0 < self.stock_quantity <= self.low_stock_threshold


class POSSale(models.Model):
    """Recorded POS checkout transaction with receipt numbering and cashier assignment."""
    PAYMENT_CHOICES = [
        ('CASH', 'Cash'),
        ('CARD', 'Credit / Debit Card (POS Machine)'),
        ('KOKO', 'Koko / Mintpay (Pay in 3)'),
        ('BANK_TRANSFER', 'Bank Transfer / QR Pay'),
        ('MEMBER_TAB', 'Member Account Tab'),
    ]

    STATUS_CHOICES = [
        ('COMPLETED', 'Completed'),
        ('REFUNDED', 'Refunded'),
        ('VOID', 'Voided'),
    ]

    receipt_number = models.CharField(max_length=40, unique=True, db_index=True)
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_sales'
    )
    customer_member = models.ForeignKey(
        'membership.MemberProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_purchases'
    )
    customer_name = models.CharField(max_length=100, default='Walk-in Customer')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=30, choices=PAYMENT_CHOICES, default='CASH')
    amount_received = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    change_returned = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = 'POS Sale'
        verbose_name_plural = 'POS Sales'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.receipt_number} — LKR {self.total_amount:,.2f} ({self.payment_method})"

    @classmethod
    def generate_receipt_number(cls):
        today_str = timezone.now().strftime('%Y%m%d')
        random_suffix = uuid.uuid4().hex[:4].upper()
        count_today = cls.objects.filter(created_at__date=timezone.now().date()).count() + 1
        return f"FITME-POS-{today_str}-{count_today:04d}-{random_suffix}"


class POSSaleItem(models.Model):
    """Line item in a POS receipt."""
    sale = models.ForeignKey(POSSale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(POSProduct, on_delete=models.SET_NULL, null=True, blank=True, related_name='sale_items')
    product_name = models.CharField(max_length=120)
    sku = models.CharField(max_length=40, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'POS Sale Item'
        verbose_name_plural = 'POS Sale Items'

    def __str__(self):
        return f"{self.quantity}x {self.product_name} @ {self.unit_price} = {self.total_price}"
