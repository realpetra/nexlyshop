from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random

app = Flask(__name__)
app.secret_key = "nexly_secret_key_petramonix"

# SQLite Veritabanı Ayarı
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- VERİTABANI MODELLERİ ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), default="user") 
    points = db.Column(db.Integer, default=0)
    rank = db.Column(db.String(20), default="Bronz Üye")
    avatar = db.Column(db.Text, nullable=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    text = db.Column(db.Text, nullable=False)
    stars = db.Column(db.Integer, default=5)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    items = db.Column(db.Text, nullable=False) 
    total = db.Column(db.Float, nullable=False)

# --- SADECE SENİN SİTENDEKİ GERÇEK 7 ÜRÜN ---
def init_db():
    db.create_all()
    
    # Vitrininde duran birebir orijinal ürün listen kanka:
    default_products = [
        {"name": "🎯 SPOTİFY 4 AYLIK KOD PREMİUM", "price": 15.00, "category": "yazilim", "description": "Kendi kişisel hesabınızda kullanabileceğiniz, 4 aylık reklamsız müzik keyfi sunan premium kod."},
        {"name": "⭐ Roblox Kaliteli Oynanmış Hesap", "price": 45, "category": "oyun", "description": "Roblox platformunda kaliteli ve önceden oynanmış, rastgele içerik garantili efsane hesap."},
        {"name": "⭐ VALORANT MÜKEMMEL RANDOM HESAP", "price": 150, "category": "oyun", "description": "TR sunucusunda geçerli, yüksek skin çıkma oranına sahip mükemmel random hesap satışı."},
        {"name": "⭐ DUOLİNGO PRMİUM KENDİ HESABINIZA OTO", "price": 30.00, "category": "yazilim", "description": "Kendi şahsi Duolingo hesabınıza otomatik olarak tanımlanan sınırsız premium üyelik paketi."},
        {"name": "✨ Sınırsız Gmail Açma Methodu [Güncel]", "price": 30.00, "category": "method", "description": "Telefon doğrulamasına takılmadan sınırsız şekilde yeni Gmail hesapları oluşturmanızı sağlayan güncel taktik."},
        {"name": "✨ 2500+ VİRAL MOTİVASYON REELS...", "price": 35.00, "category": "servis", "description": "Telif hakkı içermeyen, YouTube, Instagram ve TikTok için paylaşıma hazır yüksek kaliteli dikey videolar."},
        {"name": "VALORANT MEGA METHOD PACK", "price": 65.00, "category": "method", "description": "Valorant oyuncuları ve satıcıları için özel olarak hazırlanan yöntem arşivi."}
    ]

    # Veritabanında alakasız veya fazladan ürün kalmışsa hepsini uçur
    current_product_names = [p["name"] for p in default_products]
    all_db_products = Product.query.all()
    
    for db_p in all_db_products:
        if db_p.name not in current_product_names:
            db.session.delete(db_p)

    # Ürünleri ekle veya fiyatları eşitle
    for p_data in default_products:
        existing_p = Product.query.filter_by(name=p_data["name"]).first()
        if existing_p:
            if existing_p.price != p_data["price"]:
                existing_p.price = p_data["price"]
        else:
            new_p = Product(name=p_data["name"], price=p_data["price"], category=p_data["category"], description=p_data["description"])
            db.session.add(new_p)
            
    # Varsayılan Yönetici Hesabı
    if not User.query.filter_by(username="admin").first():
        secure_admin_pass = generate_password_hash("adminpass123")
        admin_user = User(username="admin", email="admin@nexlyshop.com", password_hash=secure_admin_pass, role="admin", rank="Kurucu")
        db.session.add(admin_user)
        
    db.session.commit()

# --- API ROTASI VE METODLAR ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{"id": p.id, "name": p.name, "price": p.price, "category": p.category, "description": p.description} for p in products])

@app.route('/api/auth/register-step1', methods=['POST'])
def reg_step1():
    data = request.json
    if User.query.filter_by(username=data['username']).first() or User.query.filter_by(email=data['email']).first():
        return jsonify({"status": "error", "msg": "Kullanıcı adı veya e-posta zaten kullanımda kanka!"})
    
    code = str(random.randint(1000, 9999))
    session['verify_code'] = code
    session['reg_data'] = data
    return jsonify({"status": "success", "msg": f"Doğrulama kodu oluşturuldu: {code} (E-posta simülasyonu)"})

@app.route('/api/auth/register-verify', methods=['POST'])
def reg_verify():
    data = request.json
    if 'verify_code' in session and session['verify_code'] == data['code']:
        reg_data = session.get('reg_data')
        secure_pass = generate_password_hash(reg_data['password'])
        new_user = User(username=reg_data['username'], email=reg_data['email'], password_hash=secure_pass)
        db.session.add(new_user)
        db.session.commit()
        
        session.pop('verify_code', None)
        session.pop('reg_data', None)
        return jsonify({"status": "success", "msg": "Kayıt başarıyla tamamlandı kanka!"})
    return jsonify({"status": "error", "msg": "Girdiğin doğrulama kodu hatalı!"})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        session['user'] = user.username
        return jsonify({
            "status": "success", 
            "username": user.username, 
            "role": user.role, 
            "points": user.points, 
            "rank": user.rank,
            "avatar": user.avatar
        })
    return jsonify({"status": "error", "msg": "Kullanıcı adı veya şifre yanlış!"})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({"status": "success"})

@app.route('/api/user/avatar', methods=['POST'])
def change_avatar():
    if 'user' not in session: return jsonify({"status": "error"})
    data = request.json
    user = User.query.filter_by(username=session['user']).first()
    user.avatar = data['image_base64']
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/api/comments/<int:product_id>', methods=['GET'])
def get_comments(product_id):
    comments = Comment.query.filter_by(product_id=product_id).all()
    return jsonify([{"username": c.username, "text": c.text, "stars": c.stars} for c in comments])

@app.route('/api/comments/add', methods=['POST'])
def add_comment():
    if 'user' not in session: return jsonify({"status": "error", "msg": "Yorum yapmak için giriş yapmalısın kanka!"})
    data = request.json
    new_comment = Comment(product_id=data['product_id'], username=session['user'], text=data['text'], stars=data['stars'])
    db.session.add(new_comment)
    db.session.commit()
    return jsonify({"status": "success"})

@app.route('/api/checkout', methods=['POST'])
def checkout():
    data = request.json
    username = session.get('user', 'Misafir Kullanıcı')
    
    new_order = Order(username=username, items=data['items_text'], total=data['total'])
    db.session.add(new_order)
    
    if 'user' in session:
        user = User.query.filter_by(username=username).first()
        user.points += int(data['total'] * 0.1)
        if user.points > 500: user.rank = "Platin Üye"
        elif user.points > 200: user.rank = "Altın Üye"
        elif user.points > 100: user.rank = "Gümüş Üye"
        
    db.session.commit()
    return jsonify({"status": "success", "msg": "Siparişiniz alındı, ItemSatış yönlendirmesi simüle ediliyor!"})

@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    orders = Order.query.all()
    users = User.query.filter(User.role != 'admin').all()
    total_revenue = sum([o.total for o in orders])
    return jsonify({
        "revenue": f"{total_revenue:.2f} ₺",
        "sales_count": len(orders),
        "users": [{"username": u.username, "rank": u.rank, "points": u.points} for u in users]
    })

@app.route('/api/admin/add-product', methods=['POST'])
def admin_add_product():
    data = request.json
    new_p = Product(name=data['name'], price=float(data['price']), category=data['category'], description="Yönetici tarafından eklenen özel ürün.")
    db.session.add(new_p)
    db.session.commit()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    with app.app_context():
        init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)