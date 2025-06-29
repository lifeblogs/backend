from flask import Flask, request, jsonify, session
from flask_cors import CORS
from models import db, Blog, slugify
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")
CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173",  # Vite dev
    "https://lifeblogs.onrender.com"
])

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blogs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

ADMIN_PASSCODE = os.getenv("ADMIN_PASSCODE", "1234")

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/api/blogs')
def get_blogs():
    category = request.args.get('category')
    blogs = Blog.query.filter_by(category=category).all() if category else Blog.query.all()
    return jsonify([
        {
            "id": blog.id,
            "title": blog.title,
            "slug": blog.slug,
            "category": blog.category,
            "date_created": blog.date_created.isoformat()
        }
        for blog in blogs
    ])

@app.route('/api/blogs/<slug>')
def get_blog(slug):
    blog = Blog.query.filter_by(slug=slug).first_or_404()
    return jsonify({
        "title": blog.title,
        "slug": blog.slug,
        "category": blog.category,
        "content": blog.content,
        "date_created": blog.date_created.isoformat()
    })

@app.route('/api/blogs', methods=['POST'])
def create_blog():
    if not session.get('admin'):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    title = data['title']
    slug = slugify(title)
    blog = Blog(title=title, slug=slug, category=data['category'], content=data['content'])
    db.session.add(blog)
    db.session.commit()
    return jsonify({"message": "Blog created", "slug": slug})

@app.route('/api/blogs/<int:blog_id>', methods=['PUT'])
def update_blog(blog_id):
    if not session.get('admin'):
        return jsonify({"error": "Unauthorized"}), 401
    blog = Blog.query.get_or_404(blog_id)
    data = request.json
    blog.title = data['title']
    blog.category = data['category']
    blog.content = data['content']
    blog.slug = slugify(blog.title)
    db.session.commit()
    return jsonify({"message": "Blog updated"})

@app.route('/api/blogs/<int:blog_id>', methods=['DELETE'])
def delete_blog(blog_id):
    if not session.get('admin'):
        return jsonify({"error": "Unauthorized"}), 401
    blog = Blog.query.get_or_404(blog_id)
    db.session.delete(blog)
    db.session.commit()
    return jsonify({"message": "Blog deleted"})

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    if data.get('passcode') == ADMIN_PASSCODE:
        session['admin'] = True
        return jsonify({"message": "Logged in"})
    return jsonify({"error": "Invalid passcode"}), 401

@app.route('/api/admin/protected')
def protected():
    if session.get('admin'):
        return jsonify({"message": "Authorized"})
    return jsonify({"error": "Unauthorized"}), 401

@app.route('/api/admin/logout')
def logout():
    session.pop('admin', None)
    return jsonify({"message": "Logged out"})

if __name__ == '__main__':
    app.run(debug=True)
