# FILE: ui_assets.py
# Questo modulo gestisce solo l'aspetto grafico (View Layer)

# --- 1. CSS STYLESHEET ---
DARK_THEME_CSS = """
<style>
    /* Import Font Tecnico */
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Inter:wght@400;800&display=swap');

    /* Reset e Colori Base */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* NASCONDE ELEMENTI STREAMLIT */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeaderActionElements"] {display: none;}
    
    /* Header Styling */
    .main-header {
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .header-title h1 { margin: 0; color: #f8fafc; font-size: 24px; font-weight: 800; letter-spacing: -0.5px; }
    .header-subtitle { color: #94a3b8; font-family: 'Roboto Mono', monospace; font-size: 12px; margin-top: 5px; }

    /* KPI CARD DARK */
    .kpi-card {
        background: #1e293b;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before { content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%; }
    .kpi-title { color: #94a3b8; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
    .kpi-value { color: #f8fafc; font-size: 2.2rem; font-weight: 700; font-family: 'Roboto Mono', monospace; }
    .kpi-unit { font-size: 1rem; color: #64748b; font-weight: 400; margin-left: 5px; }
    .kpi-icon { float: right; font-size: 1.5rem; opacity: 0.8; }

    /* Varianti Colore Border */
    .border-blue::before { background-color: #3b82f6; }
    .border-red::before { background-color: #ef4444; }
    .border-green::before { background-color: #10b981; }
    .border-orange::before { background-color: #f59e0b; }
    
    /* Effetto Glow */
    .glow-red { box-shadow: 0 0 15px rgba(239, 68, 68, 0.4); border: 1px solid #ef4444; }

    /* Status Badge */
    .status-badge { padding: 6px 12px; border-radius: 4px; font-family: 'Roboto Mono', monospace; font-weight: 700; font-size: 0.8rem; border: 1px solid; }
    .badge-green { background: rgba(16, 185, 129, 0.2); color: #34d399; border-color: #059669; }
    .badge-red { background: rgba(239, 68, 68, 0.2); color: #f87171; border-color: #b91c1c; box-shadow: 0 0 10px rgba(239,68,68,0.3); animation: pulse 2s infinite; }

    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }

    /* Log Console Style */
    .log-container {
        background: #0f172a; color: #10b981; font-family: 'Roboto Mono', monospace;
        padding: 15px; border-radius: 10px; height: 350px; overflow-y: auto;
        font-size: 0.8rem; border: 1px solid #334155;
    }
    .log-entry { border-bottom: 1px solid #1e293b; padding: 4px 0; }
</style>
"""

# --- 2. HTML TEMPLATES ---

def get_header_html(room_name, bpm):
    """Genera l'HTML per l'intestazione principale"""
    is_critical = bpm > 100 or bpm < 60
    status_class = "badge-red" if is_critical else "badge-green"
    status_text = "⚠️ CRITICAL ALERT" if is_critical else "✅ SYSTEM NOMINAL"

    return f"""
    <div class="main-header">
        <div class="header-title">
            <h1>HEALTHGUARD <span style="color:#3b82f6">PRIME</span></h1>
            <div class="header-subtitle">REAL-TIME BIOMETRIC MONITORING SYSTEM • {room_name}</div>
        </div>
        <div class="status-badge {status_class}">
            {status_text}
        </div>
    </div>
    """

def get_kpi_card(title, value, unit, icon, color_class, glow=False):
    """Genera l'HTML per le singole card (BPM, HVAC, ecc.)"""
    glow_class = "glow-red" if glow else ""
    return f"""
    <div class="kpi-card {color_class} {glow_class}">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}<span class="kpi-unit">{unit}</span></div>
    </div>
    """

def get_log_html(event_log):
    """Genera l'HTML per il log laterale stile terminale"""
    log_html = '<div class="log-container">'
    if event_log:
        for log in event_log:
            color = "#f87171" if "CRITICAL" in log or "LOW" in log else "#34d399"
            if "HVAC" in log: color = "#60a5fa"
            log_html += f'<div class="log-entry" style="color:{color}">{log}</div>'
    else:
        log_html += '<div class="log-entry" style="color:#64748b">System initialized. Listening on port 1883...</div>'
    log_html += '</div>'
    return log_html