from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import os

from werkzeug.utils import secure_filename
from flask import send_file
import shutil
app = Flask(__name__)
UPLOAD_FOLDER = '/var/www/flaskapp/uploads'
DEFAULT_LIMERICK = '/var/www/flaskapp/static/Limerick.txt'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATABASE = '/var/www/flaskapp/users.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        firstname TEXT,
        lastname TEXT,
        email TEXT,
        address TEXT,
        wordcount INTEGER
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.form
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("INSERT INTO users (username,password,firstname,lastname,email,address,wordcount) VALUES (?,?,?,?,?,?,?)",
              (data['username'], data['password'], data['firstname'], data['lastname'], data['email'], data['address'], 0))
    conn.commit()
    conn.close()
    return redirect(url_for('profile', username=data['username']))

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        return redirect(url_for('profile', username=username))
    return "Invalid login"

@app.route('/profile/<username>')
def profile(username):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/upload/<username>', methods=['POST'])
def upload_file(username):
    file = request.files['file']
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    with open(filepath, 'r') as f:
        words = f.read().split()
        wordcount = len(words)

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE users SET wordcount=? WHERE username=?", (wordcount, username))
    conn.commit()
    conn.close()

    return redirect(url_for('profile', username=username))

@app.route('/use_limerick/<username>', methods=['POST'])
def use_limerick(username):
    filename = "Limerick.txt"
    dest = os.path.join(UPLOAD_FOLDER, filename)

    # copy the server’s default file into uploads/
    shutil.copyfile(DEFAULT_LIMERICK, dest)

    with open(dest, 'r', encoding='utf-8', errors='ignore') as f:
        wordcount = len(f.read().split())

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("UPDATE users SET wordcount=?, uploaded_file=? WHERE username=?",
              (wordcount, filename, username))
    conn.commit()
    conn.close()

    return redirect(url_for('profile', username=username))

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)


if __name__ == '__main__':
    app.run()
