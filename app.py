from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret_key_123"
DB_NAME = "laundry_system.db"


# =============================
# DATABASE SETUP
# =============================
def init_db():
    """Initialize or repair the database structure."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # USERS TABLE
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            address TEXT
        )
    """)

    # SERVICES TABLE
    c.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            price_per_kg REAL NOT NULL
        )
    """)

    # ORDERS TABLE
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            service_id INTEGER,
            kilograms REAL,
            total_price REAL,
            status TEXT DEFAULT 'Pending',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (service_id) REFERENCES services(id)
        )
    """)

    # Default admin
    admin_hashed = generate_password_hash('admin123')
    c.execute("""
        INSERT OR REPLACE INTO users (id, username, password, role)
        VALUES (?, ?, ?, ?)
    """, (1, 'admin', admin_hashed, 'admin'))

    # Default services
    default_services = [
        ("Wash & Fold", 50.0),
        ("Dry Clean", 80.0),
        ("Iron Only", 30.0),
    ]
    for name, price in default_services:
        c.execute("INSERT OR IGNORE INTO services (name, price_per_kg) VALUES (?, ?)", (name, price))

    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def get_user(username):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return user


def clean_orphan_orders():
    """Delete orders linked to missing users or services."""
    conn = get_db()
    conn.execute("""
        DELETE FROM orders
        WHERE user_id NOT IN (SELECT id FROM users)
           OR service_id NOT IN (SELECT id FROM services)
    """)
    conn.commit()
    conn.close()


# Initialize DB and clean
init_db()
clean_orphan_orders()


# =============================
# ROUTES
# =============================

@app.route('/')
def home():
    """When app starts, go directly to the login page."""
    return redirect(url_for('login'))


# =============================
# REGISTER
# =============================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        conn = get_db()

        try:
            conn.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, hashed_password, 'customer')
            )
            conn.commit()
            user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
            session['username'] = user['username']
            session['role'] = user['role']
            session['user_id'] = user['id']
            flash('Account created successfully! Welcome!', 'success')
            conn.close()
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('Username already exists!', 'error')
            conn.close()
            return redirect(url_for('register'))

    return render_template('register.html')


# =============================
# LOGIN
# =============================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = get_user(username)

        if user and check_password_hash(user['password'], password):
            session['username'] = user['username']
            session['role'] = user['role'].lower()
            session['user_id'] = user['id']
            flash('Login successful!', 'success')

            if session['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


# =============================
# INDEX (Customer Home Page)
# =============================
@app.route('/index')
def index():
    """Render the main homepage (index.html)."""
    return render_template('index.html')


# =============================
# ADMIN DASHBOARD
# =============================
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'username' not in session or session.get('role') != 'admin':
        flash('Access denied! Admins only.', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    pending_count = conn.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'").fetchone()[0]
    completed_count = conn.execute("SELECT COUNT(*) FROM orders WHERE status='Delivered'").fetchone()[0]
    conn.close()

    return render_template('admin_dashboard.html',
                           username=session['username'],
                           pending_count=pending_count,
                           completed_count=completed_count)


# =============================
# ADMIN ORDERS
# =============================
@app.route('/admin_orders')
def admin_orders():
    if 'username' not in session or session.get('role') != 'admin':
        flash('Access denied! Admins only.', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    orders = conn.execute("""
        SELECT o.id, u.username AS customer_name, s.name AS service,
               o.kilograms, o.total_price, o.status, o.created_at
        FROM orders o
        JOIN users u ON o.user_id = u.id
        JOIN services s ON o.service_id = s.id
        ORDER BY o.id ASC
    """).fetchall()
    conn.close()

    return render_template('admin_orders.html',
                           username=session['username'],
                           orders=orders)


# =============================
# ADMIN: UPDATE ORDER STATUS
# =============================
@app.route('/update_order/<int:order_id>', methods=['POST'])
def update_order(order_id):
    """Allow admin to update order status."""
    if 'username' not in session or session.get('role') != 'admin':
        flash('Access denied! Admins only.', 'error')
        return redirect(url_for('login'))

    new_status = request.form['status']
    conn = get_db()
    conn.execute("UPDATE orders SET status=? WHERE id=?", (new_status, order_id))
    conn.commit()
    conn.close()

    flash('Order status updated successfully!', 'success')
    return redirect(url_for('admin_orders'))


# =============================
# ADMIN: DELETE ORDER
# =============================
@app.route('/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    """Allow admin to delete a specific order."""
    if 'username' not in session or session.get('role') != 'admin':
        flash('Access denied! Admins only.', 'error')
        return redirect(url_for('login'))

    conn = get_db()
    conn.execute("DELETE FROM orders WHERE id=?", (order_id,))
    conn.commit()
    conn.close()

    flash('Order deleted successfully!', 'success')
    return redirect(url_for('admin_orders'))


# =============================
# CUSTOMER DASHBOARD
# =============================
@app.route('/customer_dashboard')
def customer_dashboard():
    if 'username' in session and session.get('role') == 'customer':
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (session['username'],)).fetchone()
        services = conn.execute("SELECT * FROM services").fetchall()
        orders = conn.execute("""
            SELECT o.id, s.name AS service_name, o.kilograms,
                   o.total_price, o.status, o.created_at
            FROM orders o
            JOIN services s ON o.service_id = s.id
            WHERE o.user_id=?
            ORDER BY o.id DESC
        """, (session['user_id'],)).fetchall()
        conn.close()

        address = user['address'] if user['address'] else ""
        return render_template('customer_dashboard.html',
                               username=session['username'],
                               address=address,
                               services=services,
                               orders=orders)
    else:
        flash('Access denied! Customers only.', 'error')
        return redirect(url_for('login'))


# =============================
# CUSTOMER FUNCTIONS
# =============================
@app.route('/update_address', methods=['POST'])
def update_address():
    if 'username' in session and session.get('role') == 'customer':
        address = request.form['address']
        conn = get_db()
        conn.execute("UPDATE users SET address=? WHERE username=?", (address, session['username']))
        conn.commit()
        conn.close()
        flash('Address updated successfully!', 'success')
        return redirect(url_for('customer_dashboard'))
    else:
        flash('Access denied!', 'error')
        return redirect(url_for('login'))


@app.route('/place_order', methods=['POST'])
def place_order():
    if 'username' in session and session.get('role') == 'customer':
        service_id = request.form['service_id']
        kilograms = float(request.form['kilograms'])
        conn = get_db()
        price = conn.execute("SELECT price_per_kg FROM services WHERE id=?", (service_id,)).fetchone()['price_per_kg']
        total = price * kilograms
        conn.execute("""
            INSERT INTO orders (user_id, service_id, kilograms, total_price)
            VALUES (?, ?, ?, ?)
        """, (session['user_id'], service_id, kilograms, total))
        conn.commit()
        conn.close()

        flash(f'Order placed successfully! Total: ₱{total:.2f}', 'success')
        return redirect(url_for('customer_dashboard'))
    else:
        flash('Access denied!', 'error')
        return redirect(url_for('login'))


# =============================
# ABOUT US
# =============================
@app.route('/about_us')
def about_us():
    """Ensure About Us links Home correctly."""
    return render_template('about_us.html', username=session.get('username'))


# =============================
# LOGOUT
# =============================
@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
