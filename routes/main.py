from flask import Blueprint, render_template, current_app
from models import Item

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    recent_lost = (
        Item.query
        .filter(Item.type == 'lost', Item.status != 'resolved')
        .order_by(Item.created_at.desc())
        .limit(4)
        .all()
    )
    recent_found = (
        Item.query
        .filter(Item.type == 'found', Item.status != 'resolved')
        .order_by(Item.created_at.desc())
        .limit(4)
        .all()
    )
    return render_template('index.html', recent_lost=recent_lost, recent_found=recent_found)


@main_bp.route('/health')
def health():
    database_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    display_db = database_uri.split('@')[-1] if '@' in database_uri else database_uri
    return {
        'status': 'alive',
        'database': display_db,
        'debug': current_app.config.get('DEBUG', False)
    }
