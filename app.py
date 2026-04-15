import sqlite3
import os
import uuid
from functools import wraps
from flask import (
    Flask, render_template, request, g, redirect,
    url_for, flash, session,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "haspelcorp-secret-key-2026"

SITE_NAME = "PT Valentiencahayaabadi"
SITE_TAGLINE = "Produsen Steel Drum & Wooden Drum Kualitas Terbaik"
ALLOWED_CATALOG_CATEGORIES = {"semua", "steel_drum", "wooden_steel_drum", "wooden_drum", "pallet_kayu"}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "haspel.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8MB max

# Pastikan folder uploads ada
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Admin credentials (ganti sesuai kebutuhan) ───────────────
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# ═══════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ═══════════════════════════════════════════════════════════════

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file):
    """Simpan file upload, return relative path dari static/."""
    if file and allowed_file(file.filename):
        safe_name = secure_filename(file.filename)
        if not safe_name:
            return None
        ext = safe_name.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        return f"uploads/{filename}"
    return None


def build_seo_meta(title, description, *, page_type="website", image_url=None, keywords=None):
    """Bangun metadata SEO untuk template."""
    return {
        "title": title,
        "description": description,
        "keywords": keywords or "steel drum, wooden steel drum, wooden drum, pallet kayu, pabrik drum kabel",
        "canonical": request.url,
        "og_type": page_type,
        "og_image": image_url or url_for("static", filename="nature_hero.webp", _external=True),
    }


