import streamlit as st
import soundfile as sf
import io
import numpy as np
import matplotlib.pyplot as plt
import requests

st.set_page_config(page_title="SoundSnip Studio", page_icon="✂️", layout="wide")

st.title("✂️ SoundSnip Studio")
st.caption("Herramientas de edición, búsqueda y procesamiento de audio real.")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "✂️ Editor Express", 
    "🔍 Banco SFX", 
    "📥 Extractor / Convertidor", 
    "📻 Radio Live",
    "🎙️ Buscador de Música"
])

# ==========================================
# 1. EDITOR EXPRESS REAL (Corte exacto + Onda)
# ==========================================
with tab1:
    st.header("1. Editor Express: Recortar Audio con Forma de Onda")
    uploaded_file = st.file_uploader("Sube un archivo de audio (WAV, FLAC, OGG):", type=["wav", "flac", "ogg"], key="editor_file")
    
    if uploaded_file is not None:
        try:
            data, samplerate = sf.read(uploaded_file)
            
            # Matriz mono para la representación visual
            if len(data.shape) > 1:
                audio_mono = data.mean(axis=1)
            else:
                audio_mono = data
                
            duration_sec = len(data) / float(samplerate)
            
            st.success(f"Audio cargado. Duración: **{duration_sec:.2f} segundos** | Muestreo: **{samplerate} Hz**")
            st.audio(uploaded_file)
            
            # Dibuja la onda sonora real
            st.subheader("📊 Visualización de la Onda Sonora")
            fig, ax = plt.subplots(figsize=(10, 2.5))
            fig.patch.set_facecolor('#0e1117')
            ax.set_facecolor('#0e1117')
            
            time_axis = np.linspace(0, duration_sec, num=len(audio_mono))
            ax.plot(time_axis, audio_mono, color='#00d46a', alpha=0.7, linewidth=0.5)
            ax.set_xlabel("Tiempo (segundos)", color="white")
            ax.set_ylabel("Amplitud", color="white")
            ax.tick_params(colors='white')
            ax.grid(True, color='#333333', linestyle='--', alpha=0.5)
            
            st.pyplot(fig)
            
            # Proceso de recorte real
            st.subheader("✂️ Ajustar Puntos de Corte")
            col1, col2 = st.columns(2)
            
            with col1:
                start_sec = st.number_input("Punto de Inicio (segundos):", min_value=0.0, max_value=duration_sec, value=0.0, step=0.1)
            with col2:
                end_sec = st.number_input("Punto de Fin (segundos):", min_value=0.0, max_value=duration_sec, value=min(10.0, duration_sec), step=0.1)
            
            if start_sec >= end_sec:
                st.error("El tiempo de inicio debe ser menor que el tiempo de fin.")
            else:
                if st.button("✂️ Procesar y Recortar"):
                    start_sample = int(start_sec * samplerate)
                    end_sample = int(end_sec * samplerate)
                    
                    cropped_data = data[start_sample:end_sample]
                    
                    buffer = io.BytesIO()
                    sf.write(buffer, cropped_data, samplerate, format='WAV')
                    buffer.seek(0)
                    
                    st.subheader("🎧 Resultado del Recorte")
                    st.audio(buffer, format="audio/wav")
                    
                    st.download_button(
                        label="⬇️ Descargar Recorte (.wav)",
                        data=buffer,
                        file_name=f"recorte_{uploaded_file.name}",
                        mime="audio/wav"
                    )
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

# ==========================================
# 2. BANCO DE SFX REAL (Consulta API iTunes en vivo)
# ==========================================
with tab2:
    st.header("2. Banco SFX y Previsulización de Efectos/Sonidos")
    sfx_query = st.text_input("🔍 Buscar efecto o sonido (ej: 'rain', 'bell', 'guitar', 'applause'):", value="bell")
    
    if sfx_query:
        st.write(f"Resultados en tiempo real para: **{sfx_query}**")
        try:
            # Petición HTTP real a la API pública
            api_url = f"https://itunes.apple.com/search?term={sfx_query}&entity=song&limit=6"
            response = requests.get(api_url).json()
            
            results = response.get("results", [])
            if results:
                for item in results:
                    col_info, col_player = st.columns([1, 2])
                    with col_info:
                        st.write(f"🔊 **{item.get('trackName', 'Sonido')}**")
                        st.caption(f"Artista/Origen: {item.get('artistName', 'Desconocido')}")
                    with col_player:
                        preview_url = item.get("previewUrl")
                        if preview_url:
                            st.audio(preview_url)
            else:
                st.warning("No se encontraron efectos para esa búsqueda.")
        except Exception as e:
            st.error(f"Error al conectar con el servidor de sonido: {e}")

