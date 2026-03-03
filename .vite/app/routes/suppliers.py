from flask import Blueprint, request, jsonify
from sqlalchemy import or_
# Suppliers Blueprint for managing supplier and purchase order operations.
# This module provides CRUD operations for suppliers and purchase orders, including:
# - Retrieving all suppliers or a single supplier by ID.
# - Adding, updating, and deleting suppliers.
# - Retrieving all purchase orders or a specific purchase order by ID.
# - Adding new purchase orders with multiple items, updating existing purchase orders, and deleting them.
# - Handling payments for purchase orders.

# Purchase Order Status:
# 1 = Ready to Invoice
# 2 = Partially Paid
# 3 = Fully Paid
from app import db
from app.models import Account, Category, GeneralLedger, InventoryTransaction, Product, ProductUnit, Supplier, PurchaseOrder, PurchaseOrderItem, SupplierPayment
from app.utils.auth import token_required
from app.utils.gl_utils import post_to_ledger, generate_transaction_number
from datetime import datetime

from sqlalchemy.orm import joinedload
# from flask import jsonify

suppliers_bp = Blueprint('suppliers', __name__, url_prefix='/suppliers')

# ------------------ Supplier CRUD ------------------ #

@token_required
# Get all suppliers
@suppliers_bp.route('/', methods=['GET'])
def get_suppliers():
    print("Request headers:", request.headers)

    suppliers = Supplier.query.filter_by(status=1).all()
    data = [{
        'id': s.id,
        'name': s.name,
        'contact': s.contact,
        'email': s.email,
        'status': s.status,
        'created_at': s.created_at
    } for s in suppliers]
    return jsonify(data), 200


@token_required
# Get single supplier
@suppliers_bp.route('/<int:id>', methods=['GET'])

def get_supplier(id):
    s = Supplier.query.get_or_404(id)
    return jsonify({
        'id': s.id,
        'name': s.name,
        'contact': s.contact,
        'email': s.email,
        'status': s.status,
        'created_at': s.created_at
    })


@token_required
# Add a new supplier
@suppliers_bp.route('/', methods=['POST'])

def add_supplier():
    data = request.get_json()
    supplier = Supplier(
        name=data['name'],
        contact=data.get('contact'),
        email=data.get('email'),
        status=1
    )
    db.session.add(supplier)
    db.session.commit()
    return jsonify({'message': 'Supplier created successfully', 'id': supplier.id}), 201


@token_required
# Update supplier
@suppliers_bp.route('/<int:id>', methods=['PUT'])

def update_supplier(id):
    s = Supplier.query.get_or_404(id)
    data = request.get_json()
    s.name = data.get('name', s.name)
    s.contact = data.get('contact', s.contact)
    s.email = data.get('email', s.email)
    s.status = data.get('status', s.status)
    db.session.commit()
    return jsonify({'message': 'Supplier updated successfully', 'id': s.id})


@token_required
# Delete supplier
@suppliers_bp.route('/<int:id>', methods=['DELETE'])

def delete_supplier(id):
    s = Supplier.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    return jsonify({'message': 'Supplier deleted successfully', 'id': id})

