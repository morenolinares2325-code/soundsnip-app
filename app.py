import streamlit as st
from pydub import AudioSegment
import io

st.set_page_config(page_title="SoundSnip Studio", page_icon="✂️", layout="wide")

st.title("✂️ SoundSnip Studio")
st.caption("Herramientas de edición y procesamiento de audio online.")

tab1, tab2, tab3, tab4 = st.tabs([
    "✂️ Editor Express", 
    "🔍 Banco SFX", 
    "📥 Extractor MP3", 
    "📻 Radio Live"
])

# --- MÓDULO 1: EDITOR EXPRESS FUNCIONAL ---
with tab1:
    st.header("Editor Express: Recortar Audio")
    uploaded_file = st.file_uploader("Sube un archivo de audio (MP3 o WAV):", type=["mp3", "wav"])
    
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split(".")[-1].lower()
        
        # Cargar el audio con pydub
        try:
            audio = AudioSegment.from_file(uploaded_file, format=file_extension)
            duration_sec = len(audio) / 1000.0
            
            st.success(f"Audio cargado con éxito. Duración total: **{duration_sec:.2f} segundos**.")
            st.audio(uploaded_file)
            
            st.subheader("Ajustar Recorte")
            col1, col2 = st.columns(2)
            
            with col1:
                start_sec = st.number_input("Inicio (segundos):", min_value=0.0, max_value=duration_sec, value=0.0, step=0.5)
            with col2:
                end_sec = st.number_input("Fin (segundos):", min_value=0.0, max_value=duration_sec, value=min(10.0, duration_sec), step=0.5)
            
            if start_sec >= end_sec:
                st.error("El tiempo de inicio debe ser menor que el tiempo final.")
            else:
                if st.button("✂️ Procesar y Recortar"):
                    # Convertir segundos a milisegundos para pydub
                    start_ms = int(start_sec * 1000)
                    end_ms = int(end_sec * 1000)
                    
                    cropped_audio = audio[start_ms:end_ms]
                    
                    # Exportar resultado a memoria
                    buffer = io.BytesIO()
                    cropped_audio.export(buffer, format="mp3")
                    buffer.seek(0)
                    
                    st.subheader("🎧 Resultado del Recorte")
                    st.audio(buffer, format="audio/mp3")
                    
                    st.download_button(
                        label="⬇️ Descargar MP3 Cortado",
                        data=buffer,
                        file_name=f"recorte_{uploaded_file.name}",
                        mime="audio/mp3"
                    )
        except Exception as e:
            st.error(f"Error al procesar el archivo: {e}")

# --- MÓDULO 2: BANCO DE EFECTOS DE SONIDO ---
with tab2:
    st.header("Banco SFX (Efectos Rápidos)")
    st.write("Escucha y descarga efectos de sonido para tus proyectos:")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("🔔 **Notificación Pop**")
        st.audio("https://www.soundjay.com/buttons/button-1.mp3")
    with col_b:
        st.write("👏 **Aplausos corto**")
        st.audio("https://www.soundjay.com/human/applause-01.mp3")

# --- MÓDULO 3: EXTRACTOR MP3 ---
with tab3:
    st.header("Extractor de Audio")
    st.info("Sube tu archivo para extraer la pista de sonido limpia.")
    st.file_uploader("Sube un vídeo (MP4) o audio:", type=["mp4", "wav", "aac"])

# --- MÓDULO 4: RADIO LIVE ---
with tab4:
    st.header("Emisoras de Radio en Directo")
    radio_choice = st.selectbox("Selecciona una temática:", ["Música Lo-Fi / Relax", "Noticias y Charla"])
    if radio_choice == "Música Lo-Fi / Relax":
        st.audio("https://stream.zeno.fm/f3wvbbqmdg8uv")
