
from flask import Blueprint, request, jsonify
from app import db
from app.models import Product, Category, ProductUnit, PurchaseOrder, PurchaseOrderItem
from datetime import datetime
from sqlalchemy import or_, text
from app.utils.auth import token_required
from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_
from sqlalchemy.orm import joinedload

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')


# ----------------------------------------------------------------------
# Helper: latest cost price (still used for display in the table)
# ----------------------------------------------------------------------
def get_latest_cost_price(product_id):
    latest_po_item = (
        PurchaseOrderItem.query
        .filter_by(product_id=product_id)
        .filter(PurchaseOrderItem.status != 9)
        .order_by(PurchaseOrderItem.id.desc())
        .first()
    )
    return latest_po_item.unit_price if latest_po_item else 0.0


# ----------------------------------------------------------------------
# Re-build product.quantity (base units) from purchases & sales
# ----------------------------------------------------------------------
from sqlalchemy import text

def rebuild_product_quantities():
    try:
        sql = text("""
        WITH purchase_totals AS (
            SELECT 
                poi.product_id,
                COALESCE(SUM(poi.quantity * COALESCE(pu.conversion_quantity, 1.0)), 0) AS total_purchased_base
            FROM purchase_order_item poi
            LEFT JOIN product_unit pu ON poi.unit_id = pu.id
            WHERE poi.status != 9
            GROUP BY poi.product_id
        ),
        sale_totals AS (
            SELECT 
                si.product_id,
                COALESCE(SUM(si.quantity * COALESCE(pu.conversion_quantity, 1.0)), 0) AS total_sold_base
            FROM sale_item si
            LEFT JOIN product_unit pu ON si.unit_id = pu.id
            WHERE si.status != 9
            GROUP BY si.product_id
        ),
        adjustment_totals AS (
            SELECT
                sa.product_id,
                COALESCE(SUM(
                    CASE
                        WHEN UPPER(sa.adjustment_type) = 'INCREASE'
                            THEN sa.quantity * COALESCE(pu.conversion_quantity, 1.0)
                        WHEN UPPER(sa.adjustment_type) = 'DECREASE'
                            THEN -1 * sa.quantity * COALESCE(pu.conversion_quantity, 1.0)
                        ELSE 0
                    END
                ), 0) AS total_adjusted_base
            FROM stock_adjustment sa
            LEFT JOIN product_unit pu ON sa.unit_id = pu.id
            WHERE sa.status != 9
            GROUP BY sa.product_id
        )

        UPDATE product p
        SET quantity =
            COALESCE(pur.total_purchased_base, 0)
          - COALESCE(sal.total_sold_base, 0)
          + COALESCE(adj.total_adjusted_base, 0)

        FROM purchase_totals pur
        FULL JOIN sale_totals sal 
            ON pur.product_id = sal.product_id
        FULL JOIN adjustment_totals adj
            ON COALESCE(pur.product_id, sal.product_id) = adj.product_id

        WHERE p.id = COALESCE(pur.product_id, sal.product_id, adj.product_id);
        """)

        db.session.execute(sql)
        db.session.commit()
        print("✅ Product quantities rebuilt successfully (including stock adjustments).")

    except Exception as e:
        db.session.rollback()
        print(f"❌ Failed to rebuild product quantities: {e}")



# ----------------------------------------------------------------------
# CREATE PRODUCT + UNITS
# ----------------------------------------------------------------------
@token_required
@inventory_bp.route('/products', methods=['POST'])
def add_product():
    data = request.get_json()

    # ---- Product core fields ------------------------------------------------
    product = Product(
        name=data['name'],
        sku=data['sku'],
        category_id=data.get('category_id'),
        quantity=0.0,                     # always calculated later
        price=0.0,                        # ignored – price lives in units
        wholesale_price=0.0,
        status=1
    )
    db.session.add(product)
    db.session.flush()   # get product.id

    # ---- Units --------------------------------------------------------------
    units = data.get('units', [])
    if not units:
        db.session.rollback()
        return jsonify({"error": "At least one unit is required"}), 400

    for u in units:
        unit = ProductUnit(
            product_id=product.id,
            unit_name=u['unit_name'],
            conversion_quantity=u.get('conversion_quantity', 1.0),
            retail_price=u.get('retail_price', 0.0),
            wholesale_price=u.get('wholesale_price', 0.0),
            is_returnable=u.get('is_returnable', False),
            unit_code=u.get('unit_code')
        )
        db.session.add(unit)

    db.session.commit()
    return jsonify({"message": "Product added", "product_id": product.id}), 201


