from flask import Blueprint, request, jsonify
from app import db
from app.models import Account, Customer, InventoryTransaction, Payment, Product, PurchaseOrderItem, Sale, SaleItem, GeneralLedger
from app.utils.auth import token_required
from app.utils.gl_utils import post_to_ledger, generate_transaction_number_partone,generate_transaction_number
from datetime import datetime
from sqlalchemy import or_,cast ,String


sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

# ------------------ Helper function for updating timestamps ------------------ #
def update_timestamps(obj):
    obj.updated_at = datetime.utcnow()
    if not obj.created_at:
        obj.created_at = datetime.utcnow()

# # ------------------ Create a Sale & Invoice with GL ------------------ #

@token_required
@sales_bp.route('/', methods=['POST'])
def create_sale():
    data = request.json
    items = data.get('items', [])
    amount_paid = data.get('amount_paid', 0)
    payment_account_id = data.get('payment_account_id')
    sale_date_str = data.get("sale_date")

    if not items:
        return jsonify({"error": "At least one item is required"}), 400

    # Parse sale_date
    try:
        sale_date = datetime.strptime(sale_date_str, "%Y-%m-%d") if sale_date_str else datetime.utcnow()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    

    if not  payment_account_id and amount_paid >0:
        return jsonify({"error": "please give me the following the amount paid is not specify the account plases "}), 400
    try:
        total_amount = 0
        cogs_total = 0
        txn_id, txn_str = generate_transaction_number_partone('INV', transaction_date=sale_date)

        # Create the Sale
        sale = Sale(
            sale_number=txn_str,
            customer_id=data.get('customer_id', 1),
            total_paid=amount_paid,
            status=1,
            sale_date=sale_date
        )
        db.session.add(sale)
        db.session.flush()  # to get sale.id

        # --- Process Items ---
        for item_data in items:
            product = Product.query.get(item_data['product_id'])
            if not product:
                raise ValueError(f"Product {item_data['product_id']} not found")
            if product.quantity < item_data['quantity']:
                raise ValueError(f"Insufficient stock for {product.name}")

            # Get latest purchase cost for accurate COGS
            latest_purchase = (
                PurchaseOrderItem.query
                .filter(PurchaseOrderItem.product_id == product.id)
                .order_by(PurchaseOrderItem.created_at.desc())
                .first()
            )
            purchase_price = latest_purchase.unit_price if latest_purchase else item_data.get('purchase_price', 0)

            # Deduct stock
            product.quantity -= item_data['quantity']
            db.session.add(product)

            # Add Sale Item
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                product_name=product.name,
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['unit_price'] * item_data['quantity'],
                status=1
            )
            db.session.add(sale_item)

            # Add inventory transaction (OUTFLOW)
            inv_txn = InventoryTransaction(
                transaction_no=txn_id,
                sale_id=sale.id,
                product_id=product.id,
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                total_price=item_data['unit_price'] * item_data['quantity'],
                transaction_type='Sale',
                status=1
            )
            db.session.add(inv_txn)

            total_amount += sale_item.total_price
            cogs_total += purchase_price * item_data['quantity']

        # --- Finalize Sale Totals ---
        sale.total_amount = total_amount
        balance = total_amount - amount_paid
        sale.balance = balance

        if amount_paid == 0:
            sale.status = 3  # Full credit
        elif 0 < amount_paid < total_amount:
            sale.status = 4  # Partial payment
        else:
            sale.status = 1  # Fully paid

        db.session.flush()

        # --- Ledger Entries ---
        payment_type = data.get('payment_type', 'Cash')
        credit_account_code = 1100  # Accounts Receivable by default
        if payment_account_id:
            payment_account = Account.query.get(payment_account_id)
            if not payment_account:
                raise ValueError("Invalid payment account")
            credit_account_code = payment_account.code

        if amount_paid > 0:
            if amount_paid >= total_amount:
                entries = [
                    {"account_id": credit_account_code, "transaction_type": "Debit", "amount": amount_paid},
                    {"account_id": 4000, "transaction_type": "Credit", "amount": amount_paid},
                    {"account_id": 5000, "transaction_type": "Debit", "amount": cogs_total},
                    {"account_id": 1200, "transaction_type": "Credit", "amount": cogs_total},
                ]
            else:
                entries = [
                    {"account_id": credit_account_code, "transaction_type": "Debit", "amount": amount_paid},
                    {"account_id": 1100, "transaction_type": "Debit", "amount": balance},
                    {"account_id": 4000, "transaction_type": "Credit", "amount": total_amount},
                    {"account_id": 5000, "transaction_type": "Debit", "amount": cogs_total},
                    {"account_id": 1200, "transaction_type": "Credit", "amount": cogs_total},
                ]
        else:
            entries = [
                {"account_id": 1100, "transaction_type": "Debit", "amount": total_amount},#recevavable
                {"account_id": 4000, "transaction_type": "Credit", "amount": total_amount},#sales reveenue
                {"account_id": 5000, "transaction_type": "Debit", "amount": cogs_total},# cogs 
                {"account_id": 1200, "transaction_type": "Credit", "amount": cogs_total},#inventorty
            ]

        post_to_ledger(
            entries,
            transaction_no_id=txn_id,
            description=f"Sale #{sale.id}",
            transaction_date=sale_date
        )

        sale.transaction_no = txn_id

        # --- Record Payment ---
        if amount_paid > 0:
            payment = Payment(
                sale_id=sale.id,
                amount=amount_paid,
                payment_type=payment_type,
                reference=txn_str,
                payment_date=sale_date,
                payment_account_id=payment_account_id,
                status=1,
                transaction_no=txn_id
            )
            db.session.add(payment)

        db.session.commit()

        return jsonify({
            "message": "Sale created successfully",
            "sale_id": sale.id,
            "total_amount": sale.total_amount,
            "total_paid": sale.total_paid,
            "balance": sale.balance,
            "payment_status": sale.status,
            "transaction_no": txn_str,
            "sale_date": sale.sale_date.strftime("%Y-%m-%d")
        }), 201

    except ValueError as ve:
        db.session.rollback()
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500



