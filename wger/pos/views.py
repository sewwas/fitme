import json
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from wger.membership.models import MemberProfile
from .models import POSCategory, POSProduct, POSSale, POSSaleItem, POSInventoryAudit, POSCashDrawerAudit


def is_super_admin_user(user):
    """Check if the user is a superuser or belongs strictly to the super_admin role."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name='super_admin').exists()


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
    is_super_admin = request.user.is_superuser or request.user.groups.filter(name='super_admin').exists()
    members_qs = MemberProfile.objects.exclude(user__userprofile__is_temporary=True).select_related('user')
    if not is_super_admin:
        members_qs = members_qs.exclude(user__is_superuser=True).exclude(user__groups__name='super_admin')
    members = members_qs.order_by('user__first_name', 'user__username')[:200]
    
    today_sales = POSSale.objects.filter(created_at__date=today, status='COMPLETED')
    today_revenue = today_sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    today_count = today_sales.count()
    
    low_stock_products = POSProduct.objects.filter(
        is_active=True,
        stock_quantity__lte=F('low_stock_threshold')
    )

    # Missing items and audit metrics
    missing_stock_products = POSProduct.objects.filter(
        is_active=True,
        has_audit_discrepancy=True
    ).order_by('last_discrepancy_count', 'name')

    pos_val_aggs = POSProduct.objects.filter(is_active=True).aggregate(
        cost_val=Sum(ExpressionWrapper(F('cost_price') * F('stock_quantity'), output_field=DecimalField(max_digits=12, decimal_places=2))),
        retail_val=Sum(ExpressionWrapper(F('price') * F('stock_quantity'), output_field=DecimalField(max_digits=12, decimal_places=2))),
        total_units=Sum('stock_quantity')
    )
    total_cost_valuation = pos_val_aggs['cost_val'] or Decimal('0.00')
    total_retail_valuation = pos_val_aggs['retail_val'] or Decimal('0.00')
    total_units = pos_val_aggs['total_units'] or 0

    recent_sales = POSSale.objects.select_related('cashier', 'customer_member').order_by('-created_at')[:15]
    recent_audits = POSInventoryAudit.objects.select_related('product', 'auditor').order_by('-audit_date')[:15]
    recent_drawer_audits = POSCashDrawerAudit.objects.select_related('cashier').order_by('-audit_date')[:5]

    context = {
        'page_title': 'Point of Sale (POS) — Fit Me Gym Bar',
        'categories': categories,
        'products': products,
        'members': members,
        'is_admin': is_admin_user(request.user),
        'is_super_admin': is_super_admin_user(request.user),
        'today_revenue': today_revenue,
        'today_count': today_count,
        'low_stock_count': low_stock_products.count(),
        'low_stock_products': low_stock_products[:10],
        'missing_stock_count': missing_stock_products.count(),
        'missing_stock_products': missing_stock_products[:15],
        'total_cost_valuation': total_cost_valuation,
        'total_retail_valuation': total_retail_valuation,
        'total_units': total_units,
        'recent_sales': recent_sales,
        'recent_audits': recent_audits,
        'recent_drawer_audits': recent_drawer_audits,
        'audit_reasons': POSInventoryAudit.AUDIT_REASONS,
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

    price = Decimal(str(data.get('price', 0) or 0))
    cost_price = Decimal(str(data.get('cost_price', 0) or 0))
    stock_quantity = int(data.get('stock_quantity', 0) or 0)
    low_stock_threshold = int(data.get('low_stock_threshold', 5) or 5)
    unit = data.get('unit', 'unit').strip()

    prod = POSProduct.objects.create(
        category=category,
        name=name,
        sku=sku,
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
    Authorized for Admin & Super Admin.
    """
    if not is_admin_user(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Permission Denied: Only Gym Admin and Super Admin have authorization to add inventory stock.'
        }, status=403)

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
@require_POST
def pos_delete_product_api(request, product_id):
    """
    Allow strictly Admins / Super Admins to delete or deactivate a product from POS inventory.
    If the product has historical sales, it is soft-deleted (is_active=False) to preserve financial audits.
    If it has no sales attached, it is safely removed completely.
    """
    if not is_admin_user(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Permission Denied: Only Gym Administrators and Super Admins have authorization to delete items from inventory.'
        }, status=403)

    product = get_object_or_404(POSProduct, id=product_id)
    prod_name = product.name

    # Check if product has sales
    has_sales = product.sale_items.exists()

    if has_sales:
        product.is_active = False
        product.save(update_fields=['is_active', 'updated_at'])
        action_type = 'archived'
    else:
        product.delete()
        action_type = 'deleted'

    return JsonResponse({
        'success': True,
        'message': f"Product '{prod_name}' successfully removed from POS catalog ({action_type}).",
        'product_id': product_id,
        'action_type': action_type,
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


@login_required
@require_POST
def pos_stock_audit_api(request):
    """
    Record a physical stock audit verification for a product.
    Calculates discrepancy (counted - expected), records financial variance (loss/gain),
    and updates system stock level and discrepancy flags.
    """
    try:
        data = json.loads(request.body)
    except Exception as e:
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid JSON: ' + str(e)}), content_type='application/json')

    product_id = data.get('product_id')
    if not product_id:
        return JsonResponse({'success': False, 'error': 'Product ID is required.'}, status=400)

    try:
        product = POSProduct.objects.get(id=product_id)
    except POSProduct.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found.'}, status=404)

    try:
        counted_qty = int(data.get('counted_quantity', product.stock_quantity))
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid counted quantity.'}, status=400)

    if counted_qty < 0:
        return JsonResponse({'success': False, 'error': 'Counted quantity cannot be negative.'}, status=400)

    expected_qty = product.stock_quantity
    discrepancy = counted_qty - expected_qty
    reason = data.get('reason', 'COUNT_CORRECTION')
    action_taken = data.get('action_taken', 'STOCK_ADJUSTED')
    notes = data.get('notes', '').strip()

    # SECURITY CHECK: Only Gym Admin or Super Admin can adjust live inventory stock numbers
    if action_taken == 'STOCK_ADJUSTED' and not is_admin_user(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Permission Denied: Only Gym Administrators authorization to adjust live inventory stock numbers. You may record the physical count as "Flagged as Missing (Under Review)" instead.'
        }, status=403)

    unit_cost = product.cost_price or Decimal('0.00')
    unit_price = product.price or Decimal('0.00')
    variance_value = Decimal(str(discrepancy)) * unit_cost

    with transaction.atomic():
        audit = POSInventoryAudit.objects.create(
            product=product,
            auditor=request.user,
            expected_quantity=expected_qty,
            counted_quantity=counted_qty,
            discrepancy=discrepancy,
            unit_cost=unit_cost,
            unit_price=unit_price,
            variance_value=variance_value,
            reason=reason,
            action_taken=action_taken,
            notes=notes,
            audit_date=timezone.now(),
        )

        if action_taken == 'STOCK_ADJUSTED':
            product.stock_quantity = counted_qty

        product.last_audited_at = timezone.now()
        product.has_audit_discrepancy = (discrepancy < 0)
        product.last_discrepancy_count = discrepancy
        product.save()

    status_label = 'Exact Match (No Discrepancy)'
    if discrepancy < 0:
        status_label = f'MISSING {abs(discrepancy)} unit(s) (Loss: LKR {abs(variance_value):,.2f})'
    elif discrepancy > 0:
        status_label = f'EXCESS +{discrepancy} unit(s) (Gain: LKR {variance_value:,.2f})'

    return JsonResponse({
        'success': True,
        'message': f"Stock audit recorded for '{product.name}': {status_label}",
        'audit': {
            'id': audit.id,
            'product_id': product.id,
            'product_name': product.name,
            'sku': product.sku,
            'expected_quantity': expected_qty,
            'counted_quantity': counted_qty,
            'discrepancy': discrepancy,
            'variance_value': float(variance_value),
            'new_stock': product.stock_quantity,
            'has_discrepancy': product.has_audit_discrepancy,
            'reason': audit.get_reason_display(),
            'action_taken': audit.get_action_taken_display(),
            'auditor': request.user.get_full_name() or request.user.username,
            'date': audit.audit_date.strftime('%Y-%m-%d %H:%M'),
        }
    })


@login_required
@require_POST
def pos_cash_drawer_audit_api(request):
    """
    Perform cash drawer shift balancing audit.
    Compares physical cash counted in the till against recorded cash sales + float.
    """
    today = timezone.now().date()
    try:
        data = json.loads(request.body)
    except Exception as e:
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid JSON: ' + str(e)}), content_type='application/json')

    opening_float = Decimal(str(data.get('opening_float', 0) or 0))
    counted_cash = Decimal(str(data.get('counted_cash', 0) or 0))
    notes = data.get('notes', '').strip()

    # Sum of today's completed cash sales
    cash_sales = POSSale.objects.filter(
        created_at__date=today,
        status='COMPLETED',
        payment_method='CASH'
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    expected_cash = opening_float + cash_sales
    discrepancy = counted_cash - expected_cash

    if discrepancy == Decimal('0.00'):
        status = 'BALANCED'
    elif discrepancy < Decimal('0.00'):
        status = 'SHORTAGE'
    else:
        status = 'OVERAGE'

    audit = POSCashDrawerAudit.objects.create(
        cashier=request.user,
        opening_float=opening_float,
        cash_sales_total=cash_sales,
        expected_cash=expected_cash,
        counted_cash=counted_cash,
        discrepancy=discrepancy,
        status=status,
        notes=notes,
        audit_date=timezone.now(),
    )

    return JsonResponse({
        'success': True,
        'message': f"Till audit completed: {audit.get_status_display()} ({discrepancy:+,.2f} LKR)",
        'audit': {
            'id': audit.id,
            'opening_float': float(opening_float),
            'cash_sales_total': float(cash_sales),
            'expected_cash': float(expected_cash),
            'counted_cash': float(counted_cash),
            'discrepancy': float(discrepancy),
            'status': audit.status,
            'status_display': audit.get_status_display(),
            'date': audit.audit_date.strftime('%Y-%m-%d %H:%M'),
            'cashier': request.user.get_full_name() or request.user.username,
        }
    })


@login_required
@require_POST
def pos_full_stock_audit_api(request):
    """
    Perform a Full Physical Inventory Stock Audit in bulk.
    Accepts physical counts for multiple or all products, calculates individual discrepancies
    and total shrinkage/gain, atomically updates stock (if authorized) and creates POSInventoryAudit logs.
    """
    try:
        data = json.loads(request.body)
    except Exception as e:
        return HttpResponseBadRequest(json.dumps({'error': 'Invalid JSON: ' + str(e)}), content_type='application/json')

    items = data.get('items', [])
    if not items:
        return JsonResponse({'success': False, 'error': 'No inventory items provided for audit.'}, status=400)

    reason = data.get('reason', 'COUNT_CORRECTION')
    action_taken = data.get('action_taken', 'STOCK_ADJUSTED' if is_admin_user(request.user) else 'FLAGGED_MISSING')
    global_notes = data.get('notes', '').strip()

    if action_taken == 'STOCK_ADJUSTED' and not is_admin_user(request.user):
        return JsonResponse({
            'success': False,
            'error': 'Permission Denied: Only Gym Administrators and Super Admins have authorization to adjust live inventory stock numbers.'
        }, status=403)

    audited_products = []
    total_expected = 0
    total_counted = 0
    total_shrinkage_loss = Decimal('0.00')
    total_gain_value = Decimal('0.00')
    discrepancy_count = 0
    exact_matches = 0

    with transaction.atomic():
        now = timezone.now()
        for item in items:
            prod_id = item.get('product_id')
            if not prod_id:
                continue

            try:
                product = POSProduct.objects.get(id=prod_id)
            except POSProduct.DoesNotExist:
                continue

            expected_qty = product.stock_quantity
            try:
                counted_qty = int(item.get('counted_quantity', expected_qty))
            except (ValueError, TypeError):
                continue

            if counted_qty < 0:
                continue

            discrepancy = counted_qty - expected_qty
            unit_cost = product.cost_price or Decimal('0.00')
            unit_price = product.price or Decimal('0.00')
            variance_val = Decimal(str(discrepancy)) * unit_cost
            item_notes = (item.get('notes') or global_notes).strip()

            audit = POSInventoryAudit.objects.create(
                product=product,
                auditor=request.user,
                expected_quantity=expected_qty,
                counted_quantity=counted_qty,
                discrepancy=discrepancy,
                unit_cost=unit_cost,
                unit_price=unit_price,
                variance_value=variance_val,
                reason=reason,
                action_taken=action_taken,
                notes=item_notes,
                audit_date=now,
            )

            if action_taken == 'STOCK_ADJUSTED':
                product.stock_quantity = counted_qty

            product.last_audited_at = now
            product.has_audit_discrepancy = (discrepancy < 0)
            product.last_discrepancy_count = discrepancy
            product.save()

            total_expected += expected_qty
            total_counted += counted_qty
            if discrepancy < 0:
                discrepancy_count += 1
                total_shrinkage_loss += abs(variance_val)
            elif discrepancy > 0:
                discrepancy_count += 1
                total_gain_value += variance_val
            else:
                exact_matches += 1

            audited_products.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'expected': expected_qty,
                'counted': counted_qty,
                'discrepancy': discrepancy,
                'variance_value': float(variance_val),
                'new_stock': product.stock_quantity,
            })

    net_variance_value = total_gain_value - total_shrinkage_loss
    return JsonResponse({
        'success': True,
        'message': f"Full inventory audit completed: {len(audited_products)} items audited. {exact_matches} exact match, {discrepancy_count} discrepancies.",
        'summary': {
            'total_items_audited': len(audited_products),
            'exact_matches': exact_matches,
            'discrepancy_count': discrepancy_count,
            'total_expected': total_expected,
            'total_counted': total_counted,
            'net_units_diff': total_counted - total_expected,
            'total_shrinkage_loss': float(total_shrinkage_loss),
            'total_gain_value': float(total_gain_value),
            'net_variance_value': float(net_variance_value),
            'action_taken': action_taken,
        },
        'audited_products': audited_products,
    })


