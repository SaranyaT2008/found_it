import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_
from models import Item
from extensions import db, limiter
from services.upload_service import save_image_file
from services.matching_service import match_new_item
from services.validators import validate_item_payload, VALID_CATEGORIES, VALID_LOCATIONS

logger = logging.getLogger(__name__)

item_bp = Blueprint('items', __name__, url_prefix='')


@item_bp.route('/report/<item_type>', methods=['GET', 'POST'])
@login_required
@limiter.limit('30 per hour')
def report_item(item_type):
    if item_type not in ['lost', 'found']:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        payload = {
            'title': request.form.get('title', ''),
            'category': request.form.get('category', ''),
            'description': request.form.get('description', ''),
            'date': request.form.get('date', ''),
            'location': request.form.get('location', '')
        }

        error = validate_item_payload(payload)
        if error:
            flash(error, 'danger')
            return redirect(url_for('items.report_item', item_type=item_type))

        image_file = request.files.get('image')
        filename, image_hash = save_image_file(image_file, current_app.config)

        new_item = Item(
            title=payload['title'],
            category=payload['category'],
            description=payload['description'],
            date=payload['date'],
            location=payload['location'],
            image_filename=filename,
            image_hash=image_hash,
            type=item_type,
            user_id=current_user.id,
            status='open'
        )

        try:
            db.session.add(new_item)
            db.session.commit()
            matched = match_new_item(new_item, current_app.config)
            if matched:
                flash('A matching item has been found and linked to your report.', 'success')
            else:
                flash('Report submitted successfully!', 'success')
            logger.info('New report created: %s by %s', new_item.title, current_user.email)
            return redirect(url_for('items.list_items', type=item_type))
        except Exception:
            db.session.rollback()
            logger.exception('Failed to save report: %s', payload['title'])
            flash('Unable to submit report at this time. Please try again later.', 'danger')
            return redirect(url_for('items.report_item', item_type=item_type))

    return render_template('report.html', item_type=item_type)


@item_bp.route('/items')
def list_items():
    q_type = request.args.get('type')
    q_search = request.args.get('search', '').strip()
    q_category = request.args.get('category')
    q_location = request.args.get('location')
    page = request.args.get('page', 1, type=int)

    query = Item.query.filter(Item.status != 'resolved')

    if q_type in ['lost', 'found']:
        query = query.filter_by(type=q_type)

    if q_search:
        query = query.filter(or_(Item.title.ilike(f'%{q_search}%'), Item.description.ilike(f'%{q_search}%')))

    if q_category:
        query = query.filter_by(category=q_category)

    if q_location:
        query = query.filter_by(location=q_location)

    pagination = query.order_by(Item.created_at.desc()).paginate(
        page=page,
        per_page=current_app.config.get('ITEMS_PER_PAGE', 8),
        error_out=False
    )

    pagination_args = {key: value for key, value in request.args.items() if key != 'page'}

    return render_template(
        'items.html',
        items=pagination.items,
        list_type=q_type,
        pagination=pagination,
        pagination_args=pagination_args,
        categories=sorted(VALID_CATEGORIES),
        locations=sorted(VALID_LOCATIONS)
    )


@item_bp.route('/item/<int:item_id>')
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    return render_template('item_detail.html', item=item)


@item_bp.route('/item/delete/<int:item_id>')
@login_required
@limiter.limit('20 per hour')
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('You do not have permission to delete this item.', 'danger')
        return redirect(url_for('dashboard.index'))

    try:
        db.session.delete(item)
        db.session.commit()
        logger.info('Item deleted: %s by %s', item.title, current_user.email)
        flash('Item deleted successfully.', 'success')
    except Exception:
        db.session.rollback()
        logger.exception('Failed to delete item: %s', item.title)
        flash('Unable to delete the item. Please try again.', 'danger')

    return redirect(url_for('dashboard.index'))


@item_bp.route('/item/resolve/<int:item_id>')
@login_required
@limiter.limit('20 per hour')
def resolve_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        flash('You do not have permission to modify this item.', 'danger')
        return redirect(url_for('dashboard.index'))

    try:
        item.status = 'resolved'
        db.session.commit()
        logger.info('Item resolved: %s by %s', item.title, current_user.email)
        flash(f'Item "{item.title}" marked as resolved!', 'success')
    except Exception:
        db.session.rollback()
        logger.exception('Failed to resolve item: %s', item.title)
        flash('Unable to update item status. Please try again.', 'danger')

    return redirect(url_for('dashboard.index'))
