from datetime import datetime

VALID_CATEGORIES = {
    'Electronics',
    'Books & Documents',
    'Accessories & Wearables',
    'Keys & Wallets',
    'Clothing',
    'Stationery',
    'Other'
}

VALID_LOCATIONS = {
    'Administrative and AI & DS Block',
    'Imperial Hall, T & P, CoE & Exam Cell',
    'R & D',
    'Mechanical Block',
    'Civil & EEE Block',
    'KPRCAS 1 & 2',
    'Engineering Workshop',
    'Central Library',
    'Food Court',
    'Cafeteria Dining',
    'Open Theatre / Kalaiarangam',
    'Garden Cafe',
    'Girls Hostel (Ganga, Yamuna, Kaveri)',
    'Boys Hostel (Bharathi, Cheran, Cholan, Pandian, Pallavan)',
    'Bike/Car Parking',
    'Security Gate',
    'Sports Facility - Courts',
    'Ground Area / Track',
    'Multi Purpose Hall & Gym',
    'Other / Not Sure'
}


def validate_item_payload(payload: dict) -> str | None:
    if not payload['title'].strip():
        return 'The item name is required.'

    if len(payload['title']) > 100:
        return 'The item name must be under 100 characters.'

    if payload['category'] not in VALID_CATEGORIES:
        return 'Please select a valid category.'

    if not payload['description'].strip() or len(payload['description']) > 1200:
        return 'Please provide a valid description under 1200 characters.'

    if not payload['location'] or payload['location'] not in VALID_LOCATIONS:
        return 'Please select a valid location from the list.'

    try:
        date_obj = datetime.strptime(payload['date'], '%Y-%m-%d').date()
        payload['date'] = date_obj
    except (ValueError, TypeError):
        return 'Please provide a valid date.'

    return None
