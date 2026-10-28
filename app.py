"""Annachi Store - supermarket website (Flask + SQLite, no JavaScript)."""
import os
import sqlite3
from functools import wraps

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, g)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-this-secret-key")
os.makedirs(app.instance_path, exist_ok=True)
DATABASE = os.path.join(app.instance_path, "annachi.db")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "annachi123")

# ---- Edit your shop details here ------------------------------------------
STORE = {
    "name": "Annachi Store",
    "tamil_name": "அண்ணாச்சி ஸ்டோர்",
    "tagline": "Namma Kadai - Fresh, Fair & Familiar",
    "phone": "+91 98765 43210",
    "whatsapp": "919876543210",
    "email": "karthik@gmail.com .",
    "address": "12, Main Bazaar Street, Your Town - 600 000",
    "hours": "Mon - Sun: 6:30 AM to 10:00 PM",
    "year_started": 1998,
}

CATEGORIES = {
    "Rice & Dals": "🌾",
    "Spices & Masala": "🌶️",
    "Oils & Ghee": "🫙",
    "Fruits & Vegetables": "🥬",
    "Dairy": "🥛",
    "Snacks & Beverages": "🍵",
    "Household": "🧼",
}

SEED_PRODUCTS = [
    # name, tamil, category, price, unit, emoji, featured
    ("Ponni Boiled Rice", "பொன்னி புழுங்கல் அரிசி", "Rice & Dals", 62, "per kg", "🍚", 1),
    ("Idli Rice", "இட்லி அரிசி", "Rice & Dals", 55, "per kg", "🍚", 0),
    ("Toor Dal", "துவரம் பருப்பு", "Rice & Dals", 165, "per kg", "🫘", 1),
    ("Urad Dal", "உளுந்து", "Rice & Dals", 140, "per kg", "🫘", 0),
    ("Turmeric Powder", "மஞ்சள் தூள்", "Spices & Masala", 30, "100 g", "🟡", 1),
    ("Red Chilli Powder", "மிளகாய் தூள்", "Spices & Masala", 45, "100 g", "🌶️", 0),
    ("Coriander Powder", "மல்லித் தூள்", "Spices & Masala", 28, "100 g", "🌿", 0),
    ("Black Pepper", "மிளகு", "Spices & Masala", 95, "100 g", "⚫", 0),
    ("Tamarind", "புளி", "Spices & Masala", 40, "250 g", "🟤", 0),
    ("Gingelly Oil", "நல்லெண்ணெய்", "Oils & Ghee", 420, "1 litre", "🫙", 1),
    ("Coconut Oil", "தேங்காய் எண்ணெய்", "Oils & Ghee", 210, "1 litre", "🥥", 0),
    ("Pure Ghee", "நெய்", "Oils & Ghee", 640, "500 ml", "🧈", 0),
    ("Coconut", "தேங்காய்", "Fruits & Vegetables", 28, "each", "🥥", 0),
    ("Onion", "வெங்காயம்", "Fruits & Vegetables", 35, "per kg", "🧅", 1),
    ("Tomato", "தக்காளி", "Fruits & Vegetables", 30, "per kg", "🍅", 0),
    ("Robusta Banana", "வாழைப்பழம்", "Fruits & Vegetables", 45, "per kg", "🍌", 0),
    ("Fresh Milk", "பால்", "Dairy", 28, "500 ml", "🥛", 0),
    ("Curd", "தயிர்", "Dairy", 35, "500 g", "🥣", 0),
    ("Filter Coffee Powder", "காபி தூள்", "Snacks & Beverages", 180, "250 g", "☕", 1),
    ("Tea Dust", "தேயிலை", "Snacks & Beverages", 120, "250 g", "🍵", 0),
    ("Hand-made Murukku", "முறுக்கு", "Snacks & Beverages", 90, "200 g", "🥨", 0),
    ("Jaggery (Vellam)", "வெல்லம்", "Snacks & Beverages", 70, "500 g", "🟫", 0),
    ("Bath Soap", "குளியல் சோப்பு", "Household", 38, "each", "🧼", 0),
    ("Detergent Powder", "சலவைத் தூள்", "Household", 95, "1 kg", "🧺", 0),
]


