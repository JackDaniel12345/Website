from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'laundry_secret_key'

# In-memory user storage
users = {}

@app.route('/')
def home():
    if 'username' in session:
        username = session['username']
        role = session.get('role')

        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return render_template('index.html', username=username)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if not username or not password:
            flash('Please fill in all fields!', 'error')
            return redirect(url_for('register'))

        if username in users:
            flash('Username already exists!', 'error')
            return redirect(url_for('register'))

        # Save user as a customer by default
        users[username] = {
            'password': generate_password_hash(password),
            'role': 'customer'
        }

        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        # Admin login
        if username == 'admin' and password == 'admin123':
            session['username'] = 'admin'
            session['role'] = 'admin'
            flash('Welcome Admin!', 'success')
            return redirect(url_for('admin_dashboard'))

        # Regular users
        if username in users and check_password_hash(users[username]['password'], password):
            session['username'] = username
            session['role'] = users[username]['role']
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    if 'username' in session and session.get('role') == 'admin':
        return render_template('admin.html', username=session['username'])
    else:
        flash('Access denied! Admins only.', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