@login_required
def pos_audit_data_api(request):
    """
    Returns live inventory audit telemetry for POS and Admin modals.
    Provides products, summary, missing items, recent stock audits, and till shift audits.
    """
    products = POSProduct.objects.filter(is_active=True).select_related('category').order_by('category__display_order', 'name')
    total_cost = sum(p.cost_price * p.stock_quantity for p in products)
    total_retail = sum(p.price * p.stock_quantity for p in products)
    total_units = sum(p.stock_quantity for p in products)
    
    missing_items = POSProduct.objects.filter(is_active=True, has_audit_discrepancy=True).values(
        'id', 'name', 'sku', 'stock_quantity', 'last_discrepancy_count', 'cost_price', 'price', 'unit'
    )
    
    recent_audits = POSInventoryAudit.objects.select_related('product', 'auditor').order_by('-audit_date')[:30]
    recent_audits_data = [
        {
            'id': a.id,
            'product_name': a.product.name,
            'sku': a.product.sku,
            'expected': a.expected_quantity,
            'counted': a.counted_quantity,
            'discrepancy': a.discrepancy,
            'variance_value': float(a.variance_value),
            'reason': a.get_reason_display(),
            'action': a.get_action_taken_display(),
            'auditor': a.auditor.get_full_name() or a.auditor.username if a.auditor else 'Staff',
            'date': a.audit_date.strftime('%Y-%m-%d %H:%M'),
            'notes': a.notes,
        }
        for a in recent_audits
    ]

    recent_drawer_audits = POSCashDrawerAudit.objects.select_related('cashier').order_by('-audit_date')[:15]
    recent_drawer_data = [
        {
            'id': d.id,
            'expected_cash': float(d.expected_cash),
            'counted_cash': float(d.counted_cash),
            'discrepancy': float(d.discrepancy),
            'status': d.status,
            'status_display': d.get_status_display(),
            'cashier': d.cashier.get_full_name() or d.cashier.username if d.cashier else 'Staff',
            'date': d.audit_date.strftime('%Y-%m-%d %H:%M'),
            'notes': d.notes,
        }
        for d in recent_drawer_audits
    ]

    catalog_data = [
        {
            'id': p.id,
            'name': p.name,
            'sku': p.sku,
            'category_name': p.category.name if p.category else 'General',
            'category_icon': p.category.icon if p.category else 'fa-box',
            'stock_quantity': p.stock_quantity,
            'cost_price': float(p.cost_price or 0),
            'price': float(p.price or 0),
            'unit': p.unit,
            'has_audit_discrepancy': p.has_audit_discrepancy,
            'last_discrepancy_count': p.last_discrepancy_count,
        }
        for p in products
    ]

    return JsonResponse({
        'success': True,
        'summary': {
            'total_items_count': products.count(),
            'total_stock_units': total_units,
            'total_cost_valuation': float(total_cost),
            'total_retail_valuation': float(total_retail),
            'potential_profit': float(total_retail - total_cost),
            'missing_items_count': missing_items.count(),
        },
        'missing_items': list(missing_items),
        'recent_audits': recent_audits_data,
        'recent_drawer_audits': recent_drawer_data,
        'catalog': catalog_data,
    })


@login_required
def pos_audit_plan_view(request):
    """
    Renders an official, printable Stock Audit Count Plan Sheet.
    Staff take this to the gym floor/bar to count inventory and sign off.
    """
    categories = POSCategory.objects.prefetch_related('products').all().order_by('display_order', 'name')
    all_products = POSProduct.objects.filter(is_active=True).select_related('category').order_by('category__display_order', 'name')
    total_expected_units = sum(p.stock_quantity for p in all_products)
    
    context = {
        'page_title': 'Stock Audit Count Plan Sheet — Fit Me Pitigala',
        'generated_date': timezone.now(),
        'auditor_name': request.user.get_full_name() or request.user.username,
        'categories': categories,
        'products': all_products,
        'total_products': all_products.count(),
        'total_expected_units': total_expected_units,
        'club_info': {
            'name': 'Fit Me Fitness Club',
            'tagline': 'Train with Purpose & Move with Confidence',
            'address': 'New Town, Elpitiya Road, Pitigala, 80420',
            'phone': '070 762 7878',
        }
    }
    return render(request, 'pos/audit_plan_sheet.html', context)
