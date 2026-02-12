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
    # Users table - stores user information
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        firstname TEXT,
        lastname TEXT,
        email TEXT,
        address TEXT
    )''')
    # Files table - stores file information with user ownership
    c.execute('''CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        wordcount INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id)
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
    c.execute("INSERT INTO users (username,password,firstname,lastname,email,address) VALUES (?,?,?,?,?,?)",
              (data['username'], data['password'], data['firstname'], data['lastname'], data['email'], data['address']))
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

@app.route('/logout')
def logout():
    return redirect(url_for('login_page'))

@app.route('/profile/<username>')
def profile(username):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    
    # Get all files owned by this user
    c.execute("SELECT * FROM files WHERE user_id=?", (user[0],))
    files = c.fetchall()
    
    # Calculate total word count from all files
    total_wordcount = sum(f[4] for f in files) if files else 0
    
    conn.close()
    return render_template('profile.html', user=user, files=files, total_wordcount=total_wordcount)

@app.route('/upload/<username>', methods=['POST'])
def upload_file(username):
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    with open(filepath, 'r') as f:
        words = f.read().split()
        wordcount = len(words)

    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Get user id
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    user_id = c.fetchone()[0]
    
    # Insert file record
    c.execute("INSERT INTO files (user_id, filename, filepath, wordcount) VALUES (?,?,?,?)",
              (user_id, filename, filepath, wordcount))
    
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
    
    # Get user id
    c.execute("SELECT id FROM users WHERE username=?", (username,))
    user_id = c.fetchone()[0]
    
    # Insert file record
    c.execute("INSERT INTO files (user_id, filename, filepath, wordcount) VALUES (?,?,?,?)",
              (user_id, filename, dest, wordcount))
    
    conn.commit()
    conn.close()

    return redirect(url_for('profile', username=username))

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename), as_attachment=True)


if __name__ == '__main__':
    app.run()
