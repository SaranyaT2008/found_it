import os
import uuid
import logging
from PIL import Image
import imagehash

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


def validate_image_file(file) -> bool:
    """
    Validates that the uploaded file is a supported image and is not corrupted.
    """
    if file is None or file.filename == "":
        return True

    # Validate file extension
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False

    try:
        file.stream.seek(0)

        # Verify the image
        with Image.open(file.stream) as img:
            img.verify()

        # Reset stream position
        file.stream.seek(0)
        return True

    except Exception as e:
        logger.warning(f"Invalid image upload: {e}")
        file.stream.seek(0)
        return False


def _calculate_hash(image: Image.Image) -> str:
    """
    Generates a perceptual hash for image matching.
    """
    return str(imagehash.whash(image))


def save_image_file(file, config):
    """
    Saves the uploaded image securely after validation and returns
    the generated filename and image hash.
    """
    if file is None or file.filename == "":
        return None, None

    if not validate_image_file(file):
        raise ValueError("Invalid or corrupted image file.")

    upload_folder = config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    # Verify image once more before processing
    file.stream.seek(0)
    with Image.open(file.stream) as image:
        image.verify()

    # Reopen after verify()
    file.stream.seek(0)
    with Image.open(file.stream) as image:
        image = image.convert("RGB")

        # Resize while maintaining aspect ratio
        max_size = (1200, 1200)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Generate secure random filename
        random_filename = f"{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(upload_folder, random_filename)

        # Save optimized JPEG
        image.save(
            filepath,
            format="JPEG",
            quality=85,
            optimize=True
        )

        # Calculate perceptual hash
        img_hash = _calculate_hash(image)

    logger.info(f"Image uploaded successfully: {random_filename}")

    return random_filename, img_hash