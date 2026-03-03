# app/__init__.py
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    # This is the only correct path that works on Render + locally
    app = Flask(__name__, static_folder='static', static_url_path='/')

    app.config.from_object('app.config.Config')
    app.config["SECRET_KEY"] = "sjhardwaresecretkey"

    db.init_app(app)
    migrate.init_app(app, db)

    # Allow frontend from any domain (Render + localhost)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # ==================== REGISTER ALL BLUEPRINTS ====================
    from app.routes.inventory import inventory_bp
    from app.routes.suppliers import suppliers_bp
    from app.routes.sales import sales_bp
    from app.routes.payments import payments_bp
    from app.routes.expenses import expenses_bp
    from app.routes.accounts import accounts_bp
    from app.routes.ledger import ledger_bp
    from app.routes.users import users_bp
    from app.routes.customer import customer_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.reports import reports_bp
    from app.routes.stock_adjustment_crud import stock_adjustment_bp


    app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
    app.register_blueprint(suppliers_bp, url_prefix='/api/suppliers')
    app.register_blueprint(sales_bp, url_prefix='/api/sales')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    app.register_blueprint(expenses_bp, url_prefix='/api/expenses')
    app.register_blueprint(accounts_bp, url_prefix='/api/accounts')
    app.register_blueprint(ledger_bp, url_prefix='/api/ledgers')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(customer_bp, url_prefix='/api/customer')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(stock_adjustment_bp,url_prefix='/api/stock-adjustments')


    # ==================== SERVE VUE FRONTEND (THIS MUST BE LAST!) ====================
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def serve_vue(path):
        if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        else:
            index_path = os.path.join(app.static_folder, "index.html")
            if os.path.exists(index_path):
                return send_from_directory(app.static_folder, "index.html")
            else:
                return "ERROR: index.html not found! Check if Vue was built correctly.", 500

    return app