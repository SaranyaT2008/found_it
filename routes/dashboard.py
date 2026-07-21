import logging
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Item

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='')


@dashboard_bp.route('/dashboard')
@login_required
def index():
    user_items = Item.query.filter_by(user_id=current_user.id).order_by(Item.created_at.desc()).all()
    stats = {
        'total': len(user_items),
        'lost': len([item for item in user_items if item.type == 'lost']),
        'found': len([item for item in user_items if item.type == 'found']),
        'resolved': len([item for item in user_items if item.status == 'resolved']),
        'matched': len([item for item in user_items if item.status == 'matched'])
    }

    logger.debug('Dashboard loaded for user: %s', current_user.email)
    return render_template('dashboard.html', items=user_items, stats=stats)
