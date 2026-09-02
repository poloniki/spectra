import os

os.environ["SDL_VIDEODRIVER"] = "dummy"

import streamlit as st
import requests
import pandas as pd
import os
from support.classes import DEFAULT_CATEGORY, SOUNDS_DICT

#st.title("Clean MVP")

st.set_page_config(
    page_title="Spectra AI",
    page_icon="🎧",
    layout="centered",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap');

    :root {
        --bg: #121218;
        --surface: #1B1B24;
        --border: #2A2A36;
        --text: #F2F0EA;
        --text-dim: #D8D6D0;
        --cyan: #00E5C7;
        --violet: #8C6DFF;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: var(--text);
    }

    .stApp {
        background: var(--bg);
    }



#MainMenu, footer { visibility: hidden; }

header {
    background: transparent !important;
}

    /* ---- Hero ---- */
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 2.6rem;
        line-height: 1.1;
        margin-bottom: 0.3rem;
        background: linear-gradient(90deg, var(--cyan), var(--violet));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
        color: var(--text-dim);
        font-size: 1.02rem;
        max-width: 34rem;
        margin-bottom: 1.6rem;
    }

    /* ---- Waveform accent (single motion moment) ---- */
    .waveform {
        display: flex;
        align-items: flex-end;
        gap: 4px;
        height: 34px;
        margin-bottom: 1.8rem;
    }
    .waveform span {
        display: block;
        width: 4px;
        border-radius: 2px;
        background: linear-gradient(180deg, var(--cyan), var(--violet));
        animation: pulse 1.2s ease-in-out infinite;
    }
    .waveform span:nth-child(1) { height: 10px; animation-delay: 0s; }
    .waveform span:nth-child(2) { height: 24px; animation-delay: 0.1s; }
    .waveform span:nth-child(3) { height: 14px; animation-delay: 0.2s; }
    .waveform span:nth-child(4) { height: 30px; animation-delay: 0.3s; }
    .waveform span:nth-child(5) { height: 18px; animation-delay: 0.4s; }
    .waveform span:nth-child(6) { height: 26px; animation-delay: 0.5s; }
    .waveform span:nth-child(7) { height: 12px; animation-delay: 0.6s; }
    .waveform span:nth-child(8) { height: 20px; animation-delay: 0.7s; }

    @keyframes pulse {
        0%, 100% { transform: scaleY(0.6); opacity: 0.7; }
        50% { transform: scaleY(1); opacity: 1; }
    }

    /* ---- Cards (st.container(border=True)) ---- */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--surface);
        border: 1px solid var(--border) !important;
        border-radius: 14px;
        padding: 0.4rem;
    }

    /* ---- Buttons ---- */
    .stButton > button {
        background: linear-gradient(90deg, var(--cyan), var(--violet));
        color: #0D0D12;
        font-weight: 600;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.2rem;
        transition: opacity 0.15s ease;
    }
    .stButton > button:hover {
        opacity: 0.88;
        color: #0D0D12;
    }

    /* ---- Progress bars (confidence) ---- */
    [data-testid="stProgress"] > div > div {
        background: linear-gradient(90deg, var(--cyan), var(--violet));
    }

    /* ---- Section labels ---- */
    .section-label {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 1.05rem;
        margin: 1.4rem 0 0.6rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------
# HERO
# -----------------------------------------------------------------------
st.markdown(
    """
    <div class="waveform">
        <span></span><span></span><span></span><span></span>
        <span></span><span></span><span></span><span></span>
    </div>
    <div class="hero-title">Spectra AI</div>
    <div class="hero-subtitle">
        Record a sound and see it classified and visualized in real time —
        built for hearing accessibility.
    </div>
    """,
    unsafe_allow_html=True,
)

URL = "https://spectra-1087886990522.europe-west1.run.app/predict"
# -----------------------------------------------------------------------
# INPUT METHOD
# -----------------------------------------------------------------------

st.markdown(
    '<div class="section-label">Choose Input Method</div>',
    unsafe_allow_html=True,
)

if "input_mode" not in st.session_state:
    st.session_state.input_mode = None

col1, col2 = st.columns(2)

with col1:
    if st.button("🎤 Record Audio", use_container_width=True):
        st.session_state.input_mode = "record"

with col2:
    if st.button("📁 Upload File", use_container_width=True):
        st.session_state.input_mode = "upload"

audio_bytes = None

if st.session_state.input_mode == "record":

    with st.container(border=True):

        st.markdown(
            '<div class="section-label">Audio Recorder</div>',
            unsafe_allow_html=True,
        )

        audio_value = st.audio_input(
            "Click on the microphone icon to start recording",
            key="my_audio_input"
        )

        if audio_value is not None:

            audio_bytes = audio_value.getvalue()

            if len(audio_bytes) == 0:

                st.error(
                    "I'm sorry, but I don't have access to your microphone. "
                    "Please check your browser permissions and try again."
                )

                audio_bytes = None

            else:

                st.audio(
                    audio_bytes,
                    format="audio/wav",
                )

elif st.session_state.input_mode == "upload":

    with st.container(border=True):

        st.markdown(
            '<div class="section-label">Upload Audio File</div>',
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader(
            "Choose a WAV file",
            type=["wav"],
            key="uploaded_file"
        )

        if uploaded_file is not None:

            audio_bytes = uploaded_file.getvalue()

            st.audio(
                audio_bytes,
                format="audio/wav",
            )

col1, col2  = st.columns(2)
with col2:
    if st.button("Reset", type="secondary", use_container_width=True):

        # Reset recording widget
        if "my_audio_input" in st.session_state:
            del st.session_state["my_audio_input"]

        # Reset upload widget
        if "uploaded_file" in st.session_state:
            del st.session_state["uploaded_file"]

        # Go back to method selection
        st.session_state.input_mode = None

        st.rerun()

with col1:
    analyze_clicked = st.button(
        "Predict Sound",
        type="primary",
        disabled=audio_bytes is None,
        use_container_width=True,
    )

if analyze_clicked and audio_bytes:

    with st.spinner(
        "Processing audio signal and generating visualization..."
    ):

        files = {
            "file": (
                "audio.wav",
                audio_bytes,
                "audio/wav",
            )
        }

        response = requests.post(
                    URL,
                    files=files,
                    timeout=60,
                )

        predictions = response.json()["predictions"]
        df = pd.DataFrame(predictions)
        #st.dataframe(df)

        classes = []
        for group in df.class_name:
            if SOUNDS_DICT[group] not in classes:
                classes.append(SOUNDS_DICT[group])

        best_class = SOUNDS_DICT[df.sort_values(by="confidence", ascending=False).iloc[0].class_name]
        confidences = df.sort_values(by="confidence", ascending=False).confidence

        #All 3 classes belong to the same group:
        if len(classes) == 1 or confidences[1] < 0.20:

            st.subheader(best_class.title())
            st.progress(confidences[0], text="Confidence %")

            best_class_image_path = os.path.join("spectra/frontend/images", f"{best_class}.png")
            try:
                st.image(best_class_image_path)
            except:
                st.text("Background")

        #Classes from different groups - 2 images
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(best_class.title())
                st.progress(confidences[0], text="Confidence %")

                best_class_image_path = os.path.join("spectra/frontend/images", f"{best_class}.png")
                try:
                    st.image(best_class_image_path)
                except:
                    st.text("Background")

            with col2:
                st.subheader(classes[1].title())
                st.progress(confidences[1], text="Confidence %")

                class_image_path = os.path.join("spectra/frontend/images", f"{classes[1]}.png")
                try:
                    st.image(class_image_path)
                except:
                    st.text("Background")
