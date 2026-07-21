import logging
from flask import Blueprint, redirect, url_for, session, request, flash
from extensions import oauth, db
from models import User
from flask_login import login_user

logger = logging.getLogger(__name__)

oauth_bp = Blueprint('oauth', __name__, url_prefix='')


@oauth_bp.route('/login/google')
def google_login():
    redirect_uri = url_for('oauth.google_authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@oauth_bp.route('/authorize/google')
def google_authorize():
    try:
        token = oauth.google.authorize_access_token()
        user_info = oauth.google.parse_id_token(token)
        email = user_info.get('email')
        name = user_info.get('name', '')

        if not email or not email.endswith('@kpriet.ac.in'):
            flash('Google account must be a @kpriet.ac.in email.', 'danger')
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(name=name or email.split('@')[0], email=email, password_hash=None)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        logger.info('Google OAuth login succeeded for %s', email)
        return redirect(url_for('dashboard.index'))
    except Exception:
        logger.exception('Google OAuth failed.')
        flash('Google login failed. Please try again.', 'danger')
        return redirect(url_for('auth.login'))
