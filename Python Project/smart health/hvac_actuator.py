import paho.mqtt.client as mqtt
import sys
import time
import socket
import random
import atexit
import signal

# --- CONFIGURAZIONE ---
BROKER = "broker.hivemq.com"
PORT = 1883

# Colori Console
RESET = "\033[0m"
RED = "\033[91m"
BLUE = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"

# Variabile globale per il lock
app_lock_socket = None

# --- FUNZIONE DI PULIZIA FORCE (CRUCIALE) ---
def cleanup():
    """Questa funzione viene chiamata SEMPRE quando il programma si chiude."""
    global app_lock_socket
    if app_lock_socket:
        try:
            print(f"\n{YELLOW}[SYSTEM] Rilascio risorse e lock stanza...{RESET}")
            app_lock_socket.close()
            app_lock_socket = None
        except Exception:
            pass

# Registra la pulizia per ogni tipo di chiusura (CTRL+C, Errore, Chiusura Finestra)
atexit.register(cleanup)
signal.signal(signal.SIGTERM, lambda n, f: sys.exit(0))
signal.signal(signal.SIGINT, lambda n, f: sys.exit(0))

# --- FUNZIONE AUTO-DISCOVERY ---
def find_available_room():
    global app_lock_socket
    
    # Proviamo fino a 5 stanze
    for i in range(1, 6):
        room_name = f"room{i}"
        lock_port = 60000 + i
        
        try:
            # Tenta di creare il socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            
            # Opzione per riutilizzare la porta subito se è in stato TIME_WAIT (Aiuta nel riavvio veloce)
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            except AttributeError:
                pass # Su Windows potrebbe non servire per UDP, ma non fa male
                
            s.bind(('127.0.0.1', lock_port))
            
            app_lock_socket = s
            return room_name, lock_port
            
        except OSError:
            continue
            
    return None, None

# --- SETUP INIZIALE ---
print(f"{CYAN}[SYSTEM] Ricerca slot stanza disponibile...{RESET}")
ROOM_ID, LOCK_PORT = find_available_room()

if ROOM_ID is None:
    print(f"\n{RED}❌ ERRORE: Tutte le stanze sono occupate o bloccate!{RESET}")
    print("   Attendi 10 secondi che il sistema operativo liberi le porte e riprova.")
    sys.exit(1)

# Configurazione Topic
TOPIC = f"hospital/{ROOM_ID}/hvac"
CLIENT_ID = f"hvac-{ROOM_ID}-{random.randint(1000, 9999)}"

# --- CALLBACK MQTT ---
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"\n{GREEN}✅ [ASSEGNATO] Questo terminale è ora: {ROOM_ID.upper()}{RESET}")
        print(f"   Broker: {BROKER}")
        print(f"   Topic Sottoscritto: {TOPIC}")
        client.subscribe(TOPIC)
        print(f"\n{YELLOW}[IN ATTESA] Pronto a ricevere comandi...{RESET}")
    else:
        print(f"{RED}[ERRORE] Connessione Broker fallita: {reason_code}{RESET}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode().upper()
        timestamp = time.strftime("%H:%M:%S")
        
        if payload == "ON":
            print(f"[{timestamp}] {BLUE}❄️  RAFFREDDAMENTO ATTIVO (Cooling Mode){RESET}")
            print(f"            >>> Ventole: 100% | Compressore: ON")
        elif payload == "HEAT":
            print(f"[{timestamp}] {RED}🔥  RISCALDAMENTO ATTIVO (Heating Mode){RESET}")
            print(f"            >>> Resistenze: ON | Pompa: ON")
        elif payload == "OFF":
            print(f"[{timestamp}] {GREEN}💤  SISTEMA IN STANDBY (Monitoring...){RESET}")

    except Exception as e:
        print(f"{RED}[ERRORE] Parsing: {e}{RESET}")

# --- MAIN LOOP ---
if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"Connessione al cloud HiveMQ in corso...")
    try:
        client.connect(BROKER, PORT, 60)
        client.loop_forever()
    except KeyboardInterrupt:
        sys.exit(0) # Questo attiverà la funzione cleanup() registrata con atexit