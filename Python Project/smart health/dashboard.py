import streamlit as st
import paho.mqtt.client as mqtt
import time
import queue
import random
import pandas as pd
import plotly.express as px
from datetime import datetime
import ui_assets
import re # Per pulizia stringhe profonda
from streamlit.runtime.scriptrunner import add_script_run_ctx

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="HealthGuard Pro", page_icon="🏥", layout="wide")
st.markdown(ui_assets.DARK_THEME_CSS, unsafe_allow_html=True)

# --- 2. REGISTRO UNICO (SORGENTE DI VERITÀ) ---
if 'registry' not in st.session_state:
    st.session_state['registry'] = {}
if 'found_this_run' not in st.session_state:
    st.session_state['found_this_run'] = set()

PATIENT_NAMES = ["Mario Rossi", "Luca Bianchi", "Elena Verdi", "Giulia Neri", "Marco Brun"]

# --- 3. LOGICA MQTT (ID SANITIZATION) ---
@st.cache_resource
def get_data_queue(): return queue.Queue()
data_queue = get_data_queue()

def on_message(client, userdata, msg):
    try:
        parts = msg.topic.split('/')
        if len(parts) == 3:
            # ⚡ PULIZIA PROFONDA: Rimuove OGNI carattere non alfanumerico (spazi, \r, \n)
            raw_id = parts[1].lower()
            rid = re.sub(r'[^a-zA-Z0-9]', '', raw_id)
            
            if rid not in ["mover", "patient", ""]:
                data_queue.put((rid, parts[2], msg.payload.decode()))
    except: pass

@st.cache_resource
def start_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect("broker.hivemq.com", 1883, 60)
    client.subscribe("hospital/+/+")
    client.loop_start()
    for thread in client._thread_id if hasattr(client, '_thread_id') else []:
        add_script_run_ctx(thread)
    return client

mqtt_client = start_mqtt()

# --- 4. ELABORAZIONE DATI (SINCRONIZZATA) ---
new_discovery_alert = False
while not data_queue.empty():
    rid, dtype, payload = data_queue.get_nowait()
    
    # Se la stanza è nel registro attivo
    if rid in st.session_state['registry']:
        # 🛡️ PROTEZIONE: Rimuovila istantaneamente dalle scoperte se è già attiva
        st.session_state['found_this_run'].discard(rid)
        
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
            
            # Log Allarmi
            entry.setdefault('logs', [])
            if val > 100: entry['logs'].insert(0, f"⚠️ {entry['time'][-1]} | BPM CRITICO: {val}")
            elif val < 60: entry['logs'].insert(0, f"📉 {entry['time'][-1]} | BPM BASSO: {val}")
        elif dtype == 'hvac': 
            entry['hvac'] = payload
    else:
        # Se non è attiva, aggiungi a scoperte
        if rid not in st.session_state['found_this_run']:
            st.session_state['found_this_run'].add(rid)
            new_discovery_alert = True

# Watchdog Offline
for rid, data in st.session_state['registry'].items():
    if data.get('is_online') and (time.time() - data['last_seen'] > 10):
        data['is_online'] = False
        data.setdefault('logs', []).insert(0, f"❌ {datetime.now().strftime('%H:%M:%S')} | OFFLINE")

# --- 5. SIDEBAR (UNICA E GERARCHICA) ---
with st.sidebar:
    st.markdown("### 🏥 SISTEMA REPARTI")
    st.caption(f"{'🟢' if mqtt_client.is_connected() else '🔴'} Broker: {'Online' if mqtt_client.is_connected() else 'Offline'}")

    # 5a. REPARTI ATTIVI (Solo se presenti)
    active_wards = sorted(list(st.session_state['registry'].keys()))
    selected_room = None

    if active_wards:
        def ward_label(rid):
            s = "🟢" if st.session_state['registry'][rid].get('is_online') else "🔴"
            return f"{s} {rid.upper()}"
        
        selected_room = st.selectbox("REPARTI ATTIVI", active_wards, format_func=ward_label, key="main_sel")
        if st.button("🗑️ CANCELLA LOG"):
            st.session_state['registry'][selected_room]['logs'] = []
            st.rerun()
        st.markdown("---")

    # 5b. NUOVI SENSORI (Esclude categoricamente quelli già attivi)
    to_activate = [r for r in st.session_state['found_this_run'] if r not in st.session_state['registry']]
    
    if to_activate:
        st.subheader("🔎 Nuovi Sensori")
        for rid in sorted(to_activate):
            if st.button(f"Aggiungi {rid.upper()}", key=f"add_{rid}"):
                st.session_state['registry'][rid] = {
                    'bpm': 70, 'hvac': 'OFF', 'history': [], 'time': [], 'logs': [],
                    'patient': random.choice(PATIENT_NAMES), 'o2': 98,
                    'is_online': True, 'last_seen': time.time()
                }
                # Rimuovi forzatamente dalla scoperta al click
                st.session_state['found_this_run'].discard(rid)
                st.rerun()
        
        if new_discovery_alert:
            st.caption("🔄 Nuovi dati in coda. Clicca per aggiungere.")
    
    if not active_wards and not to_activate:
        st.info("In attesa di sensori...")

# --- 6. DASHBOARD ---
if selected_room:
    current = st.session_state['registry'][selected_room]
    bpm, online = current['bpm'], current.get('is_online', False)
    
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
        st.markdown("### 📈 MONITORAGGIO LIVE")
        if online and current.get('history'):
            df = pd.DataFrame({"Time": current['time'], "BPM": current['history']})
            fig = px.area(df, x="Time", y="BPM", template="plotly_dark", height=400)
            # Colore grafico dinamico
            graph_color = '#ef4444' if (bpm > 100 or bpm < 60) else '#10b981'
            fig.update_traces(line_color=graph_color)
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, width='stretch')
        else: st.warning("⚠️ Collegamento interrotto.")
    with g2:
        st.markdown("### 🖥️ LOG REPARTO")
        st.markdown(ui_assets.get_log_html(current.get('logs', [])), unsafe_allow_html=True)

time.sleep(1)
st.rerun()