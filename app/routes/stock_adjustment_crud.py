from flask import Blueprint, request, jsonify
from app import db
from app.models import ProductUnit, StockAdjustment, Product

stock_adjustment_bp = Blueprint(
    "stock_adjustment_bp",
    __name__,
    url_prefix="/stock-adjustments"
)

# ------------------------------------------------
# Serializer
# ------------------------------------------------
def serialize_adjustment(adj):
    """
    Serialize a StockAdjustment instance to dict with unit info
    """
    unit = adj.unit  # from relationship]
    if adj.unit is None:
        unit = ProductUnit.query.filter(ProductUnit.product_id==adj.product_id,ProductUnit.conversion_quantity==1,ProductUnit.status==1 ).first()
    
    
    return {
        'id': adj.id,
        'product_id': adj.product_id,
        'product_name': adj.product.name if adj.product else None,
        'unit_id': adj.unit_id if adj.unit_id else unit.id,
        'unit_name': unit.unit_name if unit else None,              # ← Added
        'adjustment_type': adj.adjustment_type,
        'quantity': float(adj.quantity),                            # quantity in the selected unit
        'previous_quantity': float(adj.previous_quantity) if adj.previous_quantity is not None else None,
        'new_quantity': float(adj.new_quantity) if adj.new_quantity is not None else None,
        'reason': adj.reason,
        'adjusted_at': adj.adjusted_at.isoformat() if adj.adjusted_at else None,
        'transaction_no': adj.transaction_no,
        'status': adj.status,
    }

# ------------------------------------------------
# GET ALL
# ------------------------------------------------
@stock_adjustment_bp.route("/", methods=["GET"])
def get_all_adjustments():
    adjustments = StockAdjustment.query.filter(StockAdjustment.status != 9).all()
    return jsonify([serialize_adjustment(a) for a in adjustments]), 200


# ------------------------------------------------
# GET ONE
# ------------------------------------------------
@stock_adjustment_bp.route("/<int:id>", methods=["GET"])
def get_adjustment(id):
    adjustment = StockAdjustment.query.get(id)
    if not adjustment or adjustment.status == 9:
        return jsonify({"error": "Stock adjustment not found"}), 404

    return jsonify(serialize_adjustment(adjustment)), 200


# ------------------------------------------------
# CREATE
# ------------------------------------------------
@stock_adjustment_bp.route("/", methods=["POST"])
def create_adjustment():
    data = request.get_json() or {}

    required = ["product_id", "adjustment_type", "quantity_change"]
    for f in required:
        if f not in data:
            return jsonify({"error": f"{f} is required"}), 400

    # ✅ Correct way to load product
    product = db.session.get(Product, data["product_id"])
    if not product:
        return jsonify({"error": "Product not found"}), 404

    previous_qty = float(product.quantity or 0)

    adj_type = data["adjustment_type"].upper()
    qty = float(data.get("quantity_change", 0))

    # ✅ Unit conversion (optional but recommended)
    unit_multiplier = 1
    if data.get("unit_id"):
        unit = db.session.get(ProductUnit, data["unit_id"])
        if not unit:
            return jsonify({"error": "Invalid unit"}), 400
        unit_multiplier = unit.conversion_quantity

    actual_qty = qty * unit_multiplier

    if adj_type == "INCREASE":
        new_qty = previous_qty + actual_qty

    elif adj_type == "DECREASE":
        new_qty = previous_qty - actual_qty
        if new_qty < 0:
            return jsonify({"error": "Stock cannot go below zero"}), 400

    else:
        return jsonify({"error": "adjustment_type must be INCREASE or DECREASE"}), 400

    # ✅ Update product stock
    product.quantity = new_qty
    db.session.add(product)   # IMPORTANT

    adjustment = StockAdjustment(
        product_id=product.id,
        unit_id=data.get("unit_id"),
        adjustment_type=adj_type,
        quantity=qty,
        previous_quantity=previous_qty,
        new_quantity=new_qty,
        reason=data.get("reason", ""),
        status=data.get("status", 1)
    )

    db.session.add(adjustment)
    db.session.commit()

    return jsonify({
        "message": "Stock adjustment created",
        "previous_qty": previous_qty,
        "new_qty": new_qty
    }), 201

# @stock_adjustment_bp.route("/", methods=["POST"])
# def create_adjustment():
#     data = request.get_json()

#     required = ["product_id", "adjustment_type", "quantity_change"]
#     for f in required:
#         if f not in data:
#             return jsonify({"error": f"{f} is required"}), 400

#     product = Product.query.get(data["product_id"])
#     if not product:
#         return jsonify({"error": "Product not found"}), 404

#     previous_qty = product.quantity or 0

#     adj_type = data["adjustment_type"].upper()
#     qty = int(data["quantity_change"] or 0)

