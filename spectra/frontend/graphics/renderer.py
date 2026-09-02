import io
import math
import random
from pathlib import Path

import numpy as np
import pygame

from .visualizer import lerp


# ==================================================
# IMPORTANT
#
# Do NOT call pygame.init() here.
#
# renderer.py is imported by Streamlit, which runs
# scripts outside the macOS main thread.
#
# pygame.init() initializes the SDL display subsystem
# and can crash Streamlit on macOS.
#
# We only need the font subsystem for off-screen
# rendering.
# ==================================================

pygame.font.init()


# ==================================================
# MOBILE SCREEN CONFIGURATION
# ==================================================

SCREEN_WIDTH = 430
SCREEN_HEIGHT = 760


# ==================================================
# ASSET PATHS
# ==================================================

ASSETS_DIR = (
    Path(__file__).resolve().parent
    / "assets"
)


# ==================================================
# FONTS
# ==================================================

title_font = pygame.font.Font(
    None,
    42,
)

subtitle_font = pygame.font.Font(
    None,
    20,
)

hero_percentage_font = pygame.font.Font(
    None,
    48,
)

hero_name_font = pygame.font.Font(
    None,
    34,
)

hero_category_font = pygame.font.Font(
    None,
    20,
)

secondary_percentage_font = pygame.font.Font(
    None,
    32,
)

secondary_name_font = pygame.font.Font(
    None,
    25,
)

secondary_category_font = pygame.font.Font(
    None,
    18,
)

confidence_label_font = pygame.font.Font(
    None,
    16,
)

small_font = pygame.font.Font(
    None,
    20,
)

rms_font = pygame.font.Font(
    None,
    25,
)


# ==================================================
# LOAD ASSETS
#
# No convert_alpha().
#
# convert_alpha() requires an initialized display,
# which we deliberately do not have here.
# ==================================================

BACKGROUND_IMAGE = pygame.image.load(
    str(
        ASSETS_DIR
        / "spectra-background.png"
    )
)

BACKGROUND_IMAGE = (
    pygame.transform.smoothscale(
        BACKGROUND_IMAGE,
        (
            SCREEN_WIDTH,
            250,
        ),
    )
)


# Largest icon the layout ever draws: the hero is base_size 55
# plus up to 45 for confidence, and draw_floating_icon doubles
# that. The PNGs are 512-800 px, so shrinking them once here
# makes the per-frame smoothscale ~15x cheaper.
MAX_ICON_SIZE = 2 * (55 + 45)


def load_icon(filename):

    image = pygame.image.load(
        str(ASSETS_DIR / filename)
    )

    return pygame.transform.smoothscale(
        image,
        (MAX_ICON_SIZE, MAX_ICON_SIZE),
    )


CLAPPING_IMAGE = load_icon("clapping-hands.png")

CAR_IMAGE = load_icon("car.png")

ALARM_IMAGE = load_icon("alarm.png")

ANIMAL_IMAGE = load_icon("animal.png")

NATURE_IMAGE = load_icon("nature.png")

TALKING_IMAGE = load_icon("talking.png")


# ==================================================
# GRAPHICS CATEGORY CONFIGURATION
#
# Purely visual mapping.
#
# renderer.py does NOT know:
# - how the sound was classified
# - which model was used
# - what ESC-50 is
# - what YAMNet is
# - where the API is
# ==================================================

CATEGORY_IMAGES = {

    "Clapping":
        CLAPPING_IMAGE,

    "Human":
        TALKING_IMAGE,

    "Alert":
        ALARM_IMAGE,

    "Vehicle":
        CAR_IMAGE,

    "Animal":
        ANIMAL_IMAGE,

    "Nature":
        NATURE_IMAGE,
}


CATEGORY_COLORS = {

    "Clapping":
        (255, 180, 50),

    "Human":
        (255, 180, 50),

    "Alert":
        (255, 50, 80),

    "Vehicle":
        (50, 150, 255),

    "Animal":
        (120, 220, 130),

    "Nature":
        (80, 210, 180),
}


# ==================================================
# MOBILE LAYOUT
# ==================================================

HERO_POSITION = (
    215,
    300,
)

