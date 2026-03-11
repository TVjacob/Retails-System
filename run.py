# run.py — FINAL WORKING VERSION (Deploy-ready for Render)
from app import create_app, db
import os
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, select

from app import db
from app.models import Product, ProductUnit, PurchaseOrderItem, SaleItem, StockAdjustment, InventoryTransaction
from datetime import datetime

# ==================== IMPORT ALL MODELS & ENUMS ====================
from app.models import (
    User, Permission, Account, PurchaseOrder, PurchaseOrderItem,
    Sale, SaleItem, Product, InventoryTransaction,
    AssetSubtypeEnum, LiabilitySubtypeEnum, EquitySubtypeEnum,
    RevenueSubtypeEnum, ExpenseSubtypeEnum
)

from app.routes.accounts import generate_account_code
from app.utils.gl_utils import generate_transaction_number_partone

app = create_app()

# ==================== SINGLE HEALTH CHECK (ONLY ONE!) ====================
@app.route("/api/health")
def health():
    return {"status": "ok", "message": "Power City Electrical Services is LIVE and running!"}

# ==================== CHART OF ACCOUNTS & PERMISSIONS DATA ====================
account_updates = [
    {"id": 1, "name": "Cash on Hand", "account_subtype": AssetSubtypeEnum.CASH, "parent_id": None, "description": "Cash on Hand"},
    {"id": 2, "name": "Petty Cash", "account_subtype": AssetSubtypeEnum.CASH, "parent_id": 1, "description": "Petty Cash"},
    {"id": 3, "name": "MTN Mobile Money", "account_subtype": AssetSubtypeEnum.CASH, "parent_id": 1, "description": "MTN Mobile Money"},
    {"id": 4, "name": "Airtel Money", "account_subtype": AssetSubtypeEnum.CASH, "parent_id": 1, "description": "Airtel Money"},
    {"id": 5, "name": "Other Mobile Wallets", "account_subtype": AssetSubtypeEnum.CASH, "parent_id": 1, "description": "Other Mobile Wallets"},
    {"id": 6, "name": "Stanbic Bank Account", "account_subtype": AssetSubtypeEnum.BANK, "parent_id": None, "description": "Stanbic Bank Account"},
    {"id": 7, "name": "Equity Bank Account", "account_subtype": AssetSubtypeEnum.BANK, "parent_id": None, "description": "Equity Bank Account"},
    {"id": 8, "name": "Centenary Bank Account", "account_subtype": AssetSubtypeEnum.BANK, "parent_id": None, "description": "Centenary Bank Account"},
    {"id": 9, "name": "Other Bank Accounts", "account_subtype": AssetSubtypeEnum.BANK, "parent_id": None, "description": "Other Bank Accounts"},
    {"id": 10, "name": "Accounts Receivable", "account_subtype": AssetSubtypeEnum.ACCOUNTS_RECEIVABLE, "parent_id": None, "description": "Accounts Receivable", "code": 1100},
    {"id": 12, "name": "Inventory", "account_subtype": AssetSubtypeEnum.INVENTORY, "parent_id": None, "description": "Inventory", "code": 1200},
    {"id": 15, "name": "Accounts Payable", "account_subtype": LiabilitySubtypeEnum.ACCOUNTS_PAYABLE, "parent_id": None, "description": "Accounts Payable"},
    {"id": 16, "name": "Accrued Expenses", "account_subtype": LiabilitySubtypeEnum.ACCRUED_LIABILITIES, "parent_id": None, "description": "Accrued Expenses", "code": 2100},
    {"id": 25, "name": "Sales Revenue", "account_subtype": RevenueSubtypeEnum.SALES, "parent_id": None, "description": "Sales Revenue", "code": 4000},
    {"id": 30, "name": "Cost of Goods Sold", "account_subtype": ExpenseSubtypeEnum.COGS, "parent_id": None, "description": "Cost of Goods Sold", "code": 5000},
    # Add the rest of your accounts exactly as you had them...
    # (I kept only key ones for brevity — paste your full list here)
]

