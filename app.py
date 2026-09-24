import streamlit as st
import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt
import requests
import io
import os
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from scipy.signal import find_peaks

# =========================================================
# CONFIGURACIÓN INICIAL (debe ser el primer comando de Streamlit)
# =========================================================
st.set_page_config(
    page_title="SoundSnip Studio PRO",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ---------------------------------------------------------
# SETUP DE DENO (runtime JS para yt-dlp) — versión FIJA 2.6.5
# ---------------------------------------------------------
@st.cache_resource(show_spinner=False)
def setup_deno():
    """Descarga Deno v2.6.5 una sola vez (sin depender de wget/unzip)."""
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


DENO_PATH = setup_deno()
FFMPEG_OK = shutil.which("ffmpeg") is not None

# Mapas de formato para Video → Audio (OGG en yt-dlp se llama "vorbis")
CODEC_MAP = {"MP3": "mp3", "WAV": "wav", "FLAC": "flac", "M4A": "m4a", "OGG": "vorbis"}
EXT_MAP = {"MP3": "mp3", "WAV": "wav", "FLAC": "flac", "M4A": "m4a", "OGG": "ogg"}
MIME_MAP = {"MP3": "audio/mpeg", "WAV": "audio/wav", "FLAC": "audio/flac",
            "M4A": "audio/mp4", "OGG": "audio/ogg"}
FFMPEG_ARGS = {
    "MP3": lambda q: ["-c:a", "libmp3lame", "-b:a", f"{q}k"],
    "M4A": lambda q: ["-c:a", "aac", "-b:a", f"{q}k"],
    "OGG": lambda q: ["-c:a", "libvorbis", "-b:a", f"{q}k"],
    "WAV": lambda q: ["-c:a", "pcm_s16le"],
    "FLAC": lambda q: ["-c:a", "flac"],
}

# ---------------------------------------------------------
# CSS INSTITUCIONAL NEÓN
# ---------------------------------------------------------
CUSTOM_CSS = """
<style>
    /* ====== BASE ====== */
    .stApp {
        background: radial-gradient(ellipse at top, #0d1520 0%, #05070b 60%);
        color: #e8edf4;
    }
    header[data-testid="stHeader"] { background: transparent; }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }

    /* ====== HERO NEÓN ====== */
    .ss-hero {
        position: relative;
        background: linear-gradient(135deg, #0f1722 0%, #131a28 50%, #0b1220 100%);
        border: 1px solid rgba(0, 212, 168, 0.25);
        border-radius: 20px;
        padding: 32px 40px;
        margin-bottom: 28px;
        overflow: hidden;
        box-shadow:
            0 0 40px rgba(0, 212, 168, 0.15),
            0 0 80px rgba(124, 92, 255, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    .ss-hero::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: conic-gradient(
            from 0deg,
            transparent,
            rgba(0, 212, 168, 0.08),
            transparent 30%,
            rgba(124, 92, 255, 0.08),
            transparent 60%
        );
        animation: rotate-bg 12s linear infinite;
        pointer-events: none;
    }
    @keyframes rotate-bg {
        to { transform: rotate(360deg); }
    }
    .ss-hero h1 {
        position: relative;
        background: linear-gradient(135deg, #00ffc8 0%, #00d4a8 40%, #7c5cff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.4rem;
        font-weight: 900;
        margin: 0;
        letter-spacing: -1px;
        filter: drop-shadow(0 0 20px rgba(0, 212, 168, 0.4));
        z-index: 1;
    }
    .ss-hero p {
        position: relative;
        color: #8fa0b5;
        margin: 10px 0 0 0;
        font-size: 1rem;
        z-index: 1;
        letter-spacing: 0.3px;
    }
    .ss-hero .ss-badge-pro {
        display: inline-block;
        background: linear-gradient(135deg, #7c5cff, #ff5c9f);
        color: white;
        font-size: 0.7rem;
        font-weight: 800;
        padding: 4px 10px;
        border-radius: 6px;
        margin-left: 12px;
        letter-spacing: 2px;
        box-shadow: 0 0 20px rgba(124, 92, 255, 0.6);
        vertical-align: middle;
    }

    /* ====== TABS NEÓN ====== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(15, 23, 34, 0.6);
        padding: 8px;
        border-radius: 14px;
        border: 1px solid rgba(0, 212, 168, 0.15);
        flex-wrap: wrap;
        backdrop-filter: blur(10px);
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #7a8699;
        border-radius: 10px;
        padding: 10px 18px;
        font-weight: 600;
        border: none;
        font-size: 0.9rem;
        transition: all 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #00d4a8;
        background: rgba(0, 212, 168, 0.08);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00d4a8 0%, #00ffc8 100%) !important;
        color: #05070b !important;
        box-shadow:
            0 0 20px rgba(0, 212, 168, 0.6),
            0 0 40px rgba(0, 212, 168, 0.3);
        font-weight: 800;
    }

    /* ====== CARDS NEÓN ====== */
    .ss-card {
        background: linear-gradient(135deg, rgba(20, 26, 36, 0.9) 0%, rgba(15, 20, 28, 0.95) 100%);
        border: 1px solid rgba(0, 212, 168, 0.2);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 14px;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    .ss-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 3px;
        height: 100%;
        background: linear-gradient(180deg, #00d4a8, #7c5cff);
        opacity: 0;
        transition: opacity 0.3s ease;
    }
    .ss-card:hover {
        border-color: rgba(0, 212, 168, 0.5);
        transform: translateY(-3px);
        box-shadow:
            0 8px 30px rgba(0, 212, 168, 0.2),
            0 0 60px rgba(0, 212, 168, 0.1);
    }
    .ss-card:hover::before { opacity: 1; }
    .ss-card-title {
        color: #e8edf4;
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 4px;
        letter-spacing: -0.2px;
    }
    .ss-card-meta {
        color: #7a8699;
        font-size: 0.85rem;
    }
    .ss-card-badge {
        display: inline-block;
        background: linear-gradient(135deg, #00d4a8, #00ffc8);
        color: #05070b;
        font-size: 0.65rem;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 5px;
        margin-right: 6px;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 0 12px rgba(0, 212, 168, 0.4);
    }
    .ss-badge-purple {
        background: linear-gradient(135deg, #7c5cff, #a58cff);
        color: white;
        box-shadow: 0 0 12px rgba(124, 92, 255, 0.5);
    }
    .ss-badge-orange {
        background: linear-gradient(135deg, #ff9f43, #ffb968);
        color: #05070b;
        box-shadow: 0 0 12px rgba(255, 159, 67, 0.5);
    }
    .ss-badge-red {
        background: linear-gradient(135deg, #ff5c5c, #ff8080);
        color: white;
        box-shadow: 0 0 12px rgba(255, 92, 92, 0.5);
    }

    /* ====== INPUTS NEÓN ====== */
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        background: rgba(15, 20, 28, 0.9) !important;
        border: 1px solid rgba(0, 212, 168, 0.2) !important;
        color: #e8edf4 !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }
    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: #00d4a8 !important;
        box-shadow: 0 0 0 2px rgba(0, 212, 168, 0.3), 0 0 20px rgba(0, 212, 168, 0.2) !important;
    }

    /* ====== BOTONES NEÓN ====== */
    .stButton button {
        background: linear-gradient(135deg, #00d4a8 0%, #00ffc8 100%);
        color: #05070b;
        border: none;
        border-radius: 10px;
        font-weight: 800;
        padding: 10px 22px;
        transition: all 0.3s ease;
        letter-spacing: 0.3px;
        box-shadow: 0 4px 20px rgba(0, 212, 168, 0.3);
        text-transform: uppercase;
        font-size: 0.85rem;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow:
            0 8px 30px rgba(0, 212, 168, 0.5),
            0 0 40px rgba(0, 212, 168, 0.3);
    }
    .stButton button:active {
        transform: translateY(0);
    }

    /* ====== AUDIO PLAYER ====== */
    audio {
        width: 100%;
        border-radius: 12px;
        background: rgba(15, 20, 28, 0.9);
        filter: drop-shadow(0 0 10px rgba(0, 212, 168, 0.15));
    }

    /* ====== ANÁLISIS ====== */
    .ss-analysis {
        background: linear-gradient(135deg, rgba(20, 26, 36, 0.9), rgba(30, 20, 45, 0.9));
        border-left: 3px solid;
        border-image: linear-gradient(180deg, #7c5cff, #00d4a8) 1;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 8px 0;
        box-shadow: 0 0 20px rgba(124, 92, 255, 0.15);
    }
    .ss-section-tag {
        display: inline-block;
        background: linear-gradient(135deg, #7c5cff, #a58cff);
        color: white;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
        margin: 4px 6px 4px 0;
        letter-spacing: 0.5px;
        box-shadow: 0 0 15px rgba(124, 92, 255, 0.4);
    }

    /* ====== STAT BOX NEÓN ====== */
    .ss-stat-box {
        background: linear-gradient(135deg, rgba(20, 26, 36, 0.9), rgba(0, 212, 168, 0.05));
        border: 1px solid rgba(0, 212, 168, 0.3);
        border-radius: 14px;
        padding: 20px 22px;
        text-align: center;
        box-shadow:
            0 0 30px rgba(0, 212, 168, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.05);
    }
    .ss-stat-number {
        background: linear-gradient(135deg, #00ffc8, #00d4a8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2rem;
        font-weight: 900;
        filter: drop-shadow(0 0 15px rgba(0, 212, 168, 0.5));
    }
    .ss-stat-label {
        color: #7a8699;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 600;
        margin-top: 4px;
    }

    /* ====== PLACEHOLDER WAVE ====== */
    .ss-placeholder-wave {
        background: linear-gradient(135deg, rgba(15, 20, 28, 0.6), rgba(20, 26, 36, 0.8));
        border: 1px dashed rgba(0, 212, 168, 0.3);
        border-radius: 14px;
        padding: 24px;
        text-align: center;
        margin: 12px 0;
        box-shadow: inset 0 0 30px rgba(0, 212, 168, 0.05);
    }

    /* ====== PROGRESS ====== */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #00d4a8, #00ffc8);
        box-shadow: 0 0 20px rgba(0, 212, 168, 0.5);
    }

    /* ====== ALERTAS ====== */
    .stAlert {
        background: rgba(20, 26, 36, 0.9) !important;
        border: 1px solid rgba(0, 212, 168, 0.2) !important;
        border-radius: 12px !important;
        backdrop-filter: blur(10px);
    }

    .streamlit-expanderHeader {
        background: rgba(20, 26, 36, 0.9) !important;
        border-radius: 10px !important;
        color: #e8edf4 !important;
    }

    /* ====== MÉTRICAS ====== */
    [data-testid="stMetricValue"] {
        color: #00ffc8 !important;
        text-shadow: 0 0 20px rgba(0, 212, 168, 0.5);
        font-weight: 800 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #7a8699 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.75rem !important;
    }

    /* ====== SCROLLBAR ====== */
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: #05070b; }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #00d4a8, #7c5cff);
        border-radius: 5px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #00ffc8, #a58cff);
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# HERO NEÓN
# ---------------------------------------------------------
st.markdown("""
<div class="ss-hero">
    <h1>✂️ SoundSnip Studio<span class="ss-badge-pro">PRO</span></h1>
    <p>Edición · Análisis · Procesamiento · Reconocimiento · Conversión · Radio</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------
st.sidebar.markdown("""
<div style="text-align:center;padding:16px 0;">
    <div style="font-size:2rem;">✂️</div>
    <div style="color:#00d4a8;font-weight:800;letter-spacing:1px;">SOUNDSNIP PRO</div>
    <div style="color:#7a8699;font-size:0.75rem;letter-spacing:2px;">v7 · NEON</div>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Streamlit** v{st.__version__}")
if DENO_PATH:
    st.sidebar.success("✅ Deno activo v2.6.5")
else:
    st.sidebar.warning("⚠️ Deno no disponible")
if FFMPEG_OK:
    st.sidebar.success("✅ ffmpeg disponible")
else:
    st.sidebar.error("❌ ffmpeg no instalado")


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def safe_image(source, **kwargs):
    try:
        st.image(source, use_container_width=True, **kwargs)
    except TypeError:
        st.image(source, use_column_width=True, **kwargs)


@st.cache_data(ttl=1800, show_spinner=False)
def search_itunes(query: str, limit: int = 12):
    try:
        r = requests.get(
            "https://itunes.apple.com/search",
            params={"term": query, "entity": "song", "limit": limit},
            timeout=8
        )
        return r.json().get("results", [])
    except Exception:
        return []


@st.cache_data(ttl=1800, show_spinner=False)
def search_itunes_sfx(query: str, limit: int = 12):
    try:
        r = requests.get(
            "https://itunes.apple.com/search",
            params={
                "term": f"{query} sound effect",
                "entity": "song",
                "limit": limit * 2,
                "media": "music"
            },
            timeout=8
        )
        results = r.json().get("results", [])
        exclusion = {"Pop", "Rock", "Hip-Hop/Rap", "Latin", "Country",
                     "R&B/Soul", "Reggae", "Jazz", "Dance", "Electronic"}
        filtered = [r for r in results if r.get("primaryGenreName", "") not in exclusion]
        return filtered[:limit]
    except Exception:
        return []


@st.cache_data(ttl=1800, show_spinner=False)
def search_radio(query: str, limit: int = 20):
    try:
        r = requests.get(
            "https://de1.api.radio-browser.info/json/stations/search",
            params={"name": query, "limit": limit, "hidebroken": "true"},
            timeout=8
        )
        return r.json()
    except Exception:
        return []


@st.cache_data(ttl=1800, show_spinner=False)
def search_radio_by_tag(tag: str, limit: int = 20):
    try:
        r = requests.get(
            "https://de1.api.radio-browser.info/json/stations/search",
            params={"tag": tag, "limit": limit, "hidebroken": "true"},
            timeout=8
        )
        return r.json()
    except Exception:
        return []


def load_audio_safe(uploaded):
    uploaded.seek(0)
    try:
        data, sr = sf.read(uploaded)
        return data, sr
    except Exception:
        try:
            from pydub import AudioSegment
            uploaded.seek(0)
            audio = AudioSegment.from_file(uploaded)
            sr = audio.frame_rate
            samples = np.array(audio.get_array_of_samples())
            if audio.channels == 2:
                samples = samples.reshape((-1, 2))
            return samples.astype(np.float32) / 32768.0, sr
        except Exception as e:
            raise RuntimeError(f"Formato no soportado: {e}")


def draw_waveform(audio_mono, sr, color="#00d4a8", figsize=(12, 2.2), fake=False):
    duration = len(audio_mono) / sr if sr > 0 else 1
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor('#0a0e14')
    ax.set_facecolor('#0a0e14')
    t = np.linspace(0, duration, num=len(audio_mono))
    ax.plot(t, audio_mono, color=color, alpha=0.9, linewidth=0.7)
    ax.fill_between(t, audio_mono, -audio_mono, color=color, alpha=0.2)
    ax.set_xlabel("Tiempo (s)", color="#7a8699", fontsize=9)
    ax.set_ylabel("Amplitud", color="#7a8699", fontsize=9)
    ax.tick_params(colors='#7a8699', labelsize=8)
    ax.grid(True, color='#1a2430', linestyle='--', alpha=0.4)
    for spine in ax.spines.values():
        spine.set_color('#1a2430')
    if fake:
        ax.text(
            0.5, 0.5, "🎧  Sube un audio para activar el análisis",
            transform=ax.transAxes, ha='center', va='center',
            color='#7a8699', fontsize=12, alpha=0.7
        )
    plt.tight_layout()
    return fig


def generate_fake_waveform(seconds=10, sr=100):
    n = seconds * sr
    t = np.linspace(0, seconds, n)
    wave = (
        np.sin(2 * np.pi * 0.5 * t) * 0.3 +
        np.sin(2 * np.pi * 2 * t) * 0.2 +
        np.sin(2 * np.pi * 5 * t) * 0.1
    )
    envelope = np.abs(np.sin(2 * np.pi * 0.15 * t)) + 0.3
    wave = wave * envelope
    wave += np.random.randn(n) * 0.03
    return wave.astype(np.float32), sr


def detect_sections(audio_mono, sr):
    hop = int(sr * 0.5)
    if hop <= 0 or len(audio_mono) < hop * 4:
        return []
    rms = np.array([
        np.sqrt(np.mean(audio_mono[i:i+hop]**2))
        for i in range(0, len(audio_mono) - hop, hop)
    ])
    if len(rms) < 4:
        return []
    rms_norm = (rms - rms.min()) / (rms.max() - rms.min() + 1e-9)
    peaks, _ = find_peaks(rms_norm, height=0.6, distance=4)
    sections = []
    for p in peaks:
        t_start = p * 0.5
        t_end = min((p + 6) * 0.5, len(audio_mono) / sr)
        sections.append({
            "tipo": "🎯 Coro / Estribillo" if rms_norm[p] > 0.75 else "🎵 Sección fuerte",
            "inicio": round(t_start, 1),
            "fin": round(t_end, 1),
            "energia": round(float(rms_norm[p]), 2)
        })
    return sections[:8]


def estimate_bpm(audio_mono, sr):
    try:
        import librosa
        tempo, _ = librosa.beat.beat_track(y=audio_mono.astype(np.float32), sr=sr)
        return int(tempo) if np.isscalar(tempo) else int(tempo[0])
    except Exception:
        return None


def apply_fade(audio, sr, fade_in_sec=0, fade_out_sec=0):
    out = audio.copy()
    if fade_in_sec > 0:
        n = int(fade_in_sec * sr)
        if n < len(out):
            ramp = np.linspace(0, 1, n)
            if out.ndim > 1:
                out[:n] = out[:n] * ramp[:, None]
            else:
                out[:n] = out[:n] * ramp
    if fade_out_sec > 0:
        n = int(fade_out_sec * sr)
        if n < len(out):
            ramp = np.linspace(1, 0, n)
            if out.ndim > 1:
                out[-n:] = out[-n:] * ramp[:, None]
            else:
                out[-n:] = out[-n:] * ramp
    return out


def apply_normalize(audio):
    peak = np.max(np.abs(audio))
    if peak > 0:
        return audio / peak * 0.95
    return audio


def apply_speed(audio, sr, factor):
    if factor == 1.0:
        return audio, sr
    new_sr = int(sr * factor)
    indices = np.linspace(0, len(audio) - 1, int(len(audio) / factor))
    if audio.ndim > 1:
        resampled = np.array([np.interp(indices, np.arange(len(audio)), audio[:, c])
                              for c in range(audio.shape[1])]).T
    else:
        resampled = np.interp(indices, np.arange(len(audio)), audio)
    return resampled, new_sr


def apply_amplify(audio, gain_db):
    factor = 10 ** (gain_db / 20)
    out = audio * factor
    peak = np.max(np.abs(out))
    if peak > 1.0:
        out = out / peak
    return out


def save_audio_to_bytes(data, sr, fmt="WAV"):
    buf = io.BytesIO()
    if fmt in ("WAV", "FLAC", "OGG"):
        sf.write(buf, data, sr, format=fmt)
    else:
        from pydub import AudioSegment
        samples_int = (np.clip(data, -1, 1) * 32767).astype(np.int16)
        ch = data.shape[1] if data.ndim > 1 else 1
        seg = AudioSegment(
            samples_int.tobytes(),
            frame_rate=sr,
            sample_width=2,
            channels=ch
        )
        seg.export(buf, format="mp3", bitrate="320k")
    buf.seek(0)
    return buf


def ffmpeg_extract_audio(in_path, fmt, kbps):
    """Extrae el audio de un vídeo local con ffmpeg. Devuelve bytes."""
    out_path = os.path.splitext(in_path)[0] + "_audio." + EXT_MAP[fmt]
    cmd = ["ffmpeg", "-y", "-i", in_path, "-vn", *FFMPEG_ARGS[fmt](kbps), out_path]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if res.returncode != 0 or not os.path.exists(out_path):
        raise RuntimeError(res.stderr[-1500:])
    with open(out_path, "rb") as f:
        return f.read()


def show_audio_result(audio_bytes, title, fmt, qual, uploader="—", duration=0):
    size_mb = len(audio_bytes) / (1024 * 1024)
    duration = int(duration or 0)
    st.success("✅ Audio extraído correctamente")
    st.markdown(f"""
    <div class="ss-card">
        <span class="ss-card-badge">READY</span>
        <span class="ss-card-badge ss-badge-purple">{fmt} · {qual}</span>
        <div class="ss-card-title">{title}</div>
        <div class="ss-card-meta">
        👤 {uploader} · ⏱ {duration // 60}:{duration % 60:02d} · 📦 {size_mb:.1f} MB
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.audio(audio_bytes, format=MIME_MAP[fmt])
    st.download_button(
        f"⬇️ Descargar {fmt}", audio_bytes,
        file_name=f"{title}.{EXT_MAP[fmt]}", mime=MIME_MAP[fmt],
        use_container_width=True,
    )


# ---------------------------------------------------------
# TABS
# ---------------------------------------------------------
tabs = st.tabs([
    "🎧 Editor & Análisis",
    "🔊 Banco SFX",
    "📥 Convertidor",
    "📻 Radio Live",
    "🎙️ Buscador Música",
    "🔗 Video → Audio",
    "🎤 Shazam",
])

# =========================================================
# TAB 1 — EDITOR & ANÁLISIS
# =========================================================
with tabs[0]:
    st.markdown("### ✂️ Editor Express con análisis estructural")
    st.caption("Sube un audio. Detectamos automáticamente BPM, secciones y te dejamos recortar.")

    up = st.file_uploader(
        "Sube audio (WAV · MP3 · FLAC · OGG · M4A)",
        type=["wav", "mp3", "flac", "ogg", "m4a"],
        key="editor_up"
    )

    if up is None:
        st.markdown("#### 📊 Onda sonora (vista previa)")
        st.markdown("""
        <div class="ss-placeholder-wave">
            <p style="color:#7a8699;margin:0;font-size:0.9rem;">
            🎧 Esperando pista de audio — la onda se activará al subir un archivo
            </p>
        </div>
        """, unsafe_allow_html=True)
        fake_wave, fake_sr = generate_fake_waveform(seconds=10, sr=100)
        st.pyplot(draw_waveform(fake_wave, fake_sr, color="#2a3a4a", fake=True))

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("⏱ Duración", "— s")
        c2.metric("🎚 Sample rate", "— Hz")
        c3.metric("📊 Canales", "—")
        c4.metric("🥁 BPM aprox.", "—")

        st.info("💡 **Consejo**: formatos soportados WAV, MP3, FLAC, OGG, M4A. Tamaño máx. 200 MB.")
    else:
        try:
            data, sr = load_audio_safe(up)
            audio_mono = data.mean(axis=1) if len(data.shape) > 1 else data
            duration = len(data) / sr

            up.seek(0)
            st.audio(up)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("⏱ Duración", f"{duration:.1f} s")
            c2.metric("🎚 Sample rate", f"{sr} Hz")
            c3.metric("📊 Canales", data.shape[1] if len(data.shape) > 1 else 1)
            bpm = estimate_bpm(audio_mono, sr)
            c4.metric("🥁 BPM aprox.", bpm if bpm else "—")

            st.markdown("#### 📊 Onda sonora")
            st.pyplot(draw_waveform(audio_mono, sr))

            with st.spinner("Analizando estructura (secciones, energía)..."):
                sections = detect_sections(audio_mono, sr)

            if sections:
                st.markdown("#### 🎼 Secciones detectadas")
                cols = st.columns(min(len(sections), 4))
                for i, sec in enumerate(sections[:4]):
                    with cols[i]:
                        st.markdown(f"""
                        <div class="ss-analysis">
                            <span class="ss-section-tag">{sec['tipo']}</span><br>
                            <small style="color:#7a8699;">
                            {sec['inicio']}s → {sec['fin']}s<br>
                            Energía: {sec['energia']}
                            </small>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown("#### ✂️ Ajustar recorte")
            col1, col2 = st.columns(2)
            with col1:
                start = st.number_input("Inicio (s)", 0.0, duration, 0.0, 0.1)
            with col2:
                end = st.number_input("Fin (s)", 0.0, duration, min(10.0, duration), 0.1)

            if start < end:
                if st.button("✂️ Recortar y exportar", use_container_width=True):
                    s_i, e_i = int(start * sr), int(end * sr)
                    cropped = data[s_i:e_i]
                    buf = save_audio_to_bytes(cropped, sr, "WAV")
                    st.success("Recorte listo")
                    st.audio(buf, format="audio/wav")
                    st.download_button(
                        "⬇️ Descargar recorte WAV",
                        buf, file_name=f"recorte_{start:.1f}-{end:.1f}.wav",
                        mime="audio/wav", use_container_width=True
                    )
            else:
                st.error("Inicio debe ser menor que fin.")
        except Exception as e:
            st.error(f"Error: {e}")

# =========================================================
# TAB 2 — BANCO SFX
# =========================================================
with tabs[1]:
    st.markdown("### 🔊 Banco de efectos y sonidos")
    st.caption("Buscador especializado en **efectos de sonido**, no en canciones.")

    st.markdown("**Categorías rápidas:**")
    cat_cols = st.columns(6)
    quick_cats = ["🌧 Lluvia", "🚗 Tráfico", "🐦 Pájaros", "⚡ Trueno", "🚪 Puerta", "🌊 Mar"]
    cat_query = None
    for i, cat in enumerate(quick_cats):
        with cat_cols[i]:
            if st.button(cat, use_container_width=True, key=f"cat_{i}"):
                cat_query = cat.split(" ", 1)[1]

    q = st.text_input(
        "🔍 Buscar efecto (ej: rain, thunder, car, birds, applause, footsteps):",
        value=cat_query if cat_query else "rain"
    )

    if q:
        with st.spinner("Buscando efectos de sonido..."):
            results = search_itunes_sfx(q, limit=12)
        if results:
            st.caption(f"🎧 {len(results)} efectos encontrados")
            cols = st.columns(2)
            for i, item in enumerate(results):
                with cols[i % 2]:
                    title = item.get("trackName", "—")
                    artist = item.get("artistName", "—")
                    genre = item.get("primaryGenreName", "—")
                    art = item.get("artworkUrl100", "")
                    preview = item.get("previewUrl")
                    st.markdown(f"""
                    <div class="ss-card">
                        <span class="ss-card-badge">SFX</span>
                        <span class="ss-card-badge ss-badge-purple">{genre}</span>
                        <div class="ss-card-title">{title}</div>
                        <div class="ss-card-meta">🎬 {artist}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if art:
                        st.image(art, width=70)
                    if preview:
                        st.audio(preview)
        else:
            st.warning("Sin resultados. Prueba otra palabra (en inglés funciona mejor).")

# =========================================================
# TAB 3 — CONVERTIDOR + PROCESADOR
# =========================================================
with tabs[2]:
    st.markdown("### 📥 Convertidor y procesador de audio")
    st.caption("Convierte formatos o aplica efectos: fade, normalizar, velocidad, ganancia.")

    up2 = st.file_uploader(
        "Sube audio a procesar",
        type=["wav", "mp3", "flac", "ogg", "m4a"],
        key="convert_up"
    )

    if up2 is not None:
        try:
            up2.seek(0)
            data, sr = load_audio_safe(up2)
            st.info(f"Origen: {sr} Hz · canales: {data.shape[1] if len(data.shape) > 1 else 1}")

            modo = st.radio(
                "🎛️ Modo de procesamiento",
                ["🔄 Convertir formato", "🎚️ Aplicar efectos"],
                horizontal=True
            )

            if modo.startswith("🔄"):
                c1, c2 = st.columns(2)
                with c1:
                    fmt_conv = st.selectbox("Formato destino", ["WAV", "FLAC", "OGG", "MP3"])
                with c2:
                    quality = st.selectbox(
                        "Calidad",
                        ["Original", "Alta (320 kbps)", "Media (192 kbps)", "Baja (128 kbps)"]
                    )

                sr_map = {"Original": sr, "Alta (320 kbps)": sr,
                          "Media (192 kbps)": 44100, "Baja (128 kbps)": 22050}
                target_sr = sr_map[quality]

                if st.button("🚀 Convertir", use_container_width=True):
                    with st.spinner("Convirtiendo..."):
                        buf = save_audio_to_bytes(data, target_sr, fmt_conv)
                    st.success(f"Convertido a {fmt_conv} · {target_sr} Hz")
                    st.audio(buf)
                    st.download_button(
                        f"⬇️ Descargar {fmt_conv}",
                        buf,
                        file_name=f"convertido.{fmt_conv.lower()}",
                        mime=MIME_MAP.get(fmt_conv, "audio/wav"),
                        use_container_width=True
                    )
            else:
                st.markdown("#### 🎚️ Procesadores disponibles")

                col1, col2 = st.columns(2)
                with col1:
                    fade_in = st.slider("Fade In (s)", 0.0, 5.0, 0.5, 0.1)
                    speed = st.slider("Velocidad (x)", 0.5, 2.0, 1.0, 0.05)
                with col2:
                    fade_out = st.slider("Fade Out (s)", 0.0, 5.0, 0.5, 0.1)
                    gain_db = st.slider("Ganancia (dB)", -20, 20, 0, 1)

                normalize = st.checkbox("🔊 Normalizar (peak -0.5 dB)", value=True)

                if st.button("🎛️ Procesar audio", use_container_width=True):
                    with st.spinner("Procesando..."):
                        processed = data.copy()

                        if speed != 1.0:
                            processed, sr = apply_speed(processed, sr, speed)

                        if gain_db != 0:
                            processed = apply_amplify(processed, gain_db)

                        if normalize:
                            processed = apply_normalize(processed)

                        if fade_in > 0 or fade_out > 0:
                            processed = apply_fade(processed, sr, fade_in, fade_out)

                        buf = save_audio_to_bytes(processed, sr, "WAV")

                    st.success("✅ Procesado completado")
                    st.audio(buf, format="audio/wav")
                    st.download_button(
                        "⬇️ Descargar procesado",
                        buf,
                        file_name=f"procesado_{up2.name.split('.')[0]}.wav",
                        mime="audio/wav",
                        use_container_width=True
                    )
        except Exception as e:
            st.error(f"Error: {e}")

# =========================================================
# TAB 4 — RADIO LIVE
# =========================================================
with tabs[3]:
    st.markdown("### 📻 Radio Live · buscador global")
    st.caption("Busca por nombre de emisora o por temática (finance, jazz, rock, news...)")

    col_q1, col_q2 = st.columns([3, 1])
    with col_q1:
        q_radio = st.text_input(
            "🔍 Buscar emisora (nombre, género, temática):",
            value="jazz",
            placeholder="jazz · rock · finance · trading · news · spain..."
        )
    with col_q2:
        tipo_busqueda = st.selectbox("Buscar por", ["Nombre", "Tag/Temática"])

    if q_radio:
        with st.spinner("Conectando con el directorio global..."):
            if tipo_busqueda == "Tag/Temática":
                stations = search_radio_by_tag(q_radio, limit=20)
            else:
                stations = search_radio(q_radio, limit=20)

        total = len(stations)
        st.markdown(f"""
        <div class="ss-stat-box">
            <div class="ss-stat-number">{total}</div>
            <div class="ss-stat-label">Emisoras encontradas para "{q_radio}"</div>
        </div>
        """, unsafe_allow_html=True)

        if stations:
            st.markdown("---")
            for s in stations:
                stream_url = s.get("url_resolved") or s.get("url")
                if not stream_url:
                    continue
                name = s.get("name", "—")
                country = s.get("country", "—")
                tags_raw = s.get("tags") or ""
                codec = s.get("codec", "—")
                bitrate = s.get("bitrate", "—")
                votes = s.get("votes", 0)

                tag_list = [t.strip() for t in tags_raw.split(",") if t.strip()][:6]
                tags_html = " ".join([
                    f'<span class="ss-card-badge ss-badge-purple" style="font-size:0.65rem;">{t}</span>'
                    for t in tag_list
                ])

                st.markdown(f"""
                <div class="ss-card">
                    <span class="ss-card-badge">LIVE</span>
                    <span class="ss-card-badge ss-badge-orange">{codec} · {bitrate} kbps</span>
                    <span class="ss-card-badge ss-badge-red">❤ {votes}</span>
                    <div class="ss-card-title">{name}</div>
                    <div class="ss-card-meta">🌍 {country}</div>
                    <div style="margin-top:8px;">{tags_html}</div>
                </div>
                """, unsafe_allow_html=True)
                try:
                    st.audio(stream_url)
                except Exception:
                    st.caption("Stream no reproducible en navegador")
        else:
            st.warning(f"Sin emisoras para '{q_radio}'. Prueba: jazz, rock, news, finance, spain...")

# =========================================================
# TAB 5 — BUSCADOR MÚSICA
# =========================================================
with tabs[4]:
    st.markdown("### 🎙️ Buscador de canciones y metadatos")
    st.caption("Identifica canciones por nombre, artista o álbum.")

    st.info(
        "⚠️ **Límite de previsualización**: la API de iTunes solo proporciona "
        "**30 segundos** por canción (restricción de Apple)."
    )

    q_music = st.text_input("🔍 Canción, artista o álbum:", value="Coldplay")
    if q_music:
        with st.spinner("Buscando..."):
            tracks = search_itunes(q_music, limit=9)
        if tracks:
            st.caption(f"🎧 {len(tracks)} resultados · vista previa 30s")
            cols = st.columns(3)
            for i, t in enumerate(tracks):
                with cols[i % 3]:
                    art = (t.get("artworkUrl100") or "").replace("100x100", "300x300")
                    if art:
                        safe_image(art)
                    st.markdown(f"""
                    <div class="ss-card">
                        <div class="ss-card-title">{t.get('trackName','—')}</div>
                        <div class="ss-card-meta">
                        👤 {t.get('artistName','—')}<br>
                        💿 {t.get('collectionName','—')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if t.get("previewUrl"):
                        st.audio(t["previewUrl"])
        else:
            st.warning("Sin resultados.")

# =========================================================
# TAB 6 — VIDEO → AUDIO
# =========================================================
with tabs[5]:
    st.markdown("### 🔗 Video → Audio")

    if not FFMPEG_OK:
        st.error("ffmpeg no está instalado. En Streamlit Cloud añade `ffmpeg` a `packages.txt`.")

    c1, c2 = st.columns(2)
    with c1:
        fmt = st.selectbox("Formato de salida", list(CODEC_MAP.keys()), key="va_fmt")
    with c2:
        qual = st.selectbox("Calidad", ["320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps"],
                            key="va_qual")
    kbps = qual.split()[0]

    modo_subida, modo_enlace = st.tabs(["📁 Subir vídeo", "🌐 Desde enlace"])

    # ---------- MODO 1: SUBIR VÍDEO (siempre funciona) ----------
    with modo_subida:
        st.caption("Sube un vídeo y te devolvemos solo la pista de audio.")
        vid = st.file_uploader("Vídeo (MP4 · MOV · MKV · WEBM · AVI)",
                               type=["mp4", "mov", "mkv", "webm", "avi"], key="va_upload")
        if vid and st.button("🎬 Extraer audio del vídeo", use_container_width=True, key="va_btn_up"):
            try:
                with st.spinner("Extrayendo audio..."):
                    tmpdir = tempfile.mkdtemp()
                    in_path = os.path.join(tmpdir, "input" + os.path.splitext(vid.name)[1])
                    with open(in_path, "wb") as f:
                        f.write(vid.getbuffer())
                    audio_bytes = ffmpeg_extract_audio(in_path, fmt, kbps)
                show_audio_result(audio_bytes, os.path.splitext(vid.name)[0], fmt, qual)
            except Exception as e:
                st.error("No se pudo extraer el audio de este archivo.")
                with st.expander("Detalles técnicos"):
                    st.code(str(e))

    # ---------- MODO 2: ENLACE (yt-dlp) ----------
    with modo_enlace:
        st.caption("YouTube, Vimeo, SoundCloud… Desde servidores en la nube YouTube suele "
                   "bloquear; en local funciona mucho mejor.")
        st.caption("🟢 Motor JS activo" if DENO_PATH else "🔴 Motor JS no disponible")
        video_url = st.text_input("🔗 Enlace del vídeo:",
                                  placeholder="https://www.youtube.com/watch?v=...",
                                  key="va_url")

        if video_url and st.button("🎬 Extraer audio", use_container_width=True, key="va_btn_url"):
            try:
                import yt_dlp
                tmpdir = tempfile.mkdtemp()
                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s"),
                    "noplaylist": True,
                    "quiet": True,
                    "no_warnings": True,
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": CODEC_MAP[fmt],
                        "preferredquality": kbps,
                    }],
                }
                if DENO_PATH:
                    ydl_opts["js_runtimes"] = {"deno": {"path": DENO_PATH}}

                with st.spinner("🎧 Procesando el vídeo..."):
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(video_url, download=True)

                files = [f for f in os.listdir(tmpdir) if f.endswith("." + EXT_MAP[fmt])]
                if not files:
                    raise RuntimeError("yt-dlp terminó pero no generó el archivo de audio.")
                with open(os.path.join(tmpdir, files[0]), "rb") as f:
                    audio_bytes = f.read()

                show_audio_result(
                    audio_bytes, info.get("title", "audio"), fmt, qual,
                    uploader=info.get("uploader", "—"), duration=info.get("duration", 0),
                )
            except Exception as e:
                err = str(e).lower()
                if "not a bot" in err or "sign in" in err:
                    st.error("🤖 YouTube está bloqueando la IP de este servidor. "
                             "Usa la pestaña **Subir vídeo** o ejecuta la app en local.")
                elif "private" in err or "unavailable" in err:
                    st.error("🔒 El vídeo es privado o no está disponible.")
                elif "unsupported url" in err:
                    st.error("🔗 Ese enlace no es de una plataforma soportada.")
                else:
                    st.error("😕 No se pudo descargar este vídeo.")
                with st.expander("Detalles técnicos"):
                    st.code(str(e))

# =========================================================
# TAB 7 — SHAZAM (búsqueda por nombre de archivo)
# =========================================================
with tabs[6]:
    st.markdown("### 🎤 Shazam — Reconocimiento de audio")
    st.caption("Sube un fragmento para identificarlo.")

    frag = st.file_uploader(
        "Sube un fragmento corto (5-15 s)",
        type=["wav", "mp3", "ogg", "m4a"],
        key="shazam_up"
    )
    if frag:
        st.audio(frag)
        if st.button("🔎 Identificar canción", use_container_width=True):
            with st.spinner("Buscando coincidencias..."):
                hint = os.path.splitext(frag.name)[0].replace("_", " ").replace("-", " ")
                results = search_itunes(hint, limit=3)

            if results:
                st.success("🎯 Coincidencias encontradas")
                for r in results:
                    art = (r.get("artworkUrl100") or "").replace("100x100", "300x300")
                    c1, c2 = st.columns([1, 3])
                    with c1:
                        if art:
                            safe_image(art)
                    with c2:
                        st.markdown(f"""
                        <div class="ss-card">
                            <span class="ss-card-badge">MATCH</span>
                            <div class="ss-card-title">{r.get('trackName','—')}</div>
                            <div class="ss-card-meta">
                            👤 {r.get('artistName','—')}<br>
                            💿 {r.get('collectionName','—')}<br>
                            📅 {(r.get('releaseDate') or '—')[:10]}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        if r.get("previewUrl"):
                            st.audio(r["previewUrl"])
            else:
                st.warning(
                    "No se pudo identificar. Prueba a renombrar el archivo con el nombre "
                    "de la canción como pista."
                )
