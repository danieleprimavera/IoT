import streamlit as st
import paho.mqtt.client as mqtt
import time
import queue
import random
import pandas as pd
import plotly.express as px
from datetime import datetime
import ui_assets
# Importiamo il correttore di contesto per i thread
from streamlit.runtime.scriptrunner import add_script_run_ctx

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="HealthGuard Pro", page_icon="🏥", layout="wide")
st.markdown(ui_assets.DARK_THEME_CSS, unsafe_allow_html=True)

# --- 2. STATO PERSISTENTE ---
if 'registry' not in st.session_state:
    st.session_state['registry'] = {}
if 'found_this_run' not in st.session_state:
    st.session_state['found_this_run'] = set()

PATIENT_NAMES = ["Mario Rossi", "Luca Bianchi", "Elena Verdi", "Giulia Neri", "Marco Brun"]

# --- 3. LOGICA MQTT (THREAD-SAFE) ---
@st.cache_resource
def get_data_queue(): return queue.Queue()
data_queue = get_data_queue()

# NOTA: Qui NON usiamo st.session_state perché siamo in un thread separato
def on_message(client, userdata, msg):
    try:
        parts = msg.topic.split('/')
        if len(parts) == 3:
            rid = parts[1].lower().strip()
            if rid not in ["mover", "patient", ""]:
                data_queue.put((rid, parts[2], msg.payload.decode()))
    except: pass

@st.cache_resource
def start_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect("broker.hivemq.com", 1883, 60)
    client.subscribe("hospital/+/+")
    
    # Avviamo il loop e gli assegniamo il contesto di Streamlit per evitare i warning
    client.loop_start()
    for thread in client._thread_id if hasattr(client, '_thread_id') else []:
        add_script_run_ctx(thread)
    
    return client

mqtt_client = start_mqtt()

# --- 4. ELABORAZIONE DATI (THREAD PRINCIPALE) ---
new_discovery = False

while not data_queue.empty():
    rid, dtype, payload = data_queue.get_nowait()
    
    # Se il reparto è già nel registro ufficiale, aggiorna i dati
    if rid in st.session_state['registry']:
        entry = st.session_state['registry'][rid]
        entry['is_online'] = True
        entry['last_seen'] = time.time()
        
        if dtype == 'data':
            val = int(payload)
            entry['bpm'] = val
            entry.setdefault('history', []).append(val)
            entry.setdefault('time', []).append(datetime.now().strftime("%H:%M:%S"))
            entry['o2'] = random.randint(96, 99) if val <= 100 else random.randint(91, 95)
            if len(entry['history']) > 50:
                entry['history'].pop(0); entry['time'].pop(0)
            
            entry.setdefault('logs', [])
            if val > 100: entry['logs'].insert(0, f"⚠️ {entry['time'][-1]} | BPM CRITICO: {val}")
            elif val < 60: entry['logs'].insert(0, f"📉 {entry['time'][-1]} | BPM BASSO: {val}")
        elif dtype == 'hvac':
            entry['hvac'] = payload
    else:
        # Se non è attivato, aggiungilo alla lista delle scoperte
        if rid not in st.session_state['found_this_run']:
            st.session_state['found_this_run'].add(rid)
            new_discovery = True

# Watchdog Offline (10 secondi)
for rid, data in st.session_state['registry'].items():
    if data.get('is_online') and (time.time() - data['last_seen'] > 10):
        data['is_online'] = False
        data.setdefault('logs', []).insert(0, f"❌ {datetime.now().strftime('%H:%M:%S')} | OFFLINE")

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("### 🏥 SISTEMA REPARTI")
    
    # Stato connessione verificato in tempo reale
    is_connected = mqtt_client.is_connected()
    st.caption(f"{'🟢' if is_connected else '🔴'} Broker: {'Online' if is_connected else 'Offline'}")

    # Notifica nuovi sensori
    if new_discovery:
        st.warning("🔄 Nuovi reparti rilevati!")
        if st.button("AGGIORNA LISTA"):
            st.rerun()
    
    # A) LISTA ATTIVAZIONE
    to_activate = [r for r in st.session_state['found_this_run'] if r not in st.session_state['registry']]
    if to_activate:
        st.subheader("🔎 Sensori Trovati")
        for rid in sorted(to_activate):
            if st.button(f"Attiva {rid.upper()}", key=f"add_{rid}"):
                st.session_state['registry'][rid] = {
                    'bpm': 70, 'hvac': 'OFF', 'history': [], 'time': [], 'logs': [],
                    'patient': random.choice(PATIENT_NAMES), 'o2': 98,
                    'is_online': True, 'last_seen': time.time()
                }
                st.rerun()
        st.markdown("---")

    # B) SELEZIONE REPARTO
    active_wards = sorted(list(st.session_state['registry'].keys()))
    selected_room = None
    if active_wards:
        def ward_label(rid):
            s = "🟢" if st.session_state['registry'][rid].get('is_online') else "🔴"
            return f"{s} {rid.upper()}"
        selected_room = st.selectbox("REPARTI ATTIVI", active_wards, format_func=ward_label, key="unique_selector")
        
        if st.button("🗑️ CANCELLA LOG"):
            st.session_state['registry'][selected_room]['logs'] = []
            st.rerun()
    else:
        st.info("Nessun reparto attivo. Accendi il Collector e i sensori.")

# --- 6. DASHBOARD ---
if selected_room:
    current = st.session_state['registry'][selected_room]
    bpm = current['bpm']
    online = current.get('is_online', False)
    
    if not online: st_txt, st_col, glow = "OFFLINE", "border-red", True
    elif bpm > 100 or bpm < 60: st_txt, st_col, glow = "CRITICAL", "border-red", True
    else: st_txt, st_col, glow = "STABLE", "border-green", False

    st.markdown(ui_assets.get_header_html(f"REPARTO: {selected_room.upper()} | {current['patient']}", bpm if online else 0), unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(ui_assets.get_kpi_card("BATTITO", bpm if online else "--", "BPM", "💓", "border-red" if (bpm > 100 or bpm < 60) else "border-green", bpm > 100), unsafe_allow_html=True)
    with c2: st.markdown(ui_assets.get_kpi_card("HVAC", current['hvac'] if online else "OFF", "", "❄️" if current['hvac']=="ON" else "💤", "border-blue"), unsafe_allow_html=True)
    with c3: st.markdown(ui_assets.get_kpi_card("OSSIGENO", current['o2'] if online else "--", "%", "💧", "border-blue" if current['o2'] > 95 else "border-orange"), unsafe_allow_html=True)
    with c4: st.markdown(ui_assets.get_kpi_card("CONDIZIONE", st_txt, "", "📋", st_col, glow), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns([2, 1])
    with g1:
        st.markdown("### 📈 ANDAMENTO LIVE")
        if online and current.get('history'):
            df = pd.DataFrame({"Time": current['time'], "BPM": current['history']})
            fig = px.area(df, x="Time", y="BPM", template="plotly_dark", height=400)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, width='stretch')
        else: st.warning("⚠️ Sensore non rilevato.")
    
    with g2:
        st.markdown("### 🖥️ LOG REPARTO")
        st.markdown(ui_assets.get_log_html(current.get('logs', [])), unsafe_allow_html=True)

time.sleep(1)
st.rerun()