import os
import shutil # needed to copy and paste the images from one directory to another

GENERATED_DIR = 'generated_images'

def run_mock_ai(car_images : list[dict], tuning_id : int) -> list[str]:
    os.makedirs(GENERATED_DIR, exist_ok=True)

    generated_images = []

    for img in car_images:
        src = img['file_path']
        filename = f"tuning_{tuning_id}_{img['image_type']}.jpg"
        dst = os.path.join(GENERATED_DIR, filename)

        shutil.copy(src, dst)
        generated_images.append(dst)

    return generated_images



