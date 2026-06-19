let allProducts = [];
let cart = [];
let currentUser = null;
let selectedStars = 5;
let currentQuickViewProductId = null;
let couponApplied = false;

// Sayfa Yüklendiğinde Ürünleri Çek
document.addEventListener("DOMContentLoaded", () => {
    fetchProducts();
    initParticles();
});

function fetchProducts() {
    fetch('/api/products')
        .then(res => res.json())
        .then(data => {
            allProducts = data;
            renderProducts(allProducts);
        })
        .catch(err => console.error("Ürünler yüklenemedi kanka:", err));
}

function renderProducts(products) {
    const grid = document.getElementById("productGrid");
    grid.innerHTML = "";
    if(products.length === 0) {
        grid.innerHTML = "<p style='grid-column: 1/-1; text-align:center; opacity:0.6;'>Ürün bulunamadı kanka.</p>";
        return;
    }
    products.forEach(p => {
        const card = document.createElement("div");
        card.className = "product-card glass-effect animate-up";
        card.innerHTML = `
            <div class="product-badge">${p.category.toUpperCase()}</div>
            <h3>${p.name}</h3>
            <p style="font-size:0.85rem; opacity:0.7; height:40px; overflow:hidden;">${p.description || ''}</p>
            <div class="price">${p.price.toFixed(2)} ₺</div>
            <div style="display:flex; gap:8px; margin-top:10px;">
                <button class="outline-btn" style="flex:1; padding:8px;" onclick="openQuickView(${p.id})">Hızlı Bakış</button>
                <button class="smooth-btn" style="flex:1; padding:8px;" onclick="addToCart(${p.id})"><i class="fa-solid fa-cart-plus"></i> Ekle</button>
            </div>
        `;
        grid.appendChild(card);
    });
}

// Canlı Arama Filtresi
function liveSearch() {
    const val = document.getElementById("searchBox").value.toLowerCase();
    const filtered = allProducts.filter(p => p.name.toLowerCase().includes(val));
    renderProducts(filtered);
}

// Kategori Filtresi
function filterProducts(cat, btn) {
    document.querySelectorAll(".filter-bar button").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    if(cat === 'all') {
        renderProducts(allProducts);
    } else {
        const filtered = allProducts.filter(p => p.category === cat);
        renderProducts(filtered);
    }
}

// Modal Kontrolleri
function openModal(id) { document.getElementById(id).style.display = "flex"; }
function closeModal(id) { document.getElementById(id).style.display = "none"; }

// Hızlı Bakış ve Canlı Yorumları Çekme
function openQuickView(id) {
    currentQuickViewProductId = id;
    const p = allProducts.find(prod => prod.id === id);
    if(!p) return;
    
    document.getElementById("qv-title").innerText = p.name;
    document.getElementById("qv-desc").innerText = p.description || 'Açıklama yok.';
    document.getElementById("qv-price").innerText = p.price.toFixed(2) + " ₺";
    
    setStar(5);
    document.getElementById("comment-text").value = "";
    
    // Yorumları Çek
    fetch(`/api/comments/${id}`)
        .then(res => res.json())
        .then(comments => {
            const container = document.getElementById("comments-container");
            container.innerHTML = "";
            if(comments.length === 0) {
                container.innerHTML = "<p style='opacity:0.5; font-size:0.85rem;'>Bu ürüne henüz yorum yapılmamış kanka, ilk sen yap!</p>";
            } else {
                comments.forEach(c => {
                    let starsHtml = "";
                    for(let i=0; i<5; i++) {
                        starsHtml += i < c.stars ? "<i class='fa-solid fa-star' style='color:#ffb400;'></i>" : "<i class='fa-regular fa-star' style='color:#ffb400;'></i>";
                    }
                    container.innerHTML += `
                        <div style="background:rgba(255,255,255,0.03); padding:8px; border-radius:8px; margin-bottom:8px; border:1px solid var(--border-color)">
                            <div style="display:flex; justify-content:between; font-size:0.8rem; font-weight:bold; margin-bottom:4px;">
                                <span>@${c.username}</span> <span style="margin-left:auto;">${starsHtml}</span>
                            </div>
                            <p style="margin:0; font-size:0.85rem; opacity:0.8;">${c.text}</p>
                        </div>
                    `;
                });
            }
        });
        
    openModal("quickViewModal");
}

function setStar(num) {
    selectedStars = num;
    const icons = document.querySelectorAll("#modal-stars i");
    icons.forEach((icon, idx) => {
        if(idx < num) {
            icon.className = "fa-solid fa-star";
        } else {
            icon.className = "fa-regular fa-star";
        }
    });
}

