from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# Database configuration
DATABASE = 'wedding.db'

def get_db():
    if 'db' not in g:
        # Make sure the instance folder exists
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
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
        with app.open_resource('scheme.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()

# Routes
@app.route('/')
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