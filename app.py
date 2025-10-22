from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'laundry_secret_key'

# Temporary in-memory user storage (use a database in the future)
users = {}

# -----------------------------
# ROUTES
# -----------------------------

@app.route('/')
def home():
    # Only show homepage if logged in
    if 'username' in session:
        username = session['username']
        return render_template('index.html', username=username)
    else:
        return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if username in users:
            flash('Username already exists!', 'error')
            return redirect(url_for('register'))

        if not username or not password:
            flash('Please fill in all fields!', 'error')
            return redirect(url_for('register'))

        # Hash the password
        users[username] = generate_password_hash(password)
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if username in users and check_password_hash(users[username], password):
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password!', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
