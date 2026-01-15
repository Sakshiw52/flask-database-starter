"""
Part 2: Full CRUD Operations with HTML Forms
=============================================
Complete Create, Read, Update, Delete operations with user forms.

What You'll Learn:
- HTML forms with POST method
- request.form to get form data
- UPDATE and DELETE SQL commands
- redirect() and url_for() functions
- Flash messages for user feedback

Prerequisites: Complete part-1 first
"""

from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for flash messages

DATABASE = 'students.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            course TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# =============================================================================
# CREATE - Add new student
# =============================================================================

@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        course = request.form['course']

        conn = get_db_connection()

        # CHECK IF EMAIL ALREADY EXISTS
        existing = conn.execute(
            'SELECT * FROM students WHERE email = ?',
            (email,)
        ).fetchone()

        if existing:
            conn.close()
            flash('Email already exists! Use a different email.', 'danger')
            return redirect(url_for('add_student'))

        # INSERT IF EMAIL IS UNIQUE
        conn.execute(
            'INSERT INTO students (name, email, course) VALUES (?, ?, ?)',
            (name, email, course)
        )
        conn.commit()
        conn.close()

        flash('Student added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add.html')


# READ - Display all students
@app.route('/')
def index():
    conn = get_db_connection()
    students = conn.execute(
        'SELECT * FROM students ORDER BY id DESC'
    ).fetchall()
    conn.close()
    return render_template('index.html', students=students)


# ===============================
# SEARCH - Find student by name
# ===============================
@app.route('/search', methods=['GET'])
def search_student():
    query = request.args.get('q')

    conn = get_db_connection()
    students = conn.execute(
        "SELECT * FROM students WHERE name LIKE ?",
        ('%' + query + '%',)
    ).fetchall()
    conn.close()

    return render_template('index.html', students=students)


# =============================================================================
# UPDATE - Edit existing student
# =============================================================================

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_student(id):
    conn = get_db_connection()

    if request.method == 'POST':  # Form submitted with new data
        name = request.form['name']
        email = request.form['email']
        course = request.form['course']

        conn.execute(
            'UPDATE students SET name = ?, email = ?, course = ? WHERE id = ?',
            (name, email, course, id)  # Update WHERE id matches
        )
        conn.commit()
        conn.close()

        flash('Student updated successfully!', 'success')
        return redirect(url_for('index'))

    # GET request: fetch current data and show in form
    student = conn.execute('SELECT * FROM students WHERE id = ?', (id,)).fetchone()
    conn.close()
    return render_template('edit.html', student=student)


# =============================================================================
# DELETE - Remove student
# =============================================================================

@app.route('/delete/<int:id>')
def delete_student(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM students WHERE id = ?', (id,))  # Remove row
    conn.commit()
    conn.close()

    flash('Student deleted!', 'danger')  # Show delete message
    return redirect(url_for('index'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)


# =============================================================================
# CRUD SUMMARY:
# =============================================================================
#
# Operation | HTTP Method | SQL Command | Route Example
# ----------|-------------|-------------|---------------
# Create    | POST        | INSERT INTO | /add
# Read      | GET         | SELECT      | / or /student/1
# Update    | POST        | UPDATE      | /edit/1
# Delete    | GET/POST    | DELETE      | /delete/1
#
# =============================================================================
# NEW CONCEPTS:
# =============================================================================
#
# 1. methods=['GET', 'POST']
#    - GET: Display the form (empty or with current data)
#    - POST: Process the submitted form
#
# 2. request.form['field_name']
#    - Gets the value from HTML form input with that name
#
# 3. redirect(url_for('function_name'))
#    - Sends user to another page after action completes
#
# 4. flash('message', 'category')
#    - Shows one-time message to user
#    - Categories: 'success', 'danger', 'warning', 'info'
#
# =============================================================================


# =============================================================================
# EXERCISE:
# =============================================================================
#
# 1. Add a "Search" feature to find students by name
# 2. Add validation to check if email already exists before adding
#
# =============================================================================