def init_db():
    """Buat tabel dan isi data awal."""
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA journal_mode=WAL")

    # ── Tabel Kategori ───────────────────────────────────────
    db.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id    INTEGER PRIMARY KEY AUTOINCREMENT,
            slug  TEXT    NOT NULL UNIQUE,
            name  TEXT    NOT NULL
        )
    """)

    # ── Tabel Produk ─────────────────────────────────────────
    db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            category    TEXT    NOT NULL,
            description TEXT,
            detail      TEXT,
            image       TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category) REFERENCES categories(slug)
        )
    """)

    # ── Tabel Artikel ────────────────────────────────────────
    db.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            content     TEXT    NOT NULL,
            image       TEXT,
            author      TEXT    DEFAULT 'Admin',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ── Seed data (hanya kalau kosong) ───────────────────────
    if db.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
        categories = [
            ("semua",  "Semua Produk"),
            ("steel_drum",   "Steel Drum"),
            ("wooden_steel_drum", "Wooden Steel Drum"),
            ("wooden_drum", "Wooden Drum"),
            ("pallet_kayu", "Pallet Kayu"),
        ]
        db.executemany("INSERT INTO categories (slug, name) VALUES (?, ?)", categories)

    db.execute("INSERT OR IGNORE INTO categories (slug, name) VALUES ('semua', 'Semua Produk')")
    db.execute("INSERT OR IGNORE INTO categories (slug, name) VALUES ('steel_drum', 'Steel Drum')")
    db.execute("INSERT OR IGNORE INTO categories (slug, name) VALUES ('wooden_steel_drum', 'Wooden Steel Drum')")
    db.execute("INSERT OR IGNORE INTO categories (slug, name) VALUES ('wooden_drum', 'Wooden Drum')")
    db.execute("INSERT OR IGNORE INTO categories (slug, name) VALUES ('pallet_kayu', 'Pallet Kayu')")
    db.execute("UPDATE products SET category = 'wooden_drum' WHERE category = 'kayu'")
    db.execute("DELETE FROM categories WHERE slug NOT IN ('semua', 'steel_drum', 'wooden_steel_drum', 'wooden_drum', 'pallet_kayu')")

    if db.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        products = [
            ("Steel Drum", "steel_drum",
             "Drum berbahan baja kuat.",
             "Steel drum kami dibuat dengan konstruksi baja unggulan, ideal untuk penggunaan berat dan umur panjang.",
             "haspel_kayu_featured.png"),
            ("Wooden Drum", "wooden_drum",
             "Haspel kayu pilihan.",
             "Haspel kayu yang tahan lama untuk kebutuhan standar kabel Anda.",
             "nature_hero.webp"),
        ]
        db.executemany(
            "INSERT INTO products (name, category, description, detail, image) VALUES (?, ?, ?, ?, ?)",
            products,
        )

    if db.execute("SELECT COUNT(*) FROM articles").fetchone()[0] == 0:
        articles = [
            ("Mengenal Jenis-Jenis Haspel Kayu untuk Industri Kabel",
             "Haspel kayu adalah alat penting dalam industri kabel. Ada beberapa jenis haspel kayu yang umum digunakan, mulai dari haspel kayu racuk, haspel kayu mahoni, hingga haspel plywood. Masing-masing memiliki kelebihan tersendiri tergantung kebutuhan dan jenis kabel yang akan digulung.\n\nHaspel kayu racuk cocok untuk penggunaan lokal dengan harga yang lebih ekonomis. Sementara haspel kayu mahoni lebih tahan lama dan biasa digunakan untuk kabel-kabel berat. Haspel plywood menjadi pilihan untuk kebutuhan yang memerlukan bobot ringan namun tetap kuat.",
             None, "Admin"),
            ("Sertifikasi ISPM #15: Pentingnya untuk Ekspor",
               "ISPM #15 (International Standards for Phytosanitary Measures No. 15) adalah standar internasional yang mengatur perlakuan terhadap kemasan kayu yang digunakan dalam perdagangan internasional. Tujuannya adalah untuk mencegah penyebaran hama dan penyakit tanaman melalui kemasan kayu.\n\nProduk haspel kayu kami tersedia dalam versi bersertifikat ISPM #15 dengan perlakuan Heat Treatment (HT) atau Methyl Bromide (MB), sehingga lebih siap untuk kebutuhan distribusi dan proyek ekspor.",
             None, "Admin"),
        ]
        db.executemany(
            "INSERT INTO articles (title, content, image, author) VALUES (?, ?, ?, ?)",
            articles,
        )

    # ── Move Generated Images & Insert Wooden Steel Drum ────────
    import shutil
    
    src1 = r"C:\Users\MY THINKPAD\.gemini\antigravity\brain\fb1edf38-18b9-4b65-b51c-542cd08cb933\product_steel_drum_1775620101570.png"
    src2 = r"C:\Users\MY THINKPAD\.gemini\antigravity\brain\fb1edf38-18b9-4b65-b51c-542cd08cb933\product_wooden_drum_1775620151640.png"
    src3 = r"C:\Users\MY THINKPAD\.gemini\antigravity\brain\fb1edf38-18b9-4b65-b51c-542cd08cb933\product_wooden_steel_drum_1775620180166.png"
    
    dest1 = os.path.join(UPLOAD_FOLDER, "product_steel_drum.png")
    dest2 = os.path.join(UPLOAD_FOLDER, "product_wooden_drum.png")
    dest3 = os.path.join(UPLOAD_FOLDER, "product_wooden_steel_drum.png")
    
    if os.path.exists(src1): shutil.copy(src1, dest1)
    if os.path.exists(src2): shutil.copy(src2, dest2)
    if os.path.exists(src3): shutil.copy(src3, dest3)
    
    # Update products with uniform images
    db.execute("UPDATE products SET image = 'uploads/product_steel_drum.png' WHERE category = 'steel_drum'")
    db.execute("UPDATE products SET image = 'uploads/product_wooden_drum.png' WHERE category = 'wooden_drum'")

    # Insert Wooden Steel Drum if it doesn't exist
    existing = db.execute("SELECT id FROM products WHERE category = 'wooden_steel_drum'").fetchone()
    if not existing:
        db.execute(
            "INSERT INTO products (name, category, description, detail, image) VALUES (?, ?, ?, ?, ?)",
            (
                "Wooden Steel Drum", 
                "wooden_steel_drum",
                "Kombinasi optimal kayu dan baja.",
                "Memberikan kekuatan struktural baja (steel) dan fleksibilitas fungsional kayu (wooden) untuk mengakomodasi distribusi kabel yang aman, awet, dan tahan banting pada ekspedisi jarak jauh.",
                "uploads/product_wooden_steel_drum.png"
            )
        )

    db.commit()
    db.close()


