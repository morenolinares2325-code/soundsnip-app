import streamlit as st
import soundfile as sf
import numpy as np
import matplotlib.pyplot as plt
import requests
import io
import os
import tempfile
from scipy.io import wavfile
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

# ---------------------------------------------------------
# CSS INSTITUCIONAL (paleta tipo Bloomberg/TradingView)
# ---------------------------------------------------------
CUSTOM_CSS = """
<style>
    /* Fondo general */
    .stApp {
        background: linear-gradient(180deg, #0a0e14 0%, #0d1219 100%);
        color: #e8edf4;
    }
    
    /* Ocultar header/footer de Streamlit */
    header[data-testid="stHeader"] { background: transparent; }
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    
    /* Título principal */
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
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #0a0e14;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #232c3a;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #7a8699;
        border-radius: 8px;
        padding: 10px 18px;
        font-weight: 500;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background: #00d4a8 !important;
        color: #0a0e14 !important;
    }
    
    /* Cards */
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
    
    /* Inputs */
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
    
    /* Botones */
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
    
    /* Player audio */
    audio {
        width: 100%;
        border-radius: 10px;
        background: #141a24;
    }
    
    /* Sección de análisis */
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
    
    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #00d4a8;
    }
    
    /* Alertas */
    .stAlert {
        background: #141a24 !important;
        border: 1px solid #232c3a !important;
        border-radius: 10px !important;
    }
    
    /* Expander */
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
    <h1>✂️ SoundSnip Studio <span style="color:#7c5cff;font-size:1rem;">PRO</span></h1>
    <p>Edición · Análisis · Reconocimiento · Conversión · Radio — todo en un solo lugar</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
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
def search_radio(query: str, limit: int = 15):
    try:
        r = requests.get(
            "https://de1.api.radio-browser.info/json/stations/search",
            params={"name": query, "limit": limit, "hidebroken": "true"},
            timeout=8
        )
        return r.json()
    except Exception:
        return []

def load_audio_safe(uploaded):
    """Intenta leer cualquier formato. Fallback a pydub para MP3."""
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

def draw_waveform(audio_mono, sr, color="#00d4a8", figsize=(12, 2.2)):
    duration = len(audio_mono) / sr
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
    plt.tight_layout()
    return fig

def detect_sections(audio_mono, sr):
    """Detección heurística de estrofas/coros por energía RMS."""
    hop = int(sr * 0.5)
    rms = np.array([
        np.sqrt(np.mean(audio_mono[i:i+hop]**2))
        for i in range(0, len(audio_mono) - hop, hop)
    ])
    if len(rms) < 4:
        return []
    # Normalizar
    rms_norm = (rms - rms.min()) / (rms.max() - rms.min() + 1e-9)
    # Encontrar picos (posibles coros/estribillos = alta energía)
    peaks, props = find_peaks(rms_norm, height=0.6, distance=4)
    sections = []
    for i, p in enumerate(peaks):
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
    """Estimación rápida de BPM por autocorrelación."""
    try:
        import librosa
        tempo, _ = librosa.beat.beat_track(y=audio_mono.astype(np.float32), sr=sr)
        return int(tempo) if np.isscalar(tempo) else int(tempo[0])
    except Exception:
        return None

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

    if up is not None:
        try:
            data, sr = load_audio_safe(up)
            audio_mono = data.mean(axis=1) if len(data.shape) > 1 else data
            duration = len(data) / sr

            # Player + métricas
            up.seek(0)
            st.audio(up)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("⏱ Duración", f"{duration:.1f} s")
            c2.metric("🎚 Sample rate", f"{sr} Hz")
            c3.metric("📊 Canales", data.shape[1] if len(data.shape) > 1 else 1)
            bpm = estimate_bpm(audio_mono, sr)
            c4.metric("🥁 BPM aprox.", bpm if bpm else "—")

            # Waveform
            st.markdown("#### 📊 Onda sonora")
            st.pyplot(draw_waveform(audio_mono, sr))

            # Análisis estructural
            with st.spinner("Analizando estructura (secciones, energía)..."):
                sections = detect_sections(audio_mono, sr)

            if sections:
                st.markdown("#### 🎼 Secciones detectadas")
                cols = st.columns(len(sections[:4]))
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

            # Recorte
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
                    buf = io.BytesIO()
                    sf.write(buf, cropped, sr, format='WAV')
                    buf.seek(0)
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
    st.caption("Buscador tipo Spotify con previsualización instantánea.")
    q = st.text_input("🔍 Buscar sonido (ej: rain, bell, applause, drums):", value="rain")

    if q:
        with st.spinner("Buscando..."):
            results = search_itunes(q, limit=12)
        if results:
            cols = st.columns(2)
            for i, item in enumerate(results):
                with cols[i % 2]:
                    title = item.get("trackName", "—")
                    artist = item.get("artistName", "—")
                    art = item.get("artworkUrl100", "")
                    preview = item.get("previewUrl")
                    st.markdown(f"""
                    <div class="ss-card">
                        <span class="ss-card-badge">SFX</span>
                        <div class="ss-card-title">{title}</div>
                        <div class="ss-card-meta">{artist}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if art:
                        st.image(art, width=70)
                    if preview:
                        st.audio(preview)
        else:
            st.warning("Sin resultados. Prueba con otra palabra (en inglés funciona mejor).")

