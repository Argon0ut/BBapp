import os
import shutil # needed to copy and paste the images from one directory to another

GENERATED_DIR = 'generated_images'

def run_mock_ai(client_photos: list[dict], preview_id: int) -> list[str]:
    os.makedirs(GENERATED_DIR, exist_ok=True)

    generated_images = []

    for photo in client_photos:
        src = photo['file_path']
        photo_type = photo.get('photo_type') or photo.get('image_type')
        filename = f"hairstyle_preview_{preview_id}_{photo_type}.jpg"
        dst = os.path.join(GENERATED_DIR, filename)

        shutil.copy(src, dst)
        generated_images.append(dst)

    return generated_images


