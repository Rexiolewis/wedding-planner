from flask import Flask, render_template, request, redirect, url_for, g, session, flash
import sqlite3
from datetime import datetime
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'S@r@WedsL@vi2026'  # Change this to a secure secret key

# User credentials
USERNAME = 'LS'
PASSWORD = 'S@r@WedsL@vi2026'

# Database configuration
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'wedding.db')
SCHEMA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scheme.sql')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db():
    if 'db' not in g:
        # Ensure database directory exists
        db_dir = os.path.dirname(DATABASE)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    try:
        with open(SCHEMA_FILE, 'r') as f:
            db.cursor().executescript(f.read())
        db.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    # Initialize database if it doesn't exist
    if not os.path.exists(DATABASE):
        init_db()
    
    db = get_db()
    
    # Get expenses summary
    expenses = db.execute('SELECT category, SUM(cost) as total FROM expenses GROUP BY category ORDER BY total DESC').fetchall()
    total_expenses = db.execute('SELECT SUM(cost) as grand_total FROM expenses').fetchone()['grand_total'] or 0
    
    # Get guest count
    guest_count = db.execute('SELECT COUNT(*) as count FROM guests').fetchone()['count']
    
    # Get guest summary
    guest_summary = db.execute('''
        SELECT side, 
               COUNT(*) as count,
               SUM(pax) as total_pax
        FROM guests 
        GROUP BY side
    ''').fetchall()
    
    # Get total pax
    total_pax = db.execute('SELECT SUM(pax) as total FROM guests').fetchone()['total'] or 0
    
    return render_template('dashboard.html',
                         expenses=expenses,
                         total_expenses=total_expenses,
                         guest_count=guest_count,
                         total_pax=total_pax,
                         guest_summary=guest_summary)

@app.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    db = get_db()
    
    if request.method == 'POST':
        item = request.form['item']
        category = request.form['category']
        cost = float(request.form['cost'])
        date = datetime.now().strftime('%Y-%m-%d')
        
        db.execute('INSERT INTO expenses (item, category, cost, date) VALUES (?, ?, ?, ?)',
                  [item, category, cost, date])
        db.commit()
        return redirect(url_for('expenses'))
    
    expenses = db.execute('SELECT * FROM expenses ORDER BY date DESC').fetchall()
    return render_template('expenses.html', expenses=expenses)

@app.route('/guests', methods=['GET', 'POST'])
@login_required
def guests():
    db = get_db()
    
    if request.method == 'POST':
        name = request.form['name']
        side = request.form['side']
        pax = int(request.form['pax'])
        status = request.form['status']
        
        db.execute('INSERT INTO guests (name, side, pax, status) VALUES (?, ?, ?, ?)',
                  [name, side, pax, status])
        db.commit()
        return redirect(url_for('guests'))
    
    guests = db.execute('SELECT * FROM guests ORDER BY name').fetchall()
    return render_template('guests.html', guests=guests)

if __name__ == '__main__':
    # Initialize database if running locally
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)