# ---- Database ---------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            tamil_name TEXT DEFAULT '',
            category TEXT NOT NULL,
            price REAL NOT NULL,
            unit TEXT NOT NULL,
            emoji TEXT DEFAULT '🛒',
            featured INTEGER DEFAULT 0,
            in_stock INTEGER DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    if db.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO products (name, tamil_name, category, price, unit, emoji, featured) "
            "VALUES (?,?,?,?,?,?,?)", SEED_PRODUCTS)
    db.commit()
    db.close()


@app.context_processor
def inject_globals():
    return {"store": STORE, "categories": CATEGORIES}


def admin_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return view(*a, **kw)
    return wrapped


# ---- Public pages -------------------------------------------------------------
@app.route("/")
def index():
    db = get_db()
    featured = db.execute(
        "SELECT * FROM products WHERE featured=1 AND in_stock=1 LIMIT 8").fetchall()
    return render_template("index.html", featured=featured)


@app.route("/products")
def products():
    q = request.args.get("q", "").strip()
    cat = request.args.get("category", "").strip()
    sql, args = "SELECT * FROM products WHERE 1=1", []
    if q:
        sql += " AND (name LIKE ? OR tamil_name LIKE ?)"
        args += [f"%{q}%", f"%{q}%"]
    if cat in CATEGORIES:
        sql += " AND category=?"
        args.append(cat)
    sql += " ORDER BY category, name"
    items = get_db().execute(sql, args).fetchall()
    return render_template("products.html", items=items, q=q, active=cat)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        message = request.form.get("message", "").strip()
        if not (name and phone and message):
            flash("Please fill in all the fields.", "error")
        else:
            db = get_db()
            db.execute("INSERT INTO messages (name, phone, message) VALUES (?,?,?)",
                       (name[:80], phone[:20], message[:1000]))
            db.commit()
            flash("Nandri! Your message has reached us. We will call you soon.", "ok")
            return redirect(url_for("contact"))
    return render_template("contact.html")


# ---- Admin ----------------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        flash("Wrong password.", "error")
    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin():
    db = get_db()
    items = db.execute("SELECT * FROM products ORDER BY category, name").fetchall()
    msgs = db.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 50").fetchall()
    return render_template("admin.html", items=items, msgs=msgs)


@app.route("/admin/add", methods=["POST"])
@admin_required
def admin_add():
    f = request.form
    try:
        price = float(f.get("price", "0"))
    except ValueError:
        price = 0
    if not f.get("name", "").strip() or price <= 0 or f.get("category") not in CATEGORIES:
        flash("Please give a valid name, category and price.", "error")
        return redirect(url_for("admin"))
    db = get_db()
    db.execute(
        "INSERT INTO products (name, tamil_name, category, price, unit, emoji, featured) "
        "VALUES (?,?,?,?,?,?,?)",
        (f["name"].strip(), f.get("tamil_name", "").strip(), f["category"], price,
         f.get("unit", "each").strip() or "each",
         f.get("emoji", "").strip() or CATEGORIES[f["category"]],
         1 if f.get("featured") else 0))
    db.commit()
    flash("Product added.", "ok")
    return redirect(url_for("admin"))


@app.route("/admin/toggle/<int:pid>/<field>", methods=["POST"])
@admin_required
def admin_toggle(pid, field):
    if field in ("in_stock", "featured"):
        db = get_db()
        db.execute(f"UPDATE products SET {field} = 1 - {field} WHERE id=?", (pid,))
        db.commit()
    return redirect(url_for("admin"))


@app.route("/admin/delete/<int:pid>", methods=["POST"])
@admin_required
def admin_delete(pid):
    db = get_db()
    db.execute("DELETE FROM products WHERE id=?", (pid,))
    db.commit()
    flash("Product removed.", "ok")
    return redirect(url_for("admin"))


init_db()

if __name__ == "__main__":
    app.run(debug=True)
