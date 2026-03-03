
from flask import Blueprint, request, jsonify
from app import db
from app.models import (
    Product, ProductUnit, Customer, Sale, SaleItem,
    InventoryTransaction, Payment, GeneralLedger, PurchaseOrderItem, Account, StockAdjustment
)
from flask import current_app   # ← ADD THIS LINE (very important!)
from app.utils.auth import token_required
from app.utils.gl_utils import post_to_ledger, generate_transaction_number_partone
from datetime import datetime
from sqlalchemy import desc, func, or_

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

def update_timestamps(obj):
    obj.updated_at = datetime.utcnow()
    if not obj.created_at:
        obj.created_at = datetime.utcnow()
# Helper: Get latest purchase unit_price for COGS
def get_latest_cost_price(product_id):
    latest = PurchaseOrderItem.query \
        .filter_by(product_id=product_id, status=1) \
        .order_by(desc(PurchaseOrderItem.id)) \
        .first()
    return float(latest.unit_price) if latest else 0.0

# ------------------ Create Sale with Product Units ------------------ #
@token_required
@sales_bp.route('/', methods=['POST'])
def create_sale():
    data = request.get_json()
    items = data.get('items', [])
    amount_paid = float(data.get('amount_paid', 0))
    payment_account_id = data.get('payment_account_id')
    sale_date_str = data.get('sale_date')
    customer_id = data.get('customer_id', 1)  # default walk-in
    memo = data.get('memo', '')

    if not items:
        return jsonify({"error": "At least one item is required"}), 400

    # Parse sale date
    try:
        sale_date = datetime.strptime(sale_date_str, "%Y-%m-%d").date() if sale_date_str else datetime.utcnow().date()
    except:
        return jsonify({"error": "Invalid sale_date format. Use YYYY-MM-DD"}), 400

    if amount_paid > 0 and not payment_account_id:
        return jsonify({"error": "Payment account required when amount_paid > 0"}), 400

    try:
        total_amount = 0.0
        cogs_total = 0.0
        txn_id, txn_str = generate_transaction_number_partone('INV', transaction_date=sale_date)

        # Create Sale header
        sale = Sale(
            sale_number=txn_str,
            customer_id=customer_id,
            total_amount=0,  # will update later
            total_paid=amount_paid,
            balance=0,
            sale_date=sale_date,
            memo=memo,
            status=1
        )
        db.session.add(sale)
        db.session.flush()  # get sale.id

        # Process each item
        for item_data in items:
            product_id = item_data['product_id']
            unit_id = item_data.get('unit_id')
            quantity = float(item_data['quantity'])  # quantity in selected unit
            retail_price= float(item_data["unit_price"])


            product = Product.query.get_or_404(product_id)

            # Get unit
            if not unit_id:
                return jsonify({"error": f"unit_id required for product {product.name}"}), 400

            unit = ProductUnit.query.filter_by(id=unit_id, product_id=product_id, status=1).first()
            if not unit:
                return jsonify({"error": f"Invalid or inactive unit for product {product.name}"}), 400

            # Check stock in base units
            required_base_qty = quantity * unit.conversion_quantity
            if product.quantity < required_base_qty:
                return jsonify({"error": f"Insufficient stock for {product.name} ({unit.unit_name})"}), 400

            # Use unit retail price
            unit_price = float(retail_price or 0)
            item_total = unit_price * quantity

            # Deduct stock in base units
            product.quantity -= required_base_qty

            # Create SaleItem
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                unit_id=unit.id,
                product_name=product.name,
                quantity=quantity,  # in selected unit
                unit_price=unit_price,
                total_price=item_total,
                status=1
            )
            db.session.add(sale_item)

            # Inventory Transaction (outflow in base units)
            inv_txn = InventoryTransaction(
                transaction_no=txn_id,
                sale_id=sale.id,
                product_id=product.id,
                unit_id=unit.id,
                quantity=required_base_qty,  # stored in base units
                unit_price=get_latest_cost_price(product.id),  # for COGS
                total_price=get_latest_cost_price(product.id) * required_base_qty,
                transaction_type='Sale',
                status=1
            )
            db.session.add(inv_txn)

            total_amount += item_total
            cogs_total += get_latest_cost_price(product.id) * required_base_qty

        # Update sale totals
        sale.total_amount = total_amount
        sale.balance = total_amount - amount_paid

        # Set status
        if amount_paid >= total_amount:
            sale.status = 1  # Fully paid
        elif amount_paid > 0:
            sale.status = 4  # Partial
        else:
            sale.status = 3  # Credit

        # Post to General Ledger
        if amount_paid > 0:
            payment_account = Account.query.get(payment_account_id)
            if not payment_account:
                raise ValueError("Invalid payment account")

            entries = [
                # Debit payment account (Cash/Bank/Mobile)
                {"account_id": payment_account.code, "transaction_type": "Debit", "amount": amount_paid},
                # Credit Sales Revenue
                {"account_id": 4000, "transaction_type": "Credit", "amount": amount_paid},
            ]

            if sale.balance > 0:
                # Debit Accounts Receivable for credit portion
                entries.append({"account_id": 1100, "transaction_type": "Debit", "amount": sale.balance})
                # Credit Sales Revenue for full amount
                entries.append({"account_id": 4000, "transaction_type": "Credit", "amount": sale.balance})

            # COGS & Inventory
            entries += [
                {"account_id": 5000, "transaction_type": "Debit", "amount": cogs_total},  # COGS
                {"account_id": 1200, "transaction_type": "Credit", "amount": cogs_total},  # Inventory
            ]
        else:
            # Full credit sale
            entries = [
                {"account_id": 1100, "transaction_type": "Debit", "amount": total_amount},  # A/R
                {"account_id": 4000, "transaction_type": "Credit", "amount": total_amount},  # Sales
                {"account_id": 5000, "transaction_type": "Debit", "amount": cogs_total},
                {"account_id": 1200, "transaction_type": "Credit", "amount": cogs_total},
            ]

        post_to_ledger(
            entries,
            transaction_no_id=txn_id,
            description=f"Sale Invoice #{txn_str}",
            transaction_date=sale_date
        )

        sale.transaction_no = txn_id

        # Record payment if any
        if amount_paid > 0:
            payment = Payment(
                sale_id=sale.id,
                amount=amount_paid,
                payment_type=data.get('payment_type', 'Cash'),
                payment_date=sale_date,
                reference=txn_str,
                payment_account_id=payment_account_id,
                transaction_no=txn_id,
                status=1
            )
            db.session.add(payment)

        db.session.commit()

        return jsonify({
            "message": "Sale created successfully",
            "sale_id": sale.id,
            "sale_number": txn_str,
            "total_amount": total_amount,
            "amount_paid": amount_paid,
            "balance": sale.balance,
            "sale_date": sale_date.strftime("%Y-%m-%d")
        }), 201

    except ValueError as ve:
        db.session.rollback()
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Sale error: {e}")
        return jsonify({"error": "Failed to create sale"}), 500