# ----------------------------------------------------------------------
# LIST ALL PRODUCTS (for table)
# ----------------------------------------------------------------------
@token_required
@inventory_bp.route('/products', methods=['GET'])
def list_products():
    # rebuild_product_quantities()
    prods = Product.query.filter(Product.status == 1).all()
    result = []

    for p in prods:
        cat = Category.query.filter_by(id=p.category_id, status=1).first()
        units = ProductUnit.query.filter_by(product_id=p.id, status=1).all()
        units_data = [{
            "id": u.id,
            "unit_name": u.unit_name,
            "conversion_quantity": u.conversion_quantity,
            "retail_price": u.retail_price,
            "wholesale_price": u.wholesale_price,
            "is_returnable": u.is_returnable,
            "unit_code": u.unit_code
        } for u in units]

        result.append({
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "category_id": p.category_id,
            "category_name": cat.name if cat else None,
            "quantity": round(p.quantity, 4),
            # NOTE: price/wholesale_price on product are **not** returned
            "cost_price": get_latest_cost_price(p.id),
            "units": units_data,
            "status": p.status
        })

    return jsonify(result)


# ----------------------------------------------------------------------
# GET SINGLE PRODUCT (core fields only – units via separate endpoint)
# ----------------------------------------------------------------------
@token_required
@inventory_bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    # rebuild_product_quantities()
    p = Product.query.get_or_404(id)
    cat = Category.query.filter_by(id=p.category_id, status=1).first()

    return jsonify({
        "id": p.id,
        "name": p.name,
        "sku": p.sku,
        "category_id": p.category_id,
        "category_name": cat.name if cat else None,
        "quantity": round(p.quantity, 4),
        "cost_price": get_latest_cost_price(p.id)
        # units are fetched separately with /products/<id>/units
    })


# ----------------------------------------------------------------------
# NEW: GET UNITS ONLY (used by the edit modal)
# ----------------------------------------------------------------------
@token_required
@inventory_bp.route('/products/<int:id>/units', methods=['GET'])
def get_product_units(id):
    Product.query.get_or_404(id)  # just to 404 if product missing
    units = ProductUnit.query.filter_by(product_id=id, status=1).all()
    purchase_price = PurchaseOrderItem.query.filter_by(product_id=id, status=1).first()
    product = Product.query.filter_by(id=id).first()

    units_data = [{
        "id": u.id,
        "unit_name": u.unit_name,
        "conversion_quantity": u.conversion_quantity,
        "retail_price": u.retail_price,
        "wholesale_price": u.wholesale_price,
        "is_returnable": u.is_returnable,
        "unit_code": u.unit_code,
        "cost_price":purchase_price.unit_price if purchase_price else 0,
        "quantity":product.quantity if product else 0,
    } for u in units]

    return jsonify(units_data)


