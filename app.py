from flask import Flask, render_template, request, redirect, url_for, flash, session

app = Flask(__name__)
app.secret_key = "secret_key_123"

# Temporary in-memory storage
users = {}

@app.route('/')
def home():
    if 'username' in session:
        # Redirect based on role
        role = session.get('role')
        if role == 'staff':
            return redirect(url_for('staff_dashboard'))
        else:
            return redirect(url_for('customer_dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']
        role = request.form['role']  # customer or staff

        if password != confirm:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('register'))
        elif username in users:
            flash('Username already exists!', 'error')
            return redirect(url_for('register'))
        else:
            users[username] = {'password': password, 'role': role}
            flash('Account created successfully! You can now login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and users[username]['password'] == password:
            session['username'] = username
            session['role'] = users[username]['role']  # store role
            flash('Login successful!', 'success')

            # Redirect based on role
            if session['role'] == 'staff':
                return redirect(url_for('staff_dashboard'))
            else:
                return redirect(url_for('customer_dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/customer_dashboard')
def customer_dashboard():
    if 'username' in session and session.get('role') == 'customer':
        return render_template('customer_dashboard.html', username=session['username'])
    else:
        flash('Access denied!', 'error')
        return redirect(url_for('login'))

@app.route('/staff_dashboard')
def staff_dashboard():
    if 'username' in session and session.get('role') == 'staff':
        return render_template('staff_dashboard.html', username=session['username'])
    else:
        flash('Access denied!', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
