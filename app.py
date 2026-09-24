import streamlit as st

st.set_page_config(page_title="SoundSnip Studio", page_icon="✂️", layout="wide")

# Encabezado principal
st.title("✂️ SoundSnip Studio")
st.caption("Suite completa de herramientas de audio para creadores de contenido, podcasters y editores.")

# Selección de módulos (Pestañas)
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "✂️ Editor Express", 
    "🔍 Banco SFX", 
    "📥 Conversor", 
    "🎛️ Separador IA", 
    "📻 Radio Live", 
    "🎙️ Shazam"
])

with tab1:
    st.header("Editor Express de Audio")
    uploaded_file = st.file_uploader("Sube tu archivo de audio (MP3, WAV)", type=["mp3", "wav"])
    if uploaded_file:
        st.audio(uploaded_file)
        col1, col2 = st.columns(2)
        with col1:
            crop_start = st.number_input("Punto de inicio (segundos)", value=0.0, step=0.1)
        with col2:
            crop_end = st.number_input("Punto final (segundos)", value=10.0, step=0.1)
        st.button("✂️ Cortar y Descargar Audio")

with tab2:
    st.header("Banco de Efectos de Sonido")
    search_query = st.text_input("Buscar efectos:", placeholder="Ej: lluvia, explosión, aplausos...")
    if search_query:
        st.write(f"Resultados para: **{search_query}**")

with tab3:
    st.header("Extractor y Conversor")
    st.file_uploader("Sube un vídeo (MP4) para extraer su MP3", type=["mp4", "mov"])

with tab4:
    st.header("Separador de Voces e Instrumentales")
    st.info("Módulo de IA para aislamiento de Stems.")

with tab5:
    st.header("Radio en Directo")
    st.radio("Categoría:", ["Noticias", "Trading & Bolsa", "Música Lo-Fi"])

with tab6:
    st.header("Reconocedor de Música")
    if st.button("🎙️ Escuchar e Identificar"):
        st.success("Canción identificada: Trading Beats - Lo-Fi Chill")