"""Regression tests for the pygame frame renderer used by the Streamlit PyGame page.

Run with: pytest tests/test_renderer.py
"""
import io
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import numpy as np
import pytest
from PIL import Image

from spectra.frontend.graphics.renderer import (
    CATEGORY_IMAGES,
    MAX_ICON_SIZE,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    render_frame,
    render_frame_jpeg,
    reset_animation_state,
)

PREDICTIONS = [
    {"category": "Human", "display_label": "Human", "confidence": 0.82},
    {"category": "Animal", "display_label": "Animal", "confidence": 0.51},
    {"category": "Vehicle", "display_label": "Vehicle", "confidence": 0.33},
]

LOUD_RMS = 0.09  # spawns particles every frame: the busiest, least compressible frame


@pytest.fixture(autouse=True)
def fresh_animation():
    reset_animation_state()


def test_render_frame_keeps_numpy_contract():
    frame = render_frame(PREDICTIONS, LOUD_RMS)

    assert frame.shape == (SCREEN_HEIGHT, SCREEN_WIDTH, 3)
    assert frame.dtype == np.uint8


def test_render_frame_jpeg_is_a_full_size_jpeg():
    data = render_frame_jpeg(PREDICTIONS, LOUD_RMS)

    assert data[:2] == b"\xff\xd8"  # JPEG start-of-image marker

    image = Image.open(io.BytesIO(data))

    assert image.format == "JPEG"
    assert image.mode == "RGB"
    assert image.size == (SCREEN_WIDTH, SCREEN_HEIGHT)


def test_render_frame_jpeg_is_much_smaller_than_streamlit_quality_100():
    # Streamlit's own encode of the numpy frame (JPEG quality 100) is ~131 KB.
    data = render_frame_jpeg(PREDICTIONS, LOUD_RMS)

    assert len(data) < 80_000


def test_render_frame_jpeg_shows_the_same_picture_as_render_frame():
    # rms=0 -> no random particles, so two renders from a reset state match.
    expected = render_frame(PREDICTIONS, 0.0).astype(np.int16)

    reset_animation_state()
    decoded = np.asarray(
        Image.open(io.BytesIO(render_frame_jpeg(PREDICTIONS, 0.0))),
        dtype=np.int16,
    )

    # A swapped channel order or transposed axes would push this far above 10.
    assert np.abs(decoded - expected).mean() < 3.0


def test_icons_are_pre_shrunk_to_the_largest_drawn_size():
    for category, image in CATEGORY_IMAGES.items():
        assert max(image.get_size()) <= MAX_ICON_SIZE, category
