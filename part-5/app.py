import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError  # <<< NEW >>>

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///default.db')

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}

db = SQLAlchemy(app)

# =============================================================================
# MODEL
# =============================================================================

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)

    def __repr__(self):
        return f'<Product {self.name}>'

# =============================================================================
# ROUTES
# =============================================================================

@app.route('/')
def index():
    try:  # <<< NEW >>>
        products = Product.query.all()
    except OperationalError as e:  # <<< NEW >>>
        return f"Database connection error: {e}", 500

    db_type = 'Unknown'
    db_url = DATABASE_URL.lower()
    if 'postgresql' in db_url or 'postgres' in db_url:
        db_type = 'PostgreSQL'
    elif 'mysql' in db_url:
        db_type = 'MySQL'
    elif 'sqlite' in db_url:
        db_type = 'SQLite'

    return render_template('index.html', products=products, db_type=db_type, db_url=DATABASE_URL)


@app.route('/add', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        try:  # <<< NEW >>>
            new_product = Product(
                name=request.form['name'],
                price=float(request.form['price']),
                stock=int(request.form.get('stock', 0)),
                description=request.form.get('description', '')
            )
            db.session.add(new_product)
            db.session.commit()
            flash('Product added!', 'success')
            return redirect(url_for('index'))

        except OperationalError as e:  # <<< NEW >>>
            db.session.rollback()
            flash('Database error while adding product.', 'danger')
            print(e)

    return render_template('add.html')


@app.route('/delete/<int:id>')
def delete_product(id):
    try:  # <<< NEW >>>
        product = Product.query.get_or_404(id)
        db.session.delete(product)
        db.session.commit()
        flash('Product deleted!', 'danger')

    except OperationalError as e:  # <<< NEW >>>
        db.session.rollback()
        flash('Database error while deleting product.', 'danger')
        print(e)

    return redirect(url_for('index'))

# =============================================================================
# INITIALIZE DATABASE
# =============================================================================

def init_db():
    try:  # <<< NEW >>>
        with app.app_context():
            db.create_all()
            print(f'Database initialized! Using: {DATABASE_URL}')

            if Product.query.count() == 0:
                sample = [
                    Product(name='Laptop', price=999.99, stock=10, description='High-performance laptop'),
                    Product(name='Mouse', price=29.99, stock=50, description='Wireless mouse'),
                    Product(name='Keyboard', price=79.99, stock=30, description='Mechanical keyboard'),
                ]
                db.session.add_all(sample)
                db.session.commit()
                print('Database connection successful!')

    except OperationalError as e:  # <<< NEW >>>
        print("❌ Database connection failed!")
        print(e)
        exit(1)


if __name__ == '__main__':
    init_db()
    app.run(debug=os.getenv('FLASK_DEBUG', 'True') == 'True')
