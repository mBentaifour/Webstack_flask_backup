from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv
from flask_migrate import Migrate

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'votre_clé_secrète_ici'  # Remplacez par une clé sécurisée en production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///droguerie.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

# Modèles de base de données
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    cart_items = db.relationship('CartItem', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_cart_count(self):
        return sum(item.quantity for item in self.cart_items)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    image_url = db.Column(db.String(200))
    cart_items = db.relationship('CartItem', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    def get_total(self):
        return self.quantity * self.product.price

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, cancelled
    total_amount = db.Column(db.Float, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)  # Prix au moment de l'achat

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Accès non autorisé.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    search_query = request.args.get('q', '')
    category = request.args.get('category', 'all')
    
    query = Product.query
    
    if search_query:
        search = f"%{search_query}%"
        query = query.filter(
            db.or_(
                Product.name.ilike(search),
                Product.description.ilike(search)
            )
        )
    
    if category and category != 'all':
        query = query.filter(Product.category == category)
    
    products = query.all()
    categories = db.session.query(Product.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('home.html', 
                         products=products, 
                         categories=categories,
                         current_category=category,
                         search_query=search_query)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            flash('Connexion réussie!')
            return redirect(url_for('home'))
        flash('Email ou mot de passe incorrect')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur existe déjà')
            return redirect(url_for('register'))
            
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Inscription réussie! Vous pouvez maintenant vous connecter.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    products = Product.query.all()
    return render_template('admin/dashboard.html', products=products)

@app.route('/admin/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        stock = int(request.form.get('stock'))
        category = request.form.get('category')
        image_url = request.form.get('image_url')

        product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category=category,
            image_url=image_url
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_product.html')

@app.route('/admin/product/<int:id>/edit', methods=['GET', 'POST'])
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.stock = int(request.form.get('stock'))
        product.category = request.form.get('category')
        product.image_url = request.form.get('image_url')
        db.session.commit()
        flash('Produit modifié avec succès!')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/edit_product.html', product=product)

@app.route('/admin/product/<int:id>/delete')
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Produit supprimé avec succès!')
    return redirect(url_for('admin_dashboard'))

@app.route('/cart')
@login_required
def view_cart():
    cart_items = current_user.cart_items
    total = sum(item.quantity * item.product.price for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    if quantity > product.stock:
        flash('Quantité non disponible en stock')
        return redirect(url_for('home'))
    
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()
    flash('Produit ajouté au panier')
    return redirect(url_for('view_cart'))

@app.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        flash('Action non autorisée')
        return redirect(url_for('view_cart'))
    
    quantity = int(request.form.get('quantity', 0))
    if quantity > 0 and quantity <= cart_item.product.stock:
        cart_item.quantity = quantity
        db.session.commit()
        flash('Panier mis à jour')
    elif quantity == 0:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Produit retiré du panier')
    else:
        flash('Quantité invalide')
    
    return redirect(url_for('view_cart'))

@app.route('/cart/remove/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user_id != current_user.id:
        flash('Action non autorisée')
        return redirect(url_for('view_cart'))
    
    db.session.delete(cart_item)
    db.session.commit()
    flash('Produit retiré du panier')
    return redirect(url_for('view_cart'))

def init_db():
    with app.app_context():
        # Supprimer et recréer toutes les tables
        db.drop_all()
        db.create_all()
        
        # Créer des produits réalistes
        if not Product.query.first():
            products = [
                Product(
                    name='Perceuse-Visseuse BOSCH GSR 18V-55',
                    description='Perceuse-visseuse sans fil 18V, 2 batteries Li-Ion 2.0Ah, couple max 55Nm, mandrin 13mm',
                    price=199.99,
                    stock=15,
                    category='Outillage',
                    image_url='https://www.mr-bricolage.fr/media/catalog/product/cache/6d1a5f86bd3587c9d44dd1f8bd4cd5e6/b/o/bosch-perceuse-visseuse-sans-fil-gsb-18v-55-2x2-0ah-0.jpg'
                ),
                Product(
                    name='Tondeuse Thermique GARDENA',
                    description='Tondeuse thermique 140cc, largeur de coupe 46cm, bac 50L, hauteur de coupe réglable',
                    price=299.99,
                    stock=8,
                    category='Jardinage',
                    image_url='https://www.mr-bricolage.fr/media/catalog/product/cache/6d1a5f86bd3587c9d44dd1f8bd4cd5e6/t/o/tondeuse-thermique-tractee-140cc-46cm-gardena.jpg'
                ),
                Product(
                    name='Peinture Dulux Valentine',
                    description='Peinture murs et plafonds, blanc mat, 10L, grande couvrance, sans éclaboussures',
                    price=49.99,
                    stock=25,
                    category='Peinture',
                    image_url='https://www.mr-bricolage.fr/media/catalog/product/cache/6d1a5f86bd3587c9d44dd1f8bd4cd5e6/v/a/valentine-credence-blanc-mat-2l.jpg'
                ),
                Product(
                    name='Établi Pliant WORKMATE',
                    description='Établi pliant multifonction, charge max 160kg, surface de travail antidérapante',
                    price=89.99,
                    stock=12,
                    category='Outillage',
                    image_url='https://www.mr-bricolage.fr/media/catalog/product/cache/6d1a5f86bd3587c9d44dd1f8bd4cd5e6/e/t/etabli-pliant-black-decker-wm536.jpg'
                ),
                Product(
                    name='Tronçonneuse STIHL MS 170',
                    description='Tronçonneuse thermique 30cm, 1.2kW/1.6ch, réservoir 0.25L, poids 4.1kg',
                    price=199.99,
                    stock=6,
                    category='Jardinage',
                    image_url='https://www.mr-bricolage.fr/media/catalog/product/cache/6d1a5f86bd3587c9d44dd1f8bd4cd5e6/t/r/tronconneuse-thermique-stihl-ms-170-d-35cm.jpg'
                ),
                Product(
                    name='Kit Douche Italienne',
                    description='Kit complet douche à l\'italienne, receveur 90x90cm, bonde, grille inox',
                    price=299.99,
                    stock=4,
                    category='Quincaillerie',
                    image_url='https://www.mr-bricolage.fr/media/catalog/product/cache/6d1a5f86bd3587c9d44dd1f8bd4cd5e6/r/e/receveur-de-douche-carre-90x90-blanc.jpg'
                ),
                Product(
                    name='Échelle Télescopique 3.8m',
                    description='Échelle télescopique en aluminium, hauteur max 3.8m, 13 échelons, charge max 150kg',
                    price=129.99,
                    stock=10,
                    category='Outillage',
                    image_url='https://www.mr-bricolage.fr/media/catalog/product/cache/6d1a5f86bd3587c9d44dd1f8bd4cd5e6/e/c/echelle-telescopique-3-80m-13-echelons.jpg'
                ),
                Product(
                    name='Karcher K5 Premium',
                    description='Nettoyeur haute pression 145 bars, débit 500L/h, moteur refroidi à l\'eau',
                    price=349.99,
                    stock=7,
                    category='Jardinage',
                    image_url='https://www.mr-bricolage.fr/media/catalog/product/cache/6d1a5f86bd3587c9d44dd1f8bd4cd5e6/n/e/nettoyeur-haute-pression-k5-premium-full-control-plus-karcher.jpg'
                ),
                Product(
                    name='Lasure Protectrice Bois',
                    description='Lasure protection UV longue durée, chêne doré, 5L, application facile',
                    price=45.99,
                    stock=18,
                    category='Peinture',
                    image_url='https://www.mr-bricolage.fr/media/catalog/product/cache/6d1a5f86bd3587c9d44dd1f8bd4cd5e6/l/a/lasure-protection-intense-chene-clair-2-5l.jpg'
                ),
                Product(
                    name='Coffret Outils 108 Pièces',
                    description='Coffret complet avec clés, douilles, embouts, pinces, marteau, tournevis',
                    price=79.99,
                    stock=20,
                    category='Outillage',
                    image_url='https://www.mr-bricolage.fr/media/catalog/product/cache/6d1a5f86bd3587c9d44dd1f8bd4cd5e6/c/o/coffret-108-outils-chrome-vanadium.jpg'
                )
            ]
            for product in products:
                db.session.add(product)
            db.session.commit()
        
        # Création du compte admin par défaut s'il n'existe pas
        admin_user = User.query.filter_by(email='admin@admin.com').first()
        if not admin_user:
            admin = User(
                username='admin',
                email='admin@admin.com'
            )
            admin.set_password('admin123')
            admin.is_admin = True
            db.session.add(admin)
            db.session.commit()
            print("Compte administrateur créé avec succès!")

if __name__ == '__main__':
    init_db()
    print("\nSite accessible sur : http://127.0.0.1:8080")
    app.run(debug=True, port=8080, host='0.0.0.0')
