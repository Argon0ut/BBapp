from src.models.client_photos import ClientPhotoType
from src.schemas.hairstyle_preview_request import (
    HairstylePreviewGenerateSchema,
    HairstylePreviewRegenerateSchema,
)


def test_generate_schema_accepts_selected_images_objects():
    payload = HairstylePreviewGenerateSchema.model_validate(
        {
            "text_prompt": "short bob haircut",
            "selected_images": [
                {"photo_type": "front"},
                {"type": "rear"},
                {"image_type": "left"},
            ],
        }
    )

    assert payload.selected_photo_types == [
        ClientPhotoType.FRONT,
        ClientPhotoType.REAR,
        ClientPhotoType.LEFT,
    ]


def test_regenerate_schema_accepts_photo_types_alias():
    payload = HairstylePreviewRegenerateSchema.model_validate(
        {
            "photo_types": ["front", "right"],
        }
    )

    assert payload.selected_photo_types == [
        ClientPhotoType.FRONT,
        ClientPhotoType.RIGHT,
    ]
