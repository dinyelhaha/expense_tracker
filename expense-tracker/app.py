from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Database setup
DATABASE = 'expenses.db'

def get_db_connection():
    """Connect to the SQLite database and return the connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enables column access by name
    return conn

# Initialize database (if it doesn't exist)
def init_db():
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                 
    )
    ''')
    conn.close()

# Route: Home Page
@app.route('/')
def index():
    """Display all tasks."""
    conn = get_db_connection()
    expenses = conn.execute('SELECT * FROM expenses').fetchall()
    conn.close()
    return render_template('index.html', expenses=expenses)

# Route: Add Task
@app.route('/add', methods=('GET', 'POST'))
def add_expenses():
    if request.method == 'POST':
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        amount = request.form.get('amount', '').strip()

        error = None
        invalid_fields = []

        if not description:
            error = "Description is required."
            invalid_fields.append('description')
        if not category:
            error = "Category is required."
            invalid_fields.append('category')
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than zero.")
        except ValueError:
            error = "Invalid. Please make sure to fill out every field correctly."
            invalid_fields.append('amount')

        if error:
            return render_template(
                'add_expenses.html', error=error, invalid_fields=invalid_fields
            )
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO expenses (category, description, amount) VALUES (?, ?, ?)',
            (category, description, amount)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('add_expenses.html', invalid_fields=[])

# Route: View All Expenses and Total
@app.route('/view')
def view_expenses():
    """View all expenses and their total."""
    conn = get_db_connection()
    expenses = conn.execute('SELECT * FROM expenses').fetchall()
    total = conn.execute('SELECT SUM(amount) AS total FROM expenses').fetchone()['total'] or 0
    total_expenses = conn.execute('SELECT COUNT(*) AS count FROM expenses').fetchone()['count']
    conn.close()
    return render_template('view_expenses.html', expenses=expenses, total=total, total_expenses=total_expenses)

# Route: View a Specific Expense
@app.route('/expense/<int:expense_id>')
def expense_info(expense_id):
    """View a specific expense by its ID."""
    conn = get_db_connection()
    expense = conn.execute('SELECT * FROM expenses WHERE id = ?', (expense_id,)).fetchone()
    conn.close()
    
    if expense is None:
        return redirect(url_for('index'))  # Redirect to the home page if the expense is not found

    return render_template('expense_info.html', expense=expense)



# Route: Delete Expenses
@app.route('/delete/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    conn = get_db_connection()
    
    conn.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('view_expenses'))

# Route: Search Expenses
@app.route('/search', methods=('GET', 'POST'))
def search_expense():
    expenses = []
    search_made = False

    if request.method == 'POST':
        keyword = request.form.get('keyword', '').strip()  # Corrected line
        if keyword:
            conn = get_db_connection()
            query = "SELECT * FROM expenses WHERE description LIKE ? OR category LIKE ?"
            expenses = conn.execute(query, (f'%{keyword}%', f'%{keyword}%')).fetchall()
            conn.close()
            search_made = True

    return render_template('search.html', expenses=expenses, search_made=search_made)


# Route: Export Expenses
@app.route('/export')
def export_expense():
    """Export all tasks to a text file."""
    conn = get_db_connection()

    conn.execute('DELETE FROM sqlite_sequence WHERE name="expenses"')
    conn.commit()

    expenses = conn.execute('SELECT * FROM expenses').fetchall()
    conn.close()

    with open('expenses.txt', 'w', encoding='utf-8') as file:
        for expense in expenses:
            formatted_amount = f"₱{expense['amount']:.2f}"
            file.write(f"{expense['id']}. {expense['description']} ({expense['category']}) - {formatted_amount}\n")
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5001)


