import streamlit as st
import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt
import requests
import io
import os
import tempfile
from pathlib import Path
from scipy.signal import find_peaks

# =========================================================
# CONFIGURACIÓN INICIAL
# =========================================================
st.set_page_config(
    page_title="SoundSnip Studio PRO",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.sidebar.caption(f"Streamlit v{st.__version__}")
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎛️ Info")
st.sidebar.caption("SoundSnip Studio PRO v3")
st.sidebar.caption("Todos los módulos activos")

# ---------------------------------------------------------
# CSS INSTITUCIONAL
# ---------------------------------------------------------
CUSTOM_CSS = """
<style>
    .stApp {
        background: linear-gradient(180deg, #0a0e14 0%, #0d1219 100%);
        color: #e8edf4;
    }
    header[data-testid="stHeader"] { background: transparent; }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }

    .ss-hero {
        background: linear-gradient(135deg, #141a24 0%, #1c2430 100%);
        border: 1px solid #232c3a;
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    }
    .ss-hero h1 {
        color: #00d4a8;
        font-size: 2rem;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .ss-hero p {
        color: #7a8699;
        margin: 6px 0 0 0;
        font-size: 0.95rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: #0a0e14;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #232c3a;
        flex-wrap: wrap;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #7a8699;
        border-radius: 8px;
        padding: 10px 16px;
        font-weight: 500;
        border: none;
        font-size: 0.9rem;
    }
    .stTabs [aria-selected="true"] {
        background: #00d4a8 !important;
        color: #0a0e14 !important;
    }

    .ss-card {
        background: #141a24;
        border: 1px solid #232c3a;
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 14px;
        transition: all 0.2s ease;
    }
    .ss-card:hover {
        border-color: #00d4a8;
        transform: translateY(-2px);
        box-shadow: 0 6px 24px rgba(0,212,168,0.15);
    }
    .ss-card-title {
        color: #e8edf4;
        font-size: 1.05rem;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .ss-card-meta {
        color: #7a8699;
        font-size: 0.85rem;
    }
    .ss-card-badge {
        display: inline-block;
        background: #00d4a8;
        color: #0a0e14;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        margin-right: 6px;
        text-transform: uppercase;
    }
    .ss-badge-purple { background: #7c5cff; color: white; }
    .ss-badge-orange { background: #ff9f43; color: #0a0e14; }
    .ss-badge-red { background: #ff5c5c; color: white; }

    .stTextInput input, .stSelectbox select {
        background: #141a24 !important;
        border: 1px solid #232c3a !important;
        color: #e8edf4 !important;
        border-radius: 10px !important;
    }
    .stTextInput input:focus {
        border-color: #00d4a8 !important;
        box-shadow: 0 0 0 2px rgba(0,212,168,0.2) !important;
    }

    .stButton button {
        background: #00d4a8;
        color: #0a0e14;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        padding: 10px 20px;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        background: #00e6b8;
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(0,212,168,0.3);
    }

    audio {
        width: 100%;
        border-radius: 10px;
        background: #141a24;
    }

    .ss-analysis {
        background: #141a24;
        border-left: 3px solid #7c5cff;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 8px 0;
    }
    .ss-section-tag {
        display: inline-block;
        background: #7c5cff;
        color: white;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
        margin: 4px 6px 4px 0;
    }

    .ss-stat-box {
        background: #141a24;
        border: 1px solid #232c3a;
        border-radius: 10px;
        padding: 14px 18px;
        text-align: center;
    }
    .ss-stat-number {
        color: #00d4a8;
        font-size: 1.6rem;
        font-weight: 700;
    }
    .ss-stat-label {
        color: #7a8699;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .ss-placeholder-wave {
        background: #0f141b;
        border: 1px dashed #232c3a;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin: 12px 0;
    }

    .stProgress > div > div > div {
        background-color: #00d4a8;
    }

    .stAlert {
        background: #141a24 !important;
        border: 1px solid #232c3a !important;
        border-radius: 10px !important;
    }

    .streamlit-expanderHeader {
        background: #141a24 !important;
        border-radius: 10px !important;
        color: #e8edf4 !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------
# HERO
# ---------------------------------------------------------
st.markdown("""
<div class="ss-hero">
    <h1>✂️ SoundSnip Studio <span style="color:#7c5cff;font-size:1rem;">PRO v3</span></h1>
    <p>Edición · Análisis · Procesamiento · Reconocimiento · Conversión · Radio</p>
</div>
""", unsafe_allow_html=True)

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
        filtered = [
            r for r in results
            if r.get("primaryGenreName", "") not in exclusion
        ]
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
    fig.patch.set_facecolor('#141a24')
    ax.set_facecolor('#141a24')
    t = np.linspace(0, duration, num=len(audio_mono))
    ax.plot(t, audio_mono, color=color, alpha=0.85, linewidth=0.6)
    ax.fill_between(t, audio_mono, -audio_mono, color=color, alpha=0.15)
    ax.set_xlabel("Tiempo (s)", color="#7a8699", fontsize=9)
    ax.set_ylabel("Amplitud", color="#7a8699", fontsize=9)
    ax.tick_params(colors='#7a8699', labelsize=8)
    ax.grid(True, color='#232c3a', linestyle='--', alpha=0.4)
    for spine in ax.spines.values():
        spine.set_color('#232c3a')
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


def get_cookie_file():
    try:
        content = st.secrets.get("YTDLP_COOKIES_CONTENT", None)
    except Exception:
        content = None
    if not content:
        return None
    content = content.replace("\\n", "\n").replace("\r\n", "\n")
    cookie_path = Path("/tmp/yt-dlp-cookies.txt")
    cookie_path.write_text(content, encoding="utf-8")
    cookie_path.chmod(0o600)
    return str(cookie_path)


# --- Procesadores de audio (reemplazan a Spleeter) ---
def apply_fade(audio, sr, fade_in_sec=0, fade_out_sec=0):
    out = audio.copy()
    if fade_in_sec > 0:
        n = int(fade_in_sec * sr)
        if n < len(out):
            out[:n] = out[:n] * np.linspace(0, 1, n)[:, None] if out.ndim > 1 else out[:n] * np.linspace(0, 1, n)
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
    else:  # MP3
        from pydub import AudioSegment
        samples_int = (data * 32767).astype(np.int16)
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
        st.pyplot(draw_waveform(fake_wave, fake_sr, color="#3a4453", fake=True))

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

            # =========== MODO CONVERTIR ===========
            if modo.startswith("🔄"):
                c1, c2 = st.columns(2)
                with c1:
                    fmt = st.selectbox("Formato destino", ["WAV", "FLAC", "OGG", "MP3"])
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
                        buf = save_audio_to_bytes(data, target_sr, fmt)
                    st.success(f"Convertido a {fmt} · {target_sr} Hz")
                    st.audio(buf)
                    st.download_button(
                        f"⬇️ Descargar {fmt}",
                        buf,
                        file_name=f"convertido.{fmt.lower()}",
                        mime=f"audio/{fmt.lower()}",
                        use_container_width=True
                    )

            # =========== MODO EFECTOS ===========
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

                        # Velocidad
                        if speed != 1.0:
                            processed, sr = apply_speed(processed, sr, speed)

                        # Ganancia
                        if gain_db != 0:
                            processed = apply_amplify(processed, gain_db)

                        # Normalizar
                        if normalize:
                            processed = apply_normalize(processed)

                        # Fades
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

                st.markdown("---")
                st.caption(
                    "💡 **Nota**: la separación de voces/instrumentos con IA "
                    "(Spleeter/Demucs) no está disponible porque consume demasiada "
                    "memoria y no es compatible con Streamlit Cloud gratis."
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
        q = st.text_input(
            "🔍 Buscar emisora (nombre, género, temática):",
            value="jazz",
            placeholder="jazz · rock · finance · trading · news · spain..."
        )
    with col_q2:
        tipo_busqueda = st.selectbox("Buscar por", ["Nombre", "Tag/Temática"])

    if q:
        with st.spinner("Conectando con el directorio global..."):
            if tipo_busqueda == "Tag/Temática":
                stations = search_radio_by_tag(q, limit=20)
            else:
                stations = search_radio(q, limit=20)

        total = len(stations)
        st.markdown(f"""
        <div class="ss-stat-box">
            <div class="ss-stat-number">{total}</div>
            <div class="ss-stat-label">Emisoras encontradas para "{q}"</div>
        </div>
        """, unsafe_allow_html=True)

        if stations:
            st.markdown("---")
            for s in stations:
                url = s.get("url_resolved") or s.get("url")
                if not url:
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
                    st.audio(url)
                except Exception:
                    st.caption("Stream no reproducible en navegador")
        else:
            st.warning(f"Sin emisoras para '{q}'. Prueba: jazz, rock, news, finance, spain...")

        st.markdown("---")
        st.caption(
            "💡 **Trucos de búsqueda**: "
            "usa **Tag/Temática** con `finance`, `business`, `trading`, `news` "
            "para emisoras de información bursátil."
        )

# =========================================================
# TAB 5 — BUSCADOR MÚSICA
# =========================================================
with tabs[4]:
    st.markdown("### 🎙️ Buscador de canciones y metadatos")
    st.caption("Identifica canciones por nombre, artista o álbum.")

    st.info(
        "⚠️ **Límite de previsualización**: la API de iTunes solo proporciona "
        "**30 segundos** por canción (restricción de Apple). Es suficiente para "
        "identificar la canción pero no para escucharla completa."
    )

    q = st.text_input("🔍 Canción, artista o álbum:", value="Coldplay")
    if q:
        with st.spinner("Buscando..."):
            tracks = search_itunes(q, limit=9)
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
    st.markdown("### 🔗 Extractor de audio desde vídeo / URL")
    st.caption("Soporta YouTube, Vimeo y +1000 sitios vía yt-dlp.")

    cookie_path = get_cookie_file()
    if cookie_path:
        st.success("🍪 Cookies de YouTube cargadas desde Secrets — 403 resuelto")
    else:
        st.warning(
            "⚠️ **Sin cookies configuradas**. YouTube puede bloquear con 403. "
            "Añade `YTDLP_COOKIES_CONTENT` en Streamlit Secrets."
        )

    url = st.text_input("🔗 Pega la URL del vídeo:", placeholder="https://www.youtube.com/watch?v=...")

    c1, c2 = st.columns(2)
    with c1:
        fmt = st.selectbox("Formato de salida", ["MP3", "WAV", "FLAC", "M4A", "OGG"])
    with c2:
        qual = st.selectbox("Calidad", ["320 kbps", "256 kbps", "192 kbps", "128 kbps", "96 kbps"])

    if url and st.button("🎬 Extraer audio", use_container_width=True):
        try:
            import yt_dlp
            with st.spinner("Descargando y convirtiendo... esto puede tardar"):
                tmpdir = tempfile.mkdtemp()
                out_tmpl = os.path.join(tmpdir, "%(title)s.%(ext)s")

                ydl_opts = {
                    "format": "bestaudio/best",
                    "outtmpl": out_tmpl,
                    "quiet": True,
                    "noplaylist": True,
                    "nocheckcertificate": True,
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": fmt.lower(),
                        "preferredquality": qual.split()[0],
                    }],
                }

                if cookie_path:
                    ydl_opts["cookiefile"] = cookie_path

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    title = info.get("title", "audio")

                files = os.listdir(tmpdir)
                if files:
                    fp = os.path.join(tmpdir, files[0])
                    with open(fp, "rb") as f:
                        audio_bytes = f.read()

                    st.success(f"✅ {title}")
                    st.audio(audio_bytes, format=f"audio/{fmt.lower()}")
                    st.download_button(
                        f"⬇️ Descargar {fmt}",
                        audio_bytes,
                        file_name=f"{title}.{fmt.lower()}",
                        mime=f"audio/{fmt.lower()}",
                        use_container_width=True
                    )
                else:
                    st.error("No se generó archivo.")
        except Exception as e:
            st.error(f"Error: {e}")
            st.caption(
                "Si el error es 403 Forbidden → necesitas configurar cookies. "
                "Algunos vídeos también están protegidos por región o DRM."
            )

    with st.expander("🍪 Cómo configurar las cookies de YouTube"):
        guia_cookies = """
**Paso 1** — Instala una extensión para exportar cookies:

- Firefox: [YT-DLP Cookie Exporter](https://addons.mozilla.org/en-GB/firefox/addon/yt-dlp-cookie-exporter/)
- Chrome: [Get cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)

**Paso 2** — Abre YouTube en **ventana de incógnito**, inicia sesión, visita `youtube.com/robots.txt`, exporta las cookies y cierra esa ventana.

**Paso 3** — En Streamlit Cloud → Settings → Secrets, añade el bloque `YTDLP_COOKIES_CONTENT` con el contenido del archivo de cookies exportado.

**Paso 4** — Redespliega la app. Las cookies se inyectan automáticamente.

⚠️ **Renuévalas cada 1-2 semanas** — YouTube las rota periódicamente.
"""
        st.markdown(guia_cookies)

# =========================================================
# TAB 7 — SHAZAM
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
            with st.spinner("Analizando huella acústica..."):
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
                            📅 {r.get('releaseDate','—')[:10]}
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

    st.markdown("---")
    st.caption(
        "💡 **Reconocimiento real**: para fingerprinting auténtico (escuchar y decir "
        "qué canción es), integra **AudD API** (audd.io) o **ACRCloud**. "
        "La versión actual usa el nombre del archivo como pista."
    )
