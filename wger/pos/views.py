import json
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, F
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from wger.membership.models import MemberProfile
from .models import POSCategory, POSProduct, POSSale, POSSaleItem


def is_admin_user(user):
    """Check if the user is a superuser or belongs to the admin/super_admin role."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    user_groups = set(user.groups.values_list('name', flat=True))
    return bool(user_groups.intersection({'super_admin', 'admin'}))


@login_required
def pos_register_view(request):
    """
    Main Point of Sale (POS) interface for Gym Drinks, Supplements, Snacks & Gear.
    Designed for Front Desk Cashier and Super Admin.
    """
    today = timezone.now().date()
    categories = POSCategory.objects.all().order_by('display_order', 'name')
    products = POSProduct.objects.filter(is_active=True).select_related('category').order_by('category__display_order', 'name')
    members = MemberProfile.objects.select_related('user').order_by('user__first_name', 'user__username')[:200]
    
    today_sales = POSSale.objects.filter(created_at__date=today, status='COMPLETED')
    today_revenue = today_sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    today_count = today_sales.count()
    
    low_stock_products = POSProduct.objects.filter(
        is_active=True,
        stock_quantity__lte=F('low_stock_threshold')
    )

    recent_sales = POSSale.objects.select_related('cashier', 'customer_member').order_by('-created_at')[:15]

    context = {
        'page_title': 'Point of Sale (POS) — Fit Me Gym Bar',
        'categories': categories,
        'products': products,
        'members': members,
        'is_admin': is_admin_user(request.user),
        'today_revenue': today_revenue,
        'today_count': today_count,
        'low_stock_count': low_stock_products.count(),
        'low_stock_products': low_stock_products[:10],
        'recent_sales': recent_sales,
        'club_info': {
            'name': 'Fit Me Fitness Club',
            'tagline': 'Train with Purpose & Move with Confidence',
            'address': 'New Town, Elpitiya Road, Pitigala, 80420',
            'phone': '070 762 7878',
        }
    }
    return render(request, 'pos/register.html', context)


@login_required
@require_POST
def pos_checkout_api(request):
    """
    Process sale checkout transaction atomically.
    Deducts inventory stock, creates POSSale, records items, and returns receipt.
    """
    try:
        data = json.loads(request.body)
    except Exception as e:
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid JSON: ' + str(e)}), content_type='application/json')

    items_data = data.get('items', [])
    if not items_data:
        return JsonResponse({'success': False, 'error': 'Cart is empty. Select products first.'}, status=400)

    payment_method = data.get('payment_method', 'CASH')
    discount = Decimal(str(data.get('discount', 0) or 0))
    tax = Decimal(str(data.get('tax', 0) or 0))
    amount_received = Decimal(str(data.get('amount_received', 0) or 0))
    customer_name = (data.get('customer_name') or 'Walk-in Customer').strip()
    member_id = data.get('member_id')
    notes = data.get('notes', '').strip()

    customer_member = None
    if member_id:
        try:
            customer_member = MemberProfile.objects.select_related('user').get(id=member_id)
            if not data.get('customer_name'):
                customer_name = customer_member.user.get_full_name() or customer_member.user.username
        except MemberProfile.DoesNotExist:
            pass

    with transaction.atomic():
        # Validate items and calculate subtotal
        subtotal = Decimal('0.00')
        line_items_to_create = []

        for item in items_data:
            prod_id = item.get('product_id')
            qty = int(item.get('quantity', 1))
            if qty <= 0:
                continue

            try:
                # Lock row for update
                product = POSProduct.objects.select_for_update().get(id=prod_id)
            except POSProduct.DoesNotExist:
                return JsonResponse({'success': False, 'error': f"Product ID {prod_id} not found."}, status=404)

            # Check stock
            if product.stock_quantity < qty:
                return JsonResponse({
                    'success': False,
                    'error': f"Insufficient stock for '{product.name}'. Available: {product.stock_quantity}, Requested: {qty}"
                }, status=400)

            unit_price = product.price
            line_total = unit_price * qty
            subtotal += line_total

            # Deduct inventory stock
            product.stock_quantity -= qty
            product.save(update_fields=['stock_quantity', 'updated_at'])

            line_items_to_create.append({
                'product': product,
                'name': product.name,
                'sku': product.sku,
                'unit_price': unit_price,
                'quantity': qty,
                'total_price': line_total,
            })

        total_amount = max(Decimal('0.00'), subtotal - discount + tax)

        change_returned = Decimal('0.00')
        if payment_method == 'CASH':
            if amount_received > 0 and amount_received >= total_amount:
                change_returned = amount_received - total_amount
            elif amount_received == 0:
                amount_received = total_amount

        receipt_number = POSSale.generate_receipt_number()

        sale = POSSale.objects.create(
            receipt_number=receipt_number,
            cashier=request.user,
            customer_member=customer_member,
            customer_name=customer_name,
            subtotal=subtotal,
            discount=discount,
            tax=tax,
            total_amount=total_amount,
            payment_method=payment_method,
            amount_received=amount_received,
            change_returned=change_returned,
            status='COMPLETED',
            notes=notes,
            created_at=timezone.now(),
        )

        for line in line_items_to_create:
            POSSaleItem.objects.create(
                sale=sale,
                product=line['product'],
                product_name=line['name'],
                sku=line['sku'],
                unit_price=line['unit_price'],
                quantity=line['quantity'],
                total_price=line['total_price'],
            )

    receipt_items = [
        {
            'name': l['name'],
            'quantity': l['quantity'],
            'unit_price': float(l['unit_price']),
            'total_price': float(l['total_price']),
        }
        for l in line_items_to_create
    ]

    return JsonResponse({
        'success': True,
        'message': f"Sale {receipt_number} completed successfully!",
        'sale': {
            'id': sale.id,
            'receipt_number': sale.receipt_number,
            'cashier': sale.cashier.get_full_name() or sale.cashier.username if sale.cashier else 'Staff',
            'customer_name': sale.customer_name,
            'subtotal': float(sale.subtotal),
            'discount': float(sale.discount),
            'total_amount': float(sale.total_amount),
            'payment_method': sale.get_payment_method_display(),
            'amount_received': float(sale.amount_received),
            'change_returned': float(sale.change_returned),
            'date': sale.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'items': receipt_items,
        }
    })


@login_required
@require_POST
def pos_add_product_api(request):
    """
    Allow ONLY Admin / Superuser to add a new product directly from the POS interface.
    """
    if not is_admin_user(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Permission denied: Only Gym Administrators have permission to add new products to inventory.'
        }, status=403)

    try:
        data = json.loads(request.body)
    except Exception as e:
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid JSON: ' + str(e)}), content_type='application/json')

    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'success': False, 'error': 'Product name is required.'}, status=400)

    category_id = data.get('category_id')
    new_category_name = data.get('new_category_name', '').strip()

    category = None
    if category_id:
        try:
            category = POSCategory.objects.get(id=category_id)
        except POSCategory.DoesNotExist:
            pass

    if not category and new_category_name:
        import re
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', new_category_name.lower()).strip('-')
        category, _ = POSCategory.objects.get_or_create(
            slug=slug,
            defaults={'name': new_category_name, 'icon': 'fa-box'}
        )

    if not category:
        # Default category
        category, _ = POSCategory.objects.get_or_create(
            slug='general',
            defaults={'name': 'General Gym Items', 'icon': 'fa-box'}
        )

    sku = data.get('sku', '').strip()
    if not sku:
        import uuid
        sku = 'FIT-' + uuid.uuid4().hex[:6].upper()

    # Check unique sku
    if POSProduct.objects.filter(sku=sku).exists():
        import uuid
        sku = f"{sku}-{uuid.uuid4().hex[:4].upper()}"

    barcode = data.get('barcode', '').strip()
    price = Decimal(str(data.get('price', 0) or 0))
    cost_price = Decimal(str(data.get('cost_price', 0) or 0))
    stock_quantity = int(data.get('stock_quantity', 0) or 0)
    low_stock_threshold = int(data.get('low_stock_threshold', 5) or 5)
    unit = data.get('unit', 'unit').strip()

    prod = POSProduct.objects.create(
        category=category,
        name=name,
        sku=sku,
        barcode=barcode,
        price=price,
        cost_price=cost_price,
        stock_quantity=stock_quantity,
        low_stock_threshold=low_stock_threshold,
        unit=unit,
        is_active=True,
    )

    return JsonResponse({
        'success': True,
        'message': f"Product '{prod.name}' added to POS inventory!",
        'product': {
            'id': prod.id,
            'name': prod.name,
            'sku': prod.sku,
            'barcode': prod.barcode,
            'price': float(prod.price),
            'stock_quantity': prod.stock_quantity,
            'category_id': category.id,
            'category_name': category.name,
            'unit': prod.unit,
        }
    })


@login_required
@require_POST
def pos_restock_api(request, product_id):
    """
    Quickly restock inventory quantity for a product.
    """
    product = get_object_or_404(POSProduct, id=product_id)
    try:
        data = json.loads(request.body)
    except Exception as e:
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid JSON: ' + str(e)}), content_type='application/json')

    added_qty = int(data.get('added_quantity', 0) or 0)
    if added_qty == 0:
        return JsonResponse({'success': False, 'error': 'Specify quantity to add.'}, status=400)

    product.stock_quantity += added_qty
    product.save(update_fields=['stock_quantity', 'updated_at'])

    return JsonResponse({
        'success': True,
        'message': f"Restocked {added_qty} units of '{product.name}'. New stock: {product.stock_quantity}",
        'new_stock': product.stock_quantity
    })


@login_required
def pos_thermal_receipt_view(request, receipt_number):
    """
    Renders an 80mm thermal printer receipt page for a POS sale.
    """
    sale = get_object_or_404(POSSale.objects.select_related('cashier', 'customer_member').prefetch_related('items'), receipt_number=receipt_number)
    context = {
        'sale': sale,
        'club_info': {
            'name': 'Fit Me Fitness Club',
            'tagline': 'Train with Purpose & Move with Confidence',
            'address': 'New Town, Elpitiya Road, Pitigala, 80420',
            'phone': '070 762 7878',
        }
    }
    return render(request, 'pos/receipt_thermal.html', context)