function submitComment() {
    const text = document.getElementById("comment-text").value.trim();
    if(!text) { showToast("Yorum alanı boş bırakılamaz kanka!", "error"); return; }
    
    fetch('/api/comments/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({product_id: currentQuickViewProductId, text: text, stars: selectedStars})
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            showToast("Yorumun başarıyla eklendi kanka!");
            openQuickView(currentQuickViewProductId);
        } else {
            showToast(data.msg, "error");
        }
    });
}

// Sepet Sistemleri
function addToCart(id) {
    const p = allProducts.find(prod => prod.id === id);
    if(p) {
        cart.push(p);
        updateCartUI();
        showToast(`${p.name} sepete eklendi!`);
    }
}
function addToCartFromModal() {
    if(currentQuickViewProductId) {
        addToCart(currentQuickViewProductId);
        closeModal("quickViewModal");
    }
}
function openCart() { document.getElementById("cartSidebar").classList.add("active"); }
function closeCart() { document.getElementById("cartSidebar").classList.remove("active"); }

function updateCartUI() {
    document.getElementById("cart-count").innerText = cart.length;
    const container = document.getElementById("cart-items");
    container.innerHTML = "";
    
    let total = 0;
    cart.forEach((item, idx) => {
        total += item.price;
        const div = document.createElement("div");
        div.className = "cart-item";
        div.style = "display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; border-bottom:1px solid var(--border-color); padding-bottom:8px;";
        div.innerHTML = `
            <div>
                <h4 style="margin:0;">${item.name}</h4>
                <span style="font-size:0.85rem; color:var(--accent);">${item.price.toFixed(2)} ₺</span>
            </div>
            <button onclick="removeFromCart(${idx})" style="background:none; border:none; color:#f44336; cursor:pointer; font-size:1.1rem;"><i class="fa-solid fa-trash"></i></button>
        `;
        container.appendChild(div);
    });
    
    if(couponApplied) total *= 0.9;
    document.getElementById("cart-total").innerText = total.toFixed(2);
}

function removeFromCart(idx) {
    cart.splice(idx, 1);
    updateCartUI();
}

function applyCoupon() {
    const code = document.getElementById("couponBox").value.trim();
    if(code === "NEXLY10") {
        couponApplied = true;
        document.getElementById("discount-notify").innerText = "%10 İndirim Uygulandı! 🎉";
        document.getElementById("discount-notify").style.display = "block";
        updateCartUI();
        showToast("Kupon başarıyla uygulandı kanka!");
    } else {
        showToast("Geçersiz kupon kodu!", "error");
    }
}

function checkoutSystem() {
    if(cart.length === 0) { showToast("Sepetin bomboş kanka!", "error"); return; }
    let itemsText = cart.map(i => i.name).join(", ");
    let total = parseFloat(document.getElementById("cart-total").innerText);
    
    fetch('/api/checkout', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({items_text: itemsText, total: total})
    })
    .then(res => res.json())
    .then(data => {
        showToast("Ödeme Sayfasına Gidiliyor...");
        setTimeout(() => {
            alert(`[ItemSatış Simülasyonu]\nToplam Ödeme: ${total.toFixed(2)} ₺\nSipariş İçeriği: ${itemsText}\n\nÖdeme onaylandı! Profilinden puanını kontrol edebilirsin kanka.`);
            cart = [];
            couponApplied = false;
            document.getElementById("discount-notify").style.display = "none";
            document.getElementById("couponBox").value = "";
            updateCartUI();
            closeCart();
            if(currentUser) {
                // Bilgileri tazele
                loginSystemSilent();
            }
        }, 1500);
    });
}

// Auth İşlemleri
function handleAuthClick() {
    if(currentUser) {
        openDashboard();
    } else {
        openModal("authModal");
    }
}

function switchAuthTab(tab, btn) {
    document.querySelectorAll(".auth-tabs button").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    document.querySelectorAll(".auth-content").forEach(c => c.classList.remove("active"));
    if(tab === 'login') document.getElementById("auth-login").classList.add("active");
    if(tab === 'register') document.getElementById("auth-register").classList.add("active");
}

function startVerification() {
    const u = document.getElementById("reg-username").value.trim();
    const e = document.getElementById("reg-email").value.trim();
    const p = document.getElementById("reg-password").value.trim();
    if(!u || !e || !p) { showToast("Tüm alanları doldur kanka!", "error"); return; }
    
    fetch('/api/auth/register-step1', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username: u, email: e, password: p})
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            document.getElementById("auth-register").classList.remove("active");
            document.getElementById("auth-verify").classList.add("active");
            alert(data.msg); // E-posta doğrulama kodunu ekrana basıyoruz kanka
        } else {
            showToast(data.msg, "error");
        }
    });
}

