# FILE: ui_assets.py
# Gestione grafica avanzata con fix per pulsante Sidebar

DARK_THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&family=Inter:wght@400;800&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Pulizia Interfaccia */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* FIX: Invece di nascondere tutto l'header, nascondiamo solo la barra colorata */
    /* Questo permette al pulsante della sidebar (freccetta) di rimanere visibile */
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
        border: none;
    }

    /* Styling specifico per il pulsante di apertura Sidebar (la freccetta) */
    button[kind="header"] {
        background-color: #1e293b !important;
        color: #3b82f6 !important;
        border: 1px solid #334155 !important;
        border-radius: 5px !important;
        margin-left: 10px !important;
    }

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
    .header-title h1 { margin: 0; color: #f8fafc; font-size: 24px; font-weight: 800; }
    .header-subtitle { color: #3b82f6; font-family: 'Roboto Mono', monospace; font-size: 13px; font-weight: 700; margin-top: 5px; }

    .kpi-card {
        background: #1e293b;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #334155;
        position: relative;
        overflow: hidden;
        transition: transform 0.3s ease;
    }
    .kpi-card:hover { transform: translateY(-5px); }
    .kpi-card::before { content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%; }
    .kpi-title { color: #94a3b8; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; }
    .kpi-value { 
        color: #f8fafc; 
        font-size: 1.8rem; /* Ridotto da 2.2rem a 1.8rem per evitare il testo a capo */
        font-weight: 700; 
        font-family: 'Roboto Mono', monospace; 
        white-space: nowrap; /* Impedisce al testo di andare a capo */
    }
    .kpi-unit { font-size: 1rem; color: #64748b; margin-left: 5px; }
    .kpi-icon { float: right; font-size: 1.5rem; opacity: 0.8; }

    .border-blue::before { background-color: #3b82f6; }
    .border-red::before { background-color: #ef4444; }
    .border-green::before { background-color: #10b981; }
    .border-orange::before { background-color: #f59e0b; }
    
    .glow-red { box-shadow: 0 0 20px rgba(239, 68, 68, 0.5); border: 1px solid #ef4444; }

    .status-badge { padding: 6px 12px; border-radius: 6px; font-family: 'Roboto Mono', monospace; font-weight: 700; font-size: 0.8rem; border: 1px solid; }
    .badge-green { background: rgba(16, 185, 129, 0.1); color: #34d399; border-color: #10b981; }
    .badge-red { background: rgba(239, 68, 68, 0.1); color: #f87171; border-color: #ef4444; animation: pulse 1.5s infinite; }

    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.5; } 100% { opacity: 1; } }

    .log-container {
        background: #0f172a; 
        color: #10b981; 
        font-family: 'Roboto Mono', monospace;
        padding: 15px; 
        border-radius: 10px; 
        height: 400px; 
        overflow-y: auto;
        font-size: 0.85rem; 
        border: 1px solid #334155;
        box-shadow: inset 0 2px 10px rgba(0,0,0,0.5);
    }
    .log-entry { 
        border-bottom: 1px solid #1e293b; 
        padding: 6px 0; 
        line-height: 1.4;
    }
</style>
"""

def get_header_html(room_display_name, bpm):
    is_critical = bpm > 100 or bpm < 60
    status_class = "badge-red" if is_critical else "badge-green"
    status_text = "● CRITICAL CONDITION" if is_critical else "● STATUS: STABLE"

    return f"""
    <div class="main-header">
        <div class="header-title">
            <h1>HEALTHGUARD <span style="color:#3b82f6">CORE</span></h1>
            <div class="header-subtitle">>> MONITORING ACTIVE: {room_display_name}</div>
        </div>
        <div class="status-badge {status_class}">
            {status_text}
        </div>
    </div>
    """

def get_kpi_card(title, value, unit, icon, color_class, glow=False):
    glow_class = "glow-red" if glow else ""
    return f"""
    <div class="kpi-card {color_class} {glow_class}">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}<span class="kpi-unit">{unit}</span></div>
    </div>
    """

def get_log_html(event_log):
    log_html = '<div class="log-container">'
    if event_log:
        for log in event_log:
            color = "#f87171" if "CRITICAL" in log or "LOW" in log else "#34d399"
            if "HVAC" in log: color = "#60a5fa"
            if "NEW DEVICE" in log: color = "#fbbf24"
            log_html += f'<div class="log-entry" style="color:{color}">{log}</div>'
    else:
        log_html += '<div class="log-entry" style="color:#64748b">>> No active events recorded for this zone.</div>'
    log_html += '</div>'
    return log_html