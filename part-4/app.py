"""
Part 4: REST API with Flask
===========================
Build a JSON API for database operations (used by frontend apps, mobile apps, etc.)

What You'll Learn:
- REST API concepts (GET, POST, PUT, DELETE)
- JSON responses with jsonify
- API error handling
- Status codes
- Testing APIs with curl or Postman

Prerequisites: Complete part-3 (SQLAlchemy)
"""

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///api_demo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# =============================================================================
# MODELS
# =============================================================================

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer)
    isbn = db.Column(db.String(20), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):  # Convert model to dictionary for JSON response
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'year': self.year,
            'isbn': self.isbn,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# =============================================================================
# REST API ROUTES
# =============================================================================

# GET /api/books - Get books with optional pagination and sorting
@app.route('/api/books', methods=['GET'])
def get_books():
    query = Book.query

    # Sorting (prevent arbitrary attribute access by limiting allowed fields)
    sort = request.args.get('sort', 'id')
    order = request.args.get('order', 'asc')
    allowed_sort = {'id', 'title', 'author', 'year', 'isbn', 'created_at'}
    if sort not in allowed_sort:
        sort = 'id'

    sort_col = getattr(Book, sort)
    if order == 'desc':
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    if page < 1:
        page = 1
    if per_page < 1:
        per_page = 10

    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page if per_page else 0

    return jsonify({
        'success': True,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages,
        'total_items': total,
        'books': [book.to_dict() for book in items]
    })


# GET /api/books/<id> - Get single book
@app.route('/api/books/<int:id>', methods=['GET'])
def get_book(id):
    book = Book.query.get(id)

    if not book:
        return jsonify({
            'success': False,
            'error': 'Book not found'
        }), 404  # Return 404 status code

    return jsonify({
        'success': True,
        'book': book.to_dict()
    })


# POST /api/books - Create new book
@app.route('/api/books', methods=['POST'])
def create_book():
    data = request.get_json()  # Get JSON data from request body

    # Validation
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    if not data.get('title') or not data.get('author'):
        return jsonify({'success': False, 'error': 'Title and author are required'}), 400

    # Check for duplicate ISBN
    if data.get('isbn'):
        existing = Book.query.filter_by(isbn=data['isbn']).first()
        if existing:
            return jsonify({'success': False, 'error': 'ISBN already exists'}), 400

    # Create book
    new_book = Book(
        title=data['title'],
        author=data['author'],
        year=data.get('year'),  # Optional field
        isbn=data.get('isbn')
    )

    db.session.add(new_book)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Book created successfully',
        'book': new_book.to_dict()
    }), 201  # 201 = Created


# PUT /api/books/<id> - Update book
@app.route('/api/books/<int:id>', methods=['PUT'])
def update_book(id):
    book = Book.query.get(id)

    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404

    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    # Update fields if provided
    if 'title' in data:
        book.title = data['title']
    if 'author' in data:
        book.author = data['author']
    if 'year' in data:
        book.year = data['year']
    if 'isbn' in data:
        book.isbn = data['isbn']

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Book updated successfully',
        'book': book.to_dict()
    })


# DELETE /api/books/<id> - Delete book
@app.route('/api/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    book = Book.query.get(id)

    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404

    db.session.delete(book)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Book deleted successfully'
    })


# =============================================================================
# BONUS: Search and Filter
# =============================================================================

# GET /api/books/search?q=python&author=john
@app.route('/api/books/search', methods=['GET'])
def search_books():
    query = Book.query

    # Filter by title (partial match)
    title = request.args.get('q')  # Query parameter: ?q=python
    if title:
        query = query.filter(Book.title.ilike(f'%{title}%'))  # Case-insensitive LIKE

    # Filter by author
    author = request.args.get('author')
    if author:
        query = query.filter(Book.author.ilike(f'%{author}%'))

    # Filter by year
    year = request.args.get('year')
    if year:
        query = query.filter_by(year=int(year))

    books = query.all()

    return jsonify({
        'success': True,
        'count': len(books),
        'books': [book.to_dict() for book in books]
    })


# =============================================================================
# SIMPLE WEB PAGE FOR TESTING
# =============================================================================