# ----------------------------------------------------------------------
# UPDATE PRODUCT + UNITS
# ----------------------------------------------------------------------
@token_required
@inventory_bp.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    print("am here under the put  ...  ")
    data = request.get_json()

    # ---- Core fields --------------------------------------------------------
    product.name = data.get('name', product.name)
    product.sku = data.get('sku', product.sku)
    product.category_id = data.get('category_id', product.category_id)
    product.updated_at = datetime.utcnow()

    # ---- Units --------------------------------------------------------------
    incoming_units = data.get('units') or []
    if not incoming_units:
        return jsonify({"error": "At least one unit required"}), 400

    # Delete old units (simple approach – replace all)
    # ProductUnit.query.filter_by(product_id=id).update()

    for u in incoming_units:
        unit_data = dict(u)  # Make a copy for easier access
        if u.get('id'):
            product_details=ProductUnit.query.filter_by(id=u['id']).first()
            print(" the value of u ",u )
            unit =dict(u)
            print("unit['unit_name'] ",unit['unit_name'] )
            print("unit['retail_price'] ",unit['retail_price'] )
            print("unit['conversion_quantity'] ",unit['conversion_quantity'] )

            # product_details.product_id=id,
            product_details.unit_name=unit['unit_name']
            product_details.conversion_quantity=unit['conversion_quantity'] or  1.0
            product_details.retail_price=unit['retail_price'] or 0
            product_details.wholesale_price=unit['wholesale_price'] or 0
            product_details.is_returnable=unit['is_returnable'] or False
            product_details.unit_code=unit['unit_code']

        else:
            unit = ProductUnit(
            product_id=product.id,
            unit_name=u['unit_name'],
            conversion_quantity=u.get('conversion_quantity', 1.0),
            retail_price=u.get('retail_price', 0.0),
            wholesale_price=u.get('wholesale_price', 0.0),
            is_returnable=u.get('is_returnable', False),
            unit_code=u.get('unit_code', "") 
            )
            db.session.add(unit)

        # product_details.id==u['id'],
        # )
        # db.session.add(unit)
        # db.session.commit()

        db.session.flush()


    db.session.commit()
    return jsonify({"message": "Product updated", "product_id": id})


# ----------------------------------------------------------------------
# DELETE PRODUCT (hard delete)
# ----------------------------------------------------------------------
@token_required
@inventory_bp.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    product.status = 9
    db.session.commit()
        # cascade deletes units
    # db.session.commit()
    return jsonify({"message": "Product deleted", "product_id": id})


# ----------------------------------------------------------------------
# CATEGORY CRUD (unchanged)
# ----------------------------------------------------------------------
@token_required
@inventory_bp.route('/categories', methods=['POST'])
def add_category():
    data = request.json
    cat = Category(name=data['name'], description=data.get('description'), status=1)
    db.session.add(cat)
    db.session.commit()
    return jsonify({"message": "Category added", "category_id": cat.id}), 201


@token_required
@inventory_bp.route('/categories', methods=['GET'])
def list_categories():
    cats = Category.query.filter(Category.status == 1).all()
    return jsonify([{"id": c.id, "name": c.name, "description": c.description} for c in cats])


@token_required
@inventory_bp.route('/categories/<int:id>', methods=['GET'])
def get_category(id):
    c = Category.query.get_or_404(id)
    return jsonify({"id": c.id, "name": c.name, "description": c.description})


@token_required
@inventory_bp.route('/categories/<int:id>', methods=['PUT'])
def update_category(id):
    c = Category.query.get_or_404(id)
    data = request.json
    c.name = data.get('name', c.name)
    c.description = data.get('description', c.description)
    c.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Category updated"})


@token_required
@inventory_bp.route('/categories/<int:id>', methods=['DELETE'])
def delete_category(id):
    c = Category.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Category deleted"})


# ----------------------------------------------------------------------
# SEARCH PRODUCTS (for autocomplete in sales)
# ----------------------------------------------------------------------
# @token_required
# @inventory_bp.route('/products/search', methods=['GET'])
# def search_products():
#     query = request.args.get('name', '').strip()
#     if not query:
#         return jsonify([])

#     # Search by name or SKU (case-insensitive)
#     search_pattern = f"%{query}%"
#     products = Product.query.filter(
#         Product.status == 1,
#         or_(
#             Product.name.ilike(search_pattern),
#             Product.sku.ilike(search_pattern)
#         )
#     ).limit(20).all()  # limit results for performance
#     # details = db.session.query(PurchaseOrderItem.unit_price).filter(PurchaseOrderItem.product_id).first()


#     result = []
#     for p in products:
#         cat = Category.query.get(p.category_id)

#         # Load units
#         units = ProductUnit.query.filter_by(product_id=p.id, status=1).all()
#         purchase_price = PurchaseOrderItem.query.filter_by(product_id=p.id, status=1).first()

