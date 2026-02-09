import asyncio
import logging
from aiocoap import *
import paho.mqtt.client as mqtt

# CONFIGURAZIONE CRITICA: Usa 127.0.0.1 per combaciare con il sensore
COAP_URI = "coap://127.0.0.1/heartrate"
MQTT_BROKER = "broker.hivemq.com"

# --- CONFIGURAZIONE TOPIC ---
MQTT_TOPIC_CMD = "hospital/room1/hvac"   # Per i comandi all'attuatore (ON/OFF)
MQTT_TOPIC_DATA = "hospital/room1/data"  # NUOVO: Per i dati del grafico (Numeri)

# --- SETUP MQTT (Versione 2 API per evitare warning) ---
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

def on_mqtt_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("[COLLECTOR] Connesso al broker MQTT")
    else:
        print(f"[COLLECTOR] Errore connessione MQTT: {reason_code}")

mqtt_client.on_connect = on_mqtt_connect
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_start()

# --- LOGICA APPLICATIVA ---
def process_data(bpm):
    # 1. INVIO DATI ALLA DASHBOARD (Visualizzazione)
    # Pubblichiamo il numero puro per farlo leggere a Streamlit
    if mqtt_client.is_connected():
        mqtt_client.publish(MQTT_TOPIC_DATA, str(bpm))

    # 2. LOGICA DI CONTROLLO (Automazione)
    # Decide cosa fare con l'HVAC in base al battito
    if bpm > 100:
        print(f" -> ⚠️  ALLARME: Battito {bpm} BPM! Attivazione RAFFREDDAMENTO.")
        mqtt_client.publish(MQTT_TOPIC_CMD, "ON")
    elif bpm < 60:
        print(f" -> 📉 ALLARME: Battito {bpm} BPM! Attivazione RISCALDAMENTO.")
        mqtt_client.publish(MQTT_TOPIC_CMD, "HEAT")
    else:
        print(f" -> ✅ Battito {bpm} BPM: Parametri nella norma.")
        mqtt_client.publish(MQTT_TOPIC_CMD, "OFF")

# --- MAIN LOOP (Versione Moderna async for) ---
async def main():
    protocol = await Context.create_client_context()
    
    # Crea la richiesta OBSERVE
    request = Message(code=GET, uri=COAP_URI, observe=0)
    pr = protocol.request(request)
    
    print(f"[COLLECTOR] In attesa di dati da {COAP_URI}...")

    try:
        # NUOVO METODO: Ciclo infinito asincrono che riceve le notifiche
        async for response in pr.observation:
            try:
                payload = response.payload.decode('ascii')
                # Ignora payload vuoti se capitano
                if not payload: continue
                
                bpm = int(payload)
                process_data(bpm)
                
            except ValueError:
                print(f"[ERRORE] Dato ricevuto non valido: {response.payload}")
                
    except Exception as e:
        print(f"[ERRORE CRITICO] Impossibile connettersi al sensore: {e}")
        print("SUGGERIMENTO: Verifica che smart_sensor.py stia girando su 127.0.0.1")

if __name__ == "__main__":
    # Disabilita i log di debug di sistema per avere una console pulita
    logging.basicConfig(level=logging.ERROR)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCollector terminato.")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()