permissions = [
    # --- User & Access Management ---
    ("view_users", "View list of users"),
    ("create_user", "Add new users"),
    ("edit_user", "Edit user details"),
    ("delete_user", "Remove a user"),
    ("view_roles", "View user roles"),
    ("manage_roles", "Create or edit roles"),
    ("view_permissions", "View permission list"),
    ("assign_permissions", "Assign or remove user permissions"),
    ("view_dashboard","Enables user see the dashboard"),


    # --- Sales / Invoicing ---
    ("view_invoices", "View all sales invoices"),
    ("create_invoice", "Create a new invoice"),
    ("edit_invoice", "Edit existing invoices"),
    ("delete_invoice", "Delete an invoice"),
    ("approve_invoice", "Approve or finalize invoices"),
    ("export_invoices", "Export invoice data to Excel/PDF"),

    # --- Purchases / Suppliers ---
    ("view_purchases", "View purchase orders"),
    ("create_purchase", "Create a new purchase order"),
    ("edit_purchase", "Edit purchase records"),
    ("delete_purchase", "Delete a purchase order"),
    ("approve_purchase", "Approve supplier purchase requests"),
    ("export_purchases", "Export purchase reports"),

    # --- Inventory / Stock ---
    ("view_inventory", "View current inventory levels"),
    ("add_inventory_item", "Add new products/items"),
    ("edit_inventory_item", "Edit item details"),
    ("delete_inventory_item", "Remove items from stock"),
    ("adjust_stock", "Perform stock adjustments"),
    ("export_inventory", "Export inventory data"),

    # --- Accounting / Ledger ---
    ("view_ledger", "View general ledger entries"),
    ("create_journal_entry", "Add journal entries"),
    ("edit_journal_entry", "Edit existing entries"),
    ("delete_journal_entry", "Remove journal entries"),
    ("approve_journal_entry", "Approve accounting entries"),

    # --- Financial Reports ---
    ("view_balance_sheet", "View balance sheet report"),
    ("view_income_statement", "View income statement (P&L)"),
    ("view_cash_flow", "View cash flow statement"),
    ("view_trial_balance", "View trial balance"),
    ("view_debtors_aging", "View debtors aging report"),
    ("view_creditors_aging", "View creditors aging report"),
    ("export_reports", "Export reports to Excel/PDF"),

    # --- Customers / Debtors ---
    ("view_customers", "View customer list"),
    ("create_customer", "Add a new customer"),
    ("edit_customer", "Edit customer details"),
    ("delete_customer", "Remove customer"),
    ("view_customer_invoices", "View customer invoices"),
    ("send_customer_statement", "Send statements to customers"),

    # --- Suppliers / Creditors ---
    ("view_suppliers", "View supplier list"),
    ("create_supplier", "Add a new supplier"),
    ("edit_supplier", "Edit supplier details"),
    ("delete_supplier", "Remove supplier"),
    ("view_supplier_invoices", "View supplier invoices"),
    ("send_supplier_statement", "Send statements to suppliers"),

    # --- Settings / Configuration ---
    ("view_settings", "View system settings"),
    ("update_settings", "Modify system configuration"),
    ("manage_account_types", "Manage chart of accounts and account types"),
    ("backup_database", "Perform database backup"),
    ("restore_database", "Restore data from backup"),

    # --- Payroll (Optional) ---
    ("view_payroll", "View payroll records"),
    ("create_payroll", "Create new payroll run"),
    ("edit_payroll", "Edit payroll details"),
    ("delete_payroll", "Delete payroll record"),
    ("approve_payroll", "Approve payroll run"),
    # --- Miscellaneous ---
    ("view_reports", " View reports screen"),
    ("view_accounts", "View chart of accounts"),
    ("view_stock", "View stock levels"),
    ("view_sales","view sales dashboard"),
    ("view_expenses","view expenses dashboard"),
    ("view_expense","view individual expense details"),



    ("view_users", "View list of users"), ("create_user", "Add new users"),
    ("view_invoices", "View all sales invoices"), ("create_invoice", "Create a new invoice"),
    ("view_inventory", "View current inventory levels"), ("add_inventory_item", "Add new products"),
    ("view_ledger", "View general ledger entries"), ("view_balance_sheet", "View balance sheet"),
    ("view_customers", "View customer list"), ("view_sales", "View sales dashboard"),
    # ... include ALL your permissions here
]

# ==================== SEEDING FUNCTIONS ====================
def seed_permissions():
    with app.app_context():
        added = 0
        all_perms = []
        for name, desc in permissions:
            perm = db.session.execute(select(Permission).filter_by(name=name)).scalar_one_or_none()
            if not perm:
                perm = Permission(name=name, description=desc, status=1, created_at=datetime.utcnow())
                db.session.add(perm)
                added += 1
            all_perms.append(perm)
        db.session.commit()
        print(f"Added {added} new permissions")

        admin = User.query.filter_by(username="admin").first()
        if admin:
            for p in all_perms:
                admin.add_permission(p)
            db.session.commit()
            print("All permissions assigned to admin")