# ==========================================
# 3. EXTRACTOR / CONVERTIDOR DE AUDIO REAL
# ==========================================
with tab3:
    st.header("3. Extractor y Convertidor de Audio")
    uploaded_convert = st.file_uploader("Sube tu archivo de audio (WAV, FLAC, OGG):", type=["wav", "flac", "ogg"], key="convert_file")
    
    if uploaded_convert is not None:
        try:
            data, samplerate = sf.read(uploaded_convert)
            st.info(f"Archivo subido correctamente. Frecuencia de muestreo original: **{samplerate} Hz**")
            
            output_format = st.selectbox("Selecciona formato de conversión:", ["WAV", "FLAC", "OGG"])
            
            if st.button("🚀 Convertir y Procesar"):
                buffer = io.BytesIO()
                sf.write(buffer, data, samplerate, format=output_format)
                buffer.seek(0)
                
                st.success(f"¡Convertido con éxito a formato {output_format}!")
                st.audio(buffer, format=f"audio/{output_format.lower()}")
                
                st.download_button(
                    label=f"⬇️ Descargar en {output_format}",
                    data=buffer,
                    file_name=f"convertido_{uploaded_convert.name.split('.')[0]}.{output_format.lower()}",
                    mime=f"audio/{output_format.lower()}"
                )
        except Exception as e:
            st.error(f"Error en la conversión: {e}")

# ==========================================
# 4. RADIO LIVE REAL (Conexión API Radio Browser)
# ==========================================
with tab4:
    st.header("4. Emisoras de Radio en Directo (Buscador Global)")
    radio_search = st.text_input("🔍 Buscar emisoras por género, ciudad o país:", value="Lo-Fi")
    
    if radio_search:
        try:
            res = requests.get(f"https://de1.api.radio-browser.info/json/stations/byname/{radio_search}?limit=5", timeout=5)
            stations = res.json()
            
            if stations:
                for st_info in stations:
                    stream_url = st_info.get("url_resolved") or st_info.get("url")
                    if stream_url:
                        st.write(f"📻 **{st_info.get('name', 'Emisora')}** — *{st_info.get('country', 'Global')}*")
                        st.audio(stream_url)
            else:
                st.warning("No se encontraron emisoras activas con ese término.")
        except Exception:
            st.warning("Servidor de radio no disponible momentáneamente. Emisora por defecto:")
            st.audio("https://stream.zeno.fm/f3wvbbqmdg8uv")

# ==========================================
# 5. BUSCADOR Y RECONOCEDOR DE MÚSICA REAL
# ==========================================
with tab5:
    st.header("5. Buscador de Canciones y Metadatos")
    song_query = st.text_input("🔍 Introduce el nombre de una canción o letra para identificar sus datos:", value="Shape of You")
    
    if song_query:
        try:
            res = requests.get(f"https://itunes.apple.com/search?term={song_query}&entity=song&limit=3").json()
            tracks = res.get("results", [])
            
            if tracks:
                for track in tracks:
                    col_img, col_det = st.columns([1, 3])
                    with col_img:
                        if track.get("artworkUrl100"):
                            st.image(track.get("artworkUrl100"))
                    with col_det:
                        st.subheader(track.get("trackName"))
                        st.write(f"**Artista:** {track.get('artistName')}")
                        st.write(f"**Álbum:** {track.get('collectionName')}")
                        if track.get("previewUrl"):
                            st.audio(track.get("previewUrl"))
            else:
                st.warning("No se encontraron resultados para esta búsqueda.")
        except Exception as e:
            st.error(f"Error al realizar la consulta: {e}")