SECONDARY_POSITIONS = [

    (
        120,
        525,
    ),

    (
        310,
        525,
    ),
]


# Used by particle generation
SOUND_POSITIONS = [

    HERO_POSITION,

    SECONDARY_POSITIONS[0],

    SECONDARY_POSITIONS[1],
]


# ==================================================
# BACKGROUND OVERLAY
# ==================================================

BACKGROUND_OVERLAY = pygame.Surface(
    (
        SCREEN_WIDTH,
        SCREEN_HEIGHT,
    ),
    pygame.SRCALPHA,
)

BACKGROUND_OVERLAY.fill(
    (
        0,
        0,
        0,
        70,
    )
)


# ==================================================
# ANIMATION STATE
# ==================================================

shape_states = {}

particles = []


# ==================================================
# RESET
# ==================================================

def reset_animation_state():
    """
    Reset all persistent visual animation state.
    """

    shape_states.clear()

    particles.clear()


# ==================================================
# FLOATING ICON
# ==================================================

def draw_floating_icon(
    surface,
    image,
    center,
    size,
    color,
    alpha,
    confidence,
):

    x, y = center


    icon_size = max(
        1,
        int(
            size * 2
        ),
    )


    # --------------------------------------------------
    # SOCLE / GLOW
    # --------------------------------------------------

    socle_width = int(
        icon_size * 0.90
    )

    socle_height = max(
        12,
        int(
            icon_size * 0.12
        ),
    )


    socle_surface = pygame.Surface(
        (
            socle_width + 40,
            socle_height + 30,
        ),
        pygame.SRCALPHA,
    )


    socle_alpha = int(
        30
        + confidence * 35
    )


    pygame.draw.ellipse(
        socle_surface,
        (
            *color,
            socle_alpha // 2,
        ),
        (
            10,
            10,
            socle_width + 20,
            socle_height + 8,
        ),
    )


    pygame.draw.ellipse(
        socle_surface,
        (
            *color,
            socle_alpha,
        ),
        (
            30,
            14,
            max(
                10,
                socle_width - 20,
            ),
            max(
                4,
                socle_height,
            ),
        ),
    )


    socle_rect = (
        socle_surface.get_rect(
            center=(
                x,
                y + size + 15,
            )
        )
    )


    surface.blit(
        socle_surface,
        socle_rect,
        special_flags=(
            pygame.BLEND_RGBA_ADD
        ),
    )


    # --------------------------------------------------
    # ICON
    # --------------------------------------------------

    scaled_image = (
        pygame.transform.smoothscale(
            image,
            (
                icon_size,
                icon_size,
            ),
        )
    )


    scaled_image.set_alpha(
        alpha
    )


    image_rect = (
        scaled_image.get_rect(
            center=(
                x,
                y,
            )
        )
    )


    surface.blit(
        scaled_image,
        image_rect,
    )


# ==================================================
# DIVIDER
# ==================================================

def draw_divider(
    surface,
    y,
):

    pygame.draw.line(
        surface,
        (
            45,
            50,
            62,
        ),
        (
            35,
            y,
        ),
        (
            395,
            y,
        ),
        1,
    )


# ==================================================
# RENDER ONE FRAME
# ==================================================

