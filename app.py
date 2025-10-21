from flask import Flask, render_template, request, session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    # Dummy check
    if username == 'user' and password == 'pass':
        session['username'] = username
        return redirect(url_for('home'))
    else:
        return render_template('index.html', error='Invalid login')

@app.route('/home')
def home():
    if 'username' in session:
        return redirect(url_for('index'))
    return render_template('home.html', user=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
