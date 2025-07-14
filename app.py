from flask import Flask, request, jsonify, session
from flask_cors import CORS
from models import db, Blog
from dotenv import load_dotenv
from sqlalchemy import desc
import os

load_dotenv()

app = Flask(__name__)

app.secret_key = os.getenv("SECRET_KEY", "dev_secret")
app.config.update(
    SESSION_COOKIE_SAMESITE=os.getenv("COOKIES"),
    SESSION_COOKIE_SECURE=True,
    SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173",
    "https://lifebulogs.onrender.com"
])

db.init_app(app)

with app.app_context():
    db.create_all()


@app.route('/api/blogs', methods=['GET'])
def get_blogs():
    category = request.args.get('category')
    blogs = Blog.query.filter_by(category=category).all() if category else Blog.query.all()
    return jsonify([blog.to_dict(full=True) for blog in blogs])


@app.route('/api/blogs/<slug>', methods=['GET'])
def get_blog(slug):
    blog = Blog.query.filter_by(slug=slug).first_or_404()
    return jsonify(blog.to_dict(full=True))


@app.route('/api/blogs', methods=['POST'])
def create_blog():
    if not session.get('admin'):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    blog = Blog(title=data['title'], category=data['category'], content=data['content'])
    db.session.add(blog)
    db.session.commit()
    return jsonify({"message": "Blog created", "slug": blog.slug})


@app.route('/api/blogs/<int:blog_id>', methods=['PUT'])
def update_blog(blog_id):
    if not session.get('admin'):
        return jsonify({"error": "Unauthorized"}), 401

    blog = Blog.query.get_or_404(blog_id)
    data = request.json
    blog.update(title=data['title'], category=data['category'], content=data['content'])
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

@app.route('/api/blogs/thisweek', methods=['GET'])
def latest_blogs_by_category():
    categories = db.session.query(Blog.category).distinct()
    result = []

    for category_obj in categories:
        category = category_obj.category
        latest_blog = Blog.query.filter_by(category=category).order_by(desc(Blog.date_created)).first()
        if latest_blog:
            result.append({
                "category": category,
                "title": latest_blog.title,
                "slug": latest_blog.slug,
                "link": f"/blogs/{latest_blog.slug}",
                "content": latest_blog.content
            })

    return jsonify(result)



@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    if data.get('passcode') == os.getenv("ADMIN_PASSCODE"):
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