#         units_data = [{
#             "id": u.id,
#             "unit_name": u.unit_name,
#             "conversion_quantity": float(u.conversion_quantity),
#             "retail_price": float(u.retail_price or 0),
#             "wholesale_price": float(u.wholesale_price or 0),
#             "is_returnable": bool(u.is_returnable),
#             "unit_code": u.unit_code,
#             "purchase_price":purchase_price.unit_price if purchase_price else 0
#         } for u in units]

#         result.append({
#             "id": p.id,
#             "name": p.name,
#             "sku": p.sku,
#             "category_id": p.category_id,
#             "category_name": cat.name if cat else None,
#             "quantity": round(float(p.quantity), 4),
#             "units": units_data  # ← Critical for sales page!
#         })

#     return jsonify(result)



# @token_required
# @inventory_bp.route('/products/search', methods=['GET'])
# def search_products():
#     query = request.args.get('name', '').strip()
#     if not query:
#         return jsonify([])

#     search_pattern = f"%{query}%"

#     # Main product query (active only, limit results)
#     products = (
#         Product.query
#         .filter(
#             Product.status == 1,
#             or_(
#                 Product.name.ilike(search_pattern),
#                 Product.sku.ilike(search_pattern)
#             )
#         )
#         .options(joinedload(Product.category))
#         .limit(20)
#         .all()
#     )

#     # Subquery: Get the latest purchase date per product
#     latest_po_subq = (
#         db.session.query(
#             PurchaseOrderItem.product_id,
#             func.max(PurchaseOrder.purchase_date).label('latest_date')
#         )
#         .join(PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.purchase_order_id)
#         .filter(PurchaseOrder.status == 1, PurchaseOrderItem.status == 1)
#         .group_by(PurchaseOrderItem.product_id)
#         .subquery()
#     )

#     # Subquery: Get latest purchase price + unit for each product
#     latest_price_subq = (
#         db.session.query(
#             PurchaseOrderItem.product_id,
#             PurchaseOrderItem.unit_id,
#             PurchaseOrderItem.unit_price,
#             PurchaseOrderItem.quantity.label('po_quantity')  # optional - can be used for weighted avg later
#         )
#         .join(PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.purchase_order_id)
#         .join(latest_po_subq, and_(
#             PurchaseOrderItem.product_id == latest_po_subq.c.product_id,
#             PurchaseOrder.purchase_date == latest_po_subq.c.latest_date
#         ))
#         .filter(PurchaseOrder.status == 1, PurchaseOrderItem.status == 1)
#         .subquery()
#     )

#     result = []

#     for product in products:
#         category = product.category

#         # Get all active units for this product
#         units = ProductUnit.query.filter_by(product_id=product.id, status=1).all()

#         # Get latest purchase record (if any)
#         latest_purchase = (
#             db.session.query(latest_price_subq)
#             .filter(latest_price_subq.c.product_id == product.id)
#             .first()
#         )

#         units_data = []

#         if latest_purchase:
#             # Latest purchase info
#             po_unit_id = latest_purchase.unit_id
#             po_unit_price = float(latest_purchase.unit_price or 0)

#             # Get the conversion quantity of the purchased unit
#             po_unit = ProductUnit.query.get(po_unit_id)
#             po_conversion = float(po_unit.conversion_quantity) if po_unit else 1.0

#             # Calculate base-unit purchase price
#             base_purchase_price = po_unit_price / po_conversion if po_conversion > 0 else po_unit_price
#         else:
#             # No purchase history → fallback to 0
#             base_purchase_price = 0.0

#         for unit in units:
#             conversion = float(unit.conversion_quantity or 1)

#             # Calculate purchase price for THIS unit
#             # = base price * this unit's conversion
#             unit_purchase_price = base_purchase_price * conversion