# ------------------ Get All Sales ------------------ #
@token_required
@sales_bp.route('/', methods=['GET'])
def get_sales():
    search = request.args.get("search", "").strip()
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    # Always inner join Customer
    query = Sale.query.join(Customer).filter(Sale.status.in_([1, 2, 3, 4]))

    # Search by sale number or customer name
    if search:
        query = query.filter(
            or_(
                Sale.sale_number.ilike(f"%{search}%"),
                Customer.name.ilike(f"%{search}%")
            )
        )

    # Date filters
    if start_date:
        query = query.filter(cast(Sale.sale_date, String) >= start_date)
    if end_date:
        query = query.filter(cast(Sale.sale_date, String) <= end_date)

    sales = query.order_by(Sale.id.desc()).all()  # Only active/filtered sales

    data = []
    for s in sales:
        sale_items = SaleItem.query.filter_by(sale_id=s.id, status=1).all()
        items = [{
            "product_id": i.product_id,
            "product_name": i.product_name,
            "quantity": i.quantity,
            "unit_price": i.unit_price,
            "total_price": i.total_price
        } for i in sale_items]

        data.append({
            "sale_id": s.id,
            "sale_number": s.sale_number,
            "total_amount": s.total_amount,
            "payment_status": s.payment_status,
            "sale_date": s.sale_date,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
            "customer_name": s.customer.name,  # always present due to inner join
            "items": items,
            "balance": s.balance,
            "total_paid": s.total_paid,
        })

    return jsonify(data)



