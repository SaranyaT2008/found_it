import re
import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from extensions import db, limiter

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit('10 per hour')
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.register'))

        if len(name) > 100 or len(password) < 8:
            flash('Name must be under 100 characters and password at least 8 characters.', 'danger')
            return redirect(url_for('auth.register'))

        if not re.match(r'^[A-Za-z0-9._%+-]+@kpriet\.ac\.in$', email):
            flash('Please use your official @kpriet.ac.in email.', 'danger')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'warning')
            return redirect(url_for('auth.register'))

        user = User(name=name, email=email, password_hash=generate_password_hash(password, method='pbkdf2:sha256'))
        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            logger.info('New user registered: %s', email)
            return redirect(url_for('dashboard.index'))
        except Exception as exc:
            logger.exception('Failed to register user: %s', email)
            db.session.rollback()
            flash('An unexpected error occurred. Please try again.', 'danger')
            return redirect(url_for('auth.register'))

    return render_template('auth.html', is_login=False)


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit('20 per hour')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            logger.info('User logged in: %s', email)
            return redirect(url_for('dashboard.index'))

        flash('Invalid email or password.', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('auth.html', is_login=True)


@auth_bp.route('/logout')
@login_required
def logout():
    email = current_user.email
    logout_user()
    logger.info('User logged out: %s', email)
    return redirect(url_for('main.index'))