# ═══════════════════════════════════════════════════════════════
# AUTH DECORATOR
# ═══════════════════════════════════════════════════════════════

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            flash("Silakan login terlebih dahulu.", "warning")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


# ═══════════════════════════════════════════════════════════════
# PUBLIC ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    db = get_db()
    category = request.args.get("category", "semua")
    if category not in ALLOWED_CATALOG_CATEGORIES:
        category = "semua"

    search_query = request.args.get("q", "").strip()
    tab = request.args.get("tab", "katalog")

    categories = db.execute(
        "SELECT * FROM categories WHERE slug IN ('semua', 'steel_drum', 'wooden_steel_drum', 'wooden_drum', 'pallet_kayu') ORDER BY id"
    ).fetchall()

    if search_query:
        products = db.execute(
            """
            SELECT * FROM products
            WHERE (category = ? OR ? = 'semua') AND (name LIKE ? OR description LIKE ? OR detail LIKE ?)
            ORDER BY 
                CASE category
                    WHEN 'wooden_drum' THEN 1
                    WHEN 'wooden_steel_drum' THEN 2
                    WHEN 'steel_drum' THEN 3
                    ELSE 4
                END, created_at DESC
            """,
            (category, category, f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"),
        ).fetchall()
    else:
        products = db.execute(
            """
            SELECT * FROM products WHERE (category = ? OR ? = 'semua') 
            ORDER BY 
                CASE category
                    WHEN 'wooden_drum' THEN 1
                    WHEN 'wooden_steel_drum' THEN 2
                    WHEN 'steel_drum' THEN 3
                    ELSE 4
                END, created_at DESC
            """,
            (category, category)
        ).fetchall()

    cat_map = {'steel_drum': 'Steel Drum', 'wooden_steel_drum': 'Wooden Steel Drum', 'wooden_drum': 'Wooden Drum', 'pallet_kayu': 'Pallet Kayu', 'semua': 'Semua Produk'}
    active_category_name = cat_map.get(category, 'Semua Produk')

    # Ambil artikel untuk tab info
    articles = db.execute("SELECT * FROM articles ORDER BY created_at DESC LIMIT 6").fetchall()

    seo_title = f"{SITE_NAME} - {SITE_TAGLINE}"
    seo_description = (
        "Produsen haspel kayu untuk industri kabel: layanan custom ukuran, standar ISPM 15, "
        "dan pengiriman untuk kebutuhan proyek lokal maupun ekspor."
    )
    if tab == "info":
        seo_title = f"Informasi Perusahaan & Artikel - {SITE_NAME}"
    if search_query:
        seo_title = f"Hasil Pencarian '{search_query}' - {SITE_NAME}"
        seo_description = (
            f"Temukan produk haspel kayu terkait '{search_query}' dari {SITE_NAME}. "
            "Melayani kebutuhan industri kabel dengan kualitas terjaga."
        )

    seo_meta = build_seo_meta(
        seo_title,
        seo_description,
        keywords="haspel kayu, produsen haspel kayu, haspel kayu ispm 15, pabrik haspel indonesia",
    )

    return render_template(
        "index.html",
        products=products,
        categories=categories,
        active_category=category,
        active_category_name=active_category_name,
        search_query=request.args.get("q", ""),
        tab=tab,
        articles=articles,
        seo=seo_meta,
    )


@app.route("/artikel")
def articles_list():
    db = get_db()
    articles = db.execute("SELECT * FROM articles ORDER BY created_at DESC").fetchall()
    
    seo_meta = build_seo_meta(
        f"Kumpulan Artikel - {SITE_NAME}",
        "Baca berbagai artikel informatif dan berita terbaru seputar industri haspel kayu dan steel drum.",
        keywords="artikel haspel kayu, berita industri, pabrik drum kayu",
    )
    
    return render_template("articles.html", articles=articles, seo=seo_meta)


@app.route("/artikel/<int:article_id>")
def article_detail(article_id):
    db = get_db()
    article = db.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()
    if not article:
        flash("Artikel tidak ditemukan.", "error")
        return redirect(url_for("index"))

    related_articles = db.execute(
        "SELECT * FROM articles WHERE id != ? ORDER BY created_at DESC LIMIT 3", (article_id,)
    ).fetchall()

    summary = (article["content"] or "").replace("\n", " ").strip()
    seo_meta = build_seo_meta(
        f"{article['title']} - {SITE_NAME}",
        summary[:160] if summary else "Artikel terbaru seputar haspel kayu untuk industri kabel.",
        page_type="article",
        image_url=(
            url_for("static", filename=article["image"], _external=True)
            if article["image"] and article["image"].startswith("uploads/")
            else article["image"]
        ),
        keywords="artikel haspel kayu, informasi haspel kayu, industri kabel",
    )

    return render_template(
        "article_detail.html",
        article=article,
        related_articles=related_articles,
        seo=seo_meta,
    )


# ═══════════════════════════════════════════════════════════════
# ADMIN ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            flash("Login berhasil!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Username atau password salah.", "error")
    return render_template("admin/login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    flash("Anda telah logout.", "info")
    return redirect(url_for("admin_login"))


@app.route("/admin")
@login_required
def admin_dashboard():
    db = get_db()
    product_count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    article_count = db.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    category_count = db.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    return render_template("admin/dashboard.html",
                           product_count=product_count,
                           article_count=article_count,
                           category_count=category_count)


# ── Product CRUD ─────────────────────────────────────────────

@app.route("/admin/products")
@login_required
def admin_products():
    db = get_db()
    products = db.execute("SELECT * FROM products ORDER BY created_at DESC").fetchall()
    return render_template("admin/products.html", products=products)


@app.route("/admin/products/add", methods=["GET", "POST"])
@login_required
def admin_product_add():
    db = get_db()
    categories = db.execute("SELECT * FROM categories ORDER BY id").fetchall()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "")
        description = request.form.get("description", "").strip()
        detail = request.form.get("detail", "").strip()
        image_url = request.form.get("image_url", "").strip()

        # Handle file upload
        file = request.files.get("image_file")
        if file and file.filename:
            saved = save_upload(file)
            if saved:
                image_url = saved

        if category not in ALLOWED_CATALOG_CATEGORIES:
            flash("Kategori produk hanya tersedia untuk Haspel Kayu.", "error")
        elif not name or not category:
            flash("Nama dan kategori wajib diisi.", "error")
        else:
            db.execute(
                "INSERT INTO products (name, category, description, detail, image) VALUES (?, ?, ?, ?, ?)",
                (name, category, description, detail, image_url),
            )
            db.commit()
            flash("Produk berhasil ditambahkan!", "success")
            return redirect(url_for("admin_products"))

    return render_template("admin/product_form.html", categories=categories, product=None)


@app.route("/admin/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required
def admin_product_edit(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    categories = db.execute("SELECT * FROM categories ORDER BY id").fetchall()

    if not product:
        flash("Produk tidak ditemukan.", "error")
        return redirect(url_for("admin_products"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "")
        description = request.form.get("description", "").strip()
        detail = request.form.get("detail", "").strip()
        image_url = request.form.get("image_url", "").strip()

        # Handle file upload (replace existing)
        file = request.files.get("image_file")
        if file and file.filename:
            saved = save_upload(file)
            if saved:
                image_url = saved

        # Kalau tidak ada perubahan gambar, pakai yang lama
        if not image_url:
            image_url = product["image"]

        if category not in ALLOWED_CATALOG_CATEGORIES:
            flash("Kategori produk hanya tersedia untuk Haspel Kayu.", "error")
        elif not name or not category:
            flash("Nama dan kategori wajib diisi.", "error")
        else:
            db.execute(
                "UPDATE products SET name=?, category=?, description=?, detail=?, image=? WHERE id=?",
                (name, category, description, detail, image_url, product_id),
            )
            db.commit()
            flash("Produk berhasil diupdate!", "success")
            return redirect(url_for("admin_products"))

    return render_template("admin/product_form.html", categories=categories, product=product)


@app.route("/admin/products/delete/<int:product_id>", methods=["POST"])
@login_required
def admin_product_delete(product_id):
    db = get_db()
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    flash("Produk berhasil dihapus.", "success")
    return redirect(url_for("admin_products"))


# ── Article CRUD ─────────────────────────────────────────────

@app.route("/admin/articles")
@login_required
def admin_articles():
    db = get_db()
    articles = db.execute("SELECT * FROM articles ORDER BY created_at DESC").fetchall()
    return render_template("admin/articles.html", articles=articles)


@app.route("/admin/articles/add", methods=["GET", "POST"])
@login_required
def admin_article_add():
    if request.method == "POST":
        db = get_db()
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        author = request.form.get("author", "Admin").strip()
        image_url = request.form.get("image_url", "").strip()

        file = request.files.get("image_file")
        if file and file.filename:
            saved = save_upload(file)
            if saved:
                image_url = saved

        if not title or not content:
            flash("Judul dan konten wajib diisi.", "error")
        else:
            db.execute(
                "INSERT INTO articles (title, content, image, author) VALUES (?, ?, ?, ?)",
                (title, content, image_url or None, author),
            )
            db.commit()
            flash("Artikel berhasil dipublikasikan!", "success")
            return redirect(url_for("admin_articles"))

    return render_template("admin/article_form.html", article=None)


@app.route("/admin/articles/edit/<int:article_id>", methods=["GET", "POST"])
@login_required
def admin_article_edit(article_id):
    db = get_db()
    article = db.execute("SELECT * FROM articles WHERE id = ?", (article_id,)).fetchone()

    if not article:
        flash("Artikel tidak ditemukan.", "error")
        return redirect(url_for("admin_articles"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        author = request.form.get("author", "Admin").strip()
        image_url = request.form.get("image_url", "").strip()

        file = request.files.get("image_file")
        if file and file.filename:
            saved = save_upload(file)
            if saved:
                image_url = saved

        if not image_url:
            image_url = article["image"]

        if not title or not content:
            flash("Judul dan konten wajib diisi.", "error")
        else:
            db.execute(
                "UPDATE articles SET title=?, content=?, image=?, author=? WHERE id=?",
                (title, content, image_url, author, article_id),
            )
            db.commit()
            flash("Artikel berhasil diupdate!", "success")
            return redirect(url_for("admin_articles"))

    return render_template("admin/article_form.html", article=article)


@app.route("/admin/articles/delete/<int:article_id>", methods=["POST"])
@login_required
def admin_article_delete(article_id):
    db = get_db()
    db.execute("DELETE FROM articles WHERE id = ?", (article_id,))
    db.commit()
    flash("Artikel berhasil dihapus.", "success")
    return redirect(url_for("admin_articles"))


# ═══════════════════════════════════════════════════════════════
# TEMPLATE HELPERS
# ═══════════════════════════════════════════════════════════════

@app.template_filter("nl2br")
def nl2br_filter(s):
    """Convert newlines to <br> tags."""
    if s:
        return s.replace("\n", "<br>")
    return ""


# ═══════════════════════════════════════════════════════════════
# STARTUP
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