def render_surface(
    predictions,
    rms=0.0,
):
    """
    Draw one complete Spectra visualization.

    Expected predictions:

    [
        {
            "category": "Human",
            "display_label": "Human",
            "confidence": 0.82
        },
        {
            "category": "Animal",
            "display_label": "Animal",
            "confidence": 0.51
        }
    ]

    renderer.py is completely independent from
    model and API logic.

    Returns
    -------
    pygame.Surface
        SCREEN_WIDTH x SCREEN_HEIGHT, RGB.

        Use render_frame() for a numpy array or
        render_frame_jpeg() for encoded bytes.
    """

    if predictions is None:

        predictions = []


    try:

        rms = float(
            rms
        )

    except (
        TypeError,
        ValueError,
    ):

        rms = 0.0


    # ==================================================
    # 1. NORMALIZE MODEL OUTPUT
    # ==================================================

    active_sounds = []


    for prediction in predictions:

        if not isinstance(
            prediction,
            dict,
        ):

            continue


        category = prediction.get(
            "category",
            prediction.get("class_name")
        )


        if not category:

            continue


        if category not in CATEGORY_IMAGES:

            continue


        display_label = prediction.get(
            "display_label",
            prediction.get(
                "class_name",
                category,
            ),
        )


        try:

            confidence = float(
                prediction.get(
                    "confidence",
                    0.0,
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            confidence = 0.0


        confidence = max(
            0.0,
            min(
                confidence,
                1.0,
            ),
        )


        active_sounds.append(
            {
                "category":
                    category,

                "display_label":
                    display_label,

                "confidence":
                    confidence,
            }
        )


    # Strongest becomes hero.
    active_sounds.sort(
        key=lambda sound:
            sound[
                "confidence"
            ],
        reverse=True,
    )


    active_sounds = (
        active_sounds[:3]
    )


    # ==================================================
    # 2. PARTICLE GENERATION
    # ==================================================

    if (
        rms >= 0.05
        and active_sounds
    ):

        if rms < 0.065:

            particle_probability = 0.15

        elif rms < 0.08:

            particle_probability = 0.40

        else:

            particle_probability = 0.80


        if (
            random.random()
            < particle_probability
        ):

            for index, sound in enumerate(
                active_sounds
            ):

                category = (
                    sound[
                        "category"
                    ]
                )


                x, y = (
                    SOUND_POSITIONS[
                        index
                    ]
                )


                angle = random.uniform(
                    0,
                    2 * math.pi,
                )


                speed = random.uniform(
                    0.8,
                    1.5
                    + rms * 15,
                )


                particles.append(
                    {
                        "x":
                            float(x),

                        "y":
                            float(y),

                        "vx":
                            math.cos(
                                angle
                            )
                            * speed,

                        "vy":
                            math.sin(
                                angle
                            )
                            * speed,

                        "life":
                            55,

                        "color":
                            CATEGORY_COLORS[
                                category
                            ],
                    }
                )


    # ==================================================
    # 3. OFF-SCREEN SURFACE
    # ==================================================

    surface = pygame.Surface(
        (
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
        )
    )


    # ==================================================
    # 4. BACKGROUND
    # ==================================================

    surface.fill(
        (
            5,
            7,
            12,
        )
    )


    # Background artwork behind hero area
    surface.blit(
        BACKGROUND_IMAGE,
        (
            0,
            125,
        ),
    )


    surface.blit(
        BACKGROUND_OVERLAY,
        (
            0,
            0,
        ),
    )


    # ==================================================
    # 5. HEADER
    # ==================================================

    title_text = title_font.render(
        "SPECTRA AI",
        True,
        (
            245,
            245,
            250,
        ),
    )


    title_rect = (
        title_text.get_rect(
            center=(
                215,
                35,
            )
        )
    )


    surface.blit(
        title_text,
        title_rect,
    )


    subtitle_text = (
        subtitle_font.render(
            "Visualize your surrounding's sounds",
            True,
            (
                155,
                160,
                175,
            ),
        )
    )


    subtitle_rect = (
        subtitle_text.get_rect(
            center=(
                215,
                66,
            )
        )
    )


    surface.blit(
        subtitle_text,
        subtitle_rect,
    )


    # ==================================================
    # 6. LISTENING STATUS
    # ==================================================

    status_y = 101


    pygame.draw.circle(
        surface,
        (
            30,
            220,
            130,
        ),
        (
            169,
            status_y,
        ),
        5,
    )


    listening_text = small_font.render(
        "LISTENING",
        True,
        (
            185,
            190,
            205,
        ),
    )


    surface.blit(
        listening_text,
        (
            182,
            status_y - 8,
        ),
    )


    draw_divider(
        surface,
        125,
    )


    # ==================================================
    # 7. DRAW SOUND PREDICTIONS
    # ==================================================

    for index, sound in enumerate(
        active_sounds
    ):

        category = (
            sound[
                "category"
            ]
        )

        display_label = (
            sound[
                "display_label"
            ]
        )

        confidence = (
            sound[
                "confidence"
            ]
        )


        color = (
            CATEGORY_COLORS[
                category
            ]
        )


        image = (
            CATEGORY_IMAGES[
                category
            ]
        )


        # --------------------------------------------------
        # HERO
        # --------------------------------------------------

        if index == 0:

            x, y = (
                HERO_POSITION
            )

            base_size = 55

            confidence_size = 45

            percentage_font = (
                hero_percentage_font
            )

            name_font = (
                hero_name_font
            )

            category_label_font = (
                hero_category_font
            )


        # --------------------------------------------------
        # SECONDARY
        # --------------------------------------------------

        else:

            x, y = (
                SECONDARY_POSITIONS[
                    index - 1
                ]
            )

            base_size = 34

            confidence_size = 24

            percentage_font = (
                secondary_percentage_font
            )

            name_font = (
                secondary_name_font
            )

            category_label_font = (
                secondary_category_font
            )


        # ==================================================
        # 8. CONFIDENCE ANIMATION
        # ==================================================

        # Use position + category as the state key.
        #
        # This is important because the same category can
        # move between hero and secondary positions.
        state_key = (
            index,
            category,
        )


        if state_key not in shape_states:

            shape_states[
                state_key
            ] = {
                "size":
                    float(
                        base_size
                        * 0.70
                    ),

                "alpha":
                    60.0,
            }


        state = (
            shape_states[
                state_key
            ]
        )


        target_size = (
            base_size
            + confidence
            * confidence_size
        )


        target_alpha = (
            130
            + confidence
            * 125
        )


        state["size"] = lerp(
            state["size"],
            target_size,
            0.15,
        )


        state["alpha"] = lerp(
            state["alpha"],
            target_alpha,
            0.15,
        )


        size = int(
            state[
                "size"
            ]
        )


        alpha = int(
            max(
                0,
                min(
                    state[
                        "alpha"
                    ],
                    255,
                ),
            )
        )


        # ==================================================
        # 9. ICON
        # ==================================================

        draw_floating_icon(
            surface,
            image,
            (
                x,
                y,
            ),
            size,
            color,
            alpha,
            confidence,
        )


        # ==================================================
        # 10. LABELS
        # ==================================================

        if index == 0:

            sound_name = (
                name_font.render(
                    display_label.upper(),
                    True,
                    (
                        245,
                        245,
                        250,
                    ),
                )
            )


            sound_rect = (
                sound_name.get_rect(
                    center=(
                        x,
                        405,
                    )
                )
            )


            surface.blit(
                sound_name,
                sound_rect,
            )


            category_text = (
                category_label_font.render(
                    category.upper(),
                    True,
                    color,
                )
            )


            category_rect = (
                category_text.get_rect(
                    center=(
                        x,
                        433,
                    )
                )
            )


            surface.blit(
                category_text,
                category_rect,
            )


            percentage_text = (
                percentage_font.render(
                    f"{confidence * 100:.0f}%",
                    True,
                    color,
                )
            )


            percentage_rect = (
                percentage_text.get_rect(
                    center=(
                        x,
                        467,
                    )
                )
            )


            surface.blit(
                percentage_text,
                percentage_rect,
            )


            confidence_text = (
                confidence_label_font.render(
                    "CONFIDENCE",
                    True,
                    (
                        145,
                        150,
                        165,
                    ),
                )
            )


            confidence_rect = (
                confidence_text.get_rect(
                    center=(
                        x,
                        492,
                    )
                )
            )


            surface.blit(
                confidence_text,
                confidence_rect,
            )


        else:

            sound_name = (
                name_font.render(
                    display_label.upper(),
                    True,
                    (
                        245,
                        245,
                        250,
                    ),
                )
            )


            sound_rect = (
                sound_name.get_rect(
                    center=(
                        x,
                        605,
                    )
                )
            )


            surface.blit(
                sound_name,
                sound_rect,
            )


            percentage_text = (
                percentage_font.render(
                    f"{confidence * 100:.0f}%",
                    True,
                    color,
                )
            )


            percentage_rect = (
                percentage_text.get_rect(
                    center=(
                        x,
                        636,
                    )
                )
            )


            surface.blit(
                percentage_text,
                percentage_rect,
            )


            category_text = (
                category_label_font.render(
                    category.upper(),
                    True,
                    color,
                )
            )


            category_rect = (
                category_text.get_rect(
                    center=(
                        x,
                        658,
                    )
                )
            )


            surface.blit(
                category_text,
                category_rect,
            )


    # ==================================================
    # 11. PARTICLES
    # ==================================================

    particle_size = max(
        3,
        int(
            3
            + rms * 10
        ),
    )


    for particle in particles:

        particle["x"] += (
            particle[
                "vx"
            ]
        )

        particle["y"] += (
            particle[
                "vy"
            ]
        )

        particle["life"] -= 1


        particle_alpha = int(
            255
            * max(
                0,
                particle[
                    "life"
                ]
                / 55,
            )
        )


        particle_surface = pygame.Surface(
            (
                12,
                12,
            ),
            pygame.SRCALPHA,
        )


        pygame.draw.circle(
            particle_surface,
            (
                *particle[
                    "color"
                ],
                particle_alpha,
            ),
            (
                6,
                6,
            ),
            particle_size,
        )


        surface.blit(
            particle_surface,
            (
                int(
                    particle[
                        "x"
                    ]
                    - 6
                ),
                int(
                    particle[
                        "y"
                    ]
                    - 6
                ),
            ),
        )


    particles[:] = [

        particle

        for particle
        in particles

        if particle[
            "life"
        ] > 0
    ]


    # ==================================================
    # 12. AUDIO LEVEL
    # ==================================================

    draw_divider(
        surface,
        685,
    )


    audio_label = small_font.render(
        "AUDIO LEVEL",
        True,
        (
            155,
            160,
            175,
        ),
    )


    surface.blit(
        audio_label,
        (
            35,
            705,
        ),
    )


    rms_value = rms_font.render(
        f"{rms:.2f}",
        True,
        (
            235,
            235,
            245,
        ),
    )


    rms_rect = (
        rms_value.get_rect(
            right=395,
            centery=713,
        )
    )


    surface.blit(
        rms_value,
        rms_rect,
    )


    meter_x = 35
    meter_y = 738

    meter_width = 360
    meter_height = 8


    pygame.draw.rect(
        surface,
        (
            40,
            45,
            55,
        ),
        (
            meter_x,
            meter_y,
            meter_width,
            meter_height,
        ),
        border_radius=4,
    )


    rms_normalized = max(
        0.0,
        min(
            rms / 0.10,
            1.0,
        ),
    )


    fill_width = int(
        meter_width
        * rms_normalized
    )


    if fill_width > 0:

        pygame.draw.rect(
            surface,
            (
                30,
                220,
                130,
            ),
            (
                meter_x,
                meter_y,
                fill_width,
                meter_height,
            ),
            border_radius=4,
        )


    return surface


# ==================================================
# OUTPUT FORMATS
# ==================================================

def render_frame(
    predictions,
    rms=0.0,
):
    """
    Render one frame as a numpy array.

    Used by the desktop Pygame app and tests.

    Returns
    -------
    numpy.ndarray
        RGB image with shape:

        height x width x RGB
    """

    surface = render_surface(
        predictions,
        rms,
    )


    frame = pygame.surfarray.array3d(
        surface
    )


    # Pygame:
    # width x height x RGB
    #
    # Streamlit:
    # height x width x RGB

    return np.swapaxes(
        frame,
        0,
        1,
    )


def render_frame_jpeg(
    predictions,
    rms=0.0,
    quality=75,
):
    """
    Render one frame as JPEG bytes.

    Used by the Streamlit page. Skips the numpy round
    trip and encodes at `quality` instead of the
    quality 100 that st.image applies to arrays, which
    is ~4x smaller and faster.

    Returns
    -------
    bytes
        JPEG file contents.
    """

    # Pillow ships with Streamlit. Import lazily so the
    # desktop app can use renderer.py without it.
    from PIL import Image


    surface = render_surface(
        predictions,
        rms,
    )


    image = Image.frombuffer(
        "RGB",
        surface.get_size(),
        pygame.image.tobytes(
            surface,
            "RGB",
        ),
        "raw",
        "RGB",
        0,
        1,
    )


    buffer = io.BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=quality,
    )


    return buffer.getvalue()