function cancelVerification() {
    document.getElementById("auth-verify").classList.remove("active");
    document.getElementById("auth-register").classList.add("active");
}

function verifyAndRegister() {
    const code = document.getElementById("verify-code").value.trim();
    fetch('/api/auth/register-verify', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({code: code})
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            showToast(data.msg);
            switchAuthTab('login', document.getElementById("tab-login-btn"));
            document.getElementById("auth-verify").classList.remove("active");
            document.getElementById("auth-login").classList.add("active");
        } else {
            showToast(data.msg, "error");
        }
    });
}

function loginSystem() {
    const u = document.getElementById("login-username").value.trim();
    const p = document.getElementById("login-password").value.trim();
    
    fetch('/api/auth/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username: u, password: p})
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            currentUser = data;
            document.getElementById("auth-btn").innerHTML = `<i class="fa-solid fa-circle-user" style="color:var(--accent);"></i> @${data.username}`;
            showToast(`Hoş geldin kanka, @${data.username}!`);
            closeModal("authModal");
            if(data.role === 'admin') {
                // Eğer admine giriş yaptıysa buton ekleyelim
                showAdminTrigger();
            }
        } else {
            showToast(data.msg, "error");
        }
    });
}

function loginSystemSilent() {
    const u = currentUser.username;
    // Sessizce verileri günceller (Sipariş sonrası puan vs.)
    fetch('/api/auth/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username: u, password: document.getElementById("login-password").value.trim()})
    })
    .then(res => res.json())
    .then(data => { if(data.status === 'success') currentUser = data; });
}

function logoutSystem() {
    fetch('/api/auth/logout', { method: 'POST' })
    .then(() => {
        currentUser = null;
        document.getElementById("auth-btn").innerHTML = `<i class="fa-solid fa-user"></i> Giriş Yap`;
        const adminBtn = document.getElementById("admin-nav-btn");
        if(adminBtn) adminBtn.remove();
        closeModal("dashboardModal");
        showToast("Başarıyla çıkış yapıldı kanka.");
    });
}

// Profil Paneli ve Gerçek Resim Yükleme
function openDashboard() {
    if(!currentUser) return;
    document.getElementById("dash-username").innerText = currentUser.username;
    document.getElementById("dash-rank").innerText = currentUser.rank;
    document.getElementById("dash-points").innerText = currentUser.points;
    
    const avatarBox = document.getElementById("dash-avatar-box");
    if(currentUser.avatar) {
        avatarBox.innerHTML = `<img src="${currentUser.avatar}" style="width:100%; height:100%; border-radius:50%; object-fit:cover;">`;
    } else {
        avatarBox.innerHTML = `<i class="fa-solid fa-user-astronaut"></i>`;
    }
    
    // Rozet simülasyonu
    const badgeContainer = document.getElementById("badges-container");
    badgeContainer.innerHTML = "<span class='badge glass-effect'><i class='fa-solid fa-award' style='color:#cd7f32;'></i> İlk Üyelik</span>";
    if(currentUser.points > 100) badgeContainer.innerHTML += "<span class='badge glass-effect'><i class='fa-solid fa-award' style='color:#c0c0c0;'></i> Bronz Alıcı</span>";
    if(currentUser.points > 200) badgeContainer.innerHTML += "<span class='badge glass-effect'><i class='fa-solid fa-award' style='color:#ffd700;'></i> Balina</span>";

    openModal("dashboardModal");
}

function uploadRealAvatar() {
    const file = document.getElementById("fileAvatarInput").files[0];
    if(!file) return;
    
    const reader = new FileReader();
    reader.onloadend = function() {
        const base64String = reader.result;
        fetch('/api/user/avatar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({image_base64: base64String})
        })
        .then(res => res.json())
        .then(data => {
            if(data.status === 'success') {
                currentUser.avatar = base64String;
                openDashboard();
                showToast("Profil resmin başarıyla güncellendi kanka!");
            }
        });
    }
    reader.readAsDataURL(file);
}

// Admin İşlemleri
function showAdminTrigger() {
    if(document.getElementById("admin-nav-btn")) return;
    const nav = document.querySelector(".top-nav");
    const btn = document.createElement("button");
    btn.id = "admin-nav-btn";
    btn.className = "login-link";
    btn.style.background = "linear-gradient(135deg, #ff3366, #ff6633)";
    btn.innerHTML = `<i class="fa-solid fa-lock-open"></i> Yönetim`;
    btn.onclick = openAdminPanel;
    nav.insertBefore(btn, document.getElementById("auth-btn"));
}

