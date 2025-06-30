from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import re

db = SQLAlchemy()

class Blog(db.Model):
    __tablename__ = 'blogs'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, title, category, content):
        self.title = title
        self.slug = self.slugify(title)
        self.category = category
        self.content = content

    def update(self, title, category, content):
        self.title = title
        self.slug = self.slugify(title)
        self.category = category
        self.content = content

    def to_dict(self, full=False):
        base = {
            "id": self.id,
            "title": self.title,
            "slug": self.slug,
            "category": self.category,
            "date_created": self.date_created.isoformat()
        }
        if full:
            base["content"] = self.content
        return base

    @staticmethod
    def slugify(title):
        return re.sub(r'\W+', '-', title.lower()).strip('-')