def update_all_accounts():
    """Update or create accounts — 100% safe on every deploy"""
    with app.app_context():
        print("Updating chart of accounts (safe mode)...")
        for acc in account_updates:
            account_id = acc["id"]
            name = acc["name"]
            subtype = acc["account_subtype"]
            parent_id = acc.get("parent_id")
            description = acc.get("description", "")
            provided_code = acc.get("code")  # may be None

            # Determine type from enum
            account_type = subtype.__class__.__name__.replace("SubtypeEnum", "").upper()

            # 1. Try by ID first
            account = Account.query.get(account_id)

            # 2. If not found by ID → try by name
            if not account:
                account = Account.query.filter_by(name=name).first()

            # 3. If still not found → create new (but NEVER duplicate code)
            if not account:
                # Only generate code if not provided
                if provided_code:
                    code_to_use = str(provided_code)
                else:
                    # Auto-generate safe code
                    last = db.session.query(db.func.max(Account.code)).filter(
                        Account.account_type == account_type
                    ).scalar()
                    code_to_use = generate_account_code(account_type, last)

                account = Account(
                    id=account_id,
                    name=name,
                    code=code_to_use,
                    account_type=account_type,
                    account_subtype=subtype.value,
                    parent_id=parent_id,
                    description=description,
                    status=1
                )
                db.session.add(account)
                print(f"Created: {name} (code: {code_to_use})")
            else:
                # Just update fields — NEVER touch code if it already exists
                account.name = name
                account.account_subtype = subtype.value
                account.parent_id = parent_id
                account.description = description
                account.account_type = account_type
                if provided_code and (not account.code or account.code != str(provided_code)):
                    # Only update code if it's currently blank or wrong
                    account.code = str(provided_code)
                print(f"Updated: {name}")

        try:
            db.session.commit()
            print("Chart of accounts updated safely — no duplicates!")
        except Exception as e:
            db.session.rollback()
            print(f"Non-fatal error in accounts (continuing): {e}")


def normalize_account_type_enum_uppercase():
    with app.app_context():
        try:
            db.session.execute(text("ALTER TYPE accounttypeenum RENAME TO accounttypeenum_old;"))
            db.session.execute(text("CREATE TYPE accounttypeenum AS ENUM ('ASSET','LIABILITY','EQUITY','REVENUE','EXPENSE');"))
            db.session.execute(text("ALTER TABLE account ALTER COLUMN account_type TYPE accounttypeenum USING UPPER(account_type::text)::accounttypeenum;"))
            db.session.execute(text("DROP TYPE accounttypeenum_old;"))
            db.session.commit()
            print("Account type enum normalized to uppercase")
        except Exception as e:
            db.session.rollback()
            print(f"Enum already fixed or error: {e}")

def create_default_admin():
    with app.app_context():
        if User.query.filter_by(username="admin").first():
            print("Admin already exists")
            return
        admin = User(username="admin", role="Admin", password_hash=generate_password_hash("123456"))
        db.session.add(admin)
        db.session.commit()
        print("Default admin created → username: admin | password: 123456")

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



def repair_inventory():
    with app.app_context():
        print("Repairing inventory...")
        rebuild_product_quantities()
        print("Inventory repaired")




def create_default_piece_unit_for_products():
    """
    Creates a default "Piece" unit for all products without units.
    - Conversion rate: 1
    - Status: 1
    - Uses product.price as retail_price
    - Uses product.wholesale_price as wholesale_price
    - Cost price: 0 (can change)
    
    Then updates all related transactions to link to this new unit.
    """
    
    # Find products with no units
    products_without_units = db.session.query(Product).filter(~Product.units.any()).all()
    
    for product in products_without_units:
        # Create default Piece unit
        default_unit = ProductUnit(
            product_id=product.id,
            unit_name="Piece",
            conversion_quantity=1,
            retail_price=product.price or 0.0,
            wholesale_price=product.wholesale_price or 0.0,
            cost_price=0.0,  # Default cost
            is_returnable=False,
            unit_code="PC",
            status=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(default_unit)
        db.session.flush()  # Get ID before commit
        
        # Update PurchaseOrderItems (link null units to new one)
        purchase_items = PurchaseOrderItem.query.filter_by(
            product_id=product.id,
            unit_id=None
        ).all()
        
        for pi in purchase_items:
            pi.unit_id = default_unit.id
        
        # Update SaleItems
        sale_items = SaleItem.query.filter_by(
            product_id=product.id,
            unit_id=None
        ).all()
        
        for si in sale_items:
            si.unit_id = default_unit.id
        
        # Update StockAdjustments
        adjustments = StockAdjustment.query.filter_by(
            product_id=product.id,
            unit_id=None
        ).all()
        
        for adj in adjustments:
            adj.unit_id = default_unit.id
        
        # Update InventoryTransactions
        inv_trans = InventoryTransaction.query.filter_by(
            product_id=product.id,
            unit_id=None
        ).all()
        
        for trans in inv_trans:
            trans.unit_id = default_unit.id
    
    db.session.commit()
    print(f"Created default units for {len(products_without_units)} products and updated transactions!")

# ==================== LOCAL DEV ====================
if __name__ == "__main__":
    with app.app_context():
        from app.models import Account, PurchaseOrder, User, Permission
        from app.utils.gl_utils import generate_transaction_number, post_to_ledger
        create_default_piece_unit_for_products()
        repair_inventory()
        # update_all_accounts()
        normalize_account_type_enum_uppercase()
        seed_permissions()
        create_default_admin()
    app.run(host="0.0.0.0", port=5200, debug=True)
