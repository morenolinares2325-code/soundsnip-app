'use client';

import React, { useState, useRef, useEffect } from 'react';
import { 
  Scissors, Radio, Search, Wand2, Download, Play, Pause, 
  Volume2, Music, Sparkles, Check, ArrowRight, Zap, RefreshCw, 
  Globe, Mic, Disc, ShieldCheck, HelpCircle, FileAudio, ZoomIn, ZoomOut
} from 'lucide-react';

export default function Home() {
  const [activeTab, setActiveTab] = useState('editor');
  const [isPro, setIsPro] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(12.4);
  const [duration, setDuration] = useState(180);
  const [cropStart, setCropStart] = useState(15.0);
  const [cropEnd, setCropEnd] = useState(45.5);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [exportFormat, setExportFormat] = useState('MP3 (320kbps - HQ)');
  
  // Estados para módulos
  const [searchSFX, setSearchSFX] = useState('');
  const [radioCategory, setRadioCategory] = useState('news');
  const [isShazaming, setIsShazaming] = useState(false);
  const [shazamResult, setShazamResult] = useState(null);

  // Lienzo para el Histograma / Forma de Onda
  const canvasRef = useRef(null);

  // Dibujar Histograma de Onda y Ritmo en el Editor
  useEffect(() => {
    if (activeTab !== 'editor') return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    // Fondo del lienzo
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(0, 0, width, height);

    // Rejilla de tiempo
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    for (let x = 0; x < width; x += 40 * zoomLevel) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }

    // Dibujar Histograma / Forma de Onda
    const barWidth = 3 * zoomLevel;
    const gap = 1.5;
    const totalBars = Math.floor(width / (barWidth + gap));

    for (let i = 0; i < totalBars; i++) {
      const x = i * (barWidth + gap);
      
      // Simular volumen con picos de batería y silencios
      const timeSec = (i / totalBars) * duration;
      let amplitude = Math.sin(i * 0.15) * 0.4 + Math.cos(i * 0.3) * 0.3 + 0.3;
      
      if ((i > 30 && i < 42) || (i > 110 && i < 125)) {
        amplitude = 0.05; 
      }

      const barHeight = Math.max(4, amplitude * (height * 0.75));
      const y = (height - barHeight) / 2;

      if (timeSec >= cropStart && timeSec <= cropEnd) {
        ctx.fillStyle = '#6366f1'; 
      } else {
        ctx.fillStyle = '#334155'; 
      }

      ctx.fillRect(x, y, barWidth, barHeight);
    }

    // Marcador de ENTRADA (Inicio de corte)
    const startX = (cropStart / duration) * width;
    ctx.fillStyle = '#10b981';
    ctx.fillRect(startX - 2, 0, 4, height);
    
    // Marcador de SALIDA (Fin de corte)
    const endX = (cropEnd / duration) * width;
    ctx.fillStyle = '#ef4444';
    ctx.fillRect(endX - 2, 0, 4, height);

  }, [activeTab, cropStart, cropEnd, zoomLevel, duration]);

  // Simular Identificador Shazam
  const handleShazam = () => {
    setIsShazaming(true);
    setShazamResult(null);
    setTimeout(() => {
      setIsShazaming(false);
      setShazamResult({
        title: "Trading Frequencies & Beats",
        artist: "Lo-Fi Master",
        album: "Financial Chill 2026",
        genre: "Electronic / Deep House"
      });
    }, 3000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      
      {/* HEADER / BARRA NAVEGACIÓN */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-3 flex justify-between items-center">
          <div className="flex items-center gap-2 cursor-pointer" onClick={() => setActiveTab('editor')}>
            <div className="p-2 bg-indigo-600 rounded-lg text-white">
              <Zap className="w-5 h-5 fill-current" />
            </div>
            <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
              SoundSnip<span className="text-slate-100">Studio</span>
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${isPro ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 'bg-slate-800 text-slate-400'}`}>
              {isPro ? '✨ PLAN PRO ACTIVO' : 'PLAN GRATUITO'}
            </span>
            <button 
              onClick={() => setIsPro(!isPro)} 
              className="bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white px-4 py-1.5 rounded-lg text-sm font-semibold shadow-lg transition"
            >
              {isPro ? 'Gestionar Cuenta' : 'Obtener Pro (5€/mes)'}
            </button>
          </div>
        </div>
      </header>

      {/* NAVEGACIÓN POR PESTAÑAS (LOS 6 MÓDULOS) */}
      <nav className="bg-slate-900 border-b border-slate-800 sticky top-[57px] z-40">
        <div className="max-w-7xl mx-auto px-4 flex overflow-x-auto gap-1 py-2 scrollbar-none">
          {[
            { id: 'editor', name: '✂️ Editor Express', desc: 'Corte por histograma' },
            { id: 'sfx', name: '🔍 Banco SFX', desc: '+500k efectos' },
            { id: 'conversor', name: '📥 Extractor & Conversor', desc: 'Vídeo a MP3 / Formatos' },
            { id: 'stems', name: '🎛️ Separador IA', desc: 'Vocal Remover' },
            { id: 'radio', name: '📻 Radio en Directo', desc: 'Noticias, Trading y Música' },
            { id: 'shazam', name: '🎙️ Identificar Música', desc: 'Reconocedor Shazam' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex flex-col px-4 py-2 rounded-lg text-left whitespace-nowrap transition ${
                activeTab === tab.id 
                  ? 'bg-indigo-600 text-white shadow' 
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <span className="font-bold text-sm">{tab.name}</span>
              <span className="text-[10px] opacity-80">{tab.desc}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* CONTENIDO PRINCIPAL DE LA APP */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 md:p-6">

        {/* 1. MÓDULO: EDITOR EXPRESS */}
        {activeTab === 'editor' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center flex-wrap gap-4">
              <div>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                  <Scissors className="text-indigo-400" /> Editor Express con Histograma
                </h1>
                <p className="text-slate-400 text-sm">Visualiza los golpes de percusión y silencios para cortar la estrofa exacta.</p>
              </div>

              <div className="flex items-center gap-2 bg-slate-900 p-1.5 rounded-lg border border-slate-800">
                <button onClick={() => setZoomLevel(Math.max(0.5, zoomLevel - 0.25))} className="p-1.5 hover:bg-slate-800 rounded">
                  <ZoomOut className="w-4 h-4" />
                </button>
                <span className="text-xs font-mono w-12 text-center">{Math.round(zoomLevel * 100)}%</span>
                <button onClick={() => setZoomLevel(Math.min(2.5, zoomLevel + 0.25))} className="p-1.5 hover:bg-slate-800 rounded">
                  <ZoomIn className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* VISOR CANVAS HISTOGRAMA */}
            <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 shadow-xl space-y-4">
              <div className="relative">
                <canvas 
                  ref={canvasRef} 
                  width={1000} 
                  height={180} 
                  className="w-full h-44 rounded-lg bg-slate-950 cursor-crosshair"
                />
              </div>

              {/* PANEL DE CONTROL DE TIEMPO Y AJUSTES */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-950 p-4 rounded-lg border border-slate-800/80">
                <div>
                  <label className="text-xs text-emerald-400 font-bold block mb-1">🟢 INICIO CORTE (ENTRADA)</label>
                  <input 
                    type="number" 
                    step="0.1" 
                    value={cropStart} 
                    onChange={e => setCropStart(Number(e.target.value))}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-sm font-mono text-emerald-400"
                  />
                </div>

                <div>
                  <label className="text-xs text-rose-400 font-bold block mb-1">🔴 FIN CORTE (SALIDA)</label>
                  <input 
                    type="number" 
                    step="0.1" 
                    value={cropEnd} 
                    onChange={e => setCropEnd(Number(e.target.value))}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-sm font-mono text-rose-400"
                  />
                </div>

                <div>
                  <label className="text-xs text-indigo-400 font-bold block mb-1">⏱️ DURACIÓN SELECCIONADA</label>
                  <div className="bg-slate-900 border border-slate-800 rounded px-3 py-1.5 text-sm font-mono text-indigo-300">
                    {(cropEnd - cropStart).toFixed(2)} segundos
                  </div>
                </div>
              </div>

              {/* OPCIONES DE EXPORTACIÓN Y DESCARGA */}
              <div className="flex flex-wrap justify-between items-center gap-4 pt-2">
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium">Formato de Descarga:</span>
                  <select 
                    value={exportFormat} 
                    onChange={e => setExportFormat(e.target.value)}
                    className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-sm font-semibold text-indigo-300"
                  >
                    <option>MP3 (320kbps - Alta Calidad)</option>
                    <option>WAV (24-bit Sin Pérdida)</option>
                    <option>FLAC (Audio Studio)</option>
                    <option>OGG Web Format</option>
                  </select>
                </div>

                <button className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2.5 rounded-lg font-bold flex items-center gap-2 shadow-lg transition">
                  <Download className="w-5 h-5" /> Exportar y Descargar Audio
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 2. MÓDULO: BANCO SFX */}
        {activeTab === 'sfx' && (
          <div className="space-y-6">
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Search className="text-indigo-400" /> Banco de Efectos de Sonido
            </h1>
            <div className="flex gap-2">
              <input 
                type="text" 
                placeholder="Buscar efectos: 'lluvia', 'explosión', 'transición', 'notificación'..." 
                value={searchSFX}
                onChange={e => setSearchSFX(e.target.value)}
                className="flex-1 bg-slate-900 border border-slate-800 rounded-lg px-4 py-2.5 text-sm"
              />
              <button className="bg-indigo-600 px-6 py-2.5 rounded-lg font-bold">Buscar</button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {['Explosión Cine HD', 'Lluvia Ligera y Trueno', 'Transición Whoosh 02', 'Aplausos Público'].map((item, idx) => (
                <div key={idx} className="bg-slate-900 p-4 rounded-xl border border-slate-800 flex justify-between items-center">
                  <div>
                    <h3 className="font-bold text-sm">{item}</h3>
                    <span className="text-xs text-slate-500">Formato WAV • 0:05 seg</span>
                  </div>
                  <div className="flex gap-2">
                    <button className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg"><Play className="w-4 h-4" /></button>
                    <button onClick={() => setActiveTab('editor')} className="px-3 py-1.5 bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs rounded-lg font-semibold">Abrir en Editor</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 3. MÓDULO: CONVERSOR */}
        {activeTab === 'conversor' && (
          <div className="max-w-2xl mx-auto space-y-6 text-center py-8">
            <h1 className="text-2xl font-bold">📥 Extractor de Vídeo a MP3 y Conversor</h1>
            <div className="border-2 border-dashed border-slate-800 bg-slate-900/50 rounded-2xl p-10 hover:border-indigo-500 transition cursor-pointer">
              <FileAudio className="w-12 h-12 text-indigo-400 mx-auto mb-3" />
              <p className="font-bold text-lg">Arrastra tu archivo aquí o haz clic para subir</p>
              <p className="text-slate-500 text-xs mt-1">Soporta MP4, MOV, AVI, MP3, WAV, FLAC, OGG</p>
            </div>
          </div>
        )}

        {/* 4. MÓDULO: SEPARADOR IA */}
        {activeTab === 'stems' && (
          <div className="space-y-6">
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Wand2 className="text-indigo-400" /> Separador de Voces y Pistas (IA)
            </h1>
            <p className="text-slate-400 text-sm">Aísla automáticamente la voz, batería, bajo y música de cualquier canción.</p>
            
            <div className="bg-slate-900 p-6 rounded-xl border border-slate-800 space-y-4">
              {['🎤 Pista Vocal', '🥁 Batería y Percusión', '🎸 Bajo', '🎹 Instrumental / Melodía'].map((stem, i) => (
                <div key={i} className="flex items-center justify-between bg-slate-950 p-3 rounded-lg border border-slate-800">
                  <span className="font-bold text-sm">{stem}</span>
                  <div className="flex items-center gap-3">
                    <input type="range" className="w-32 accent-indigo-500" />
                    <button className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-xs font-bold">Descargar Stem</button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 5. MÓDULO: RADIO EN DIRECTO */}
        {activeTab === 'radio' && (
          <div className="space-y-6">
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Radio className="text-indigo-400" /> Radio Mundial en Directo
            </h1>
            <div className="flex gap-2">
              {['news', 'trading', 'music'].map(cat => (
                <button 
                  key={cat} 
                  onClick={() => setRadioCategory(cat)}
                  className={`px-4 py-1.5 rounded-lg text-sm font-bold capitalize ${radioCategory === cat ? 'bg-indigo-600 text-white' : 'bg-slate-900 text-slate-400'}`}
                >
                  {cat === 'news' ? '📰 Noticias' : cat === 'trading' ? '📈 Trading & Bolsa' : '🎵 Música Lo-Fi / Chill'}
                </button>
              ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {['Bloomberg Radio Live', 'Radio Intereconomía', 'CNBC Market Watch', 'BBC World Service'].map((station, i) => (
                <div key={i} className="bg-slate-900 p-4 rounded-xl border border-slate-800 flex justify-between items-center">
                  <div>
                    <h3 className="font-bold text-sm">{station}</h3>
                    <span className="text-xs text-emerald-400">🔴 En Directo • 128 kbps</span>
                  </div>
                  <button className="p-3 bg-indigo-600 hover:bg-indigo-500 rounded-full text-white"><Play className="w-4 h-4" /></button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 6. MÓDULO: RECONOCEDOR SHAZAM */}
        {activeTab === 'shazam' && (
          <div className="max-w-md mx-auto text-center space-y-6 py-8">
            <h1 className="text-2xl font-bold">🎙️ Identificador de Música</h1>
            <p className="text-slate-400 text-sm">Escucha la música de tu entorno o de una pestaña y reconoce el título en segundos.</p>
            
            <button 
              onClick={handleShazam} 
              disabled={isShazaming}
              className={`w-36 h-36 rounded-full border-4 border-indigo-500/30 bg-gradient-to-tr from-indigo-600 to-violet-600 mx-auto flex flex-col items-center justify-center shadow-2xl transition transform hover:scale-105 ${isShazaming ? 'animate-pulse' : ''}`}
            >
              <Disc className={`w-12 h-12 text-white ${isShazaming ? 'animate-spin' : ''}`} />
              <span className="text-xs font-bold mt-2">{isShazaming ? 'Escuchando...' : 'PULSAR'}</span>
            </button>

            {shazamResult && (
              <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 text-left space-y-2">
                <h3 className="font-bold text-indigo-400">{shazamResult.title}</h3>
                <p className="text-sm text-slate-300">Artista: {shazamResult.artist}</p>
                <p className="text-xs text-slate-500">Álbum: {shazamResult.album}</p>
                <button onClick={() => setActiveTab('editor')} className="w-full mt-2 py-2 bg-indigo-600 text-white rounded-lg font-bold text-xs">
                  Buscar en el Editor / Cortar
                </button>
              </div>
            )}
          </div>
        )}

      </main>

      {/* FOOTER */}
      <footer className="border-t border-slate-800 bg-slate-900/50 py-6 text-center text-xs text-slate-500">
        <p>© 2026 SoundSnip Studio — Todos los derechos reservados. Listo para desplegar en Vercel.</p>
      </footer>
    </div>
  );
}