@app.route('/')
def index():
    return '''
    <html>
    <head>
        <title>Part 4 - REST API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a2e; color: #eee; }
            h1 { color: #e94560; }
            .endpoint { background: #16213e; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #e94560; }
            .method { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; margin-right: 10px; }
            .get { background: #27ae60; }
            .post { background: #f39c12; }
            .put { background: #3498db; }
            .delete { background: #e74c3c; }
            code { background: #0f3460; padding: 2px 6px; border-radius: 3px; }
            pre { background: #0f3460; padding: 15px; border-radius: 8px; overflow-x: auto; }
            a { color: #e94560; }
            .control { background: #0f3460; padding: 12px; border-radius: 6px; margin-bottom: 12px; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th, td { padding: 8px; text-align: left; border-bottom: 1px solid #233044; }
        </style>
    </head>
    <body>
        <h1>Part 4: REST API Demo</h1>
        <p>This is a JSON API - use curl, Postman, or the built-in JavaScript frontend below to test!</p>

        <h2>API Endpoints:</h2>

        <div class="endpoint">
            <span class="method get">GET</span>
            <code>/api/books</code> - Get all books (supports <code>page</code>, <code>per_page</code>, <code>sort</code>, <code>order</code>)
            <br><a href="/api/books" target="_blank">Try it →</a>
        </div>

        <!-- simple frontend demo -->
        <h2>Frontend Demo (fetch)</h2>
        <div class="control">
            <label>Page: <input id="page" type="number" value="1" min="1" style="width:70px"></label>
            <label>Per page: <input id="per_page" type="number" value="5" min="1" style="width:70px"></label>
            <label>Sort: 
                <select id="sort">
                    <option value="id">id</option>
                    <option value="title">title</option>
                    <option value="author">author</option>
                    <option value="year">year</option>
                    <option value="created_at">created_at</option>
                </select>
            </label>
            <label>Order: 
                <select id="order">
                    <option value="asc">asc</option>
                    <option value="desc">desc</option>
                </select>
            </label>
            <button onclick="fetchBooks()">Fetch</button>
        </div>

        <div id="results">
            <p>Click <strong>Fetch</strong> to load books.</p>
        </div>

        <script>
            async function fetchBooks() {
                const page = document.getElementById('page').value;
                const per_page = document.getElementById('per_page').value;
                const sort = document.getElementById('sort').value;
                const order = document.getElementById('order').value;
                const url = `/api/books?page=${page}&per_page=${per_page}&sort=${sort}&order=${order}`;

                const res = await fetch(url);
                const data = await res.json();
                const container = document.getElementById('results');

                if (!data.success) {
                    container.innerHTML = `<p style="color: #ff8080">Error loading books</p>`;
                    return;
                }

                let html = `<p>Showing page ${data.page} of ${data.total_pages} (total ${data.total_items} books)</p>`;
                html += `<table><thead><tr><th>ID</th><th>Title</th><th>Author</th><th>Year</th><th>ISBN</th></tr></thead><tbody>`;
                for (const b of data.books) {
                    html += `<tr><td>${b.id}</td><td>${b.title}</td><td>${b.author}</td><td>${b.year || ''}</td><td>${b.isbn || ''}</td></tr>`;
                }
                html += `</tbody></table>`;
                html += `<div style="margin-top:8px;"><button onclick="prev()">Prev</button> <button onclick="next()">Next</button></div>`;

                container.innerHTML = html;
            }

            function prev() {
                const p = document.getElementById('page');
                let v = parseInt(p.value, 10);
                if (v > 1) { p.value = v - 1; fetchBooks(); }
            }
            function next() {
                const p = document.getElementById('page');
                p.value = parseInt(p.value, 10) + 1;
                fetchBooks();
            }

            // initial load
            fetchBooks();
        </script>

        <h2>Test with curl:</h2>
        <pre>
# Get all books (with pagination & sorting)
curl "http://localhost:5000/api/books?page=1&per_page=5&sort=title&order=asc"

    '''

# =============================================================================
# INITIALIZE DATABASE WITH SAMPLE DATA
# =============================================================================

def init_db():
    with app.app_context():
        db.create_all()

        if Book.query.count() == 0:
            sample_books = [
                Book(title='Python Crash Course', author='Eric Matthes', year=2019, isbn='978-1593279288'),
                Book(title='Flask Web Development', author='Miguel Grinberg', year=2018, isbn='978-1491991732'),
                Book(title='Clean Code', author='Robert C. Martin', year=2008, isbn='978-0132350884'),
            ]
            db.session.add_all(sample_books)
            db.session.commit()
            print('Sample books added!')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)


# =============================================================================
# REST API CONCEPTS:
# =============================================================================
#
# HTTP Method | CRUD      | Typical Use
# ------------|-----------|---------------------------
# GET         | Read      | Retrieve data
# POST        | Create    | Create new resource
# PUT         | Update    | Update entire resource
# PATCH       | Update    | Update partial resource
# DELETE      | Delete    | Remove resource
#
# =============================================================================
# HTTP STATUS CODES:
# =============================================================================
#
# Code | Meaning
# -----|------------------
# 200  | OK (Success)
# 201  | Created
# 400  | Bad Request (client error)
# 404  | Not Found
# 500  | Internal Server Error
#
# =============================================================================
# KEY FUNCTIONS:
# =============================================================================
#
# jsonify()           - Convert Python dict to JSON response
# request.get_json()  - Get JSON data from request body
# request.args.get()  - Get query parameters (?key=value)
#
# =============================================================================


# =============================================================================
# EXERCISE:
# =============================================================================
#
# 1. Add pagination: `/api/books?page=1&per_page=10`
# 2. Add sorting: `/api/books?sort=title&order=desc`
# 3. Create a simple frontend using JavaScript fetch()
#
# =============================================================================