# ------------------ Get All Sales ------------------ #
@token_required
@sales_bp.route('/', methods=['GET'])
def get_sales():
    search = request.args.get('search', '').strip()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Sale.query.join(Customer).filter(Sale.status.in_([1, 3, 4]))

    if search:
        query = query.filter(
            # or_(
                Sale.sale_number.ilike(f"%{search}%")|
                Sale.memo.ilike(f"%{search}%")|
                Customer.name.ilike(f"%{search}%")
            # )
        )

    if start_date:
        query = query.filter(Sale.sale_date >= start_date)
    if end_date:
        query = query.filter(Sale.sale_date <= end_date)

    sales = query.order_by(Sale.id.desc()).all()

    result = []
    for s in sales:
        items = SaleItem.query.filter_by(sale_id=s.id, status=1).all()
        items_data = []
        for i in items:
            unit = ProductUnit.query.get(i.unit_id) if i.unit_id else None
            items_data.append({
                "product_id": i.product_id,
                "product_name": i.product_name,
                "unit_name": unit.unit_name if unit else "Unknown",
                "quantity": float(i.quantity),
                "unit_price": float(i.unit_price),
                "total_price": float(i.total_price)
            })

        result.append({
            "id": s.id,
            "sale_id": s.id,
            "sale_number": s.sale_number,
            "memo": s.memo if hasattr(s, 'memo') else "",
            "customer_name": s.customer.name,
            "total_amount": float(s.total_amount), 
            "total_paid": float(s.total_paid),
            "balance": float(s.balance),
            "sale_date": s.sale_date.strftime("%Y-%m-%d"),
            "status": s.status,
            "items": items_data
        })

    return jsonify(result)

