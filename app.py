from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'petramonix_ozel_sifre_123'

# SQLite Veritabanı Ayarı
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nexlyshop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- VERİTABANI MODELLERİ ---
class Kullanici(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    bakiye = db.Column(db.Float, default=0.0)

class Urun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isim = db.Column(db.String(100), nullable=False)
    aciklama = db.Column(db.Text, nullable=False)
    fiyat = db.Column(db.Float, nullable=False)
    kategori = db.Column(db.String(50), nullable=False)
    resim = db.Column(db.String(200), nullable=False)

# Veritabanını Oluşturma ve Otomatik Ürün Ekleme Bölümü
with app.app_context():
    db.create_all()
    
    # Eğer veritabanında hiç ürün yoksa, senin 7 ürününü otomatik yükle
    if not Urun.query.first():
        ornek_urunler = [
            Urun(isim="NEXLY LOGO", aciklama="Özel tasarım Nexly Mağaza Logosu", fiyat=15.0, kategori="tasarim", resim="nx.jpg"),
            Urun(isim="PETRAMONIX REKLAM ALANI", aciklama="Sitede Premium reklam bandı alanı", fiyat=120.0, kategori="reklam", resim="nx_2.png"),
            Urun(isim="NEXLY PREMIUM ROZET", aciklama="Profiliniz için parıl parıl Premium üye rozeti", fiyat=30.0, kategori="rozet", resim="nx.jpg"),
            Urun(isim="NEXLY GENERATION", aciklama="Gelişmiş altyapı ve kod desteği paketi", fiyat=250.0, kategori="yazilim", resim="nx_2.png"),
            Urun(isim="NEXLY V1 ALTYAPI", aciklama="E-ticaret siteleri için hazır taptaze Flask altyapısı", fiyat=450.0, kategori="yazilim", resim="nx.jpg"),
            Urun(isim="NEXLY PLUS ROZET", aciklama="Ekonomik ve şık Plus üye rozeti avantajları", fiyat=10.0, kategori="rozet", resim="nx_2.png"),
            Urun(isim="NEXLY APPS", aciklama="Mağazanıza entegre edilebilecek hazır modüller", fiyat=150.0, kategori="yazilim", resim="nx.jpg")
        ]
        db.session.bulk_save_objects(ornek_urunler)
        db.session.commit()

# --- SAYFA YÖNLENDİRMELERİ (ROUTES) ---
@app.route('/')
def index():
    kategori = request.args.get('kategori')
    if kategori:
        urunler = Urun.query.filter_by(kategori=kategori).all()
    else:
        urunler = Urun.query.all()
    return render_template('index.html', urunler=urunler)

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
        flash('Önce giriş yapmalısın kanka!', 'danger')
        return redirect(url_for('giris'))
    
    miktar = request.form.get('miktar', type=float)
    if miktar and miktar > 0:
        kullanici = Kullanici.query.get(session['kullanici_id'])
        kullanici.bakiye += miktar
        db.session.commit()
        flash(f'{miktar} TL bakiyene eklendi!', 'success')
    return redirect(url_for('index'))

@app.route('/satinal/<int:urun_id>', methods=['POST'])
def satinal(urun_id):
    if 'kullanici_id' not in session:
        flash('Ürün satın almak için önce giriş yapmalısın kanka!', 'danger')
        return redirect(url_for('giris'))
        
    kullanici = Kullanici.query.get(session['kullanici_id'])
    urun = Urun.query.get_or_400(urun_id)
    
    if kullanici.bakiye >= urun.fiyat:
        kullanici.bakiye -= urun.fiyat
        db.session.commit()
        flash(f'{urun.isim} başarıyla satın alındı! Hayırlı olsun kanka.', 'success')
    else:
        flash('Bakiye yetersiz kanka! Lütfen önce bakiye yükle.', 'danger')
        
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