function openAdminPanel() {
    fetch('/api/admin/stats')
    .then(res => res.json())
    .then(data => {
        document.getElementById("stat-revenue").innerText = data.revenue;
        document.getElementById("stat-sales").innerText = data.sales_count;
        
        const list = document.getElementById("admin-user-list");
        list.innerHTML = "";
        data.users.forEach(u => {
            list.innerHTML += `<p style='margin:5px 0; font-size:0.9rem; opacity:0.8;'>👤 @${u.username} - <strong>${u.rank}</strong> (${u.points} Puan)</p>`;
        });
        openModal("adminModal");
    });
}

function adminAddProduct() {
    const name = document.getElementById("new-prod-name").value.trim();
    const price = document.getElementById("new-prod-price").value.trim();
    const cat = document.getElementById("new-prod-cat").value;
    
    if(!name || !price) { showToast("Ürün adı ve fiyat boş geçilemez!", "error"); return; }
    
    fetch('/api/admin/add-product', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name: name, price: price, category: cat})
    })
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            showToast("Yeni ürün başarıyla eklendi kanka!");
            fetchProducts();
            closeModal("adminModal");
        }
    });
}

// Toast Bildirimi
function showToast(msg, type="success") {
    const t = document.getElementById("toast");
    const m = document.getElementById("toast-msg");
    m.innerText = msg;
    t.style.background = type === "success" ? "rgba(20, 20, 35, 0.85)" : "rgba(244, 67, 54, 0.85)";
    t.classList.add("show");
    setTimeout(() => { t.classList.remove("show"); }, 3000);
}

// Chatbot Zekası v2.5
function toggleChat() {
    const panel = document.getElementById("chatbot-panel");
    panel.style.display = panel.style.display === "flex" ? "none" : "flex";
}
function handleChatPress(e) { if(e.key === 'Enter') sendChatMessage(); }

function sendChatMessage() {
    const inp = document.getElementById("chat-input");
    const text = inp.value.trim();
    if(!text) return;
    
    const body = document.getElementById("chat-body");
    body.innerHTML += `<div class="user-msg">${text}</div>`;
    inp.value = "";
    body.scrollTop = body.scrollHeight;
    
    setTimeout(() => {
        let reply = "Kanka ne dediğini tam anlayamadım ama her türlü yardımcı olurum! Ürünlerimize göz atabilir veya NEXLY10 kuponunu sepetinde deneyebilirsin. 🚀";
        let lower = text.toLowerCase();
        
        if(lower.includes("bütçe") || lower.includes("param var") || lower.includes("tl var")) {
            let money = parseInt(lower.replace(/[^0-9]/g, ''));
            if(money && !isNaN(money)) {
                let matches = allProducts.filter(p => p.price <= money);
                if(matches.length > 0) {
                    reply = `Ooo kanka ${money} ₺ bütçeye kapabileceğin canavarlar şunlar:<br><br>` + matches.map(m => `• <strong>${m.name}</strong> (${m.price.toFixed(2)} ₺)`).join("<br>");
                } else {
                    reply = `Kanka ${money} ₺ bütçeye şu an mağazada ürün yok ama senin için admin paneline haber uçurdum, ucuz ürün getirecekler!`;
                }
            }
        } else if(lower.includes("kupon") || lower.includes("indirim") || lower.includes("kod")) {
            reply = "Kanka sana Petramonix özel sürprizi patlatıyorum! Sepette <strong>NEXLY10</strong> kodunu kullan, anında %10 indirimi kap! 🎁";
        } else if(lower.includes("sepet") || lower.includes("alınır")) {
            if(cart.length > 0) {
                reply = `Sepetinde şu an ${cart.length} ürün var kanka. Bence tam zamanında ödeme yapıyorsun, kaçırma derim! 🛒`;
            } else {
                reply = "Sepetin şu an bomboş kanka, hemen yukarıdan Valorant veya Spotify hesaplarından birini sepete fırlat! 🔥";
            }
        }
        
        body.innerHTML += `<div class="bot-msg">${reply}</div>`;
        body.scrollTop = body.scrollHeight;
    }, 800);
}

function initParticles() {
    particlesJS("particles-js", {
        "particles": {
            "number": { "value": 50, "density": { "enable": true, "value_area": 800 } },
            "color": { "value": "#6c5ce7" },
            "shape": { "type": "circle" },
            "opacity": { "value": 0.2 },
            "size": { "value": 3 },
            "line_linked": { "enable": true, "distance": 150, "color": "#6c5ce7", "opacity": 0.1, "width": 1 },
            "move": { "enable": true, "speed": 1.5 }
        },
        "interactivity": { "events": { "onhover": { "enable": false }, "onclick": { "enable": false } } },
        "retina_detect": true
    });
}