# ------------------ Get Single Sale ------------------ #
@token_required
@sales_bp.route('/<int:sale_id>', methods=['GET'])
def get_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    sale_items = SaleItem.query.filter_by(sale_id=sale.id, status=1).all()

    items = [{
        "product_id": i.product_id,
        "product_name": i.product_name,
        "quantity": i.quantity,
        "unit_price": i.unit_price,
        "total_price": i.total_price
    } for i in sale_items]

    return jsonify({
        "sale_id": sale.id,
        "sale_number": sale.sale_number,
        "total_amount": sale.total_amount,
        "payment_status": sale.payment_status,
        "sale_date": sale.sale_date,
        "created_at": sale.created_at,
        "updated_at": sale.updated_at,
        "items": items
    })


# ------------------ Update Sale ------------------ #
@token_required
@sales_bp.route('/<int:sale_id>', methods=['PUT'])
def update_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    data = request.json
    new_items = data.get('items')

    # Reverse old GL entries
    if sale.transaction_no:
        original_entries = GeneralLedger.query.filter_by(transaction_no=sale.transaction_no).all()
        for entry in original_entries:
            reverse_type = 'Credit' if entry.transaction_type == 'Debit' else 'Debit'
            reverse_entry = GeneralLedger(
                account_id=entry.account_id,
                transaction_type=reverse_type,
                amount=entry.amount,
                description=f"Reversal of {entry.description} before update",
                transaction_date=datetime.utcnow(),
                transaction_no=entry.transaction_no
            )
            db.session.add(reverse_entry)

    # Update Sale main fields
    sale.sale_number = data.get('sale_number', sale.sale_number)
    sale.payment_status = data.get('payment_status', sale.payment_status)
    update_timestamps(sale)

    # Update sale items
    if new_items:
        # Restore stock from old items
        for item in sale.saleitem_set:
            product = Product.query.get(item.product_id)
            if product:
                product.quantity += item.quantity
                db.session.add(product)
            db.session.delete(item)

        # Add new items
        total_amount = 0
        for item in new_items:
            product = Product.query.get(item['product_id'])
            if not product:
                return jsonify({"error": f"Product {item['product_id']} not found"}), 404
            if product.quantity < item['quantity']:
                return jsonify({"error": f"Insufficient stock for {product.name}"}), 400

            product.quantity -= item['quantity']
            db.session.add(product)

            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                product_name=product.name,
                quantity=item['quantity'],
                unit_price=product.price,
                total_price=product.price * item['quantity'],
                status=1
            )
            update_timestamps(sale_item)
            total_amount += sale_item.total_price
            db.session.add(sale_item)

        sale.total_amount = total_amount

        # Post new GL entries
        txn_id, txn_no_str = generate_transaction_number('SAL')
        entries = [
            {"account_id": 1, "transaction_type": "Debit", "amount": total_amount},   # Cash/Bank
            {"account_id": 2, "transaction_type": "Credit", "amount": total_amount}  # Sales Revenue
        ]
        gl_entries = post_to_ledger(entries, txn_id, description=f"Sale #{sale.id} updated")
        sale.transaction_no = txn_id

    db.session.commit()
    return jsonify({"message": "Sale updated with GL entries", "sale_id": sale.id})


# from sqlalchemy import or_
# from sqlalchemy import or_

# ------------------ Soft Delete Sale (Status = 9) ------------------ #
@token_required
@sales_bp.route('/<int:sale_id>', methods=['DELETE'])
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)

    try:
        # 1️⃣ Soft delete sale
        sale.status = 9
        update_timestamps(sale)
        db.session.add(sale)

        # 2️⃣ Soft delete sale items & restore stock
        sale_items = SaleItem.query.filter_by(sale_id=sale.id, status=1).all()
        for item in sale_items:
            item.status = 9
            update_timestamps(item)

            # Restore product stock
            product = Product.query.get(item.product_id)
            if product:
                product.quantity += item.quantity
                db.session.add(product)

            db.session.add(item)

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
        print("gl_entries ",len(gl_entries))

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
        return jsonify({"message": f"Sale #{sale_id} soft deleted (status=9), stock restored, GL reversed"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Failed to delete sale: {str(e)}"}), 500
