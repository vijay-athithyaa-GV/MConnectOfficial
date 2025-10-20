import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, abort, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.utils import secure_filename
from jinja2 import ChoiceLoader, FileSystemLoader

# ----------------------------------------------
# Flask App Configuration
# ----------------------------------------------
TEMPLATE_DIR = None  # will be set after helper definitions
STATIC_DIR = None

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')

# File upload and data storage configuration
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Resolve app root for templates/static robustly on Azure or local
WWWROOT_DIR = '/home/site/wwwroot'
def _pick_existing_path(primary: str, fallback: str) -> str:
    return primary if os.path.isdir(primary) else fallback

TEMPLATE_DIR = _pick_existing_path(
    os.path.join(BASE_DIR, 'templates'),
    os.path.join(WWWROOT_DIR, 'templates'),
)
STATIC_DIR = _pick_existing_path(
    os.path.join(BASE_DIR, 'static'),
    os.path.join(WWWROOT_DIR, 'static'),
)

# After resolving template/static directories, update Flask app paths
app.template_folder = TEMPLATE_DIR
app.static_folder = STATIC_DIR
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join('/home', 'site', 'wwwroot', 'templates')),
    FileSystemLoader(TEMPLATE_DIR),
])

# Use Azure App Service writable directory when available
IS_AZURE = bool(os.environ.get('WEBSITE_INSTANCE_ID') or os.environ.get('WEBSITE_SITE_NAME'))
DATA_DIR = os.environ.get('DATA_DIR') or (os.path.join('/home', 'site', 'data') if IS_AZURE else BASE_DIR)

UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# Email domain restriction (e.g., only @college.edu)
ALLOWED_EMAIL_DOMAIN = os.environ.get('ALLOWED_EMAIL_DOMAIN', 'college.edu')

# Database configuration (SQLite by default). Store DB in writable data dir
db_path = os.path.join(DATA_DIR, 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----------------------------------------------
# Database Model
# ----------------------------------------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    seller_email = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='available')  # available | sold

    def image_url(self):
        if self.image_filename:
            return url_for('uploaded_file', filename=self.image_filename)
        return url_for('static', filename='placeholder.png')

# Initialize DB (create tables on first run)
class PurchaseRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    buyer_name = db.Column(db.String(120), nullable=False)
    buyer_email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship('Product', backref=db.backref('purchase_requests', lazy=True))


with app.app_context():
    # Create new tables
    db.create_all()
    # Safe migration for Product.status if missing
    try:
        columns = db.session.execute(text("PRAGMA table_info(product)")).mappings().all()
        col_names = {c['name'] for c in columns}
        if 'status' not in col_names:
            db.session.execute(text("ALTER TABLE product ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'available'"))
            db.session.commit()
    except Exception:
        db.session.rollback()

# ----------------------------------------------
# Helpers
# ----------------------------------------------
def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_college_email(email: str) -> bool:
    return isinstance(email, str) and email.lower().endswith(f"@{ALLOWED_EMAIL_DOMAIN}")


# ----------------------------------------------
# Routes
# ----------------------------------------------
@app.route('/')
def index():
    return redirect(url_for('buy'))


@app.route('/buy')
def buy():
    products = Product.query.filter_by(status='available').order_by(Product.created_at.desc()).all()
    categories = sorted({p.category for p in products})
    return render_template('index.html', products=products, categories=categories)


@app.route('/sell')
def sell():
    return redirect(url_for('upload'))


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        price_raw = request.form.get('price', '').strip()
        seller_email = request.form.get('seller_email', '').strip()
        image = request.files.get('image')

        # Basic validation
        errors = []
        if not name:
            errors.append('Product name is required.')
        if not category:
            errors.append('Category is required.')
        if not description:
            errors.append('Description is required.')
        try:
            price = float(price_raw)
            if price <= 0:
                errors.append('Price must be greater than 0.')
        except ValueError:
            errors.append('Price must be a valid number.')
        if not validate_college_email(seller_email):
            errors.append(f'Only emails ending with @{ALLOWED_EMAIL_DOMAIN} can post items.')

        image_filename = None
        if image and image.filename:
            if not allowed_file(image.filename):
                errors.append('Invalid image type. Allowed: png, jpg, jpeg, gif, webp')
            else:
                safe_name = secure_filename(image.filename)
                ext = safe_name.rsplit('.', 1)[1].lower()
                image_filename = f"{uuid.uuid4().hex}.{ext}"
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        if errors:
            for e in errors:
                flash(e, 'error')
            return redirect(url_for('upload'))

        product = Product(
            name=name,
            category=category,
            description=description,
            price=price,
            image_filename=image_filename,
            seller_email=seller_email,
        )
        db.session.add(product)
        db.session.commit()
        flash('Product listed successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('upload.html')


@app.route('/uploads/<path:filename>')
def uploaded_file(filename: str):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    query = Product.query

    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Product.name.ilike(like),
                Product.description.ilike(like),
                Product.category.ilike(like),
            )
        )
    if category:
        query = query.filter(Product.category.ilike(category))

    products = query.order_by(Product.created_at.desc()).all()
    categories = sorted({p.category for p in Product.query.all()})
    return render_template('index.html', products=products, categories=categories, q=q, selected_category=category)


