from flask import Flask, render_template, redirect, url_for, request
import sqlite3

app = Flask(__name__)

DATABASE = 'courses.db'


# =============================================================================
# DATABASE HELPER FUNCTIONS
# =============================================================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            instructor TEXT NOT NULL,
            duration TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


# =============================================================================
# ROUTES
# =============================================================================

@app.route('/')
def index():
    conn = get_db_connection()
    courses = conn.execute('SELECT * FROM courses').fetchall()
    conn.close()
    return render_template('index.html', courses=courses)


@app.route('/add', methods=['GET', 'POST'])
def add_course():
    if request.method == 'POST':
        title = request.form['title']
        instructor = request.form['instructor']
        duration = request.form['duration']
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO courses (title, instructor, duration) VALUES (?, ?, ?)',
            (title, instructor, duration)
        )
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('add.html')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
