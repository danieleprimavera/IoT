import streamlit as st
import paho.mqtt.client as mqtt
import time
import queue
import pandas as pd
import plotly.express as px
from datetime import datetime
import ui_assets  # <--- IMPORTIAMO IL NUOVO FILE

# --- 1. CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="HealthGuard Center",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inietta il CSS dal file esterno
st.markdown(ui_assets.DARK_THEME_CSS, unsafe_allow_html=True)

# --- 2. LOGICA BACKEND (MQTT & STATE) ---
BROKER = "broker.hivemq.com"
TOPIC_DATA = "hospital/room1/data"
TOPIC_CMD = "hospital/room1/hvac"

# Inizializzazione Stato
if 'bpm_history' not in st.session_state: st.session_state['bpm_history'] = []
if 'time_history' not in st.session_state: st.session_state['time_history'] = []
if 'current_bpm' not in st.session_state: st.session_state['current_bpm'] = 70
if 'hvac_status' not in st.session_state: st.session_state['hvac_status'] = "OFF"
if 'event_log' not in st.session_state: st.session_state['event_log'] = []

@st.cache_resource
def get_data_queue(): return queue.Queue()
data_queue = get_data_queue()

def on_message(client, userdata, msg):
    try: data_queue.put((msg.topic, msg.payload.decode()))
    except: pass

@st.cache_resource
def start_mqtt_client():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    client.connect(BROKER, 1883, 60)
    client.subscribe([(TOPIC_DATA, 0), (TOPIC_CMD, 0)])
    client.loop_start()
    return client

start_mqtt_client()

# Elaborazione Coda Messaggi
while not data_queue.empty():
    try:
        topic, payload = data_queue.get_nowait()
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if topic == TOPIC_DATA:
            val = int(payload)
            st.session_state['current_bpm'] = val
            st.session_state['bpm_history'].append(val)
            st.session_state['time_history'].append(timestamp)
            
            if len(st.session_state['bpm_history']) > 50:
                st.session_state['bpm_history'].pop(0)
                st.session_state['time_history'].pop(0)
                
            if val > 100: st.session_state['event_log'].insert(0, f"⚠️ {timestamp} >> CRITICAL BPM: {val}")
            elif val < 60: st.session_state['event_log'].insert(0, f"📉 {timestamp} >> LOW BPM: {val}")
            
        elif topic == TOPIC_CMD:
            if st.session_state['hvac_status'] != payload:
                st.session_state['hvac_status'] = payload
                st.session_state['event_log'].insert(0, f"⚙️ {timestamp} >> HVAC SYSTEM: {payload}")
    except: break

# --- 3. LAYOUT & RENDER ---

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ SYSTEM CONTROL")
    st.caption("IoT ARCHITECTURE MANAGER")
    st.success("🟢 MQTT BROKER: CONNECTED")
    st.info(f"📡 SENSOR NODE: 127.0.0.1")
    st.markdown("---")
    room = st.selectbox("TARGET ZONE", ["ROOM 101 - INFECTIOUS", "ROOM 102 - SURGERY"])
    if st.button("CLR EVENT LOG", type="primary"):
        st.session_state['event_log'] = []
    st.markdown("---")
    st.code(f"Topic: {TOPIC_DATA}\nProtocol: CoAP+MQTT", language="bash")

# Header
bpm = st.session_state['current_bpm']
st.markdown(ui_assets.get_header_html(room, bpm), unsafe_allow_html=True)

# KPI Section
col1, col2, col3, col4 = st.columns(4)

with col1:
    color = "border-red" if bpm > 100 else ("border-green" if bpm >= 60 else "border-orange")
    glow = True if bpm > 100 else False
    st.markdown(ui_assets.get_kpi_card("HEART RATE", bpm, "BPM", "💓", color, glow), unsafe_allow_html=True)

with col2:
    hvac = st.session_state['hvac_status']
    icon_hvac = "❄️" if hvac == "ON" else ("🔥" if hvac == "HEAT" else "💤")
    color_hvac = "border-blue" if hvac == "ON" else ("border-orange" if hvac == "HEAT" else "border-green")
    st.markdown(ui_assets.get_kpi_card("HVAC STATUS", hvac, "", icon_hvac, color_hvac), unsafe_allow_html=True)

with col3:
    st.markdown(ui_assets.get_kpi_card("O2 SATURATION", "98", "%", "💧", "border-blue"), unsafe_allow_html=True)

with col4:
    st.markdown(ui_assets.get_kpi_card("BLOOD PRESS.", "120/80", "", "🩺", "border-green"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Main Dashboard Content (Grafico + Log)
grid_col1, grid_col2 = st.columns([2, 1])

with grid_col1:
    st.markdown("### 📈 LIVE BIOMETRICS")
    
    if st.session_state['bpm_history']:
        df = pd.DataFrame({"Time": st.session_state['time_history'], "BPM": st.session_state['bpm_history']})
        
        fig = px.area(df, x="Time", y="BPM", template="plotly_dark", height=350)
        is_critical = bpm > 100 or bpm < 60
        line_color = '#ef4444' if is_critical else '#10b981'
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(showgrid=False, title=None, nticks=5),
            yaxis=dict(showgrid=True, gridcolor='#334155', range=[40, 140]),
            hovermode="x unified"
        )
        fig.update_traces(line_color=line_color, fillcolor=line_color)
        
        st.plotly_chart(fig, key="bpm_chart", width="stretch", config={'displayModeBar': False})
    else:
        st.info("WAITING FOR SENSOR DATA STREAM...")

with grid_col2:
    st.markdown("### 🖥️ SYSTEM LOG")
    # Chiama la funzione di render dal file esterno
    st.markdown(ui_assets.get_log_html(st.session_state['event_log']), unsafe_allow_html=True)

# Auto-refresh
time.sleep(1)
st.rerun()