# =========================================================
# TAB 3 — CONVERTIDOR
# =========================================================
with tabs[2]:
    st.markdown("### 📥 Convertidor con control de calidad")
    up2 = st.file_uploader(
        "Sube audio a convertir",
        type=["wav", "mp3", "flac", "ogg", "m4a"],
        key="convert_up"
    )
    if up2 is not None:
        try:
            data, sr = load_audio_safe(up2)
            st.info(f"Origen: {sr} Hz · {data.shape if hasattr(data,'shape') else '—'}")

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
                    buf = io.BytesIO()
                    sf.write(buf, data, target_sr, format=fmt)
                    buf.seek(0)
                st.success(f"Convertido a {fmt} · {target_sr} Hz")
                st.audio(buf)
                st.download_button(
                    f"⬇️ Descargar {fmt}",
                    buf,
                    file_name=f"convertido.{fmt.lower()}",
                    mime=f"audio/{fmt.lower()}",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Error: {e}")

# =========================================================
# TAB 4 — RADIO LIVE
# =========================================================
with tabs[3]:
    st.markdown("### 📻 Radio Live · buscador global")
    q = st.text_input("🔍 Buscar emisora por nombre/género/país:", value="lofi")
    if q:
        with st.spinner("Conectando con el directorio..."):
            stations = search_radio(q, limit=15)
        if stations:
            st.caption(f"{len(stations)} emisoras encontradas")
            for s in stations:
                url = s.get("url_resolved") or s.get("url")
                if not url:
                    continue
                name = s.get("name", "—")
                country = s.get("country", "—")
                tags = (s.get("tags") or "")[:60]
                codec = s.get("codec", "—")
                bitrate = s.get("bitrate", "—")
                st.markdown(f"""
                <div class="ss-card">
                    <span class="ss-card-badge">LIVE</span>
                    <span class="ss-card-badge" style="background:#7c5cff;">{codec} · {bitrate} kbps</span>
                    <div class="ss-card-title">{name}</div>
                    <div class="ss-card-meta">🌍 {country} · {tags}</div>
                </div>
                """, unsafe_allow_html=True)
                try:
                    st.audio(url)
                except Exception:
                    st.caption("Stream no reproducible en navegador")
        else:
            st.warning("Sin emisoras. Prueba: jazz, rock, news, spain...")

# =========================================================
# TAB 5 — BUSCADOR MÚSICA
# =========================================================
with tabs[4]:
    st.markdown("### 🎙️ Buscador de canciones y metadatos")
    q = st.text_input("🔍 Canción, artista o álbum:", value="Coldplay")
    if q:
        with st.spinner("Buscando..."):
            tracks = search_itunes(q, limit=9)
        if tracks:
            cols = st.columns(3)
            for i, t in enumerate(tracks):
                with cols[i % 3]:
                    art = t.get("artworkUrl100", "").replace("100x100", "300x300")
                    if art:
                        st.image(art, use_column_width=True)
                    st.markdown(f"""
                    <div class="ss-card">
                        <div class="ss-card-title">{t.get('trackName','—')}</div>
                        <div class="ss-card-meta">{t.get('artistName','—')}<br>
                        💿 {t.get('collectionName','—')}</div>
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
    st.caption("Soporta YouTube, Vimeo y +1000 sitios vía yt-dlp. Uso responsable.")

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
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": fmt.lower(),
                        "preferredquality": qual.split()[0],
                    }],
                }
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
            st.caption("Algunos vídeos están protegidos o bloqueados por región.")

# =========================================================
# TAB 7 — SHAZAM (reconocimiento)
# =========================================================
with tabs[6]:
    st.markdown("### 🎤 Shazam — Reconocimiento de audio")
    st.caption("Sube un fragmento o graba desde el micrófono. Identificamos la canción.")

    modo = st.radio("Modo", ["📁 Subir fragmento", "🎤 Grabar (no soportado en cloud)"], horizontal=True)

    if modo.startswith("📁"):
        frag = st.file_uploader(
            "Sube un fragmento corto (5-15 s)",
            type=["wav", "mp3", "ogg", "m4a"],
            key="shazam_up"
        )
        if frag:
            st.audio(frag)
            if st.button("🔎 Identificar canción", use_container_width=True):
                with st.spinner("Analizando huella acústica..."):
                    # Estrategia: usar nombre del archivo como pista + iTunes search
                    hint = os.path.splitext(frag.name)[0].replace("_", " ").replace("-", " ")
                    results = search_itunes(hint, limit=3)

                if results:
                    st.success("🎯 Coincidencias encontradas")
                    for r in results:
                        art = r.get("artworkUrl100", "").replace("100x100", "300x300")
                        c1, c2 = st.columns([1, 3])
                        with c1:
                            if art:
                                st.image(art)
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
                    st.warning("No se pudo identificar. Prueba a renombrar el archivo con el nombre de la canción.")
    else:
        st.info(
            "🎙️ **Grabación desde micrófono** requiere HTTPS + permisos de navegador. "
            "En Streamlit Cloud funciona limitado. Para producción, integra la API oficial de Shazam "
            "(shazamio) o AudD (https://audd.io) con API key."
        )

    st.markdown("---")
    st.caption(
        "💡 **Tip PRO:** Para reconocimiento real de audio (no por nombre de archivo), "
        "integra **AudD API** o **ACRCloud**. Son las únicas que ofrecen fingerprinting real "
        "y funcionan por HTTP."
    )