#     if adj_type == "INCREASE":
#         new_qty = previous_qty + qty

#     elif adj_type == "DECREASE":
#         new_qty = previous_qty - qty
#         if new_qty < 0:
#             return jsonify({"error": "Stock cannot go below zero"}), 400

#     else:
#         return jsonify({"error": "adjustment_type must be INCREASE or DECREASE"}), 400

#     # Update product stock
#     product.quantity = new_qty

#     adjustment = StockAdjustment(
#         product_id=data["product_id"],
#         adjustment_type=adj_type,
#         quantity=qty,
#         previous_quantity=previous_qty,
#         new_quantity=new_qty,
#         reason=data.get("reason", ""),
#         status=data.get("status", 1)
#     )

#     db.session.add(adjustment)
#     db.session.commit()

#     return jsonify({
#         "message": "Stock adjustment created",
#         "adjustment": serialize_adjustment(adjustment)
#     }), 201


# ------------------------------------------------
# UPDATE (PUT)
# ------------------------------------------------
@stock_adjustment_bp.route("/<int:id>", methods=["PUT"])
def update_adjustment(id):
    adjustment = StockAdjustment.query.get(id)
    if not adjustment or adjustment.status == 9:
        return jsonify({"error": "Stock adjustment not found"}), 404

    data = request.get_json()
    product = adjustment.product

    # First reverse original effect
    if adjustment.adjustment_type.upper() == "INCREASE":
        product.quantity -= adjustment.quantity
    else:
        product.quantity += adjustment.quantity

    previous_qty = product.quantity

    new_type = data.get("adjustment_type", adjustment.adjustment_type).upper()
    new_qty = int(data.get("quantity_change", adjustment.quantity))

    # Apply new effect
    if new_type == "INCREASE":
        final_qty = previous_qty + new_qty

    elif new_type == "DECREASE":
        final_qty = previous_qty - new_qty
        if final_qty < 0:
            return jsonify({"error": "Stock cannot go below zero"}), 400

    else:
        return jsonify({"error": "adjustment_type must be INCREASE or DECREASE"}), 400

    product.quantity = final_qty

    adjustment.adjustment_type = new_type
    adjustment.quantity = new_qty
    adjustment.previous_quantity = previous_qty
    adjustment.new_quantity = final_qty
    adjustment.reason = data.get("reason", adjustment.reason)
    adjustment.status = data.get("status", adjustment.status)

    db.session.commit()

    return jsonify({
        "message": "Stock adjustment updated",
        "adjustment": serialize_adjustment(adjustment)
    }), 200


# ------------------------------------------------
# PATCH
# ------------------------------------------------
@stock_adjustment_bp.route("/<int:id>", methods=["PATCH"])
def patch_adjustment(id):
    adjustment = StockAdjustment.query.get(id)
    if not adjustment or adjustment.status == 9:
        return jsonify({"error": "Stock adjustment not found"}), 404

    data = request.get_json()
    product = adjustment.product

    # Undo old effect
    if adjustment.adjustment_type.upper() == "INCREASE":
        product.quantity -= adjustment.quantity
    else:
        product.quantity += adjustment.quantity

    previous_qty = product.quantity

    new_type = data.get("adjustment_type", adjustment.adjustment_type).upper()
    new_qty = int(data.get("quantity_change", adjustment.quantity))

    if new_type == "INCREASE":
        final_qty = previous_qty + new_qty

    elif new_type == "DECREASE":
        final_qty = previous_qty - new_qty
        if final_qty < 0:
            return jsonify({"error": "Stock cannot go below zero"}), 400

    else:
        return jsonify({"error": "adjustment_type must be INCREASE or DECREASE"}), 400

    # Apply
    product.quantity = final_qty

    adjustment.adjustment_type = new_type
    adjustment.quantity = new_qty
    adjustment.previous_quantity = previous_qty
    adjustment.new_quantity = final_qty

    for f in ["reason", "status"]:
        if f in data:
            setattr(adjustment, f, data[f])

    db.session.commit()

    return jsonify({
        "message": "Stock adjustment partially updated",
        "adjustment": serialize_adjustment(adjustment)
    }), 200


# ------------------------------------------------
# DELETE – REVERSE ONLY THE CHANGE
# ------------------------------------------------
@stock_adjustment_bp.route("/<int:id>", methods=["DELETE"])
def delete_adjustment(id):
    adjustment = StockAdjustment.query.get(id)
    if not adjustment or adjustment.status == 9:
        return jsonify({"error": "Stock adjustment not found"}), 404

    product = adjustment.product

    # Reverse the effect
    if adjustment.adjustment_type.upper() == "INCREASE":
        product.quantity -= adjustment.quantity
    else:
        product.quantity += adjustment.quantity

    adjustment.status = 9

    db.session.commit()

    return jsonify({"message": "Stock adjustment deleted"}), 200