#             units_data.append({
#                 "id": unit.id,
#                 "unit_name": unit.unit_name,
#                 "conversion_quantity": conversion,
#                 "retail_price": float(unit.retail_price or 0),
#                 "wholesale_price": float(unit.wholesale_price or 0),
#                 "is_returnable": bool(unit.is_returnable),
#                 "unit_code": unit.unit_code or "",
#                 "purchase_price": round(unit_purchase_price, 2)  # ← this is what you want!
#             })

#         result.append({
#             "id": product.id,
#             "name": product.name,
#             "sku": product.sku,
#             "category_id": product.category_id,
#             "category_name": category.name if category else None,
#             "quantity": round(float(product.quantity or 0), 4),
#             "units": units_data
#         })

#     return jsonify(result)


@token_required
@inventory_bp.route('/products/search', methods=['GET'])
def search_products():
    query = request.args.get('name', '').strip()
    if not query:
        return jsonify([])

    search_pattern = f"%{query}%"

    # Main product query
    products = (
        Product.query
        .filter(
            Product.status == 1,
            or_(
                Product.name.ilike(search_pattern),
                Product.sku.ilike(search_pattern)
            )
        )
        .options(joinedload(Product.category))
        .limit(20)
        .all()
    )

    if not products:
        return jsonify([])

    product_ids = [p.id for p in products]

    # Subquery: Get the single most recent purchase per product
    # Using ROW_NUMBER() to pick exactly one record when dates are tied
    latest_po_cte = (
        db.session.query(
            PurchaseOrderItem.product_id,
            PurchaseOrderItem.unit_id,
            PurchaseOrderItem.unit_price,
            PurchaseOrderItem.quantity,
            PurchaseOrder.purchase_date,
            func.row_number().over(
                partition_by=PurchaseOrderItem.product_id,
                order_by=[
                    PurchaseOrder.purchase_date.desc(),
                    PurchaseOrderItem.id.desc()  # deterministic tie-breaker
                ]
            ).label('rn')
        )
        .join(PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.purchase_order_id)
        .filter(
            PurchaseOrder.status != 9,
            PurchaseOrderItem.status != 9,
            PurchaseOrderItem.product_id.in_(product_ids)
        )
        .cte('latest_po')
    )

    # Get only the latest row (rn = 1) for each product
    latest_purchases = (
        db.session.query(latest_po_cte)
        .filter(latest_po_cte.c.rn == 1)
        .all()
    )

    # Make lookup dict: product_id → latest purchase info
    latest_dict = {lp.product_id: lp for lp in latest_purchases}

    result = []

    for product in products:
        category = product.category

        # Get latest purchase for this product (if exists)
        latest = latest_dict.get(product.id)

        # Calculate base-unit purchase price
        if latest:
            po_unit = ProductUnit.query.get(latest.unit_id)
            po_conversion = float(po_unit.conversion_quantity) if po_unit else 1.0
            po_unit_price = float(latest.unit_price or 0)

            # Base price = price per base unit
            base_purchase_price = po_unit_price / po_conversion if po_conversion > 0 else po_unit_price
        else:
            base_purchase_price = 0.0

        # Load all active units
        units = ProductUnit.query.filter_by(product_id=product.id, status=1).all()

        units_data = []

        for unit in units:
            conversion = float(unit.conversion_quantity or 1)

            # Purchase price in this unit = base price × conversion factor
            unit_purchase_price = base_purchase_price * conversion

            units_data.append({
                "id": unit.id,
                "unit_name": unit.unit_name,
                "conversion_quantity": conversion,
                "retail_price": float(unit.retail_price or 0),
                "wholesale_price": float(unit.wholesale_price or 0),
                "is_returnable": bool(unit.is_returnable),
                "unit_code": unit.unit_code or "",
                "purchase_price": round(unit_purchase_price, 2),  # ← final value per unit
                # Optional: show source info (good for debugging)
                "last_purchase_date": latest.purchase_date.strftime('%Y-%m-%d') if latest else None,
                "source_unit_id": latest.unit_id if latest else None
            })

        result.append({
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "category_id": product.category_id,
            "category_name": category.name if category else None,
            "quantity": round(float(product.quantity or 0), 4),
            "units": units_data
        })

    return jsonify(result)