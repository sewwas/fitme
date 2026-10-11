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
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Retail Price in LKR")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Cost Price in LKR")
    stock_quantity = models.IntegerField(default=0, help_text="Current units in stock at front desk")
    low_stock_threshold = models.IntegerField(default=5, help_text="Triggers warning badge when stock reaches this level")
    unit = models.CharField(max_length=30, default='unit', help_text="e.g. bottle, scoop, can, bar, piece")
    image_url = models.URLField(max_length=500, blank=True, null=True, help_text="Product picture URL")
    is_active = models.BooleanField(default=True, help_text="Visible in POS catalog")
    last_audited_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of last physical stock audit")
    has_audit_discrepancy = models.BooleanField(default=False, help_text="Flagged when recent audit found missing stock")
    last_discrepancy_count = models.IntegerField(default=0, help_text="Units missing (negative) or excess (positive) in last audit")
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
        ('KOKO', 'Koko Pay (Buy Now, Pay in 3)'),
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


class POSInventoryAudit(models.Model):
    """
    Physical stock audit and discrepancy tracking log.
    Enables staff/admins to reconcile counted units against system expectation,
    flag missing items, and record financial shrinkage/variance.
    """
    AUDIT_REASONS = [
        ('MISSING_SHRINKAGE', 'Missing / Unexplained Stock Loss'),
        ('COUNT_CORRECTION', 'Physical Count Adjustment'),
        ('DAMAGED_EXPIRED', 'Damaged or Expired Stock'),
        ('THEFT_SUSPECTED', 'Suspected Loss / Theft'),
        ('RESTOCK_DISCREPANCY', 'Supplier Invoice / Restock Discrepancy'),
        ('SAMPLE_PROMO', 'Gym Bar / Coach Demo Sample'),
    ]

    ACTION_CHOICES = [
        ('STOCK_ADJUSTED', 'Stock Level Adjusted'),
        ('FLAGGED_MISSING', 'Flagged as Missing (Pending Review)'),
        ('RECONCILED', 'Reconciled & Closed'),
    ]

    product = models.ForeignKey(POSProduct, on_delete=models.CASCADE, related_name='audit_logs')
    auditor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_audits'
    )
    expected_quantity = models.IntegerField(help_text="Units expected in system before physical count")
    counted_quantity = models.IntegerField(help_text="Physical count verified on shelf")
    discrepancy = models.IntegerField(help_text="counted - expected (negative indicates missing stock)")
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Cost price at audit")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Retail price at audit")
    variance_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Financial impact = discrepancy * unit_cost")
    reason = models.CharField(max_length=40, choices=AUDIT_REASONS, default='COUNT_CORRECTION')
    action_taken = models.CharField(max_length=40, choices=ACTION_CHOICES, default='STOCK_ADJUSTED')
    notes = models.TextField(blank=True, help_text="Notes on where item was searched or audit details")
    audit_date = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = 'POS Inventory Audit'
        verbose_name_plural = 'POS Inventory Audits'
        ordering = ['-audit_date']

    def __str__(self):
        sign = "+" if self.discrepancy > 0 else ""
        return f"Audit {self.product.name}: {sign}{self.discrepancy} units ({self.get_reason_display()})"

    @property
    def is_missing(self):
        return self.discrepancy < 0

    @property
    def missing_units(self):
        return abs(self.discrepancy) if self.discrepancy < 0 else 0


class POSCashDrawerAudit(models.Model):
    """
    Cash drawer balancing and shift reconciliation audit.
    Compares physical cash counted in drawer against recorded cash sales.
    """
    STATUS_CHOICES = [
        ('BALANCED', 'Balanced (Exact Match)'),
        ('SHORTAGE', 'Cash Shortage (Missing Cash)'),
        ('OVERAGE', 'Cash Overage (Excess Cash)'),
    ]

    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cash_drawer_audits'
    )
    opening_float = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Starting cash float in drawer")
    cash_sales_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Recorded POS cash sales")
    expected_cash = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="opening_float + cash_sales_total")
    counted_cash = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Physical cash counted in till")
    discrepancy = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="counted_cash - expected_cash")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BALANCED')
    notes = models.TextField(blank=True)
    audit_date = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = 'POS Cash Drawer Audit'
        verbose_name_plural = 'POS Cash Drawer Audits'
        ordering = ['-audit_date']

    def __str__(self):
        return f"Drawer Audit {self.audit_date.strftime('%Y-%m-%d')} — {self.status} ({self.discrepancy})"
