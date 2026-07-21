import os
import logging
from datetime import datetime
from PIL import Image
import imagehash
import cv2
import numpy as np
from models import Item
from extensions import db
from services.email_service import send_match_notification

logger = logging.getLogger(__name__)

HASH_THRESHOLD = 20
FEATURE_THRESHOLD = 6


def _resize_gray_image(img_path: str, max_dim: int = 800):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None

    h, w = img.shape
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        return cv2.resize(img, (int(w * scale), int(h * scale)))
    return img


def calculate_feature_match_score(img1_path: str, img2_path: str) -> int:
    img1 = _resize_gray_image(img1_path)
    img2 = _resize_gray_image(img2_path)
    if img1 is None or img2 is None:
        return 0

    sift = cv2.SIFT_create(contrastThreshold=0.02, edgeThreshold=10)
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    if des1 is None or des2 is None or len(kp1) < 5 or len(kp2) < 5:
        return 0

    index_params = dict(algorithm=1, trees=5)
    search_params = dict(checks=50)
    matcher = cv2.FlannBasedMatcher(index_params, search_params)
    matches = matcher.knnMatch(des1, des2, k=2)

    good_matches = [m for m, n in matches if m.distance < 0.75 * n.distance]
    if len(good_matches) < 5:
        return 0

    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    _, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    inliers = int(np.sum(mask)) if mask is not None else 0
    return inliers


def _hash_distance(hash1: str, hash2: str) -> int:
    try:
        ph1 = imagehash.hex_to_hash(hash1)
        ph2 = imagehash.hex_to_hash(hash2)
        return ph1 - ph2
    except Exception:
        logger.exception('Failed to compute hash distance.')
        return 999


def match_new_item(new_item: Item, config) -> bool:
    opposite_type = 'found' if new_item.type == 'lost' else 'lost'
    candidates = Item.query.filter_by(type=opposite_type, status='open', category=new_item.category).all()
    upload_folder = config['UPLOAD_FOLDER']

    for candidate in candidates:
        match_linked = False

        if new_item.image_filename and candidate.image_filename and new_item.image_hash and candidate.image_hash:
            distance = _hash_distance(new_item.image_hash, candidate.image_hash)
            if distance <= HASH_THRESHOLD:
                match_linked = _link_items(new_item, candidate)

        if not match_linked and new_item.image_filename and candidate.image_filename:
            img1_path = os.path.join(upload_folder, new_item.image_filename)
            img2_path = os.path.join(upload_folder, candidate.image_filename)
            if os.path.exists(img1_path) and os.path.exists(img2_path):
                inliers = calculate_feature_match_score(img1_path, img2_path)
                if inliers >= FEATURE_THRESHOLD:
                    match_linked = _link_items(new_item, candidate)

        if not match_linked and candidate.location.strip().lower() == new_item.location.strip().lower():
            match_linked = _link_items(new_item, candidate)

        if match_linked:
            send_match_notification(new_item, candidate, config)
            return True

    return False


def _link_items(new_item: Item, candidate: Item) -> bool:
    new_item.status = 'matched'
    candidate.status = 'matched'
    new_item.matched_with_id = candidate.id
    candidate.matched_with_id = new_item.id

    try:
        db.session.commit()
        logger.info('Matched items: %s and %s', new_item.id, candidate.id)
        return True
    except Exception:
        db.session.rollback()
        logger.exception('Failed to link matched items.')
        return False