# ------------------ Purchase Orders ------------------ #
# ------------------ Get Purchase Orders ------------------ #
@token_required
@suppliers_bp.route('/orders', methods=['GET'])
def get_purchase_orders():
        # Get query params
    search = request.args.get('search', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    
    
    
    query = PurchaseOrder.query.join(Supplier).filter(PurchaseOrder.status.in_([1,2,3,4,5]))

    # orders = PurchaseOrder.query.filter(PurchaseOrder.status.in_([1, 2, 3, 4, 5])).all()
        # Search filter
    if search:
        search_pattern = f"%{search.lower()}%"
        query = query.filter(
            db.or_(
                db.func.lower(Supplier.name).like(search_pattern),
                db.func.lower(PurchaseOrder.invoice_number).like(search_pattern),
                db.func.lower(PurchaseOrder.memo).like(search_pattern)
            )
        )
        # Date filter
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(PurchaseOrder.purchase_date >= start_dt)
        except ValueError:
            return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD."}), 400

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(PurchaseOrder.purchase_date <= end_dt)
        except ValueError:
            return jsonify({"error": "Invalid end_date format. Use YYYY-MM-DD."}), 400
        

    orders = query.all()
    data = []
    # for o in orders:
    #     data.append({
    #         'id': o.id,
    #         'supplier_id': o.supplier_id,
    #         'supplier_name': o.supplier.name if o.supplier else None,
    #         'invoice_number': o.invoice_number,
    #         'total_amount': o.total_amount,
    #         'total_paid': o.total_paid,
    #         'total_balance': o.total_balance,
    #         'status': o.status,
    #         'created_at': o.created_at.strftime("%Y-%m-%d"),
    #         'purchase_date': o.purchase_date.strftime("%Y-%m-%d") if o.purchase_date else None
    #     })
    # return jsonify(data), 200


    data = [{
        'id': o.id,
        'supplier_id': o.supplier_id,
        'supplier_name': o.supplier.name if o.supplier else None,
        'invoice_number': o.invoice_number,
        'memo': o.memo,
        'total_amount': o.total_amount,
        'total_paid': o.total_paid,
        'total_balance': o.total_balance,
        'status': o.status,
        'created_at': o.created_at.strftime("%Y-%m-%d"),
        'purchase_date': o.purchase_date.strftime("%Y-%m-%d"),
        'items': [
            {
                'id': item.id,
                'product_id': item.product_id,
                'product_name': item.product.name if item.product else None,
                'quantity': item.quantity,
                'unit_price': item.unit_price,
                'total_price': item.total_price
            } for item in o.items
        ]
    } for o in orders]

    return jsonify(data), 200


# @token_required
# # Get all purchase orders
# @suppliers_bp.route('/orders', methods=['GET'])

# def get_purchase_orders():
#     orders = PurchaseOrder.query.filter(PurchaseOrder.status.in_([1, 2, 3,5,4])).all()
#     data = [{
#         'id': o.id,
#         'supplier_id': o.supplier_id,
#         'supplier_name': o.supplier.name if o.supplier else None,
#         'invoice_number': o.invoice_number,
#         'total_amount': o.total_amount,
#         'total_paid': o.total_paid,
#         'total_balance': o.total_balance,
#         'status': o.status,
#         'created_at': o.created_at.strftime("%Y-%m-%d"),
#         'purchase_date':o.purchase_date.strftime("%Y-%m-%d")
#     } for o in orders]
#     return jsonify(data), 200

# ------------------ Get Single Purchase Order ------------------ #
@token_required
@suppliers_bp.route('/orders/<int:id>', methods=['GET'])
def get_purchase_order(id):
    po = PurchaseOrder.query.get_or_404(id)

    items = []
    for item in po.items:
        if item.status == 9:
            continue
        unit = ProductUnit.query.get(item.unit_id) if item.unit_id else None
        items.append({
            'id': item.id,
            'product_id': item.product_id,
            'product_name': item.product.name if item.product else 'Unknown',
            'unit_id': item.unit_id,
            'unit_name': unit.unit_name if unit else 'N/A',
            'quantity': float(item.quantity),
            'unit_price': float(item.unit_price),
            'total_price': float(item.total_price)
        })

    return jsonify({
        'id': po.id,
        'supplier_id': po.supplier_id,
        'supplier_name': po.supplier.name if po.supplier else None,
        'invoice_number': po.invoice_number,
        'memo': po.memo,
        'purchase_date': po.purchase_date.strftime("%Y-%m-%d") if po.purchase_date else None,
        'total_amount': float(po.total_amount),
        'total_paid': float(po.total_paid),
        'total_balance': float(po.total_balance),
        'status': po.status,
        'items': items
    })

# -----
# @token_required
# # Get purchase order by ID
# @suppliers_bp.route('/orders/<int:id>', methods=['GET'])

# def get_purchase_order(id):
#     po = PurchaseOrder.query.get_or_404(id)
#     return jsonify({
#         'id': po.id,
#         'supplier_id': po.supplier_id,
#         'supplier_name': po.supplier.name if po.supplier else None,
#         'invoice_number': po.invoice_number,
#         'memo': po.memo,
#         'purchase_date': po.purchase_date.strftime("%Y-%m-%d"),
#         'total_amount': po.total_amount,
#         'total_paid': po.total_paid,
#         'total_balance': po.total_balance,
#         'status': po.status,
#         'items': [{
#             'id': item.id,
#             'product_id': item.product_id,
#             'product_name': Product.query.get(item.product_id).name if item.product_id else None,
#             'stock_quantity': Product.query.get(item.product_id).quantity if item.product_id else None,
#             'unit': db.session.query(Category).filter_by(id=Product.query.get(item.product_id).category_id).first().name if item.product_id and Product.query.get(item.product_id) else None,
#             'quantity': item.quantity,
#             'unit_price': item.unit_price,
#             'total_price': item.total_price,
#             'status': item.status
#         } for item in po.items]
#     })



# @token_required
# # Add new purchase order with multiple items
# @suppliers_bp.route('/orders', methods=['POST'])
# def add_purchase_order():
#     data = request.get_json()

#     if not data.get('items') or len(data['items']) == 0:
#         return jsonify({'error': 'At least one item is required'}), 400

#     # Create new Purchase Order
#     po = PurchaseOrder(
#         supplier_id=data['supplier_id'],
#         invoice_number=data['invoice_number'],
#         purchase_date=data.get('purchase_date', datetime.utcnow()),
#         memo=data.get('memo'),
#         status=1
#     )
#     db.session.add(po)
#     db.session.flush()  # to get PO id before committing

#     total_amount = 0
#     txn_id, txn_str = generate_transaction_number('CREDIT-PAY',transaction_date=po.purchase_date)
#     po.transaction_no=txn_id
#     # Add purchase order items
#     for item_data in data['items']:
#         item = PurchaseOrderItem(
#             purchase_order_id=po.id,
#             product_id=item_data['product_id'],
#             quantity=item_data['quantity'],
#             unit_price=item_data['cost_price'],
#             status=1
#         )
#         item.calculate_total()
#         db.session.add(item)
#         total_amount += item.total_price

#         # Update product stock
#         product = Product.query.get(item.product_id)
#         if product:
#             product.quantity = (product.quantity or 0) + item.quantity
#             db.session.add(product)
#                 # ✅ Add InventoryTransaction entry
#         inv_txn = InventoryTransaction(
#             transaction_no=txn_id,
#             purchase_order_id=po.id,
#             product_id=item.product_id,
#             quantity=item.quantity,
#             unit_price=item.unit_price,
#             total_price=item.total_price,
#             transaction_type='Purchase',
#             status=1
#         )
#         db.session.add(inv_txn)

#     # Update totals
#     po.total_amount = total_amount
#     po.total_balance = total_amount

#     entries = [
#         {
#             "account_id": 1200,  # Stock Inventory
#             "transaction_type": "Debit",
#             "amount": total_amount
#         },
#         {
#             "account_id": 2100,# Accounts Payable  
#             "transaction_type": "Credit",
#             "amount": total_amount
#         }
#     ]

#     post_to_ledger(
#         entries,
#         transaction_no_id=txn_id,
#         description=f"Credit for PO #{po.id}",
#         transaction_date=po.purchase_date
#     )

#     db.session.commit()

#     return jsonify({'message': 'Purchase Order created successfully', 'po_id': po.id}), 200
@token_required
@suppliers_bp.route('/orders', methods=['POST'])
def add_purchase_order():
    data = request.get_json()

    if not data.get('items') or len(data['items']) == 0:
        return jsonify({'error': 'At least one item is required'}), 400

    # Create new Purchase Order
    po = PurchaseOrder(
        supplier_id=data['supplier_id'],
        invoice_number=data['invoice_number'],
        purchase_date=datetime.strptime(data.get('purchase_date'), '%Y-%m-%d') if data.get('purchase_date') else datetime.utcnow(),
        memo=data.get('memo'),
        status=1
    )
    db.session.add(po)
    db.session.flush()  # Get po.id

    total_amount = 0.0
    txn_id, txn_str = generate_transaction_number('CREDIT-PAY', transaction_date=po.purchase_date)
    po.transaction_no = txn_id

    # Process each item
    for item_data in data['items']:
        product_id = item_data['product_id']
        unit_id = item_data.get('unit_id')
        quantity = float(item_data['quantity'])  # quantity in selected unit
        unit_price = float(item_data['unit_price'])

        product = Product.query.get_or_404(product_id)

        if not unit_id:
            return jsonify({'error': f'unit_id required for {product.name}'}), 400

        unit = ProductUnit.query.filter_by(id=unit_id, product_id=product_id, status=1).first()
        if not unit:
            return jsonify({'error': f'Invalid unit for {product.name}'}), 400

        # Convert to base units for stock addition
        base_quantity = quantity * unit.conversion_quantity

        # Create PurchaseOrderItem
        item = PurchaseOrderItem(
            purchase_order_id=po.id,
            product_id=product_id,
            unit_id=unit.id,
            quantity=quantity,  # stored in selected unit
            unit_price=unit_price,
            total_price=quantity * unit_price,
            status=1
        )
        db.session.add(item)
        total_amount += item.total_price

        # Update product stock in base units
        product.quantity = (product.quantity or 0) + base_quantity
        db.session.add(product)

        # Inventory Transaction (inflow in base units)
        inv_txn = InventoryTransaction(
            transaction_no=txn_id,
            purchase_order_id=po.id,
            product_id=product_id,
            unit_id=unit.id,
            quantity=base_quantity,  # base units
            unit_price=unit_price,
            total_price=quantity * unit_price,
            transaction_type='Purchase',
            status=1
        )
        db.session.add(inv_txn)

    # Update PO totals
    po.total_amount = total_amount
    po.total_balance = total_amount

    # GL Entries
    entries = [
        {"account_id": 1200, "transaction_type": "Debit", "amount": total_amount},  # Inventory
        {"account_id": 2100, "transaction_type": "Credit", "amount": total_amount}  # Accounts Payable
    ]

    post_to_ledger(
        entries,
        transaction_no_id=txn_id,
        description=f"Credit for PO #{po.id}",
        transaction_date=po.purchase_date
    )

    db.session.commit()

    return jsonify({
        'message': 'Purchase Order created successfully',
        'po_id': po.id,
        'total_amount': total_amount
    }), 201
# Update purchase order details
@token_required
@suppliers_bp.route('/orders/<int:id>', methods=['PUT'])
def update_purchase_order(id):
    po = PurchaseOrder.query.get_or_404(id)
    data = request.get_json()

    po.supplier_id = data.get('supplier_id', po.supplier_id)
    po.invoice_number = data.get('invoice_number', po.invoice_number)
    po.memo = data.get('memo', po.memo)
    po.purchase_date = data.get('purchase_date', po.purchase_date)

    # Update items if provided
    if 'items' in data:
        for item_data in data['items']:
            if 'id' in item_data:
                # Update existing item
                item = PurchaseOrderItem.query.get(item_data['id'])
                if item and item.purchase_order_id == po.id:
                    item.quantity = item_data.get('quantity', item.quantity)
                    item.unit_price = item_data.get('unit_price', item.unit_price)
                    item.calculate_total()
            else:
                # Add new item
                new_item = PurchaseOrderItem(
                    purchase_order_id=po.id,
                    product_id=item_data['product_id'],
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    status=1
                )
                new_item.calculate_total()
                db.session.add(new_item)



    # Recalculate totals
    po.update_totals()
    db.session.commit()

    return jsonify({'message': 'Purchase Order updated successfully', 'id': po.id})


# @token_required
# # Delete purchase order
# @suppliers_bp.route('/orders/<int:id>', methods=['DELETE'])

# def delete_purchase_order(id):
#     po = PurchaseOrder.query.get_or_404(id)
#     db.session.delete(po)
#     db.session.commit()
#     return jsonify({'message': 'Purchase Order deleted successfully', 'id': id})


@token_required
@suppliers_bp.route('/orders/<int:id>/pay', methods=['POST'])
def pay_purchase_order(id):
    po = PurchaseOrder.query.get_or_404(id)
    data = request.get_json()

    amount = data['amount']
    payment_type = data.get('payment_type', 'Cash')
    reference = data.get('reference')
    payment_account_id = data.get('payment_account_id')
    transaction_date_str = data.get('transaction_date')  # <-- New field from frontend

    # Validate transaction date or fallback to UTC now
    try:
        if transaction_date_str:
            # Parse provided date
            transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d')
        else:
            transaction_date = datetime.utcnow()
    except ValueError:
        return jsonify({'error': 'Invalid transaction date format. Use YYYY-MM-DD'}), 400

    if not payment_account_id:
        return jsonify({'error': 'Payment account is required'}), 400

    # Validate payment account exists
    payment_account = Account.query.get(payment_account_id)
    if not payment_account:
        return jsonify({'error': 'Invalid payment account selected'}), 400

    if amount <= 0:
        return jsonify({'error': 'Invalid payment amount'}), 400

    if amount > po.total_balance:
        return jsonify({'error': 'Payment exceeds remaining balance'}), 400

    # ---------- Generate Transaction Number First ----------
    txn_id, txn_str = generate_transaction_number('SUPP-PAY',transaction_date=transaction_date)

    # Create supplier payment record AFTER txn number exists
    payment = SupplierPayment(
        purchase_order_id=po.id,
        payment_account_id=payment_account_id,
        amount=amount,
        payment_type=payment_type,
        reference=reference,
        transaction_no=txn_id,  # ✅ Now guaranteed to exist
        payment_date=transaction_date,
        status=1
    )
    db.session.add(payment)
    db.session.flush()

    # Update PurchaseOrder totals
    po.total_paid += amount
    po.total_balance = po.total_amount - po.total_paid
    po.status = 3 if po.total_balance == 0 else 5 if po.total_paid == po.total_balance else 4

    # ---------- Generate GL Double Entry ----------
    entries = [
        {
            "account_id": 2100,  # Accounts Payable
            "transaction_type": "Debit",
            "amount": amount
        },
        {
            "account_id": payment_account.code,  # Dynamic account
            "transaction_type": "Credit",
            "amount": amount
        }
    ]

    post_to_ledger(
        entries,
        transaction_no_id=txn_id,
        description=f"Payment for PO #{po.id}",
        transaction_date=transaction_date
    )

    # Final commit
    db.session.commit()

    return jsonify({
        "message": f"Payment of {amount} recorded for PO #{po.id}",
        "payment_id": payment.id,
        "new_balance": po.total_balance,
        "po_status": po.status,
        "gl_transaction_id": txn_id
    }), 201




# @token_required
# @suppliers_bp.route('/orders/<int:id>/delete', methods=['PUT'])
# def delete_purchase_order(id):
#     """
#     Soft delete a purchase order (status=9) and reverse its GL entries.
#     """
#     po = PurchaseOrder.query.get_or_404(id)

#     # Prevent double deletion
#     if po.status == 9:
#         return jsonify({'error': f'Purchase Order #{po.id} is already deleted'}), 400

#     # ---------- Reverse General Ledger Entries ----------
#     gl_entries = GeneralLedger.query.filter(
#         GeneralLedger.description.in_([
#             f"Credit for PO #{po.id}",
#             f"Payment for PO #{po.id}"
#         ])
#     ).all()

#     if gl_entries:
#         reversal_date = datetime.utcnow()
#         reversal_description = f"Reversal of PO #{po.id} deletion"

#         for entry in gl_entries:
#             reversed_entry = GeneralLedger(
#                 account_id=entry.account_id,
#                 transaction_type="Credit" if entry.transaction_type == "Debit" else "Debit",
#                 amount=entry.amount,
#                 description=reversal_description,
#                 transaction_date=reversal_date,
#                 transaction_no=entry.transaction_no,
#                 status=1
#             )
#             db.session.add(reversed_entry)

#     # ---------- Soft Delete Purchase Order and Related Records ----------
#     po.status = 9

#     # Mark purchase order items as deleted
#     for item in po.items:
#         item.status = 9

#     # Mark supplier payments related to this PO as deleted
#     SupplierPayment.query.filter_by(purchase_order_id=po.id).update({'status': 9})

#     # Optionally rollback stock (inventory transactions)
#     inv_txns = InventoryTransaction.query.filter_by(purchase_order_id=po.id, status=1).all()
#     for txn in inv_txns:
#         txn.status = 9
#         product = Product.query.get(txn.product_id)
#         if product:
#             # Decrease the stock that was previously added
#             product.quantity = (product.quantity or 0) - txn.quantity
#             db.session.add(product)

#     db.session.commit()

#     return jsonify({
#         'message': f'Purchase Order #{po.id} deleted successfully (soft delete)',
#         'reversed_entries': len(gl_entries)
#     }), 200

# ------------------ Soft Delete PO ------------------ #
@token_required
@suppliers_bp.route('/orders/<int:id>/delete', methods=['PUT'])
def delete_purchase_order(id):
    po = PurchaseOrder.query.get_or_404(id)

    if po.status == 9:
        return jsonify({'error': 'Already deleted'}), 400

    # Reverse GL
    gl_entries = GeneralLedger.query.filter(
        or_(
            GeneralLedger.description.ilike(f"%PO #{po.id}%"),
            GeneralLedger.description.ilike(f"%Payment for PO #{po.id}%")
        )
    ).all()

    for entry in gl_entries:
        reversed_entry = GeneralLedger(
            account_id=entry.account_id,
            transaction_type="Credit" if entry.transaction_type == "Debit" else "Debit",
            amount=entry.amount,
            description=f"Reversal of deleted PO #{po.id}",
            transaction_date=datetime.utcnow(),
            transaction_no=entry.transaction_no,
            status=1
        )
        db.session.add(reversed_entry)

    # Rollback stock
    for item in po.items:
        if item.status == 9:
            continue
        unit = ProductUnit.query.get(item.unit_id)
        if unit and item.product:
            base_qty = item.quantity * unit.conversion_quantity
            item.product.quantity = max((item.product.quantity or 0) - base_qty, 0)
            db.session.add(item.product)

    # Soft delete
    po.status = 9
    for item in po.items:
        item.status = 9
    SupplierPayment.query.filter_by(purchase_order_id=po.id).update({'status': 9})
    InventoryTransaction.query.filter_by(purchase_order_id=po.id).update({'status': 9})

    db.session.commit()

    return jsonify({'message': f'PO #{po.id} deleted and stock reversed'}), 200



# @token_required
# @suppliers_bp.route('/orders/<int:id>/edit', methods=['PUT'])
# def edit_purchase_order(id):
#     """
#     Edit an existing purchase order, update stock & inventory transaction log,
#     handle overpayments, and mark as fully paid if necessary.
#     """
#     po = PurchaseOrder.query.get_or_404(id)
#     data = request.get_json()

#     old_total = po.total_amount
#     old_paid = po.total_paid

#     # Update PO header
#     po.supplier_id = data.get('supplier_id', po.supplier_id)
#     po.invoice_number = data.get('invoice_number', po.invoice_number)
#     po.memo = data.get('memo', po.memo)
#     po.purchase_date = data.get('purchase_date', po.purchase_date)

#     # Prepare a new transaction number for this edit
#     txn_id, txn_str = generate_transaction_number('PO-EDIT', transaction_date=po.purchase_date)

#     # ---- Handle items ----
#     if 'items' in data:
#         existing_item_ids = [item.id for item in po.items]
#         new_item_ids = [i.get('id') for i in data['items'] if i.get('id')]

#         # Delete removed items
#         for item in po.items:
#             if item.id not in new_item_ids:
#                 # Reduce product stock accordingly
#                 product = Product.query.get(item.product_id)
#                 if product:
#                     product.quantity = max((product.quantity or 0) - item.quantity, 0)

#                 # Remove old inventory transaction entries for that item
#                 InventoryTransaction.query.filter_by(
#                     purchase_order_id=po.id,
#                     product_id=item.product_id
#                 ).delete()

#                 db.session.delete(item)

#         # Update or add items
#         for item_data in data['items']:
#             if 'id' in item_data and item_data['id']:
#                 # Existing item
#                 item = PurchaseOrderItem.query.get(item_data['id'])
#                 old_qty = item.quantity
#                 item.quantity = item_data.get('quantity', item.quantity)
#                 item.unit_price = item_data.get('unit_price', item.unit_price)
#                 item.calculate_total()

#                 # Adjust stock based on quantity change
#                 qty_diff = item.quantity - old_qty
#                 if qty_diff != 0:
#                     product = Product.query.get(item.product_id)
#                     if product:
#                         product.quantity = (product.quantity or 0) + qty_diff

#                 # Update inventory transaction
#                 inv_txn = InventoryTransaction.query.filter_by(
#                     purchase_order_id=po.id,
#                     product_id=item.product_id
#                 ).first()

#                 if inv_txn:
#                     inv_txn.quantity = item.quantity
#                     inv_txn.unit_price = item.unit_price
#                     inv_txn.total_price = item.total_price
#                     inv_txn.transaction_no = txn_id
#                     inv_txn.transaction_type = 'Purchase'
#                 else:
#                     new_inv = InventoryTransaction(
#                         transaction_no=txn_id,
#                         purchase_order_id=po.id,
#                         product_id=item.product_id,
#                         quantity=item.quantity,
#                         unit_price=item.unit_price,
#                         total_price=item.total_price,
#                         transaction_type='Purchase',
#                         status=1
#                     )
#                     db.session.add(new_inv)

#             else:
#                 # New item
#                 new_item = PurchaseOrderItem(
#                     purchase_order_id=po.id,
#                     product_id=item_data['product_id'],
#                     quantity=item_data['quantity'],
#                     unit_price=item_data['unit_price'],
#                     status=1
#                 )
#                 new_item.calculate_total()
#                 db.session.add(new_item)

#                 # Increase product stock
#                 product = Product.query.get(new_item.product_id)
#                 if product:
#                     product.quantity = (product.quantity or 0) + new_item.quantity

#                 # Add inventory transaction
#                 inv_txn = InventoryTransaction(
#                     transaction_no=txn_id,
#                     purchase_order_id=po.id,
#                     product_id=new_item.product_id,
#                     quantity=new_item.quantity,
#                     unit_price=new_item.unit_price,
#                     total_price=new_item.total_price,
#                     transaction_type='Purchase',
#                     status=1
#                 )
#                 db.session.add(inv_txn)

#     # ---- Recalculate totals ----
#     po.update_totals()
#     new_total = po.total_amount

#     # Get all existing payments
#     payments = SupplierPayment.query.filter_by(purchase_order_id=po.id, status=1).all()
#     total_paid = sum(p.amount for p in payments)

#     # --- Handle overpayment ---
#     if total_paid >= new_total:
#         po.total_paid = new_total
#         po.total_balance = 0
#         po.status = 3  # fully paid

#         excess_payment = total_paid - new_total
#         if excess_payment > 0:
#             # Refund ledger entry
#             refund_txn_id, refund_txn_str = generate_transaction_number('PO-REFUND', transaction_date=po.purchase_date)
#             refund_entries = [
#                 {"account_id": 2100, "transaction_type": "Debit", "amount": excess_payment},  # AP
#                 {"account_id": 1000, "transaction_type": "Credit", "amount": excess_payment}  # Cash/Bank
#             ]
#             post_to_ledger(refund_entries, transaction_no_id=refund_txn_id,
#                            description=f"Refund excess payment for PO #{po.id}",
#                            transaction_date=po.purchase_date)

#             refund_payment = SupplierPayment(
#                 purchase_order_id=po.id,
#                 amount=-excess_payment,
#                 payment_account_id=payments[0].payment_account_id if payments else None,
#                 payment_type='Refund',
#                 payment_date=po.purchase_date,
#                 status=1
#             )
#             db.session.add(refund_payment)
#     else:
#         po.total_paid = total_paid
#         po.total_balance = new_total - total_paid
#         po.status = 2 if po.total_balance > 0 else 3

#     # --- GL Adjustment for total difference ---
#     diff = new_total - old_total
#     if diff != 0:
#         if diff > 0:
#             entries = [
#                 {"account_id": 1200, "transaction_type": "Debit", "amount": diff},
#                 {"account_id": 2100, "transaction_type": "Credit", "amount": diff}
#             ]
#             desc = f"Adjustment for increased PO #{po.id} by {diff}"
#         else:
#             entries = [
#                 {"account_id": 2100, "transaction_type": "Debit", "amount": abs(diff)},
#                 {"account_id": 1200, "transaction_type": "Credit", "amount": abs(diff)}
#             ]
#             desc = f"Adjustment for reduced PO #{po.id} by {abs(diff)}"

#         post_to_ledger(entries, transaction_no_id=txn_id, description=desc, transaction_date=po.purchase_date)

#     db.session.commit()

#     return jsonify({
#         "message": f"Purchase Order #{po.id} updated successfully",
#         "old_total": old_total,
#         "new_total": new_total,
#         "total_paid": po.total_paid,
#         "balance": po.total_balance,
#         "status": po.status,
#         "refund": total_paid - new_total if total_paid > new_total else 0,
#         "gl_transaction_id": txn_id
#     }), 200



# ------------------ Pay Purchase Order (unchanged, already good) ------------------ #
# Your pay_purchase_order route is already excellent — no changes needed

# # ------------------ Edit Purchase Order (with unit support) ------------------ #
# @token_required
# @suppliers_bp.route('/orders/<int:id>/edit', methods=['PUT'])
# def edit_purchase_order(id):
#     po = PurchaseOrder.query.get_or_404(id)
#     data = request.get_json()

#     old_total = po.total_amount

#     # Update header
#     po.supplier_id = data.get('supplier_id', po.supplier_id)
#     po.invoice_number = data.get('invoice_number', po.invoice_number)
#     po.memo = data.get('memo', po.memo)
#     po.purchase_date = datetime.strptime(data.get('purchase_date'), '%Y-%m-%d') if data.get('purchase_date') else po.purchase_date

#     txn_id, txn_str = generate_transaction_number('PO-EDIT', transaction_date=po.purchase_date)

#     if 'items' in data:
#         # Track old items for stock rollback
#         old_items = {item.id: item for item in po.items if item.status != 9}

#         # Delete removed items
#         incoming_ids = {i.get('id') for i in data['items'] if i.get('id')}
#         for old_item in list(old_items.values()):
#             if old_item.id not in incoming_ids:
#                 # Rollback stock
#                 unit = ProductUnit.query.get(old_item.unit_id)
#                 if unit and old_item.product:
#                     base_qty = old_item.quantity * unit.conversion_quantity
#                     old_item.product.quantity = max((old_item.product.quantity or 0) - base_qty, 0)
#                 old_item.status = 9

#         # Update or add items
#         for item_data in data['items']:
#             product_id = item_data['product_id']
#             unit_id = item_data['unit_id']
#             quantity = float(item_data['quantity'])
#             unit_price = float(item_data['unit_price'])

#             product = Product.query.get_or_404(product_id)
#             unit = ProductUnit.query.filter_by(id=unit_id, product_id=product_id, status=1).first_or_404()

#             base_qty = quantity * unit.conversion_quantity

#             if 'id' in item_data and item_data['id']:
#                 # Update existing
#                 item = PurchaseOrderItem.query.get(item_data['id'])
#                 old_base = item.quantity * unit.conversion_quantity
#                 qty_diff = base_qty - old_base

#                 item.quantity = quantity
#                 item.unit_price = unit_price
#                 item.total_price = quantity * unit_price

#                 # Adjust stock
#                 product.quantity = (product.quantity or 0) + qty_diff
#             else:
#                 # New item
#                 item = PurchaseOrderItem(
#                     purchase_order_id=po.id,
#                     product_id=product_id,
#                     unit_id=unit_id,
#                     quantity=quantity,
#                     unit_price=unit_price,
#                     total_price=quantity * unit_price,
#                     status=1
#                 )
#                 db.session.add(item)
#                 product.quantity = (product.quantity or 0) + base_qty

#             # Update inventory transaction
#             inv_txn = InventoryTransaction.query.filter_by(
#                 purchase_order_id=po.id,
#                 product_id=product_id,
#                 unit_id=unit_id
#             ).first()
#             if inv_txn:
#                 inv_txn.quantity = base_qty
#                 inv_txn.unit_price = unit_price
#                 inv_txn.total_price = quantity * unit_price
#                 inv_txn.transaction_no = txn_id
#             else:
#                 new_inv = InventoryTransaction(
#                     transaction_no=txn_id,
#                     purchase_order_id=po.id,
#                     product_id=product_id,
#                     unit_id=unit_id,
#                     quantity=base_qty,
#                     unit_price=unit_price,
#                     total_price=quantity * unit_price,
#                     transaction_type='Purchase',
#                     status=1
#                 )
#                 db.session.add(new_inv)

#     # Recalculate totals
#     po.update_totals()
#     diff = po.total_amount - old_total

#     if diff != 0:
#         entries = [
#             {"account_id": 1200, "transaction_type": "Debit" if diff > 0 else "Credit", "amount": abs(diff)},
#             {"account_id": 2100, "transaction_type": "Credit" if diff > 0 else "Debit", "amount": abs(diff)}
#         ]
#         post_to_ledger(entries, transaction_no_id=txn_id,
#                        description=f"PO #{po.id} edit adjustment", transaction_date=po.purchase_date)

#     db.session.commit()

#     return jsonify({'message': 'Purchase Order updated successfully', 'po_id': po.id})


# ------------------ Edit Purchase Order (FIXED: unit_id updates) ------------------ #
@token_required
@suppliers_bp.route('/orders/<int:id>/edit', methods=['PUT'])
def edit_purchase_order(id):
    po = PurchaseOrder.query.get_or_404(id)
    data = request.get_json()

    old_total = po.total_amount

    # Update header
    po.supplier_id = data.get('supplier_id', po.supplier_id)
    po.invoice_number = data.get('invoice_number', po.invoice_number)
    po.memo = data.get('memo', po.memo)
    if data.get('purchase_date'):
        po.purchase_date = datetime.strptime(data.get('purchase_date'), '%Y-%m-%d')

    txn_id, txn_str = generate_transaction_number('PO-EDIT', transaction_date=po.purchase_date)

    if 'items' in data:
        # Track old items for stock rollback
        old_items = {item.id: item for item in po.items if item.status != 9}

        # Delete removed items (soft delete + stock rollback)
        incoming_ids = {i.get('id') for i in data['items'] if i.get('id')}
        for old_item in list(old_items.values()):
            if old_item.id not in incoming_ids:
                unit = ProductUnit.query.get(old_item.unit_id)
                if unit and old_item.product:
                    base_qty = old_item.quantity * unit.conversion_quantity
                    old_item.product.quantity = max((old_item.product.quantity or 0) - base_qty, 0)
                old_item.status = 9

        # Process incoming items
        for item_data in data['items']:
            product_id = item_data['product_id']
            unit_id = item_data['unit_id']
            quantity = float(item_data['quantity'])
            unit_price = float(item_data['unit_price'])

            product = Product.query.get_or_404(product_id)
            unit = ProductUnit.query.filter_by(id=unit_id, product_id=product_id, status=1).first_or_404()

            base_qty = quantity * unit.conversion_quantity

            if 'id' in item_data and item_data['id']:
                # === UPDATE EXISTING ITEM ===
                item = PurchaseOrderItem.query.get_or_404(item_data['id'])

                # Rollback old stock
                old_unit = ProductUnit.query.get(item.unit_id)
                if old_unit:
                    old_base = item.quantity * old_unit.conversion_quantity
                    product.quantity = (product.quantity or 0) - old_base

                # Update fields — INCLUDING UNIT_ID!
                item.unit_id = unit_id
                item.quantity = quantity
                item.unit_price = unit_price
                item.total_price = quantity * unit_price

                # Add new stock
                product.quantity = (product.quantity or 0) + base_qty

            else:
                # === ADD NEW ITEM ===
                item = PurchaseOrderItem(
                    purchase_order_id=po.id,
                    product_id=product_id,
                    unit_id=unit_id,
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=quantity * unit_price,
                    status=1
                )
                db.session.add(item)
                product.quantity = (product.quantity or 0) + base_qty

            # Update or create inventory transaction
            inv_txn = InventoryTransaction.query.filter_by(
                purchase_order_id=po.id,
                product_id=product_id,
                unit_id=unit_id
            ).first()

            if inv_txn:
                inv_txn.quantity = base_qty
                inv_txn.unit_price = unit_price
                inv_txn.total_price = quantity * unit_price
                inv_txn.transaction_no = txn_id
            else:
                new_inv = InventoryTransaction(
                    transaction_no=txn_id,
                    purchase_order_id=po.id,
                    product_id=product_id,
                    unit_id=unit_id,
                    quantity=base_qty,
                    unit_price=unit_price,
                    total_price=quantity * unit_price,
                    transaction_type='Purchase',
                    status=1
                )
                db.session.add(new_inv)

    # Recalculate totals
    po.update_totals()
    diff = po.total_amount - old_total

    if diff != 0:
        entries = [
            {"account_id": 1200, "transaction_type": "Debit" if diff > 0 else "Credit", "amount": abs(diff)},
            {"account_id": 2100, "transaction_type": "Credit" if diff > 0 else "Debit", "amount": abs(diff)}
        ]
        post_to_ledger(entries, transaction_no_id=txn_id,
                       description=f"PO #{po.id} edit adjustment", transaction_date=po.purchase_date)

    db.session.commit()

    return jsonify({'message': 'Purchase Order updated successfully', 'po_id': po.id}), 200


@token_required
@suppliers_bp.route('/purchase-order/<int:purchase_order_id>', methods=['GET'])

def purchase_order_details(purchase_order_id):
    return get_purchase_order_details(purchase_order_id)


def get_purchase_order_details(purchase_order_id):
    """
    Retrieve complete purchase order details including supplier info,
    items, payments, and financial totals.
    """
    # Fetch the Purchase Order with related Supplier, Items, and Payments
    purchase_order = (
        PurchaseOrder.query
        .options(
            joinedload(PurchaseOrder.supplier),
            joinedload(PurchaseOrder.items),
            joinedload(PurchaseOrder.supplier).joinedload(Supplier.purchase_orders)
        )
        .filter(PurchaseOrder.id == purchase_order_id, PurchaseOrder.status != 9)
        .first()
    )

    if not purchase_order:
        return {"error": "Purchase order not found or inactive"}, 404

    # Fetch all payments linked to this purchase order
    payments = SupplierPayment.query.filter_by(
        purchase_order_id=purchase_order_id,
        status=1
    ).all()

    # Calculate totals
    total_amount = sum(item.total_price for item in purchase_order.items if item.status != 9)
    total_paid = sum(payment.amount for payment in payments)
    balance = total_amount - total_paid

    # Prepare item details
    item_details = [
        {
            "product_id": item.product_id,
            "product_name": item.product.name if item.product else None,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "total_price": item.total_price
        }
        for item in purchase_order.items if item.status != 9
    ]

    # Prepare payment details
    payment_details = [

        {
            "payment_id": p.id,
            "amount": p.amount,
            "payment_type": p.payment_type,
            "payment_date": p.payment_date.strftime("%Y-%m-%d"),
            "reference": p.reference,
            "account_id":  Account.query.get(p.payment_account_id).name if p.payment_account_id else None,
        }
        for p in payments
    ]

    # Final response
    response = {
        "purchase_order_id": purchase_order.id,
        "invoice_number": purchase_order.invoice_number,
        "purchase_date": purchase_order.purchase_date.strftime("%Y-%m-%d"),
        "supplier": {
            "supplier_id": purchase_order.supplier.id,
            "name": purchase_order.supplier.name,
            "contact": purchase_order.supplier.contact,
            "email": purchase_order.supplier.email
        },
        "items": item_details,
        "payments": payment_details,
        "summary": {
            "total_amount": total_amount,
            "total_paid": total_paid,
            "balance": balance,
            "grand_total": total_amount  # Can add tax or other charges here later
        }
    }

    return jsonify(response)
