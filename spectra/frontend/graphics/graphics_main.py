import threading
import time

import numpy as np
import pygame
import requests

from renderer import (
    render_frame,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)

from support.classes import DEFAULT_CATEGORY, SOUNDS_DICT


# ==================================================
# CONFIGURATION
# ==================================================

API_URL = (
    "https://spectra-1087886990522."
    "europe-west1.run.app"
)

RECENT_PREDICTION_URL = (
    f"{API_URL}/recent?n=1"
)

FPS = 60

# Ask API once per second.
API_POLL_INTERVAL = 1.0


# ==================================================
# SHARED STATE
# ==================================================

predictions = []

predictions_lock = threading.Lock()

running = True


# ==================================================
# API -> GRAPHICS ADAPTER
# ==================================================

def adapt_predictions(api_predictions):

    if not api_predictions:
        return []

    best_by_category = {}

    for prediction in api_predictions:

        class_name = prediction.get(
            "class_name",
            "",
        )

        if not class_name:
            continue

        category = SOUNDS_DICT.get(
            class_name,
            DEFAULT_CATEGORY,
        )

        if category == DEFAULT_CATEGORY:
            continue

        try:
            confidence = float(
                prediction.get(
                    "confidence",
                    0.0,
                )
            )

        except (TypeError, ValueError):
            confidence = 0.0

        confidence = max(
            0.0,
            min(confidence, 1.0),
        )

        current = best_by_category.get(
            category
        )

        # Only one icon per broad category.
        # Keep the strongest prediction.
        if (
            current is None
            or confidence > current["confidence"]
        ):

            best_by_category[category] = {
                "category": category,
                "display_label": category,
                "confidence": confidence,
            }

    adapted = list(
        best_by_category.values()
    )

    adapted.sort(
        key=lambda item: item["confidence"],
        reverse=True,
    )

    return adapted[:3]


# ==================================================
# API POLLING THREAD
# ==================================================

def poll_api():
    """
    Runs separately from the Pygame loop.

    This is important because requests.get() can wait
    several seconds for Cloud Run.

    Pygame therefore remains responsive while the
    network request is running.
    """

    global predictions
    global running

    http = requests.Session()

    latest_timestamp = None

    try:

        while running:

            try:

                response = http.get(
                    RECENT_PREDICTION_URL,
                    timeout=10,
                )

                response.raise_for_status()

                data = response.json()

                history = data.get(
                    "predictions",
                    [],
                )

                if history:

                    latest = history[-1]

                    timestamp = latest.get(
                        "timestamp"
                    )

                    # Only update graphics when the
                    # API actually has a new result.
                    if timestamp != latest_timestamp:

                        raw_predictions = latest.get(
                            "predictions",
                            [],
                        )

                        new_predictions = (
                            adapt_predictions(
                                raw_predictions
                            )
                        )

                        with predictions_lock:

                            predictions = (
                                new_predictions
                            )

                        latest_timestamp = (
                            timestamp
                        )

            except requests.RequestException as error:

                print(
                    "Spectra API unavailable:",
                    error,
                )

            except ValueError as error:

                print(
                    "Invalid API response:",
                    error,
                )

            # Poll once per second.
            time.sleep(
                API_POLL_INTERVAL
            )

    finally:

        http.close()


# ==================================================
# NUMPY -> PYGAME
# ==================================================

def numpy_frame_to_surface(frame):

    pygame_frame = np.swapaxes(
        frame,
        0,
        1,
    )

    return pygame.surfarray.make_surface(
        pygame_frame
    )


# ==================================================
# PYGAME SETUP
# ==================================================

pygame.init()

screen = pygame.display.set_mode(
    (
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
    )
)

pygame.display.set_caption(
    "Spectra AI"
)

clock = pygame.time.Clock()


# ==================================================
# START API THREAD
# ==================================================

api_thread = threading.Thread(
    target=poll_api,
    daemon=True,
)

api_thread.start()


# ==================================================
# MAIN PYGAME LOOP
# ==================================================

try:

    while running:

        # ------------------------------------------
        # EVENTS
        # ------------------------------------------

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

        # ------------------------------------------
        # COPY CURRENT PREDICTIONS
        # ------------------------------------------

        with predictions_lock:

            current_predictions = (
                predictions.copy()
            )

        # ------------------------------------------
        # DRAW FRAME
        # ------------------------------------------

        frame = render_frame(
            current_predictions,

            # /recent does not currently provide RMS.
            0.0,
        )

        # ------------------------------------------
        # NUMPY -> PYGAME
        # ------------------------------------------

        frame_surface = (
            numpy_frame_to_surface(
                frame
            )
        )

        # ------------------------------------------
        # DISPLAY
        # ------------------------------------------

        screen.blit(
            frame_surface,
            (0, 0),
        )

        pygame.display.flip()

        # ------------------------------------------
        # 60 FPS
        # ------------------------------------------

        clock.tick(FPS)


# ==================================================
# CLEANUP
# ==================================================

finally:

    running = False

    pygame.quit()
