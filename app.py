import html
import hmac
import io
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request
import zipfile
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import requests
import streamlit as st
from scipy.signal import find_peaks, spectrogram

# =========================================================
# CONFIGURACIÓN INICIAL (primer comando de Streamlit)
# =========================================================
st.set_page_config(
    page_title="SoundSnip Studio PRO",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_VERSION = "v9 · NEON"


def get_secret(name, default=None):
    """Lee un secreto de Streamlit sin romper si no hay secrets configurados."""
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


# Contraseña: usa el secreto APP_PASSWORD si existe; si no, 2325
APP_PASSWORD = str(get_secret("APP_PASSWORD", "2325"))
AUDD_TOKEN = get_secret("AUDD_API_TOKEN")          # reconocimiento real (opcional)
IS_CLOUD = platform.system() == "Linux"
# Los enlaces de YouTube solo funcionan fiablemente en tu PC
LINK_MODE = (not IS_CLOUD) or bool(get_secret("ENABLE_LINK_MODE", False))

FFMPEG_OK = shutil.which("ffmpeg") is not None
FFPROBE_OK = shutil.which("ffprobe") is not None


# ---------------------------------------------------------
# DENO (solo necesario para el modo enlace)
# ---------------------------------------------------------
@st.cache_resource(show_spinner=False)
def setup_deno():
    deno_dir = "/tmp/deno_bin"
    deno_path = os.path.join(deno_dir, "deno")
    if not os.path.exists(deno_path):
        os.makedirs(deno_dir, exist_ok=True)
        url = ("https://github.com/denoland/deno/releases/download/"
               "v2.6.5/deno-x86_64-unknown-linux-gnu.zip")
        zip_path = "/tmp/deno.zip"
        try:
            urllib.request.urlretrieve(url, zip_path)
            with zipfile.ZipFile(zip_path) as z:
                z.extractall(deno_dir)
            os.chmod(deno_path, 0o755)
        except Exception:
            return None
    os.environ["PATH"] = deno_dir + os.pathsep + os.environ.get("PATH", "")
    return deno_path


if LINK_MODE:
    DENO_PATH = setup_deno() if IS_CLOUD else shutil.which("deno")
else:
    DENO_PATH = None

# ---------------------------------------------------------
# FORMATOS
# ---------------------------------------------------------
FORMATS = ["MP3", "WAV", "FLAC", "OGG", "M4A"]
LOSSY = {"MP3", "OGG", "M4A"}
AUDIO_TYPES = ["wav", "mp3", "flac", "ogg", "m4a", "aac", "opus", "aiff", "aif", "wma"]
VIDEO_TYPES = ["mp4", "mov", "mkv", "webm", "avi", "m4v"]
CODEC_MAP = {"MP3": "mp3", "WAV": "wav", "FLAC": "flac", "M4A": "m4a", "OGG": "vorbis"}
EXT_MAP = {"MP3": "mp3", "WAV": "wav", "FLAC": "flac", "M4A": "m4a", "OGG": "ogg"}
MIME_MAP = {"MP3": "audio/mpeg", "WAV": "audio/wav", "FLAC": "audio/flac",
            "M4A": "audio/mp4", "OGG": "audio/ogg"}
FFMPEG_ARGS = {
    "MP3": lambda q: ["-c:a", "libmp3lame", "-b:a", f"{q}k"],
    "M4A": lambda q: ["-c:a", "aac", "-b:a", f"{q}k"],
    "OGG": lambda q: ["-c:a", "libvorbis", "-q:a",
                      str({320: 9, 256: 8, 192: 6, 160: 5, 128: 4, 96: 2}.get(int(q), 6))],
    "WAV": lambda q: ["-c:a", "pcm_s16le"],
    "FLAC": lambda q: ["-c:a", "flac"],
}
BITRATES = [320, 256, 192, 160, 128, 96]

# =========================================================
# CSS NEÓN PRO
# =========================================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');

:root {
    --neon: #00ffc8;
    --neon2: #00d4a8;
    --violet: #7c5cff;
    --pink: #ff5c9f;
    --amber: #ffb347;
    --bg: #05070b;
    --panel: rgba(13, 19, 29, 0.72);
    --line: rgba(0, 212, 168, 0.18);
    --muted: #7a8699;
    --text: #e8edf4;
}

/* ====== BASE ====== */
.stApp {
    background:
        radial-gradient(1100px 600px at 8% -10%, rgba(0, 212, 168, 0.13), transparent 60%),
        radial-gradient(900px 520px at 96% -5%, rgba(124, 92, 255, 0.16), transparent 60%),
        radial-gradient(900px 700px at 50% 115%, rgba(255, 92, 159, 0.08), transparent 60%),
        #05070b;
    color: var(--text);
}
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(0, 212, 168, 0.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 212, 168, 0.045) 1px, transparent 1px);
    background-size: 44px 44px;
    -webkit-mask-image: radial-gradient(ellipse at top, black 20%, transparent 70%);
    mask-image: radial-gradient(ellipse at top, black 20%, transparent 70%);
    pointer-events: none;
}
.stApp, .stMarkdown, p, label, input, textarea, button, h1, h2, h3, h4 {
    font-family: 'Space Grotesk', system-ui, -apple-system, sans-serif;
}
header[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
.block-container { padding-top: 2.2rem; max-width: 1280px; }

/* ====== HERO ====== */
.ss-hero {
    position: relative;
    background: linear-gradient(135deg, rgba(15, 23, 34, 0.92), rgba(11, 16, 28, 0.92));
    border: 1px solid rgba(0, 212, 168, 0.28);
    border-radius: 22px;
    padding: 30px 36px 26px;
    margin-bottom: 22px;
    overflow: hidden;
    box-shadow: 0 0 50px rgba(0, 212, 168, 0.13), 0 0 90px rgba(124, 92, 255, 0.08),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
}
.ss-hero::before {
    content: '';
    position: absolute;
    top: -60%; left: -30%;
    width: 160%; height: 220%;
    background: conic-gradient(from 0deg, transparent, rgba(0, 212, 168, 0.09),
                transparent 30%, rgba(124, 92, 255, 0.09), transparent 60%);
    animation: ss-rotate 14s linear infinite;
    pointer-events: none;
}
.ss-hero::after {
    content: '';
    position: absolute;
    left: 0; right: 0; bottom: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--neon), var(--violet), var(--pink), transparent);
    background-size: 200% 100%;
    animation: ss-slide 4s linear infinite;
}
@keyframes ss-rotate { to { transform: rotate(360deg); } }
@keyframes ss-slide { to { background-position: 200% 0; } }
.ss-hero-top { position: relative; display: flex; align-items: center; gap: 18px; z-index: 1; }
.ss-logo {
    width: 62px; height: 62px; flex: 0 0 62px;
    display: grid; place-items: center;
    font-size: 1.9rem;
    border-radius: 18px;
    background: linear-gradient(135deg, rgba(0, 255, 200, 0.18), rgba(124, 92, 255, 0.22));
    border: 1px solid rgba(0, 255, 200, 0.35);
    box-shadow: 0 0 25px rgba(0, 255, 200, 0.35), inset 0 0 18px rgba(0, 255, 200, 0.12);
}
.ss-hero h1 {
    background: linear-gradient(135deg, #00ffc8 0%, #00d4a8 40%, #a58cff 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    font-size: 2.3rem; font-weight: 700; margin: 0; padding: 0; letter-spacing: -1px;
    filter: drop-shadow(0 0 18px rgba(0, 212, 168, 0.35));
}
.ss-hero p { color: #8fa0b5; margin: 4px 0 0 0; font-size: 1rem; }
.ss-badge-pro {
    display: inline-block;
    background: linear-gradient(135deg, #7c5cff, #ff5c9f);
    -webkit-text-fill-color: #fff; color: #fff;
    font-size: 0.7rem; font-weight: 700;
    padding: 4px 10px; border-radius: 7px;
    margin-left: 12px; letter-spacing: 2px; vertical-align: middle;
    box-shadow: 0 0 20px rgba(124, 92, 255, 0.6);
}
.ss-chips { position: relative; z-index: 1; display: flex; flex-wrap: wrap; gap: 8px; margin-top: 20px; }
.ss-chips span {
    font-size: 0.8rem; color: #cfe9e3;
    padding: 6px 12px; border-radius: 999px;
    background: rgba(0, 212, 168, 0.07);
    border: 1px solid rgba(0, 212, 168, 0.22);
}
.ss-eq {
    position: absolute; right: 38px; top: 34px; z-index: 1;
    display: flex; align-items: flex-end; gap: 4px; height: 56px;
}
.ss-eq i {
    display: block; width: 5px; height: 30%;
    border-radius: 3px;
    background: linear-gradient(180deg, var(--neon), var(--violet));
    box-shadow: 0 0 10px rgba(0, 255, 200, 0.55);
    animation: ss-eq 1.1s ease-in-out infinite;
}
@keyframes ss-eq { 0%, 100% { height: 18%; } 50% { height: 100%; } }
@media (max-width: 820px) { .ss-eq { display: none; } .ss-hero h1 { font-size: 1.7rem; } }

/* ====== TABS ====== */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: rgba(12, 18, 28, 0.7);
    padding: 7px;
    border-radius: 16px;
    border: 1px solid var(--line);
    flex-wrap: wrap;
    backdrop-filter: blur(12px);
}
.stTabs [data-baseweb="tab"] {
    background: transparent; color: #8592a6;
    border-radius: 11px; padding: 9px 16px;
    font-weight: 600; border: none; font-size: 0.9rem;
    transition: all 0.25s ease;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--neon); background: rgba(0, 212, 168, 0.08); }
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #00d4a8 0%, #00ffc8 100%) !important;
    color: #05070b !important; font-weight: 700;
    box-shadow: 0 0 18px rgba(0, 212, 168, 0.55), 0 0 36px rgba(0, 212, 168, 0.25);
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

/* ====== CABECERAS DE SECCIÓN ====== */
.ss-sec { display: flex; align-items: center; gap: 16px; margin: 10px 0 18px; }
.ss-sec-icon {
    width: 50px; height: 50px; flex: 0 0 50px;
    display: grid; place-items: center; font-size: 1.5rem;
    border-radius: 15px;
    background: linear-gradient(135deg, rgba(0, 255, 200, 0.14), rgba(124, 92, 255, 0.16));
    border: 1px solid rgba(0, 255, 200, 0.3);
    box-shadow: 0 0 22px rgba(0, 255, 200, 0.22);
}
.ss-sec-title { font-size: 1.45rem; font-weight: 700; color: var(--text); letter-spacing: -0.4px; }
.ss-sec-sub { color: var(--muted); font-size: 0.9rem; margin-top: 2px; }
.ss-sub {
    display: flex; align-items: center; gap: 10px;
    margin: 22px 0 10px; font-weight: 700; font-size: 0.82rem;
    text-transform: uppercase; letter-spacing: 1.8px; color: #b9c6d6;
}
.ss-sub::before {
    content: ''; width: 4px; height: 16px; border-radius: 2px;
    background: linear-gradient(180deg, var(--neon), var(--violet));
    box-shadow: 0 0 10px rgba(0, 255, 200, 0.7);
}

/* ====== CARDS ====== */
.ss-card {
    background: linear-gradient(135deg, rgba(20, 27, 38, 0.88), rgba(13, 18, 27, 0.94));
    border: 1px solid rgba(0, 212, 168, 0.18);
    border-radius: 15px;
    padding: 16px 18px; margin-bottom: 12px;
    transition: all 0.25s ease;
    position: relative; overflow: hidden;
}
.ss-card::before {
    content: ''; position: absolute; top: 0; left: 0; width: 3px; height: 100%;
    background: linear-gradient(180deg, var(--neon), var(--violet));
    opacity: 0; transition: opacity 0.25s ease;
}
.ss-card:hover {
    border-color: rgba(0, 212, 168, 0.5);
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(0, 212, 168, 0.16), 0 0 50px rgba(0, 212, 168, 0.08);
}
.ss-card:hover::before { opacity: 1; }
.ss-card a { color: var(--neon); text-decoration: none; font-weight: 600; }
.ss-card a:hover { text-shadow: 0 0 10px rgba(0, 255, 200, 0.7); }
.ss-card-title { color: var(--text); font-size: 1.02rem; font-weight: 700; margin: 6px 0 3px; }
.ss-card-meta { color: var(--muted); font-size: 0.85rem; line-height: 1.55; }
.ss-result { border-color: rgba(0, 255, 200, 0.45); box-shadow: 0 0 30px rgba(0, 255, 200, 0.12); }
.ss-empty {
    text-align: center; padding: 34px 20px; margin: 10px 0;
    border: 1.5px dashed rgba(0, 212, 168, 0.28); border-radius: 16px;
    background: rgba(10, 15, 24, 0.5); color: var(--muted);
}
.ss-empty b { color: var(--text); display: block; font-size: 1.05rem; margin: 8px 0 4px; }
.ss-empty .ss-empty-icon { font-size: 2.2rem; filter: drop-shadow(0 0 12px rgba(0, 255, 200, 0.5)); }

/* ====== BADGES ====== */
.ss-card-badge {
    display: inline-block;
    background: linear-gradient(135deg, #00d4a8, #00ffc8); color: #05070b;
    font-size: 0.63rem; font-weight: 700;
    padding: 3px 8px; border-radius: 6px; margin: 0 5px 3px 0;
    text-transform: uppercase; letter-spacing: 1px;
    box-shadow: 0 0 12px rgba(0, 212, 168, 0.35);
}
.ss-badge-purple { background: linear-gradient(135deg, #7c5cff, #a58cff); color: #fff; box-shadow: 0 0 12px rgba(124, 92, 255, 0.45); }
.ss-badge-orange { background: linear-gradient(135deg, #ff9f43, #ffc27a); color: #05070b; box-shadow: 0 0 12px rgba(255, 159, 67, 0.45); }
.ss-badge-red { background: linear-gradient(135deg, #ff5c9f, #ff8ab8); color: #fff; box-shadow: 0 0 12px rgba(255, 92, 159, 0.45); }
.ss-badge-ghost { background: rgba(255, 255, 255, 0.06); color: #b9c6d6; box-shadow: none; border: 1px solid rgba(255, 255, 255, 0.1); }

/* ====== STATS ====== */
.ss-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 12px; margin: 14px 0 6px; }
.ss-stat {
    background: linear-gradient(135deg, rgba(20, 27, 38, 0.85), rgba(0, 212, 168, 0.05));
    border: 1px solid rgba(0, 212, 168, 0.22);
    border-radius: 14px; padding: 14px 14px 12px; text-align: center;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}
.ss-stat-v {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.35rem; font-weight: 700;
    background: linear-gradient(135deg, #00ffc8, #00d4a8);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    filter: drop-shadow(0 0 10px rgba(0, 212, 168, 0.45));
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.ss-stat-l { color: var(--muted); font-size: 0.68rem; text-transform: uppercase; letter-spacing: 1.6px; font-weight: 600; margin-top: 4px; }
.ss-stat-box {
    background: linear-gradient(135deg, rgba(20, 27, 38, 0.9), rgba(0, 212, 168, 0.05));
    border: 1px solid rgba(0, 212, 168, 0.3); border-radius: 14px;
    padding: 16px 20px; text-align: center; margin-bottom: 8px;
    box-shadow: 0 0 30px rgba(0, 212, 168, 0.12);
}

/* ====== INPUTS ====== */
[data-baseweb="input"] > div, [data-baseweb="select"] > div, [data-baseweb="base-input"],
.stTextInput input, .stNumberInput input {
    background: rgba(10, 15, 24, 0.9) !important;
    border-color: rgba(0, 212, 168, 0.22) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
}
[data-baseweb="input"]:focus-within > div, [data-baseweb="select"]:focus-within > div {
    border-color: var(--neon2) !important;
    box-shadow: 0 0 0 2px rgba(0, 212, 168, 0.25), 0 0 18px rgba(0, 212, 168, 0.18) !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: rgba(10, 15, 24, 0.6) !important;
    border: 1.5px dashed rgba(0, 212, 168, 0.35) !important;
    border-radius: 16px !important;
    transition: all 0.25s ease;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--neon) !important;
    box-shadow: 0 0 25px rgba(0, 255, 200, 0.15);
}

/* ====== BOTONES ====== */
.stButton button, [data-testid="stFormSubmitButton"] button {
    position: relative; overflow: hidden;
    background: linear-gradient(135deg, #00d4a8 0%, #00ffc8 100%);
    color: #05070b; border: none; border-radius: 11px;
    font-weight: 700; padding: 10px 20px;
    letter-spacing: 0.4px; text-transform: uppercase; font-size: 0.82rem;
    box-shadow: 0 4px 20px rgba(0, 212, 168, 0.28);
    transition: all 0.25s ease;
}
.stButton button p, [data-testid="stFormSubmitButton"] button p { color: #05070b; font-weight: 700; }
.stButton button::after, [data-testid="stFormSubmitButton"] button::after {
    content: ''; position: absolute; top: 0; left: -120%;
    width: 60%; height: 100%;
    background: linear-gradient(120deg, transparent, rgba(255, 255, 255, 0.45), transparent);
    transition: left 0.6s ease;
}
.stButton button:hover::after, [data-testid="stFormSubmitButton"] button:hover::after { left: 130%; }
.stButton button:hover, [data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-2px); color: #05070b;
    box-shadow: 0 8px 30px rgba(0, 212, 168, 0.5), 0 0 40px rgba(0, 212, 168, 0.3);
}
.stButton button:disabled { opacity: 0.4; transform: none; box-shadow: none; }
.stDownloadButton button {
    background: linear-gradient(135deg, #7c5cff 0%, #ff5c9f 100%);
    color: #fff; border: none; border-radius: 11px;
    font-weight: 700; padding: 10px 20px;
    text-transform: uppercase; letter-spacing: 0.4px; font-size: 0.82rem;
    box-shadow: 0 4px 22px rgba(124, 92, 255, 0.4);
    transition: all 0.25s ease;
}
.stDownloadButton button p { color: #fff; font-weight: 700; }
.stDownloadButton button:hover {
    transform: translateY(-2px); color: #fff;
    box-shadow: 0 8px 32px rgba(255, 92, 159, 0.45), 0 0 40px rgba(124, 92, 255, 0.35);
}

/* ====== FORMULARIO / EXPANDER / ALERTAS ====== */
[data-testid="stForm"] {
    background: var(--panel);
    border: 1px solid rgba(0, 212, 168, 0.28) !important;
    border-radius: 18px; padding: 20px;
    box-shadow: 0 0 40px rgba(0, 212, 168, 0.12);
}
[data-testid="stExpander"] details {
    background: rgba(13, 19, 29, 0.7);
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
}
.stAlert { border-radius: 12px !important; backdrop-filter: blur(10px); }
audio { width: 100%; border-radius: 12px; filter: drop-shadow(0 0 10px rgba(0, 212, 168, 0.15)); }
.stProgress > div > div > div > div { background: linear-gradient(90deg, #00d4a8, #00ffc8, #7c5cff); box-shadow: 0 0 18px rgba(0, 212, 168, 0.5); }
[data-testid="stImage"] img { border-radius: 12px; }

/* ====== SIDEBAR ====== */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #080d15 0%, #05070b 100%);
    border-right: 1px solid var(--line);
}
.ss-side-brand { text-align: center; padding: 10px 0 6px; }
.ss-side-brand .ss-logo { margin: 0 auto 10px; }
.ss-side-name { color: var(--neon); font-weight: 700; letter-spacing: 2px; }
.ss-side-ver { color: var(--muted); font-size: 0.72rem; letter-spacing: 2px; }
.ss-status { display: flex; justify-content: space-between; align-items: center; font-size: 0.84rem; padding: 7px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: #b9c6d6; }
.ss-dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.ss-on { background: var(--neon); box-shadow: 0 0 10px var(--neon); }
.ss-off { background: #ff5c5c; box-shadow: 0 0 10px #ff5c5c; }
.ss-mid { background: var(--amber); box-shadow: 0 0 10px var(--amber); }
.ss-hist { font-size: 0.8rem; color: #b9c6d6; padding: 7px 10px; margin-bottom: 6px; border-radius: 9px; background: rgba(0, 212, 168, 0.05); border: 1px solid rgba(0, 212, 168, 0.12); }
.ss-hist small { color: var(--muted); }

/* ====== LOGIN ====== */
.ss-login-head { text-align: center; margin: 7vh 0 22px; }
.ss-lock {
    width: 92px; height: 92px; margin: 0 auto 18px;
    display: grid; place-items: center; font-size: 2.6rem;
    border-radius: 26px;
    background: linear-gradient(135deg, rgba(0, 255, 200, 0.16), rgba(124, 92, 255, 0.24));
    border: 1px solid rgba(0, 255, 200, 0.4);
    animation: ss-pulse 2.4s ease-in-out infinite;
}
@keyframes ss-pulse {
    0%, 100% { box-shadow: 0 0 25px rgba(0, 255, 200, 0.3); }
    50% { box-shadow: 0 0 65px rgba(0, 255, 200, 0.6), 0 0 90px rgba(124, 92, 255, 0.35); }
}
.ss-login-head h1 {
    background: linear-gradient(135deg, #00ffc8, #00d4a8 45%, #a58cff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    font-size: 2.2rem; font-weight: 700; margin: 0; letter-spacing: -1px;
}
.ss-login-head p { color: var(--muted); margin-top: 6px; }
.ss-login-eq { display: flex; justify-content: center; align-items: flex-end; gap: 4px; height: 30px; margin-top: 18px; }
.ss-login-eq i { display: block; width: 4px; height: 30%; border-radius: 2px; background: linear-gradient(180deg, var(--neon), var(--violet)); animation: ss-eq 1.1s ease-in-out infinite; }

/* ====== FOOTER ====== */
.ss-footer {
    margin-top: 40px; padding: 18px 0 6px; text-align: center;
    color: #5d6878; font-size: 0.78rem; letter-spacing: 1px;
    border-top: 1px solid rgba(0, 212, 168, 0.12);
}
.ss-footer b { color: var(--neon2); }

/* ====== SCROLLBAR ====== */
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: #05070b; }
::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #00d4a8, #7c5cff); border-radius: 5px; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =========================================================
# HELPERS DE INTERFAZ
# =========================================================
def esc(x):
    return html.escape(str(x if x not in (None, "") else "—"), quote=True)


def _stretch(fn, *args, **kwargs):
    """Botón a ancho completo compatible con versiones nuevas y viejas de Streamlit."""
    try:
        return fn(*args, width="stretch", **kwargs)
    except TypeError:
        return fn(*args, use_container_width=True, **kwargs)


def btn(label, **kw):
    return _stretch(st.button, label, **kw)


def dl_btn(label, data, **kw):
    return _stretch(st.download_button, label, data, **kw)


def safe_image(src, width=None):
    if width:
        st.image(src, width=width)
        return
    for kw in ({"width": "stretch"}, {"use_container_width": True}, {"use_column_width": True}):
        try:
            st.image(src, **kw)
            return
        except Exception:
            continue
    st.image(src)


def html_block(markup):
    st.markdown(markup, unsafe_allow_html=True)


def section_header(icon, title, subtitle=""):
    html_block(
        f'<div class="ss-sec"><div class="ss-sec-icon">{icon}</div>'
        f'<div><div class="ss-sec-title">{title}</div>'
        f'<div class="ss-sec-sub">{subtitle}</div></div></div>'
    )


def sub(title):
    html_block(f'<div class="ss-sub">{title}</div>')


def stats_row(items):
    cells = "".join(
        f'<div class="ss-stat"><div class="ss-stat-v">{esc(v)}</div>'
        f'<div class="ss-stat-l">{esc(l)}</div></div>'
        for v, l in items
    )
    html_block(f'<div class="ss-stats">{cells}</div>')


def empty_state(icon, title, text):
    html_block(
        f'<div class="ss-empty"><div class="ss-empty-icon">{icon}</div>'
        f'<b>{title}</b>{text}</div>'
    )


def fmt_time(seconds):
    seconds = int(round(max(0.0, float(seconds or 0))))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def safe_name(name):
    name = re.sub(r'[\\/:*?"<>|]+', "_", str(name)).strip(" .")
    return name[:120] or "audio"


def log_history(tool, name):
    hist = st.session_state.setdefault("history", [])
    hist.insert(0, {"t": datetime.now().strftime("%H:%M"), "tool": tool, "name": name})
    del hist[10:]


def set_result(slot, data, name, label, mime, meta="", audio=True, tool=""):
    st.session_state[slot] = {"data": data, "name": name, "label": label,
                              "mime": mime, "meta": meta, "audio": audio}
    log_history(tool or label, name)


def show_result(slot):
    r = st.session_state.get(slot)
    if not r:
        return
    size = len(r["data"]) / 1048576
    meta = f" · {esc(r['meta'])}" if r.get("meta") else ""
    html_block(
        f'<div class="ss-card ss-result"><span class="ss-card-badge">LISTO</span>'
        f'<span class="ss-card-badge ss-badge-purple">{esc(r["label"])}</span>'
        f'<div class="ss-card-title">{esc(r["name"])}</div>'
        f'<div class="ss-card-meta">📦 {size:.1f} MB{meta}</div></div>'
    )
    if r.get("audio", True):
        st.audio(r["data"], format=r["mime"])
    dl_btn(f"⬇️ Descargar {r['label']}", r["data"], file_name=r["name"],
           mime=r["mime"], key=f"dl_{slot}")


# =========================================================
# ARCHIVOS Y FFMPEG
# =========================================================
def fid_of(up):
    return f"{up.name}|{up.size}|{getattr(up, 'file_id', '')}"


def save_upload(up):
    """Guarda el archivo subido en disco una sola vez por sesión."""
    paths = st.session_state.setdefault("_upload_paths", {})
    fid = fid_of(up)
    p = paths.get(fid)
    if p and os.path.exists(p):
        return p
    ext = os.path.splitext(up.name)[1].lower() or ".bin"
    p = os.path.join(tempfile.mkdtemp(prefix="ss_"), "input" + ext)
    with open(p, "wb") as fh:
        fh.write(up.getbuffer())
    paths[fid] = p
    return p


def run_cmd(cmd, timeout=1800):
    res = subprocess.run(cmd, capture_output=True, timeout=timeout)
    if res.returncode != 0:
        raise RuntimeError(res.stderr.decode("utf-8", "ignore")[-1500:])
    return res


@st.cache_data(show_spinner=False, max_entries=128)
def probe_audio(path):
    info = {"sr": 44100, "channels": 2, "duration": 0.0, "codec": "—", "kbps": None}
    if not FFPROBE_OK:
        return info
    try:
        res = run_cmd(["ffprobe", "-v", "error", "-print_format", "json",
                       "-show_format", "-show_streams", "-select_streams", "a:0", path], 60)
        j = json.loads(res.stdout.decode("utf-8", "ignore") or "{}")
        s = (j.get("streams") or [{}])[0]
        f = j.get("format") or {}
        info["sr"] = int(s.get("sample_rate") or info["sr"])
        info["channels"] = int(s.get("channels") or info["channels"])
        info["codec"] = s.get("codec_name") or "—"
        info["duration"] = float(f.get("duration") or s.get("duration") or 0.0)
        br = s.get("bit_rate") or f.get("bit_rate")
        info["kbps"] = int(int(br) / 1000) if br else None
        info["has_audio"] = bool(j.get("streams"))
    except Exception:
        pass
    return info


def volume_stats(path, start=0.0, length=None):
    """Pico y RMS (dBFS) con astats. Funciona también con audio en coma flotante."""
    cmd = ["ffmpeg", "-hide_banner", "-nostats"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    cmd += ["-i", path]
    if length:
        cmd += ["-t", f"{length:.3f}"]
    cmd += ["-vn", "-map", "0:a:0", "-af", "astats", "-f", "null", "-"]
    err = run_cmd(cmd).stderr.decode("utf-8", "ignore")

    def last(label):
        vals = re.findall(label + r": (-?[\d.]+|-inf)", err)
        if not vals or vals[-1] == "-inf":
            return None
        return float(vals[-1])

    return last("Peak level dB"), last("RMS level dB")


def silence_edges(path, thr_db, dur):
    """Devuelve (inicio, fin) quitando solo el silencio del principio y del final."""
    err = run_cmd(["ffmpeg", "-hide_banner", "-nostats", "-i", path,
                   "-af", f"silencedetect=n={thr_db}dB:d=0.1", "-f", "null", "-"]
                  ).stderr.decode("utf-8", "ignore")
    starts = [float(x) for x in re.findall(r"silence_start: (-?[\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    lead, tail = 0.0, dur
    if starts and starts[0] <= 0.05 and ends:
        lead = ends[0]
    if starts and (len(starts) > len(ends) or ends[-1] >= dur - 0.05):
        tail = starts[-1]
    lead, tail = max(0.0, lead - 0.05), min(dur, tail + 0.05)
    return (lead, tail) if tail - lead > 0.1 else (0.0, dur)


def ffmpeg_render(in_path, out_fmt, kbps=320, start=None, length=None, af=None, extra=None):
    """Exporta (o recorta) con ffmpeg y devuelve los bytes del resultado."""
    extra = list(extra or [])
    src_sr = probe_audio(in_path)["sr"]
    target_sr = int(extra[extra.index("-ar") + 1]) if "-ar" in extra else src_sr
    if out_fmt == "MP3":
        if target_sr > 48000:
            extra += ["-ar", "48000"]
            target_sr = 48000
        if target_sr < 32000:
            kbps = min(kbps, 160)
    out = os.path.join(tempfile.mkdtemp(prefix="ss_out_"), "out." + EXT_MAP[out_fmt])
    cmd = ["ffmpeg", "-y", "-hide_banner"]
    if start:
        cmd += ["-ss", f"{start:.3f}"]
    cmd += ["-i", in_path]
    if length:
        cmd += ["-t", f"{length:.3f}"]
    cmd += ["-vn", "-map", "0:a:0"]
    if af:
        cmd += ["-af", ",".join(af)]
    cmd += extra + FFMPEG_ARGS[out_fmt](kbps) + [out]
    run_cmd(cmd)
    with open(out, "rb") as fh:
        return fh.read()


def post_filters(normalize, peak_db, gain_db, fade_in, fade_out, length, limiter):
    """Volumen, normalización, limitador y fundidos (última etapa)."""
    af = []
    if normalize and peak_db is not None:
        af.append(f"volume={-0.5 - peak_db:.2f}dB")
    elif gain_db:
        af.append(f"volume={gain_db}dB")
    if limiter and not normalize:
        af.append("alimiter=limit=0.97:level=0")
    if fade_in > 0:
        af.append(f"afade=t=in:st=0:d={min(fade_in, length / 2):.3f}")
    if fade_out > 0:
        fo = min(fade_out, length / 2)
        af.append(f"afade=t=out:st={max(0.0, length - fo):.3f}:d={fo:.3f}")
    return af


def conv_extra(sr_opt, ch_opt):
    extra = []
    if sr_opt != "Original":
        extra += ["-ar", str(sr_opt)]
    if ch_opt == "Mono":
        extra += ["-ac", "1"]
    elif ch_opt == "Estéreo":
        extra += ["-ac", "2"]
    return extra


# ---------------------------------------------------------
# EFECTOS
# ---------------------------------------------------------
DENOISE_LEVELS = {"Desactivado": 0, "Suave": 6, "Media": 12, "Fuerte": 24}
SILENCE_MODES = ["No", "Solo al inicio y al final", "Todos (también en medio)"]


def _atempo_chain(t):
    parts = []
    while t > 2.0:
        parts.append("atempo=2.0")
        t /= 2.0
    while t < 0.5:
        parts.append("atempo=0.5")
        t /= 0.5
    if abs(t - 1.0) > 1e-3:
        parts.append(f"atempo={t:.5f}")
    return parts


def build_ffmpeg_filters(sr, denoise="Desactivado", remove_mid_silence=False,
                         silence_db=-45, silence_min=0.8,
                         bass_db=0, mid_db=0, treble_db=0,
                         speed=1.0, semitones=0, mono=False):
    f = [f"aresample={sr}"]
    nr = DENOISE_LEVELS.get(denoise, 0)
    if nr:
        f.append(f"afftdn=nr={nr}:nf=-40:tn=1")
    if remove_mid_silence:
        f.append(
            f"silenceremove=start_periods=1:start_threshold={silence_db}dB:"
            f"stop_periods=-1:stop_duration={silence_min}:"
            f"stop_threshold={silence_db}dB:stop_silence=0.15"
        )
    if bass_db:
        f.append(f"bass=g={bass_db}:f=100")
    if mid_db:
        f.append(f"equalizer=f=1000:t=q:w=1:g={mid_db}")
    if treble_db:
        f.append(f"treble=g={treble_db}:f=4000")
    tempo = speed
    if semitones:
        p = 2 ** (semitones / 12)
        f += [f"asetrate={int(round(sr * p))}", f"aresample={sr}"]
        tempo = speed / p
    f += _atempo_chain(tempo)
    if mono:
        f.append("pan=mono|c0=0.5*c0+0.5*c1")
    return f


def fx_process(path, info, o, out_fmt):
    """Efectos en streaming con ffmpeg: rápido y con poca memoria."""
    fx = os.path.join(tempfile.mkdtemp(prefix="ss_fx_"), "fx.wav")
    filters = build_ffmpeg_filters(
        info["sr"], o["denoise"], o["silence"].startswith("Todos"),
        o["sil_db"], o["sil_min"], o["bass"], o["mid"], o["treble"],
        o["speed"], o["semitones"], mono=o["mono"] and info["channels"] >= 2,
    )
    run_cmd(["ffmpeg", "-y", "-hide_banner", "-i", path, "-vn", "-map", "0:a:0",
             "-af", ",".join(filters), "-c:a", "pcm_f32le", fx])
    dur = probe_audio(fx)["duration"]
    start, end = 0.0, dur
    if o["silence"].startswith("Solo"):
        start, end = silence_edges(fx, o["sil_db"], dur)
    length = max(0.1, end - start)
    peak = volume_stats(fx, start, length)[0] if o["norm"] else None
    af = post_filters(o["norm"], peak, o["gain"], o["fade_in"], o["fade_out"], length, limiter=True)
    data = ffmpeg_render(fx, out_fmt, 320, start=start or None, length=length, af=af)
    return data, length


def merge_to_wav(paths, crossfade):
    out = os.path.join(tempfile.mkdtemp(prefix="ss_merge_"), "merged.wav")
    cmd = ["ffmpeg", "-y", "-hide_banner"]
    for p in paths:
        cmd += ["-i", p]
    parts = [f"[{i}:a:0]aformat=sample_rates=44100:channel_layouts=stereo[a{i}]"
             for i in range(len(paths))]
    if crossfade > 0:
        cur = "a0"
        for i in range(1, len(paths)):
            parts.append(f"[{cur}][a{i}]acrossfade=d={crossfade}:c1=tri:c2=tri[x{i}]")
            cur = f"x{i}"
    else:
        parts.append("".join(f"[a{i}]" for i in range(len(paths)))
                     + f"concat=n={len(paths)}:v=0:a=1[x]")
        cur = "x"
    cmd += ["-filter_complex", ";".join(parts), "-map", f"[{cur}]", "-c:a", "pcm_f32le", out]
    run_cmd(cmd)
    return out


# ---------------------------------------------------------
# ANÁLISIS
# ---------------------------------------------------------
NOTES = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]
MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def decode_for_analysis(path, sr_a):
    res = run_cmd(["ffmpeg", "-v", "error", "-i", path, "-vn", "-map", "0:a:0",
                   "-ac", "1", "-ar", str(sr_a), "-f", "f32le", "-"])
    return np.frombuffer(res.stdout, dtype=np.float32).copy()


def estimate_bpm(seg, sr):
    try:
        import librosa
        tempo, _ = librosa.beat.beat_track(y=seg, sr=sr)
        tempo = float(np.atleast_1d(tempo)[0])
        return int(round(tempo)) if tempo > 0 else None
    except Exception:
        return None


def estimate_key(seg, sr):
    if len(seg) < sr * 3:
        return None
    try:
        import librosa
        prof = librosa.feature.chroma_stft(y=seg, sr=sr).mean(axis=1)
        best, name = -2.0, None
        for i in range(12):
            for ref, mode in ((MAJOR, "mayor"), (MINOR, "menor")):
                c = np.corrcoef(prof, np.roll(ref, i))[0, 1]
                if c > best:
                    best, name = c, f"{NOTES[i]} {mode}"
        return name
    except Exception:
        return None


def detect_sections(mono, sr):
    hop = int(sr * 0.5)
    if hop <= 0 or len(mono) < hop * 8:
        return []
    n = len(mono) // hop
    rms = np.sqrt(np.mean(mono[: n * hop].reshape(n, hop) ** 2, axis=1))
    rms_norm = (rms - rms.min()) / (rms.max() - rms.min() + 1e-9)
    peaks, _ = find_peaks(rms_norm, height=0.6, distance=16)
    if len(peaks) == 0:
        return []
    top = sorted(peaks, key=lambda p: rms_norm[p], reverse=True)[:8]
    total = len(mono) / sr
    out = []
    for p in sorted(top):
        out.append({
            "tipo": "🎯 Estribillo" if rms_norm[p] > 0.8 else "🎵 Parte fuerte",
            "inicio": round(max(0.0, p * 0.5 - 2.0), 1),
            "fin": round(min(total, p * 0.5 + 8.0), 1),
            "energia": int(round(float(rms_norm[p]) * 100)),
        })
    return out


def envelope(mono, sr, n=2400):
    if len(mono) == 0:
        return np.array([0.0]), np.array([0.0]), np.array([0.0])
    chunk = max(1, len(mono) // n)
    m = (len(mono) // chunk) * chunk
    r = mono[:m].reshape(-1, chunk)
    x = (np.arange(r.shape[0]) * chunk + chunk / 2) / sr
    return x, r.min(axis=1), r.max(axis=1)


@st.cache_resource(show_spinner=False, max_entries=3)
def analyze_file(path):
    info = probe_audio(path)
    dur = info["duration"]
    sr_a = 22050 if dur <= 900 else 8000
    mono = decode_for_analysis(path, sr_a)
    if dur <= 0:
        dur = len(mono) / sr_a
    peak, rms = volume_stats(path)
    seg = mono[: sr_a * 120]
    return {
        "info": info, "dur": dur, "sr_a": sr_a,
        "peak": peak, "rms": rms,
        "bpm": estimate_bpm(seg, sr_a),
        "key": estimate_key(seg, sr_a),
        "sections": detect_sections(mono, sr_a),
        "env": envelope(mono, sr_a),
        "spec": mono[: sr_a * 90].copy(),
    }


def _style_axes(fig, ax):
    fig.patch.set_facecolor("#070b12")
    ax.set_facecolor("#070b12")
    ax.tick_params(colors="#6b7789", labelsize=8)
    ax.grid(True, color="#142231", linestyle="--", alpha=0.5)
    for spine in ax.spines.values():
        spine.set_color("#142231")


def draw_wave(x, lo, hi, dur, sel=None, sections=None, placeholder=False):
    fig, ax = plt.subplots(figsize=(12, 2.6), dpi=110)
    _style_axes(fig, ax)
    c = "#2a3a4a" if placeholder else "#00ffc8"
    lim = float(max(np.max(np.abs(lo)), np.max(np.abs(hi)), 1e-3)) * 1.25
    if not placeholder:
        ax.fill_between(x, lo * 1.18, hi * 1.18, color=c, alpha=0.10, lw=0)
    ax.fill_between(x, lo, hi, color=c, alpha=0.85, lw=0)
    ax.axhline(0, color="#12303a", lw=0.6)
    for s in sections or []:
        ax.axvspan(s["inicio"], s["fin"], color="#ff5c9f", alpha=0.07, lw=0)
    if sel:
        ax.axvspan(sel[0], sel[1], color="#7c5cff", alpha=0.25, lw=0)
        for v in sel:
            ax.axvline(v, color="#ff5c9f", lw=1.4)
    ax.set_xlim(0, max(dur, 0.1))
    ax.set_ylim(-lim, lim)
    ax.set_yticks([])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_time(v)))
    if placeholder:
        ax.text(0.5, 0.5, "Sube un audio para activar el analisis",
                transform=ax.transAxes, ha="center", va="center",
                color="#7a8699", fontsize=12, alpha=0.8)
    fig.tight_layout()
    return fig


def draw_spec(seg, sr):
    fig, ax = plt.subplots(figsize=(12, 3.0), dpi=110)
    _style_axes(fig, ax)
    if len(seg) > 2048:
        f, t, S = spectrogram(seg, fs=sr, nperseg=1024, noverlap=512)
        SdB = 10 * np.log10(S + 1e-10)
        ax.pcolormesh(t, f, SdB, cmap="magma", shading="auto", vmin=SdB.max() - 80, vmax=SdB.max())
        ax.set_ylim(0, min(sr / 2, 12000))
    ax.set_ylabel("Hz", color="#6b7789", fontsize=8)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt_time(v)))
    fig.tight_layout()
    return fig


def fake_wave(seconds=10, sr=100):
    n = seconds * sr
    t = np.linspace(0, seconds, n)
    w = (np.sin(2 * np.pi * 0.5 * t) * 0.3 + np.sin(2 * np.pi * 2 * t) * 0.2
         + np.sin(2 * np.pi * 5 * t) * 0.1) * (np.abs(np.sin(2 * np.pi * 0.15 * t)) + 0.3)
    w += np.random.default_rng(7).normal(0, 0.03, n)
    return w.astype(np.float32), sr


# ---------------------------------------------------------
# APIS EXTERNAS
# ---------------------------------------------------------
@st.cache_data(ttl=1800, show_spinner=False)
def search_itunes(query, limit=12):
    try:
        r = requests.get("https://itunes.apple.com/search",
                         params={"term": query, "entity": "song", "limit": limit}, timeout=8)
        return r.json().get("results", [])
    except Exception:
        return []


@st.cache_data(ttl=1800, show_spinner=False)
def search_itunes_sfx(query, limit=12):
    try:
        r = requests.get("https://itunes.apple.com/search",
                         params={"term": f"{query} sound effect", "entity": "song",
                                 "limit": limit * 2, "media": "music"}, timeout=8)
        results = r.json().get("results", [])
        excl = {"Pop", "Rock", "Hip-Hop/Rap", "Latin", "Country", "R&B/Soul",
                "Reggae", "Jazz", "Dance", "Electronic"}
        return [x for x in results if x.get("primaryGenreName", "") not in excl][:limit]
    except Exception:
        return []


@st.cache_data(ttl=900, show_spinner=False)
def search_radio(query, by_tag, country, limit):
    params = {"limit": limit, "hidebroken": "true", "order": "votes", "reverse": "true"}
    if query:
        params["tag" if by_tag else "name"] = query
    if country:
        params["countrycode"] = country
    for server in ("de1", "de2", "fi1"):
        try:
            r = requests.get(f"https://{server}.api.radio-browser.info/json/stations/search",
                             params=params, timeout=8)
            if r.ok:
                return r.json()
        except Exception:
            continue
    return []


def audd_recognize(clip_bytes):
    r = requests.post(
        "https://api.audd.io/",
        data={"api_token": AUDD_TOKEN, "return": "apple_music,spotify"},
        files={"file": ("clip.mp3", clip_bytes, "audio/mpeg")},
        timeout=40,
    )
    return r.json()


# =========================================================
# LOGIN
# =========================================================
def login_gate():
    if st.session_state.get("auth_ok"):
        return True
    html_block('<style>[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }</style>')
    bars = "".join(f'<i style="animation-delay:{i * 0.09:.2f}s"></i>' for i in range(14))
    html_block(
        '<div class="ss-login-head"><div class="ss-lock">✂️</div>'
        '<h1>SoundSnip Studio <span class="ss-badge-pro">PRO</span></h1>'
        '<p>Acceso privado · introduce tu contraseña para entrar</p>'
        f'<div class="ss-login-eq">{bars}</div></div>'
    )
    _, mid, _ = st.columns([1, 1.15, 1])
    with mid:
        lock_until = st.session_state.get("lock_until", 0.0)
        if time.time() < lock_until:
            st.error(f"🔒 Demasiados intentos. Espera {int(lock_until - time.time()) + 1} s y recarga.")
            return False
        with st.form("login_form"):
            pin = st.text_input("Contraseña", type="password", placeholder="••••")
            ok = _stretch(st.form_submit_button, "🔓 Entrar")
        if ok:
            if hmac.compare_digest(pin.strip().encode(), APP_PASSWORD.encode()):
                st.session_state["auth_ok"] = True
                st.session_state["fails"] = 0
                st.rerun()
            else:
                fails = st.session_state.get("fails", 0) + 1
                st.session_state["fails"] = fails
                if fails >= 5:
                    st.session_state["lock_until"] = time.time() + 60
                    st.session_state["fails"] = 0
                    st.error("🔒 Demasiados intentos. Bloqueado 60 segundos.")
                else:
                    st.error(f"Contraseña incorrecta · te quedan {5 - fails} intentos.")
    return False


if not login_gate():
    st.stop()

# =========================================================
# HERO
# =========================================================
_bars = "".join(f'<i style="animation-delay:{i * 0.08:.2f}s"></i>' for i in range(16))
html_block(f"""
<div class="ss-hero">
  <div class="ss-eq">{_bars}</div>
  <div class="ss-hero-top">
    <div class="ss-logo">✂️</div>
    <div>
      <h1>SoundSnip Studio<span class="ss-badge-pro">PRO</span></h1>
      <p>Tu estudio de audio en el navegador · edita, limpia, transforma y convierte en segundos</p>
    </div>
  </div>
  <div class="ss-chips">
    <span>🎧 BPM y tonalidad</span><span>🎛️ EQ · tono · velocidad</span>
    <span>🧹 Quita ruido y silencios</span><span>📦 Conversión por lotes</span>
    <span>🧩 Unión con crossfade</span><span>🎤 Reconocimiento</span><span>📻 Miles de radios</span>
  </div>
</div>
""")

tabs = st.tabs([
    "🎧 Editor", "🎛️ Estudio FX", "🧩 Unir audios", "🔗 Vídeo → Audio",
    "🎤 Reconocer", "🔊 Banco SFX", "🎙️ Música", "📻 Radio",
])


# =========================================================
# TAB 1 — EDITOR & ANÁLISIS
# =========================================================
def _set_range(a, b):
    st.session_state["ed_range"] = (float(a), float(b))


def render_editor():
    section_header("✂️", "Editor & Análisis",
                   "Detecta BPM, tonalidad y volumen, localiza las partes fuertes y exporta el fragmento exacto.")
    up = st.file_uploader("Sube audio o vídeo", type=AUDIO_TYPES + VIDEO_TYPES, key="editor_up")

    if up is None:
        w, s = fake_wave()
        x, lo, hi = envelope(w, s, n=1000)
        stats_row([("—", "Duración"), ("—", "Sample rate"), ("—", "BPM"),
                   ("—", "Tonalidad"), ("—", "Pico"), ("—", "Volumen medio")])
        fig = draw_wave(x, lo, hi, 10, placeholder=True)
        st.pyplot(fig)
        plt.close(fig)
        st.caption("💡 Formatos: WAV, MP3, FLAC, OGG, M4A, AAC, OPUS… y también vídeos (MP4, MOV, MKV). Máx. 200 MB.")
        return
    if not FFMPEG_OK:
        st.error("El editor necesita ffmpeg instalado.")
        return

    path = save_upload(up)
    try:
        with st.spinner("Analizando audio (BPM, tonalidad, energía)..."):
            A = analyze_file(path)
    except Exception as e:
        st.error("No se pudo leer este archivo.")
        with st.expander("Detalles técnicos"):
            st.code(str(e))
        return

    dur = A["dur"]
    max_t = max(0.1, float(np.floor(dur * 10) / 10))
    fid = fid_of(up)
    if st.session_state.get("ed_fid") != fid:
        st.session_state["ed_fid"] = fid
        st.session_state["ed_range"] = (0.0, min(30.0, max_t))
        st.session_state.pop("res_editor", None)
    a0, b0 = st.session_state["ed_range"]
    st.session_state["ed_range"] = (min(a0, max_t), min(max(b0, 0.0), max_t))

    st.audio(up)
    info = A["info"]
    stats_row([
        (fmt_time(dur), "Duración"),
        (f"{info['sr'] / 1000:.1f} kHz", "Sample rate"),
        ("Estéreo" if info["channels"] >= 2 else "Mono", "Canales"),
        (A["bpm"] or "—", "BPM"),
        (A["key"] or "—", "Tonalidad"),
        (f"{A['peak']:.1f} dB" if A["peak"] is not None else "—", "Pico"),
        (f"{A['rms']:.1f} dB" if A["rms"] is not None else "—", "Volumen medio"),
    ])
    if A["peak"] is not None and A["peak"] > -0.1:
        st.warning("⚠️ El audio llega a 0 dB: puede tener saturación (clipping).")

    view = st.radio("Vista", ["〰️ Onda", "🌈 Espectrograma"], horizontal=True,
                    key="ed_view", label_visibility="collapsed")
    if view.startswith("〰"):
        fig = draw_wave(*A["env"], dur, st.session_state["ed_range"], A["sections"])
    else:
        fig = draw_spec(A["spec"], A["sr_a"])
        st.caption("Espectrograma de los primeros 90 segundos.")
    st.pyplot(fig)
    plt.close(fig)

    if A["sections"]:
        sub("🎼 Partes con más energía · pulsa para seleccionarlas")
        cols = st.columns(4)
        for i, sec in enumerate(A["sections"]):
            with cols[i % 4]:
                html_block(
                    f'<div class="ss-card"><span class="ss-card-badge ss-badge-purple">{esc(sec["tipo"])}</span>'
                    f'<div class="ss-card-meta">⏱ {fmt_time(sec["inicio"])} → {fmt_time(sec["fin"])}<br>'
                    f'⚡ Energía {sec["energia"]}%</div></div>'
                )
                btn("🎯 Seleccionar", key=f"sec_{i}", on_click=_set_range,
                    args=(min(sec["inicio"], max_t), min(sec["fin"], max_t)))

    sub("✂️ Recorte y exportación")
    st.slider("Selección", 0.0, max_t, key="ed_range", step=0.1, format="%.1f s")
    a, b = st.session_state["ed_range"]
    length = b - a
    st.caption(f"Fragmento: **{fmt_time(a)} → {fmt_time(b)}** · {length:.1f} s")

    c1, c2, c3 = st.columns(3)
    out_fmt = c1.selectbox("Formato", FORMATS, key="ed_fmt")
    fade_in = c2.slider("Fade In (s)", 0.0, 5.0, 0.0, 0.1, key="ed_fi")
    fade_out = c3.slider("Fade Out (s)", 0.0, 5.0, 0.0, 0.1, key="ed_fo")
    normalize = st.checkbox("🔊 Normalizar el fragmento (pico −0.5 dB)", value=False, key="ed_norm")

    if length < 0.1:
        st.warning("Selecciona un fragmento de al menos 0.1 s.")
    elif btn("✂️ Recortar y exportar", key="ed_go"):
        try:
            with st.spinner("Exportando fragmento..."):
                peak = volume_stats(path, a, length)[0] if normalize else None
                af = post_filters(normalize, peak, 0, fade_in, fade_out, length, limiter=False)
                data = ffmpeg_render(path, out_fmt, 320, start=a or None, length=length, af=af)
            base = safe_name(os.path.splitext(up.name)[0])
            set_result("res_editor", data, f"{base}_{fmt_time(a).replace(':', '-')}.{EXT_MAP[out_fmt]}",
                       out_fmt, MIME_MAP[out_fmt], meta=f"{length:.1f} s", tool="Editor")
        except Exception as e:
            st.error("No se pudo exportar el fragmento.")
            with st.expander("Detalles técnicos"):
                st.code(str(e))
    show_result("res_editor")


with tabs[0]:
    render_editor()


# =========================================================
# TAB 2 — ESTUDIO FX (efectos, conversión, lote)
# =========================================================
FX_DEFAULTS = {
    "fx_speed": 1.0, "fx_semitones": 0, "fx_bass": 0, "fx_mid": 0, "fx_treble": 0,
    "fx_denoise": "Desactivado", "fx_silence": "No", "fx_sil_db": -45, "fx_sil_min": 0.8,
    "fx_fade_in": 0.0, "fx_fade_out": 0.0, "fx_gain": 0, "fx_norm": True, "fx_mono": False,
}
PRESETS = {
    "✏️ Personalizado": {},
    "🎙️ Voz clara / Podcast": {"fx_bass": -2, "fx_mid": 2, "fx_treble": 3, "fx_denoise": "Media",
                               "fx_silence": "Todos (también en medio)", "fx_mono": True},
    "🔊 Bass boost": {"fx_bass": 8, "fx_treble": 1},
    "⚡ Nightcore": {"fx_speed": 1.25, "fx_semitones": 3},
    "🌙 Slowed": {"fx_speed": 0.85, "fx_semitones": -2, "fx_bass": 3},
    "📻 Radio antigua": {"fx_bass": -12, "fx_mid": 6, "fx_treble": -8, "fx_mono": True},
    "🧹 Limpieza rápida": {"fx_denoise": "Media", "fx_silence": "Solo al inicio y al final"},
}


def apply_preset():
    values = dict(FX_DEFAULTS)
    values.update(PRESETS.get(st.session_state.get("fx_preset"), {}))
    for k, v in values.items():
        st.session_state[k] = v


def render_convert(path, info, name):
    c1, c2, c3, c4 = st.columns(4)
    fmt = c1.selectbox("Formato", FORMATS, key="cv_fmt")
    kbps = c2.selectbox("Bitrate (kbps)", BITRATES, key="cv_kbps", disabled=fmt not in LOSSY)
    sr_opt = c3.selectbox("Sample rate", ["Original", 48000, 44100, 32000, 22050], key="cv_sr")
    ch_opt = c4.selectbox("Canales", ["Original", "Estéreo", "Mono"], key="cv_ch")
    if btn("🚀 Convertir", key="cv_go"):
        try:
            with st.spinner("Convirtiendo..."):
                data = ffmpeg_render(path, fmt, kbps, extra=conv_extra(sr_opt, ch_opt))
            before = os.path.getsize(path) / 1048576
            after = len(data) / 1048576
            diff = (after - before) / before * 100 if before else 0
            base = safe_name(os.path.splitext(name)[0])
            set_result("res_fx", data, f"{base}.{EXT_MAP[fmt]}", fmt, MIME_MAP[fmt],
                       meta=f"{before:.1f} MB → {after:.1f} MB ({diff:+.0f}%)", tool="Conversión")
        except Exception as e:
            st.error("No se pudo convertir el archivo.")
            with st.expander("Detalles técnicos"):
                st.code(str(e))


def render_effects(path, info, name):
    for k, v in FX_DEFAULTS.items():
        st.session_state.setdefault(k, v)

    st.selectbox("🎨 Preset", list(PRESETS.keys()), key="fx_preset", on_change=apply_preset,
                 help="Carga una combinación de ajustes. Después puedes retocarlos.")

    sub("⏩ Velocidad y tono")
    c1, c2 = st.columns(2)
    c1.slider("Velocidad (x) · no cambia el tono", 0.5, 2.0, step=0.05, key="fx_speed")
    c2.slider("Tono (semitonos) · no cambia la velocidad", -12, 12, step=1, key="fx_semitones")

    sub("🎛️ Ecualizador")
    e1, e2, e3 = st.columns(3)
    e1.slider("Graves · 100 Hz (dB)", -12, 12, step=1, key="fx_bass")
    e2.slider("Medios · 1 kHz (dB)", -12, 12, step=1, key="fx_mid")
    e3.slider("Agudos · 4 kHz (dB)", -12, 12, step=1, key="fx_treble")

    sub("🧹 Limpieza")
    l1, l2 = st.columns(2)
    with l1:
        st.select_slider("Reducción de ruido", options=list(DENOISE_LEVELS.keys()), key="fx_denoise")
        st.caption("Ideal para ruido constante: soplido, zumbido, ventilador.")
    with l2:
        st.selectbox("Quitar silencios", SILENCE_MODES, key="fx_silence")
    if st.session_state["fx_silence"] != "No":
        s1, s2 = st.columns(2)
        s1.slider("Umbral de silencio (dB)", -70, -20, step=1, key="fx_sil_db",
                  help="Lo que suene por debajo de este volumen se considera silencio.")
        s2.slider("Silencio mínimo a quitar (s)", 0.2, 3.0, step=0.1, key="fx_sil_min",
                  disabled=st.session_state["fx_silence"].startswith("Solo"))

    sub("🔊 Volumen, fundidos y salida")
    v1, v2, v3 = st.columns(3)
    with v1:
        st.slider("Fade In (s)", 0.0, 5.0, step=0.1, key="fx_fade_in")
        st.slider("Ganancia (dB)", -20, 20, step=1, key="fx_gain",
                  disabled=st.session_state["fx_norm"])
    with v2:
        st.slider("Fade Out (s)", 0.0, 5.0, step=0.1, key="fx_fade_out")
        out_fmt = st.selectbox("Formato de salida", FORMATS, key="fx_fmt")
    with v3:
        st.checkbox("🔊 Normalizar (pico −0.5 dB)", key="fx_norm")
        st.checkbox("🎚️ Convertir a mono", key="fx_mono", disabled=info["channels"] < 2)

    if info["duration"] > 1800:
        st.warning(f"Este audio dura {fmt_time(info['duration'])}. Procesarlo puede tardar varios minutos.")

    if btn("🎛️ Procesar audio", key="fx_go"):
        o = {
            "speed": st.session_state["fx_speed"], "semitones": st.session_state["fx_semitones"],
            "bass": st.session_state["fx_bass"], "mid": st.session_state["fx_mid"],
            "treble": st.session_state["fx_treble"], "denoise": st.session_state["fx_denoise"],
            "silence": st.session_state["fx_silence"], "sil_db": st.session_state["fx_sil_db"],
            "sil_min": st.session_state["fx_sil_min"], "fade_in": st.session_state["fx_fade_in"],
            "fade_out": st.session_state["fx_fade_out"], "gain": st.session_state["fx_gain"],
            "norm": st.session_state["fx_norm"], "mono": st.session_state["fx_mono"],
        }
        try:
            with st.spinner("Aplicando efectos..."):
                data, new_len = fx_process(path, info, o, out_fmt)
            base = safe_name(os.path.splitext(name)[0])
            set_result("res_fx", data, f"{base}_fx.{EXT_MAP[out_fmt]}", out_fmt, MIME_MAP[out_fmt],
                       meta=f"Duración {fmt_time(info['duration'])} → {fmt_time(new_len)}", tool="Efectos")
        except Exception as e:
            st.error("No se pudo procesar el audio.")
            with st.expander("Detalles técnicos"):
                st.code(str(e))


def render_batch():
    ups = st.file_uploader("Sube varios archivos", type=AUDIO_TYPES + VIDEO_TYPES,
                           accept_multiple_files=True, key="batch_up")
    c1, c2, c3, c4 = st.columns(4)
    fmt = c1.selectbox("Formato", FORMATS, key="b_fmt")
    kbps = c2.selectbox("Bitrate (kbps)", BITRATES, key="b_kbps", disabled=fmt not in LOSSY)
    sr_opt = c3.selectbox("Sample rate", ["Original", 48000, 44100, 32000, 22050], key="b_sr")
    ch_opt = c4.selectbox("Canales", ["Original", "Estéreo", "Mono"], key="b_ch")
    if not ups:
        empty_state("📦", "Conversión por lotes", "Sube todos los archivos a la vez y descárgalos en un ZIP.")
        return
    total = sum(u.size for u in ups) / 1048576
    st.caption(f"{len(ups)} archivos · {total:.1f} MB en total")
    if btn(f"📦 Convertir {len(ups)} archivos", key="b_go"):
        prog = st.progress(0.0)
        buf = io.BytesIO()
        errors, used = [], set()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for i, u in enumerate(ups):
                try:
                    data = ffmpeg_render(save_upload(u), fmt, kbps, extra=conv_extra(sr_opt, ch_opt))
                    base = safe_name(os.path.splitext(u.name)[0])
                    fname, n = f"{base}.{EXT_MAP[fmt]}", 2
                    while fname in used:
                        fname, n = f"{base} ({n}).{EXT_MAP[fmt]}", n + 1
                    used.add(fname)
                    zf.writestr(fname, data)
                except Exception:
                    errors.append(u.name)
                prog.progress((i + 1) / len(ups), text=f"{i + 1}/{len(ups)} · {u.name}")
        if errors:
            st.warning("No se pudieron convertir: " + ", ".join(errors))
        if len(used):
            set_result("res_batch", buf.getvalue(), "soundsnip_lote.zip", "ZIP", "application/zip",
                       meta=f"{len(used)} archivos en {fmt}", audio=False, tool="Lote")
    show_result("res_batch")


def render_fx_tab():
    section_header("🎛️", "Estudio FX",
                   "Efectos profesionales, conversión de formato y procesamiento por lotes.")
    if not FFMPEG_OK:
        st.error("Esta sección necesita ffmpeg instalado.")
        return
    mode = st.radio("Modo", ["🎚️ Efectos", "🔄 Convertir", "📦 Lote"], horizontal=True,
                    key="fx_mode", label_visibility="collapsed")
    if mode.startswith("📦"):
        render_batch()
        return
    up = st.file_uploader("Sube audio o vídeo", type=AUDIO_TYPES + VIDEO_TYPES, key="fx_up")
    if up is None:
        empty_state("🎛️", "Sube un archivo para empezar",
                    "Presets, ecualizador, tono, velocidad, reducción de ruido y más.")
        return
    fid = fid_of(up)
    if st.session_state.get("fx_fid") != fid:
        st.session_state["fx_fid"] = fid
        st.session_state.pop("res_fx", None)
    path = save_upload(up)
    info = probe_audio(path)
    stats_row([
        (fmt_time(info["duration"]), "Duración"),
        (f"{info['sr'] / 1000:.1f} kHz", "Sample rate"),
        ("Estéreo" if info["channels"] >= 2 else "Mono", "Canales"),
        (str(info["codec"]).upper(), "Códec"),
        (f"{info['kbps']} kbps" if info["kbps"] else "—", "Bitrate"),
        (f"{up.size / 1048576:.1f} MB", "Tamaño"),
    ])
    if mode.startswith("🔄"):
        render_convert(path, info, up.name)
    else:
        render_effects(path, info, up.name)
    show_result("res_fx")


with tabs[1]:
    render_fx_tab()


# =========================================================
# TAB 3 — UNIR AUDIOS
# =========================================================
def render_merge():
    section_header("🧩", "Unir audios",
                   "Encadena varias pistas en un solo archivo, con fundido cruzado entre ellas.")
    if not FFMPEG_OK:
        st.error("Esta sección necesita ffmpeg instalado.")
        return
    ups = st.file_uploader("Sube 2 o más archivos", type=AUDIO_TYPES + VIDEO_TYPES,
                           accept_multiple_files=True, key="mg_up")
    if not ups or len(ups) < 2:
        empty_state("🧩", "Sube al menos 2 archivos", "Ideal para mixtapes, podcasts por partes o recopilatorios.")
        return
    labels = [f"{i + 1}. {u.name}" for i, u in enumerate(ups)]
    order = st.multiselect("Orden de reproducción", labels, default=labels,
                           help="Quita un archivo y vuelve a añadirlo para moverlo al final.")
    c1, c2, c3 = st.columns(3)
    cf = c1.slider("Fundido cruzado (s)", 0.0, 10.0, 2.0, 0.5, key="mg_cf")
    fmt = c2.selectbox("Formato", FORMATS, key="mg_fmt")
    kbps = c3.selectbox("Bitrate (kbps)", BITRATES, key="mg_kbps", disabled=fmt not in LOSSY)
    norm = st.checkbox("🔊 Normalizar el resultado", value=True, key="mg_norm")

    if len(order) < 2:
        st.warning("Deja al menos 2 archivos en el orden.")
    elif btn(f"🧩 Unir {len(order)} pistas", key="mg_go"):
        try:
            with st.spinner("Uniendo pistas..."):
                paths = [save_upload(ups[labels.index(l)]) for l in order]
                merged = merge_to_wav(paths, cf)
                length = probe_audio(merged)["duration"]
                peak = volume_stats(merged)[0] if norm else None
                af = post_filters(norm, peak, 0, 0, 0, length, limiter=True)
                data = ffmpeg_render(merged, fmt, kbps, af=af)
            set_result("res_merge", data, f"soundsnip_union.{EXT_MAP[fmt]}", fmt, MIME_MAP[fmt],
                       meta=f"{len(order)} pistas · {fmt_time(length)}", tool="Unir")
        except Exception as e:
            st.error("No se pudieron unir las pistas. Si usas fundido cruzado, "
                     "comprueba que cada pista dure más que el fundido.")
            with st.expander("Detalles técnicos"):
                st.code(str(e))
    show_result("res_merge")


with tabs[2]:
    render_merge()


# =========================================================
# TAB 4 — VÍDEO → AUDIO
# =========================================================
def _video_upload_mode(fmt, kbps, qual):
    st.caption("Sube un vídeo y te devolvemos solo la pista de audio.")
    vid = st.file_uploader("Vídeo", type=VIDEO_TYPES, key="va_upload")
    if not vid:
        empty_state("🎬", "Sube un vídeo", "MP4, MOV, MKV, WEBM, AVI · puedes extraer solo un fragmento.")
        return
    path = save_upload(vid)
    info = probe_audio(path)
    dur = info["duration"]
    fid = fid_of(vid)
    if st.session_state.get("va_fid") != fid:
        st.session_state["va_fid"] = fid
        st.session_state.pop("res_video", None)
        st.session_state["va_range"] = (0.0, max(0.1, float(np.floor(dur * 10) / 10)))
    if not info.get("has_audio", True):
        st.error("Este vídeo no tiene pista de audio.")
        return
    stats_row([(fmt_time(dur), "Duración"), (f"{info['sr'] / 1000:.1f} kHz", "Sample rate"),
               (str(info["codec"]).upper(), "Códec audio"), (f"{vid.size / 1048576:.1f} MB", "Tamaño")])
    start, length = None, None
    rng = st.session_state.get("va_range")
    if not isinstance(rng, (tuple, list)) or len(rng) != 2:
        st.session_state["va_range"] = (0.0, max(0.1, float(np.floor(dur * 10) / 10)))
    if st.checkbox("✂️ Extraer solo un fragmento", key="va_cut") and dur > 0.2:
        st.slider("Fragmento", 0.0, max(0.1, float(np.floor(dur * 10) / 10)),
                  key="va_range", step=0.1, format="%.1f s")
        a, b = st.session_state["va_range"]
        start, length = (a or None), max(0.1, b - a)
        st.caption(f"{fmt_time(a)} → {fmt_time(b)}")
    if btn("🎬 Extraer audio del vídeo", key="va_btn_up"):
        try:
            with st.spinner("Extrayendo audio..."):
                data = ffmpeg_render(path, fmt, kbps, start=start, length=length)
            base = safe_name(os.path.splitext(vid.name)[0])
            set_result("res_video", data, f"{base}.{EXT_MAP[fmt]}", fmt, MIME_MAP[fmt],
                       meta=qual, tool="Vídeo → Audio")
        except Exception as e:
            st.error("No se pudo extraer el audio de este archivo.")
            with st.expander("Detalles técnicos"):
                st.code(str(e))


def _video_link_mode(fmt, kbps, qual):
    st.caption("YouTube, Vimeo, SoundCloud… · uso personal.")
    st.caption("🟢 Motor JS activo" if DENO_PATH else "🔴 Motor JS no disponible")
    video_url = st.text_input("🔗 Enlace del vídeo:", placeholder="https://www.youtube.com/watch?v=...",
                              key="va_url")
    if video_url and btn("🎬 Extraer audio", key="va_btn_url"):
        try:
            import yt_dlp
            tmpdir = tempfile.mkdtemp()
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s"),
                "noplaylist": True, "quiet": True, "no_warnings": True,
                "postprocessors": [{"key": "FFmpegExtractAudio",
                                    "preferredcodec": CODEC_MAP[fmt],
                                    "preferredquality": str(kbps)}],
            }
            if DENO_PATH:
                ydl_opts["js_runtimes"] = {"deno": {"path": DENO_PATH}}
            with st.spinner("🎧 Procesando el vídeo..."):
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=True)
            files = [f for f in os.listdir(tmpdir) if f.endswith("." + EXT_MAP[fmt])]
            if not files:
                raise RuntimeError("yt-dlp terminó pero no generó el archivo de audio.")
            with open(os.path.join(tmpdir, files[0]), "rb") as fh:
                data = fh.read()
            title = safe_name(info.get("title", "audio"))
            set_result("res_video", data, f"{title}.{EXT_MAP[fmt]}", fmt, MIME_MAP[fmt],
                       meta=f"{info.get('uploader', '—')} · {fmt_time(info.get('duration', 0))}",
                       tool="Enlace → Audio")
        except Exception as e:
            err = str(e).lower()
            if "not a bot" in err or "sign in" in err or "403" in err:
                st.error("🤖 La plataforma está bloqueando esta conexión. Prueba más tarde o usa **Subir vídeo**.")
            elif "private" in err or "unavailable" in err:
                st.error("🔒 El vídeo es privado o no está disponible.")
            elif "unsupported url" in err:
                st.error("🔗 Ese enlace no es de una plataforma soportada.")
            else:
                st.error("😕 No se pudo descargar este vídeo.")
            with st.expander("Detalles técnicos"):
                st.code(str(e))


def render_video():
    section_header("🔗", "Vídeo → Audio", "Extrae la pista de audio de cualquier vídeo, entera o solo un fragmento.")
    if not FFMPEG_OK:
        st.error("Esta sección necesita ffmpeg instalado.")
        return
    c1, c2 = st.columns(2)
    fmt = c1.selectbox("Formato de salida", FORMATS, key="va_fmt")
    qual = c2.selectbox("Calidad", [f"{b} kbps" for b in BITRATES], key="va_qual", disabled=fmt not in LOSSY)
    kbps = int(qual.split()[0])
    if LINK_MODE:
        t_up, t_link = st.tabs(["📁 Subir vídeo", "🌐 Desde enlace"])
        with t_up:
            _video_upload_mode(fmt, kbps, qual)
        with t_link:
            _video_link_mode(fmt, kbps, qual)
    else:
        _video_upload_mode(fmt, kbps, qual)
    show_result("res_video")


with tabs[3]:
    render_video()


# =========================================================
# TAB 5 — RECONOCER CANCIÓN
# =========================================================
def _song_card(title, artist, album, extra_lines, art=None, preview=None, links=None, badge="MATCH"):
    c1, c2 = st.columns([1, 3])
    with c1:
        if art:
            safe_image(art)
    with c2:
        lk = " · ".join(f'<a href="{esc(u)}" target="_blank">{esc(t)}</a>' for t, u in (links or []) if u)
        html_block(
            f'<div class="ss-card"><span class="ss-card-badge">{badge}</span>'
            f'<div class="ss-card-title">{esc(title)}</div>'
            f'<div class="ss-card-meta">👤 {esc(artist)}<br>💿 {esc(album)}'
            + "".join(f"<br>{l}" for l in extra_lines)
            + (f"<br>{lk}" if lk else "") + "</div></div>"
        )
        if preview:
            st.audio(preview)


def render_recognize():
    section_header("🎤", "Reconocer canción", "Sube un fragmento y descubre qué canción es.")
    if AUDD_TOKEN:
        html_block('<span class="ss-card-badge">Reconocimiento acústico activo</span>')
    else:
        st.info("ℹ️ **Modo básico:** busca coincidencias por el nombre del archivo. "
                "Para reconocer el sonido de verdad, añade la clave `AUDD_API_TOKEN` en los secretos.")
    frag = st.file_uploader("Fragmento de audio o vídeo", type=AUDIO_TYPES + VIDEO_TYPES, key="shazam_up")
    if not frag:
        empty_state("🎤", "Sube un fragmento", "Con 10-15 segundos suele bastar.")
        return
    st.audio(frag)

    if AUDD_TOKEN and FFMPEG_OK:
        path = save_upload(frag)
        dur = probe_audio(path)["duration"]
        start = 0.0
        if dur > 20:
            start = st.slider("Analizar a partir de (s)", 0.0, float(max(0.0, dur - 12)), 0.0, 1.0, key="rc_start")
        if btn("🔎 Identificar canción", key="rc_go"):
            try:
                with st.spinner("Escuchando la huella acústica..."):
                    clip = ffmpeg_render(path, "MP3", 128, start=start or None, length=15, extra=["-ac", "1"])
                    j = audd_recognize(clip)
                if j.get("status") == "success" and j.get("result"):
                    r = j["result"]
                    am = r.get("apple_music") or {}
                    art = ((am.get("artwork") or {}).get("url") or "").replace("{w}", "300").replace("{h}", "300")
                    prev = ((am.get("previews") or [{}])[0]).get("url")
                    sp = ((r.get("spotify") or {}).get("external_urls") or {}).get("spotify")
                    st.success("🎯 ¡Canción reconocida!")
                    _song_card(r.get("title"), r.get("artist"), r.get("album"),
                               [f"📅 {esc(r.get('release_date'))}", f"🏷️ {esc(r.get('label'))}"],
                               art or None, prev,
                               [("Escuchar", r.get("song_link")), ("Spotify", sp), ("Apple Music", am.get("url"))])
                    log_history("Reconocer", f"{r.get('artist')} – {r.get('title')}")
                elif j.get("status") == "error":
                    st.error(f"Error del servicio: {esc((j.get('error') or {}).get('error_message'))}")
                else:
                    st.warning("No se ha reconocido. Prueba con otro fragmento más limpio o más largo.")
            except Exception as e:
                st.error("No se pudo contactar con el servicio de reconocimiento.")
                with st.expander("Detalles técnicos"):
                    st.code(str(e))
        return

    if btn("🔎 Buscar por nombre del archivo", key="rc_basic"):
        hint = os.path.splitext(frag.name)[0].replace("_", " ").replace("-", " ")
        with st.spinner("Buscando..."):
            results = search_itunes(hint, limit=3)
        if results:
            st.success("Posibles coincidencias")
            for r in results:
                _song_card(r.get("trackName"), r.get("artistName"), r.get("collectionName"),
                           [f"📅 {esc((r.get('releaseDate') or '—')[:10])}"],
                           (r.get("artworkUrl100") or "").replace("100x100", "300x300") or None,
                           r.get("previewUrl"), [("Apple Music", r.get("trackViewUrl"))], badge="POSIBLE")
        else:
            st.warning("Sin coincidencias. Renombra el archivo con el título de la canción.")


with tabs[4]:
    render_recognize()


# =========================================================
# TAB 6 — BANCO SFX
# =========================================================
SFX_CATS = {
    "🌧 Lluvia": "rain", "⚡ Trueno": "thunder", "🌊 Mar": "ocean waves", "🐦 Pájaros": "birds",
    "🚗 Tráfico": "traffic", "🚪 Puerta": "door", "👏 Aplausos": "applause", "👣 Pasos": "footsteps",
    "🔥 Fuego": "fire crackling", "💥 Explosión": "explosion", "🎮 Arcade": "arcade", "🔔 Campana": "bell",
}


def _set_sfx(q):
    st.session_state["sfx_q"] = q


def render_sfx():
    section_header("🔊", "Banco SFX", "Encuentra efectos de sonido por categoría o palabra clave.")
    st.session_state.setdefault("sfx_q", "rain")
    names = list(SFX_CATS.keys())
    for row in range(0, len(names), 6):
        cols = st.columns(6)
        for i, cat in enumerate(names[row:row + 6]):
            with cols[i]:
                btn(cat, key=f"cat_{row + i}", on_click=_set_sfx, args=(SFX_CATS[cat],))
    c1, c2 = st.columns([4, 1])
    q = c1.text_input("🔍 Buscar efecto (en inglés funciona mejor)", key="sfx_q")
    limit = c2.selectbox("Resultados", [8, 12, 20], index=1, key="sfx_lim")
    if not q:
        return
    with st.spinner("Buscando efectos..."):
        results = search_itunes_sfx(q, limit=limit)
    if not results:
        st.warning("Sin resultados. Prueba otra palabra (rain, door, crowd, whoosh...).")
        return
    st.caption(f"🎧 {len(results)} efectos · vistas previas de 30 s")
    cols = st.columns(2)
    for i, item in enumerate(results):
        with cols[i % 2]:
            html_block(
                f'<div class="ss-card"><span class="ss-card-badge">SFX</span>'
                f'<span class="ss-card-badge ss-badge-purple">{esc(item.get("primaryGenreName"))}</span>'
                f'<div class="ss-card-title">{esc(item.get("trackName"))}</div>'
                f'<div class="ss-card-meta">🎬 {esc(item.get("artistName"))}</div></div>'
            )
            if item.get("previewUrl"):
                st.audio(item["previewUrl"])


with tabs[5]:
    render_sfx()


# =========================================================
# TAB 7 — BUSCADOR DE MÚSICA
# =========================================================
def render_music():
    section_header("🎙️", "Buscador de música", "Canciones, artistas y álbumes con portada, datos y vista previa.")
    c1, c2 = st.columns([4, 1])
    q = c1.text_input("🔍 Canción, artista o álbum", value="Coldplay", key="mu_q")
    limit = c2.selectbox("Resultados", [6, 9, 12, 24], index=1, key="mu_lim")
    if not q:
        return
    with st.spinner("Buscando..."):
        tracks = search_itunes(q, limit=limit)
    if not tracks:
        st.warning("Sin resultados.")
        return
    st.caption(f"🎧 {len(tracks)} resultados · vista previa de 30 s (límite de Apple)")
    cols = st.columns(3)
    for i, t in enumerate(tracks):
        with cols[i % 3]:
            art = (t.get("artworkUrl100") or "").replace("100x100", "400x400")
            if art:
                safe_image(art)
            ms = t.get("trackTimeMillis") or 0
            link = t.get("trackViewUrl")
            html_block(
                f'<div class="ss-card"><span class="ss-card-badge ss-badge-purple">{esc(t.get("primaryGenreName"))}</span>'
                f'<span class="ss-card-badge ss-badge-ghost">⏱ {fmt_time(ms / 1000)}</span>'
                f'<div class="ss-card-title">{esc(t.get("trackName"))}</div>'
                f'<div class="ss-card-meta">👤 {esc(t.get("artistName"))}<br>💿 {esc(t.get("collectionName"))}'
                f'<br>📅 {esc((t.get("releaseDate") or "—")[:4])}'
                + (f'<br><a href="{esc(link)}" target="_blank">Abrir en Apple Music ↗</a>' if link else "")
                + "</div></div>"
            )
            if t.get("previewUrl"):
                st.audio(t["previewUrl"])


with tabs[6]:
    render_music()


# =========================================================
# TAB 8 — RADIO
# =========================================================
COUNTRIES = {"🌍 Todos": "", "🇪🇸 España": "ES", "🇲🇽 México": "MX", "🇦🇷 Argentina": "AR",
             "🇨🇴 Colombia": "CO", "🇨🇱 Chile": "CL", "🇺🇸 EE. UU.": "US", "🇬🇧 Reino Unido": "GB",
             "🇫🇷 Francia": "FR", "🇩🇪 Alemania": "DE", "🇮🇹 Italia": "IT", "🇧🇷 Brasil": "BR"}


def _toggle_fav(station):
    favs = st.session_state.setdefault("radio_favs", {})
    uid = station.get("stationuuid")
    if uid in favs:
        favs.pop(uid)
    else:
        favs[uid] = station


def _station_card(s, prefix):
    stream = s.get("url_resolved") or s.get("url")
    if not stream:
        return
    tags = [t.strip() for t in (s.get("tags") or "").split(",") if t.strip()][:5]
    tags_html = " ".join(f'<span class="ss-card-badge ss-badge-ghost">{esc(t)}</span>' for t in tags)
    home = s.get("homepage")
    html_block(
        f'<div class="ss-card"><span class="ss-card-badge">LIVE</span>'
        f'<span class="ss-card-badge ss-badge-orange">{esc(s.get("codec"))} · {esc(s.get("bitrate"))} kbps</span>'
        f'<span class="ss-card-badge ss-badge-red">❤ {esc(s.get("votes", 0))}</span>'
        f'<div class="ss-card-title">{esc(s.get("name"))}</div>'
        f'<div class="ss-card-meta">🌍 {esc(s.get("country"))}'
        + (f' · <a href="{esc(home)}" target="_blank">Web ↗</a>' if home else "")
        + f'</div><div style="margin-top:8px;">{tags_html}</div></div>'
    )
    c1, c2 = st.columns([6, 1])
    with c1:
        st.audio(stream)
    with c2:
        is_fav = s.get("stationuuid") in st.session_state.get("radio_favs", {})
        btn("★" if is_fav else "☆", key=f"{prefix}_{s.get('stationuuid')}",
            on_click=_toggle_fav, args=(s,), help="Guardar en favoritas")


def render_radio():
    section_header("📻", "Radio en directo", "Miles de emisoras de todo el mundo por nombre, género o país.")
    favs = st.session_state.get("radio_favs", {})
    if favs:
        with st.expander(f"⭐ Mis favoritas ({len(favs)})"):
            for s in list(favs.values()):
                _station_card(s, "favlist")
    c1, c2, c3, c4 = st.columns([3, 1.3, 1.5, 1])
    q = c1.text_input("🔍 Emisora, género o temática", value="jazz", key="rd_q",
                      placeholder="jazz · rock · news · lofi · flamenco...")
    by = c2.selectbox("Buscar por", ["Temática", "Nombre"], key="rd_by")
    country = c3.selectbox("País", list(COUNTRIES.keys()), key="rd_country")
    limit = c4.selectbox("Máx.", [10, 20, 40], index=1, key="rd_lim")
    if not q and not COUNTRIES[country]:
        st.info("Escribe algo o elige un país.")
        return
    with st.spinner("Conectando con el directorio global..."):
        stations = search_radio(q.strip(), by == "Temática", COUNTRIES[country], limit)
    html_block(
        f'<div class="ss-stat-box"><div class="ss-stat-v">{len(stations)}</div>'
        f'<div class="ss-stat-l">emisoras encontradas</div></div>'
    )
    if not stations:
        st.warning("Sin emisoras. Prueba: jazz, rock, news, pop, lofi, classical...")
        return
    for s in stations:
        _station_card(s, "fav")


with tabs[7]:
    render_radio()


# =========================================================
# SIDEBAR
# =========================================================
def _status(label, state):
    cls = {"on": "ss-on", "off": "ss-off", "mid": "ss-mid"}[state]
    return f'<div class="ss-status"><span>{label}</span><span class="ss-dot {cls}"></span></div>'


with st.sidebar:
    html_block(
        '<div class="ss-side-brand"><div class="ss-logo">✂️</div>'
        '<div class="ss-side-name">SOUNDSNIP PRO</div>'
        f'<div class="ss-side-ver">{APP_VERSION}</div></div>'
    )
    html_block('<div class="ss-sub">Estado</div>')
    html_block(
        _status("Motor de audio (ffmpeg)", "on" if FFMPEG_OK else "off")
        + _status("Reconocimiento acústico", "on" if AUDD_TOKEN else "mid")
        + (_status("Descarga por enlace", "on" if DENO_PATH else "mid") if LINK_MODE else "")
    )
    html_block('<div class="ss-sub">Actividad reciente</div>')
    hist = st.session_state.get("history", [])
    if hist:
        html_block("".join(
            f'<div class="ss-hist">{esc(h["name"])}<br><small>{esc(h["tool"])} · {esc(h["t"])}</small></div>'
            for h in hist
        ))
    else:
        st.caption("Aquí verás lo que vayas procesando.")
    st.write("")
    if _stretch(st.button, "🔒 Cerrar sesión", key="logout"):
        for k in ("auth_ok", "fails"):
            st.session_state.pop(k, None)
        st.rerun()

html_block(
    f'<div class="ss-footer">✂️ <b>SoundSnip Studio PRO</b> · {APP_VERSION} · '
    'Procesado privado en tu sesión · Hecho con 💚 y mucho neón</div>'
)
