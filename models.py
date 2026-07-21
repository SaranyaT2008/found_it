from datetime import datetime
from flask_login import UserMixin
from extensions import db


class User(UserMixin, db.Model):
    """Represents a registered user."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=True)

    items = db.relationship(
        'Item',
        back_populates='author',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )

    def __repr__(self) -> str:
        return f'<User {self.email}>'


class Item(db.Model):
    """Represents a lost or found report."""
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(100), nullable=False, index=True)
    image_filename = db.Column(db.String(200), nullable=True)
    image_hash = db.Column(db.String(64), nullable=True, index=True)
    type = db.Column(db.String(10), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='open', index=True)
    matched_with_id = db.Column(db.Integer, db.ForeignKey('items.id', ondelete='SET NULL'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    author = db.relationship('User', back_populates='items')
    matched_item = db.relationship('Item', remote_side=[id], post_update=True)

    def __repr__(self) -> str:
        return f'<Item {self.title} ({self.type})>'

