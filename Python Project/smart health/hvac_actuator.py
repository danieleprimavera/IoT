import paho.mqtt.client as mqtt

# Configurazione
BROKER = "broker.hivemq.com"
TOPIC = "hospital/room1/hvac"

# Callback aggiornata per API v2
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"[ATTUATORE] Connesso al Broker con successo!")
        client.subscribe(TOPIC)
    else:
        print(f"[ATTUATORE] Errore connessione: {reason_code}")

def on_message(client, userdata, msg):
    try:
        comando = msg.payload.decode()
        print(f"[ATTUATORE] Ricevuto comando: {comando}")
        
        if comando == "ON":
            print(" >> ❄️  RAFFREDDAMENTO ATTIVATO ❄️ <<")
        elif comando == "OFF":
            print(" >> Sistema in Standby <<")
        elif comando == "ALARM":
            print(" >> 🚨 ALLARME CRITICO ATTIVATO 🚨 <<")
    except Exception as e:
        print(f"Errore lettura messaggio: {e}")

# Inizializzazione specifica per evitare DeprecationWarning
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

client.on_connect = on_connect
client.on_message = on_message

print(f"[ATTUATORE] In attesa di comandi su {TOPIC}...")
client.connect(BROKER, 1883, 60)

try:
    client.loop_forever()
except KeyboardInterrupt:
    print("\n[ATTUATORE] Disconnessione...")
    client.disconnect()