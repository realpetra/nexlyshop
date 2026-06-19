from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'petramonix_ozel_sifre_123'

# Kullanıcı giriş/kayıt ve bakiye işlemleri için hafif bir DB kalıyor
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nexlyshop_auth.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- VERİTABANI MODELLERİ (Giriş Sistemi) ---
class Kullanici(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    bakiye = db.Column(db.Float, default=0.0)

with app.app_context():
    db.create_all()

# --- SADECE SENİN SİTENDEKİ GERÇEK 7 ÜRÜN (Hafızadan Çekilen Güvenli Sistem) ---
SABIT_URUNLER = [
    {"id": 1, "isim": "🔮 SPOTIFY 4 AYLIK KOD PREMIUM", "fiyat": 15.00, "kategori": "yazilim", "aciklama": "Kendi kişisel hesabınızda kullanabileceğiniz, 4 aylık reklamsız müzik keyfi sunan premium kod.", "resim": "nx.jpg"},
    {"id": 2, "isim": "⭐ Roblox Kaliteli Oynanmış Hesap", "fiyat": 45.00, "kategori": "oyun", "aciklama": "Roblox platformunda kaliteli ve önceden oynanmış, rastgele içerik garantili efsane hesap.", "resim": "nx_2.png"},
    {"id": 3, "isim": "⭐ VALORANT MÜKEMMEL RANDOM HESAP", "fiyat": 150.00, "kategori": "oyun", "aciklama": "TR sunucusunda geçerli, yüksek skin çıkma oranına sahip mükemmel random hesap satışı.", "resim": "nx.jpg"},
    {"id": 4, "isim": "⭐ DUOLINGO PREMIUM KENDİ HESABINIZA OTO", "fiyat": 30.00, "kategori": "yazilim", "aciklama": "Kendi şahsi Duolingo hesabınıza otomatik olarak tanımlanan sınırsız premium üyelik paketi.", "resim": "nx_2.png"},
    {"id": 5, "isim": "✨ Sınırsız Gmail Açma Methodu [Güncel]", "fiyat": 30.00, "kategori": "method", "aciklama": "Telefon doğrulamasına takılmadan sınırsız şekilde yeni Gmail hesapları oluşturmanızı sağlayan güncel taktik.", "resim": "nx.jpg"},
    {"id": 6, "isim": "✨ 2500+ VİRAL MOTİVASYON REELS...", "fiyat": 35.00, "kategori": "servis", "aciklama": "Telif hakkı içermeyen, YouTube, Instagram ve TikTok için paylaşıma hazır yüksek kaliteli dikey videolar.", "resim": "nx_2.png"},
    {"id": 7, "isim": "✨ VALORANT MEGA METHOD PACK", "fiyat": 65.00, "kategori": "method", "aciklama": "Valorant oyuncuları ve satıcıları için özel olarak hazırlanan yöntem arşivi.", "resim": "nx.jpg"}
]

# --- CSS ÇÖKMESİNİ ENGELLEYEN ÖZEL SUNUCU AYARI ---
@app.route('/static/<path:filename>')
def custom_static(filename):
    response = send_from_directory(os.path.join(app.root_path, 'static'), filename)
    if filename.endswith('.css'):
        response.headers['Content-Type'] = 'text/css'
    return response

# --- SAYFA YÖNLENDİRMELERİ ---
@app.route('/')
def index():
    kategori = request.args.get('kategori')
    if kategori:
        # Kategorileri senin HTML butonlarındaki ('oyun', 'yazilim', 'method', 'servis') yapıya göre filtreler
        urunler = [u for u in SABIT_URUNLER if u['kategori'] == kategori]
    else:
        urunler = SABIT_URUNLER
    
    kullanici = None
    if 'kullanici_id' in session:
        kullanici = Kullanici.query.get(session['kullanici_id'])
        
    return render_template('index.html', urunler=urunler, kullanici=kullanici)

@app.route('/kayit', methods=['GET', 'POST'])
def kayit():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if Kullanici.query.filter_by(username=username).first():
            flash('Bu kullanıcı adı zaten kapılmış kanka!', 'danger')
            return redirect(url_for('kayit'))
            
        sifreli_password = generate_password_hash(password)
        yeni_kullanici = Kullanici(username=username, password=sifreli_password)
        db.session.add(yeni_kullanici)
        db.session.commit()
        flash('Kayıt başarılı! Giriş yapabilirsin kanka.', 'success')
        return redirect(url_for('giris'))
    return render_template('kayit.html')

@app.route('/giris', methods=['GET', 'POST'])
def giris():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        kullanici = Kullanici.query.filter_by(username=username).first()
        if kullanici and check_password_hash(kullanici.password, password):
            session['kullanici_id'] = kullanici.id
            session['username'] = kullanici.username
            flash(f'Hoş geldin {kullanici.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Kullanıcı adı veya şifre hatalı kanka!', 'danger')
    return render_template('giris.html')

@app.route('/cikis')
def cikis():
    session.clear()
    flash('Çıkış yapıldı, yine bekleriz kanka!', 'info')
    return redirect(url_for('index'))

@app.route('/bakiye-ekle', methods=['POST'])
def bakiye_ekle():
    if 'kullanici_id' not in session:
        return redirect(url_for('giris'))
    miktar = request.form.get('miktar', type=float)
    if miktar and miktar > 0:
        kullanici = Kullanici.query.get(session['kullanici_id'])
        kullanici.bakiye += miktar
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/satinal/<int:urun_id>', methods=['POST'])
def satinal(urun_id):
    if 'kullanici_id' not in session:
        return redirect(url_for('giris'))
        
    kullanici = Kullanici.query.get(session['kullanici_id'])
    urun = next((u for u in SABIT_URUNLER if u['id'] == urun_id), None)
    
    if urun and kullanici.bakiye >= urun['fiyat']:
        kullanici.bakiye -= urun['fiyat']
        db.session.commit()
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
