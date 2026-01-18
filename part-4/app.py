"""
Part 4: REST API with Flask
===========================
Build a JSON API for database operations
"""
from flask import Flask, request, jsonify, render_template
from models import db, Author, Book
from datetime import datetime
import os

app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'api_demo.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# =============================================================================
# REST API ROUTES FOR BOOKS
# =============================================================================

@app.route('/api/books', methods=['GET'])
def get_books():
    query = Book.query

    # Sorting
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


@app.route('/api/books/<int:id>', methods=['GET'])
def get_book(id):
    book = Book.query.get(id)
    if not book:
        return jsonify({'success': False, 'error': 'Book not found'}), 404
    return jsonify({'success': True, 'book': book.to_dict()})


@app.route('/api/books', methods=['POST'])
def create_book():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    if not data.get('title') or not data.get('author'):
        return jsonify({'success': False, 'error': 'Title and author are required'}), 400

    # Check for duplicate ISBN
    if data.get('isbn'):
        existing = Book.query.filter_by(isbn=data['isbn']).first()
        if existing:
            return jsonify({'success': False, 'error': 'ISBN already exists'}), 400

    # Check if author exists when author_id is provided
    author_id = data.get('author_id')
    if author_id:
        author = Author.query.get(author_id)
        if not author:
            return jsonify({'success': False, 'error': 'Author not found'}), 400

    # Create book
    new_book = Book(
        title=data['title'],
        author=data['author'],
        year=data.get('year'),
        isbn=data.get('isbn'),
        author_id=author_id
    )

    db.session.add(new_book)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Book created successfully',
        'book': new_book.to_dict()
    }), 201


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
    if 'author_id' in data:
        # Verify author exists
        author = Author.query.get(data['author_id'])
        if not author and data['author_id'] is not None:
            return jsonify({'success': False, 'error': 'Author not found'}), 400
        book.author_id = data['author_id']

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Book updated successfully',
        'book': book.to_dict()
    })


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
# REST API ROUTES FOR AUTHORS
# =============================================================================

@app.route('/api/authors', methods=['GET'])
def get_authors():
    query = Author.query

    # Sorting
    sort = request.args.get('sort', 'id')
    order = request.args.get('order', 'asc')
    allowed_sort = {'id', 'name', 'city', 'created_at'}
    if sort not in allowed_sort:
        sort = 'id'

    sort_col = getattr(Author, sort)
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
        'authors': [author.to_dict() for author in items]
    })


@app.route('/api/authors/<int:id>', methods=['GET'])
def get_author(id):
    author = Author.query.get(id)
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404

    return jsonify({
        'success': True,
        'author': author.to_dict(),
        'books': [book.to_dict() for book in author.books] if author.books else []
    })


@app.route('/api/authors', methods=['POST'])
def create_author():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    if not data.get('name'):
        return jsonify({'success': False, 'error': 'Name is required'}), 400

    # Create author
    new_author = Author(
        name=data['name'],
        bio=data.get('bio'),
        city=data.get('city')
    )

    db.session.add(new_author)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Author created successfully',
        'author': new_author.to_dict()
    }), 201


@app.route('/api/authors/<int:id>', methods=['PUT'])
def update_author(id):
    author = Author.query.get(id)
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    # Update fields if provided
    if 'name' in data:
        author.name = data['name']
    if 'bio' in data:
        author.bio = data['bio']
    if 'city' in data:
        author.city = data['city']

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Author updated successfully',
        'author': author.to_dict()
    })


@app.route('/api/authors/<int:id>', methods=['DELETE'])
def delete_author(id):
    author = Author.query.get(id)
    if not author:
        return jsonify({'success': False, 'error': 'Author not found'}), 404

    db.session.delete(author)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Author deleted successfully'
    })


# =============================================================================
# SEARCH ENDPOINTS
# =============================================================================

@app.route('/api/books/search', methods=['GET'])
def search_books():
    query = Book.query

    title = request.args.get('q')
    if title:
        query = query.filter(Book.title.ilike(f'%{title}%'))

    author = request.args.get('author')
    if author:
        query = query.filter(Book.author.ilike(f'%{author}%'))

    year = request.args.get('year')
    if year:
        query = query.filter_by(year=int(year))

    author_id = request.args.get('author_id')
    if author_id:
        query = query.filter_by(author_id=int(author_id))

    books = query.all()

    return jsonify({
        'success': True,
        'count': len(books),
        'books': [book.to_dict() for book in books]
    })


@app.route('/api/authors/search', methods=['GET'])
def search_authors():
    query = Author.query

    name = request.args.get('name')
    if name:
        query = query.filter(Author.name.ilike(f'%{name}%'))

    city = request.args.get('city')
    if city:
        query = query.filter(Author.city.ilike(f'%{city}%'))

    authors = query.all()

    return jsonify({
        'success': True,
        'count': len(authors),
        'authors': [author.to_dict() for author in authors]
    })


# =============================================================================
# MAIN ROUTE
# =============================================================================

@app.route('/')
def index():
    return render_template('index.html')


# =============================================================================
# DATABASE INITIALIZATION - UPDATED TO FIX ERROR
# =============================================================================

def init_db():
    with app.app_context():
        # Drop all tables to fix schema issues
        db.drop_all()
        # Create fresh tables with current schema
        db.create_all()

        # Create sample authors
        sample_authors = [
            Author(name='Eric Matthes', city='Portland', bio='Author of Python Crash Course'),
            Author(name='Miguel Grinberg', city='Portland', bio='Flask expert and author'),
            Author(name='Robert C. Martin', city='New York', bio='Clean Code author and software engineer'),
        ]
        db.session.add_all(sample_authors)
        db.session.commit()
        print('Sample authors added!')

        # Create sample books
        authors = Author.query.all()
        
        sample_books = [
            Book(title='Python Crash Course', author='Eric Matthes', year=2019, 
                 isbn='978-1593279288', author_id=authors[0].id),
            Book(title='Flask Web Development', author='Miguel Grinberg', year=2018, 
                 isbn='978-1491991732', author_id=authors[1].id),
            Book(title='Clean Code', author='Robert C. Martin', year=2008, 
                 isbn='978-0132350884', author_id=authors[2].id),
        ]
        db.session.add_all(sample_books)
        db.session.commit()
        print('Sample books added!')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)