@app.route('/my-listings')
def my_listings():
    seller_email = request.args.get('seller_email', '').strip()
    products = []
    if seller_email:
        products = Product.query.filter_by(seller_email=seller_email).order_by(Product.created_at.desc()).all()
    return render_template('my_listings.html', products=products, seller_email=seller_email)


# Product detail page
@app.route('/product/<int:product_id>')
def product_detail(product_id: int):
    product = Product.query.get_or_404(product_id)
    # Optionally fetch related items in same category (excluding self)
    related = Product.query.filter(
        Product.category.ilike(product.category),
        Product.id != product.id
    ).order_by(Product.created_at.desc()).limit(6).all()
    return render_template('product_detail.html', product=product, related=related)


@app.route('/api/product/<int:product_id>')
def api_product(product_id: int):
    p = Product.query.get_or_404(product_id)
    return jsonify({
        'id': p.id,
        'name': p.name,
        'category': p.category,
        'description': p.description,
        'price': p.price,
        'image_url': p.image_url(),
        'seller_email': p.seller_email,
        'status': p.status,
        'created_at': p.created_at.isoformat(),
    })


# Request to buy a product
@app.route('/product/<int:product_id>/buy', methods=['POST'])
def request_to_buy(product_id: int):
    product = Product.query.get_or_404(product_id)
    if product.status == 'sold':
        flash('This item is already sold.', 'error')
        return redirect(url_for('product_detail', product_id=product.id))

    buyer_name = request.form.get('buyer_name', '').strip()
    buyer_email = request.form.get('buyer_email', '').strip()
    message = request.form.get('message', '').strip()

    errors = []
    if not buyer_name:
        errors.append('Buyer name is required.')
    if not validate_college_email(buyer_email):
        errors.append(f'Only emails ending with @{ALLOWED_EMAIL_DOMAIN} can request to buy.')

    if errors:
        for e in errors:
            flash(e, 'error')
        return redirect(url_for('product_detail', product_id=product.id))

    pr = PurchaseRequest(
        product_id=product.id,
        buyer_name=buyer_name,
        buyer_email=buyer_email,
        message=message or None,
    )
    db.session.add(pr)
    db.session.commit()
    flash('Your request to buy has been sent. The seller may contact you via email.', 'success')
    return redirect(url_for('product_detail', product_id=product.id))


# Mark product as sold (simple seller email confirmation)
@app.route('/product/<int:product_id>/mark_sold', methods=['POST'])
def mark_product_sold(product_id: int):
    product = Product.query.get_or_404(product_id)
    seller_email_confirm = request.form.get('seller_email_confirm', '').strip().lower()
    if seller_email_confirm != (product.seller_email or '').lower():
        flash('Seller email confirmation does not match.', 'error')
        return redirect(url_for('product_detail', product_id=product.id))
    product.status = 'sold'
    db.session.commit()
    flash('Marked as sold.', 'success')
    return redirect(url_for('product_detail', product_id=product.id))


# Health check (useful for Azure)
@app.route('/healthz')
def healthz():
    return {'status': 'ok'}


if __name__ == '__main__':
    # For local development
    app.run(debug=True)