# ------------------ Get Single Sale ------------------ #
@token_required
@sales_bp.route('/<int:sale_id>', methods=['GET'])
def get_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)

    items = SaleItem.query.filter_by(sale_id=sale.id, status=1).all()
    items_data = []
    for i in items:
        unit = ProductUnit.query.get(i.unit_id) if i.unit_id else None
        items_data.append({
            "product_id": i.product_id,
            "product_name": i.product_name,
            "unit_id": i.unit_id,
            "unit_name": unit.unit_name if unit else "N/A",
            "quantity": float(i.quantity),
            "unit_price": float(i.unit_price),
            "total_price": float(i.total_price)
        })

    return jsonify({
        "id": sale.id,
        "sale_number": sale.sale_number,
        "customer_id": sale.customer_id,
        "memo": sale.memo if hasattr(sale, 'memo') else "",
        "customer_name": sale.customer.name,
        "total_amount": float(sale.total_amount),
        "total_paid": float(sale.total_paid),
        "balance": float(sale.balance),
        "sale_date": sale.sale_date.strftime("%Y-%m-%d"),
        "items": items_data
    })




@token_required
@sales_bp.route('/<int:sale_id>/delete', methods=['DELETE'])
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)

    try:
        # 1️⃣ Soft delete sale
        sale.status = 9
        update_timestamps(sale)
        db.session.add(sale)

        # 2️⃣ Soft delete sale items & restore stock correctly
        sale_items = SaleItem.query.filter_by(sale_id=sale.id, status=1).all()

        for item in sale_items:
            item.status = 9
            update_timestamps(item)
            db.session.add(item)

            product = db.session.get(Product, item.product_id)
            if not product:
                continue

            previous_qty = float(product.quantity or 0)

            # ✅ Apply unit conversion
            multiplier = 1
            if item.unit_id:
                unit = db.session.get(ProductUnit, item.unit_id)
                if unit:
                    multiplier = unit.conversion_quantity

            restored_qty = float(item.quantity) * multiplier
            new_qty = previous_qty + restored_qty

            # ✅ Update product stock
            product.quantity = new_qty
            db.session.add(product)

            # ✅ OPTIONAL (Recommended): log stock adjustment
            adjustment = StockAdjustment(
                product_id=product.id,
                unit_id=item.unit_id,
                adjustment_type="INCREASE",
                quantity=item.quantity,   # original unit qty
                previous_quantity=previous_qty,
                new_quantity=new_qty,
                reason=f"Sale #{sale_id} deleted - stock restored",
                status=1
            )
            db.session.add(adjustment)

        # 3️⃣ Soft delete payments
        payments = Payment.query.filter_by(sale_id=sale.id, status=1).all()
        for payment in payments:
            payment.status = 9
            update_timestamps(payment)
            db.session.add(payment)

        # 4️⃣ Soft delete inventory transactions
        inv_txns = InventoryTransaction.query.filter_by(sale_id=sale.id, status=1).all()
        for txn in inv_txns:
            txn.status = 9
            update_timestamps(txn)
            db.session.add(txn)

        # 5️⃣ Reverse all related General Ledger entries
        gl_entries = GeneralLedger.query.filter(
            or_(
                GeneralLedger.description.ilike(f"%Sale #{sale_id}%"),
                GeneralLedger.description.ilike(f"%Payment for Sale #{sale_id}%")
            )
        ).all()

        for entry in gl_entries:
            reverse_type = 'Credit' if entry.transaction_type == 'Debit' else 'Debit'
            reverse_entry = GeneralLedger(
                account_id=entry.account_id,
                transaction_type=reverse_type,
                amount=entry.amount,
                description=f"Reversal of {entry.description}",
                transaction_date=datetime.utcnow(),
                transaction_no=entry.transaction_no,
                status=1
            )
            db.session.add(reverse_entry)

        db.session.commit()

        return jsonify({
            "message": f"Sale #{sale_id} soft deleted, stock restored correctly, GL reversed"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete sale: {str(e)}"}), 500


# ------------------------------------------------
# GET Sale for EDIT - Full detailed data
# ------------------------------------------------
@token_required
@sales_bp.route('/<int:sale_id>/edit', methods=['GET'])
def get_sale_for_edit(sale_id):
    """
    Returns complete sale data optimized for editing:
    - Header: sale info, customer, totals, payment status
    - Items: full product details + all available units + current stock
    - Payments: summary + list
    """
    sale = Sale.query.get_or_404(sale_id)

    # Customer info (fallback to Walk-in if missing)
    customer = sale.customer
    customer_data = {
        "id": customer.id if customer else 1,
        "name": customer.name if customer else "Walk-in Customer",
        "phone": customer.phone if customer else "",
        "email": customer.email if customer else "",
        "address": customer.address if customer else ""
    } if customer else {
        "id": 1,
        "name": "Walk-in Customer",
        "phone": "",
        "email": "",
        "address": ""
    }

    # Sale Items - enriched with units & stock
    sale_items = SaleItem.query.filter_by(sale_id=sale.id, status=1).all()
    items = []

    for si in sale_items:
        product = si.product

        # Category
        category_name = None
        if product and product.category:
            category_name = product.category.name

        # All available units for this product
        units = []
        if product:
            for u in product.units:
                units.append({
                    "id": u.id,
                    "unit_name": u.unit_name,
                    "conversion_quantity": u.conversion_quantity,
                    "retail_price": float(u.retail_price) if u.retail_price else 0.0,
                    "wholesale_price": float(u.wholesale_price) if u.wholesale_price else 0.0,
                    "cost_price": float(u.cost_price) if u.cost_price else 0.0,
                    "is_returnable": u.is_returnable
                })
        
        
        purchase_price = PurchaseOrderItem.query.filter_by(product_id=si.product_id, status=1).first()


        # Currently selected unit (if exists)
        selected_unit = next((u for u in product.units if u.id == si.unit_id), None) if product else None

        # Current stock (in base units)
        current_stock_base = float(product.quantity) if product else 0.0

        items.append({
            "id": si.id,
            "product_id": si.product_id,
            "product_name": si.product_name or (product.name if product else "Unknown Product"),
            "sku": product.sku if product else None,
            "category_name": category_name,
            "quantity": float(si.quantity),
            "unit_price": float(si.unit_price),
            "stock_qty":0,
            "total_price": float(si.total_price),
            "unit_id": si.unit_id,
            "unit_name": selected_unit.unit_name if selected_unit else None,
            "current_stock_base": current_stock_base,
            "last_purchase_price":purchase_price.unit_price if purchase_price else 0,
            "units": units,  # ← all available units for editing
            # Helpful for frontend validation/display
            "max_quantity_allowed": current_stock_base if not selected_unit else current_stock_base / selected_unit.conversion_quantity if selected_unit.conversion_quantity > 0 else 0
        })

    # Payments summary + list
    payments = Payment.query.filter_by(sale_id=sale.id, status=1).all()
    payment_list = [
        {
            "id": p.id,
            "amount": float(p.amount),
            "payment_type": p.payment_type,
            "payment_date": p.payment_date.strftime("%Y-%m-%d %H:%M") if p.payment_date else None,
            "reference": p.reference,
            "payment_account_id": p.payment_account_id
        }
        for p in payments
    ]

    total_paid = sum(float(p.amount) for p in payments)

    # Final response structure
    data = {
        "sale_id": sale.id,
        "sale_number": sale.sale_number,
        "sale_date": sale.sale_date.strftime("%Y-%m-%d") if sale.sale_date else None,
        "customer_id": sale.customer_id,
        "customer": customer_data,
        "total_amount": float(sale.total_amount),
        "total_paid": total_paid,
        "balance": float(sale.balance),
        "payment_status": sale.payment_status,
        "memo": sale.memo if hasattr(sale, 'memo') else "",  # in case you add memo later
        "payment_account_id": getattr(sale, "payment_account_id", None),
        "items": items,
        "payments": payment_list,
        "created_at": sale.created_at.isoformat() if sale.created_at else None,
        "updated_at": sale.updated_at.isoformat() if sale.updated_at else None
    }

    return jsonify({
        "status": "success",
        "message": f"Sale #{sale.sale_number} loaded for editing",
        "data": data
    }), 200


# ------------------------------------------------
# GET Single Sale - Lightweight view version
# ------------------------------------------------
@token_required
@sales_bp.route('/<int:sale_id>', methods=['GET'])
def get_sale_edit(sale_id):
    """
    Lightweight version for viewing sale details (no full units list)
    Used in list views, receipts, etc.
    """
    sale = Sale.query.get_or_404(sale_id)

    # Basic customer info
    customer_name = sale.customer.name if sale.customer else "Walk-in Customer"

    # Sale items (minimal)
    sale_items = SaleItem.query.filter_by(sale_id=sale.id, status=1).all()
    items = [
        {
            "product_id": si.product_id,
            "product_name": si.product_name or (si.product.name if si.product else "Unknown"),
            "quantity": float(si.quantity),
            "unit_price": float(si.unit_price),
            "total_price": float(si.total_price),
            "unit_id": si.unit_id,
            "unit_name": si.unit.unit_name if si.unit else None
        }
        for si in sale_items
    ]

    # Basic payment summary
    total_paid = db.session.query(func.sum(Payment.amount))\
        .filter(Payment.sale_id == sale.id, Payment.status == 1)\
        .scalar() or 0.0

    return jsonify({
        "sale_id": sale.id,
        "sale_number": sale.sale_number,
        "sale_date": sale.sale_date.strftime("%Y-%m-%d") if sale.sale_date else None,
        "customer_name": customer_name,
        "total_amount": float(sale.total_amount),
        "total_paid": float(total_paid),
        "balance": float(sale.balance),
        "payment_status": sale.payment_status,
        "items": items,
        "created_at": sale.created_at.isoformat() if sale.created_at else None
    }), 200




@token_required
@sales_bp.route('/edit_old', methods=['POST'])
def create_or_update_sale_old():
    data = request.json

    try:
        sale_id = data.get("sale_id")  # Optional - present if updating
        items = data.get('items', [])
        amount_paid = float(data.get('amount_paid', 0))
        payment_account_id = data.get('payment_account_id')
        sale_date_str = data.get("sale_date")
        payment_type = data.get('payment_type', 'Cash')
        memo = data.get("memo", "")
        customer_id = data.get("customer_id", 1)  # Default walk-in

        if not items:
            return jsonify({"error": "At least one item is required"}), 400

        # Parse sale date
        try:
            sale_date = datetime.strptime(sale_date_str, "%Y-%m-%d") if sale_date_str else datetime.utcnow()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        if amount_paid > 0 and not payment_account_id:
            return jsonify({"error": "Payment account required when amount_paid > 0"}), 400

        # --- If updating, soft-delete previous sale first (reversal) ---
        if sale_id:
            from flask import current_app
            current_app.logger.info(f"Updating sale #{sale_id}: reversing previous sale.")
            success = delete_sale(sale_id)
            # You can call your delete_sale(sale_id) function here if it handles reversal properly
            # For now, we create new sale and let old one stay soft-deleted

        # --- Initialize totals & transaction ---
        total_amount = 0.0
        cogs_total = 0.0
        txn_id, txn_str = generate_transaction_number_partone('INV', transaction_date=sale_date)

        # --- Create new Sale record ---
        sale = Sale(
            sale_number=txn_str,
            customer_id=customer_id,
            total_amount=0,  # updated later
            total_paid=amount_paid,
            balance=0,
            sale_date=sale_date,
            memo=memo,
            status=1
        )
        db.session.add(sale)
        db.session.flush()  # Get sale.id

        # --- Process Sale Items ---
        for idx, item_data in enumerate(items, start=1):
            product_id = item_data.get("product_id")
            unit_id = item_data.get("unit_id")
            quantity = float(item_data.get("quantity", 0))  # in selected unit
            unit_price = float(item_data.get("unit_price", 0))
            total_price = float(item_data.get("total_price", unit_price * quantity))

            if not product_id or not unit_id:
                return jsonify({"error": f"Product ID and Unit ID required for item #{idx}"}), 400

            product = Product.query.get_or_404(product_id)

            unit = ProductUnit.query.filter_by(id=unit_id, product_id=product_id, status=1).first()
            if not unit:
                return jsonify({"error": f"Invalid unit {unit_id} for product {product.name}"}), 400

            # Convert to base units for stock check
            base_qty_required = quantity * (unit.conversion_quantity or 1)
            if product.quantity < base_qty_required:
                return jsonify({"error": f"Insufficient stock for {product.name} ({unit.unit_name})"}), 400

            # Deduct stock in base units
            product.quantity -= base_qty_required
            db.session.add(product)

            # COGS calculation (latest purchase price)
            latest_cost = get_latest_cost_price(product.id)  # You already have this helper
            cogs_amount = latest_cost * base_qty_required

            # Record sale item
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                unit_id=unit.id,
                product_name=product.name,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                status=1
            )
            db.session.add(sale_item)

            # Inventory transaction (base units)
            inv_txn = InventoryTransaction(
                transaction_no=txn_id,
                sale_id=sale.id,
                product_id=product.id,
                unit_id=unit.id,
                quantity=base_qty_required,
                unit_price=latest_cost,
                total_price=cogs_amount,
                transaction_type='Sale',
                status=1
            )
            db.session.add(inv_txn)

            total_amount += total_price
            cogs_total += cogs_amount

        # --- Final Sale updates ---
        sale.total_amount = total_amount
        sale.balance = total_amount - amount_paid

        # Set payment status
        if amount_paid >= total_amount:
            sale.status = 1  # Paid
        elif amount_paid > 0:
            sale.status = 4  # Partial
        else:
            sale.status = 3  # Credit

        sale.update_totals()  # Use your built-in method

        # --- General Ledger Entries ---
        entries = []

        # Sales Revenue (always credit full amount)
        entries.append({
            "account_id": 4000,           # Sales Revenue
            "transaction_type": "Credit",
            "amount": total_amount
        })

        # COGS & Inventory
        entries.extend([
            {"account_id": 5000, "transaction_type": "Debit", "amount": cogs_total},    # COGS Debit
            {"account_id": 1200, "transaction_type": "Credit", "amount": cogs_total},   # Inventory Credit
        ])

        # Payment portion
        if amount_paid > 0:
            payment_account = Account.query.get(payment_account_id)
            if not payment_account:
                raise ValueError("Invalid payment account")

            entries.append({
                "account_id": payment_account.code,    # Cash/Bank/Mobile
                "transaction_type": "Debit",
                "amount": amount_paid
            })

            # Remaining balance → Accounts Receivable
            if sale.balance > 0:
                entries.append({
                    "account_id": 1100,                # A/R
                    "transaction_type": "Debit",
                    "amount": sale.balance
                })

        else:
            # Full credit sale
            entries.append({
                "account_id": 1100,                    # A/R full amount
                "transaction_type": "Debit",
                "amount": total_amount
            })

        # Post to ledger
        post_to_ledger(
            entries,
            transaction_no_id=txn_id,
            description=f"Sale Invoice #{txn_str} - {'Update' if sale_id else 'Create'}",
            transaction_date=sale_date
        )

        sale.transaction_no = txn_id

        # --- Record Payment (if any) ---
        if amount_paid > 0:
            payment = Payment(
                sale_id=sale.id,
                amount=amount_paid,
                payment_type=payment_type,
                payment_date=sale_date,
                reference=data.get("memo", txn_str),
                payment_account_id=payment_account_id,
                transaction_no=txn_id,
                status=1
            )
            db.session.add(payment)

        db.session.commit()

        return jsonify({
            "message": f"Sale {'updated' if sale_id else 'created'} successfully",
            "sale_id": sale.id,
            "sale_number": txn_str,
            "total_amount": total_amount,
            "total_paid": amount_paid,
            "balance": sale.balance,
            "payment_status": sale.payment_status,
            "transaction_no": txn_str,
            "sale_date": sale_date.strftime("%Y-%m-%d")
        }), 201

    except ValueError as ve:
        db.session.rollback()
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Sale creation/update failed: {str(e)}")
        return jsonify({"error": "Failed to process sale"}), 500
    





@token_required
@sales_bp.route('/edit', methods=['POST'])
def create_or_update_sale():
    data = request.json

    try:
        sale_id = data.get("sale_id")  # present when updating
        items = data.get('items', [])
        amount_paid = float(data.get('amount_paid', 0))
        payment_account_id = data.get('payment_account_id')
        sale_date_str = data.get("sale_date")
        payment_type = data.get('payment_type', 'Cash')
        memo = data.get("memo", "")
        customer_id = data.get("customer_id", 1)

        if not items:
            return jsonify({"error": "At least one item is required"}), 400

        # Parse sale date
        try:
            sale_date = datetime.strptime(sale_date_str, "%Y-%m-%d").date() if sale_date_str else datetime.utcnow().date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        if amount_paid > 0 and not payment_account_id:
            return jsonify({"error": "Payment account required when amount_paid > 0"}), 400

        total_amount = 0.0
        cogs_total = 0.0

        if sale_id:
            # === UPDATE MODE ===
            sale = Sale.query.get_or_404(sale_id)

            # 1. Reverse / clean up old data
            # Restore stock from old items
            old_items = SaleItem.query.filter_by(sale_id=sale.id, status=1).all()
            for old_item in old_items:
                product = Product.query.get(old_item.product_id)
                if product:
                    unit = ProductUnit.query.get(old_item.unit_id)
                    conv = unit.conversion_quantity if unit else 1
                    restored_qty = old_item.quantity * conv
                    product.quantity = float(product.quantity or 0) + restored_qty
                    db.session.add(product)

                # Soft-delete old sale item
                old_item.status = 9
                db.session.add(old_item)

            # Soft-delete old inventory transactions
            InventoryTransaction.query.filter_by(sale_id=sale.id, status=1).update({"status": 9})

            # Soft-delete old payments (we'll re-create if needed)
            Payment.query.filter_by(sale_id=sale.id, status=1).update({"status": 9})

            # Optional: reverse GL entries (you can improve this later with proper reversal)
            # For now we will post new entries below

            # Update sale header
            sale.customer_id = customer_id
            sale.sale_date = sale_date
            sale.memo = memo
            sale.total_paid = amount_paid  # will be updated after new payment
            sale.balance = 0  # recalculated later
            sale.updated_at = datetime.utcnow()

            # Keep original sale_number & transaction_no
            txn_id = sale.transaction_no
            txn_str = sale.sale_number

            current_app.logger.info(f"Updating existing sale #{sale_id} - {txn_str}")

        else:
            # === CREATE MODE ===
            txn_id, txn_str = generate_transaction_number_partone('INV', transaction_date=sale_date)

            sale = Sale(
                sale_number=txn_str,
                customer_id=customer_id,
                total_amount=0,
                total_paid=amount_paid,
                balance=0,
                sale_date=sale_date,
                memo=memo,
                status=1,
                transaction_no=txn_id
            )
            db.session.add(sale)
            db.session.flush()  # get sale.id

        # === COMMON: Process new items (create or re-create) ===
        for idx, item_data in enumerate(items, start=1):
            product_id = item_data.get("product_id")
            unit_id = item_data.get("unit_id")
            quantity = float(item_data.get("quantity", 0))
            unit_price = float(item_data.get("unit_price", 0))

            if not product_id or not unit_id:
                return jsonify({"error": f"Product ID and Unit ID required for item #{idx}"}), 400

            product = Product.query.get_or_404(product_id)

            unit = ProductUnit.query.filter_by(id=unit_id, product_id=product_id, status=1).first()
            if not unit:
                return jsonify({"error": f"Invalid or inactive unit for product {product.name}"}), 400

            base_qty_required = quantity * unit.conversion_quantity

            # In update mode — we already restored old stock, so product.quantity is current + old
            if product.quantity < base_qty_required:
                return jsonify({"error": f"Insufficient stock for {product.name} ({unit.unit_name}). "
                                        f"Available: {product.quantity}, Required: {base_qty_required}"}), 400

            # Deduct new quantity
            product.quantity -= base_qty_required
            db.session.add(product)

            latest_cost = get_latest_cost_price(product.id)
            cogs_amount = latest_cost * base_qty_required

            # Create new SaleItem
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                unit_id=unit.id,
                product_name=product.name,
                quantity=quantity,
                unit_price=unit_price,
                total_price=quantity * unit_price,
                status=1
            )
            db.session.add(sale_item)

            # New inventory transaction
            inv_txn = InventoryTransaction(
                transaction_no=txn_id,
                sale_id=sale.id,
                product_id=product.id,
                unit_id=unit.id,
                quantity=base_qty_required,
                unit_price=latest_cost,
                total_price=cogs_amount,
                transaction_type='Sale',
                status=1
            )
            db.session.add(inv_txn)

            total_amount += sale_item.total_price
            cogs_total += cogs_amount

        # Update sale totals
        sale.total_amount = total_amount
        sale.balance = total_amount - amount_paid

        if amount_paid >= total_amount:
            sale.status = 1  # Fully paid
        elif amount_paid > 0:
            sale.status = 4  # Partial
        else:
            sale.status = 3  # Credit

        sale.update_totals()  # if you have this method

        # === General Ledger ===
        entries = [
            {"account_id": 4000, "transaction_type": "Credit", "amount": total_amount},     # Sales
            {"account_id": 5000, "transaction_type": "Debit", "amount": cogs_total},       # COGS
            {"account_id": 1200, "transaction_type": "Credit", "amount": cogs_total},      # Inventory
        ]

        if amount_paid > 0:
            payment_account = Account.query.get(payment_account_id)
            if not payment_account:
                raise ValueError("Invalid payment account")

            entries.append({"account_id": payment_account.code, "transaction_type": "Debit", "amount": amount_paid})

            if sale.balance > 0:
                entries.append({"account_id": 1100, "transaction_type": "Debit", "amount": sale.balance})
        else:
            entries.append({"account_id": 1100, "transaction_type": "Debit", "amount": total_amount})

        post_to_ledger(
            entries,
            transaction_no_id=txn_id,
            description=f"Sale Invoice #{txn_str} - {'Update' if sale_id else 'Create'}",
            transaction_date=sale_date
        )

        # Record new payment if amount_paid > 0
        if amount_paid > 0:
            new_payment = Payment(
                sale_id=sale.id,
                amount=amount_paid,
                payment_type=payment_type,
                payment_date=sale_date,
                reference=memo or txn_str,
                payment_account_id=payment_account_id,
                transaction_no=txn_id,
                status=1
            )
            db.session.add(new_payment)

        db.session.commit()

        return jsonify({
            "message": f"Sale {'updated' if sale_id else 'created'} successfully",
            "sale_id": sale.id,
            "sale_number": sale.sale_number,
            "total_amount": total_amount,
            "amount_paid": amount_paid,
            "balance": sale.balance,
            "sale_date": sale.sale_date.strftime("%Y-%m-%d")
        }), 200 if sale_id else 201

    except ValueError as ve:
        db.session.rollback()
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Sale {'update' if sale_id else 'create'} failed: {str(e)}", exc_info=True)
        return jsonify({"error": "Failed to process sale"}), 500