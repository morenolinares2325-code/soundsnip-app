# =====================================================================
# 1) SUSTITUYE tu función setup_deno() y la línea DENO_PATH = ... por esto
#    (añade también arriba: import urllib.request, zipfile, shutil)
# =====================================================================
import urllib.request
import zipfile
import shutil


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

# Mapas de formato (OGG en yt-dlp se llama "vorbis")
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


# =====================================================================
# 2) SUSTITUYE todo el bloque "with tabs[5]:" por esto
# =====================================================================
with tabs[5]:
    st.markdown("### 🔗 Video → Audio")

    if not FFMPEG_OK:
        st.error("ffmpeg no está instalado. En Streamlit Cloud crea `packages.txt` con la línea `ffmpeg`.")

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
        st.caption("YouTube, Vimeo, SoundCloud… Desde servidores en la nube YouTube suele bloquear; en local funciona mucho mejor.")
        st.caption("🟢 Motor JS activo" if DENO_PATH else "🔴 Motor JS no disponible")
        url = st.text_input("🔗 Enlace del vídeo:", placeholder="https://www.youtube.com/watch?v=...",
                            key="va_url")

        if url and st.button("🎬 Extraer audio", use_container_width=True, key="va_btn_url"):
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
                        info = ydl.extract_info(url, download=True)

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
