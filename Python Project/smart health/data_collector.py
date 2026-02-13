import asyncio
import logging
import sys
import socket
from aiocoap import *
import aiocoap.error as error
import paho.mqtt.client as mqtt

# --- CONFIGURAZIONE ---
MQTT_BROKER = "broker.hivemq.com"
MAX_ROOMS = 5
BASE_PORT = 5683
TIMEOUT_SECONDS = 6  # Se non ricevo dati per 6s, considero il sensore perso

# Colori Console
GREEN = "\033[92m"
CYAN = "\033[96m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

# --- ZITTIRE ERRORI INTERNI ---
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("aiocoap").setLevel(logging.CRITICAL)

# --- SETUP WINDOWS ---
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# --- MQTT SETUP ---
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"{GREEN}[COLLECTOR] Connesso al Cloud MQTT{RESET}")

mqtt_client.on_connect = on_connect
mqtt_client.connect(MQTT_BROKER, 1883, 60)
mqtt_client.loop_start()

# --- TASK DI MONITORAGGIO CON WATCHDOG ---
async def monitor_room_task(room_id, port):
    uri = f"coap://127.0.0.1:{port}/heartrate"
    topic_data = f"hospital/{room_id}/data"
    topic_cmd = f"hospital/{room_id}/hvac"
    
    # Questo loop esterno serve a RICREARE il protocollo se qualcosa si rompe
    while True:
        protocol = None
        try:
            protocol = await Context.create_client_context()
            request = Message(code=GET, uri=uri, observe=0)
            pr = protocol.request(request)
            
            # Otteniamo l'iteratore manuale per poter applicare il timeout
            iterator = pr.observation.__aiter__()
            
            is_connected = False
            
            # Loop interno: Lettura pacchetti
            while True:
                try:
                    # ⚡ WATCHDOG: Aspetta il prossimo dato per MAX 'TIMEOUT_SECONDS'
                    # Se il sensore muore, qui scatta il TimeoutError e ci sblocca!
                    response = await asyncio.wait_for(iterator.__anext__(), timeout=TIMEOUT_SECONDS)
                    
                    if not is_connected:
                        print(f"{GREEN}[NEW DEVICE] {room_id.upper()} agganciato su porta {port}!{RESET}")
                        is_connected = True

                    payload = response.payload.decode('ascii')
                    if not payload: continue
                    
                    # --- LOGICA DI BUSINESS ---
                    try:
                        bpm = int(payload)
                        mqtt_client.publish(topic_data, str(bpm))
                        
                        command = "OFF"
                        log_prefix = f"[{room_id.upper()}]"
                        
                        if bpm > 100:
                            print(f"{log_prefix} {RED}⚠️  ALLARME: {bpm} BPM -> COOLING{RESET}")
                            command = "ON"
                        elif bpm < 60:
                            print(f"{log_prefix} {RED}📉 ALLARME: {bpm} BPM -> HEATING{RESET}")
                            command = "HEAT"
                        
                        mqtt_client.publish(topic_cmd, command)

                    except ValueError:
                        pass

                except asyncio.TimeoutError:
                    # NESSUN DATO RICEVUTO PER 6 SECONDI
                    if is_connected:
                        print(f"{YELLOW}[WARN] Segnale perso da {room_id}. Riconnessione in corso...{RESET}")
                    # Rompiamo il loop interno per forzare la ricreazione del protocollo
                    break 
                
                except Exception:
                    # Qualsiasi altro errore (es. WinError 10054 improvviso)
                    break

        except Exception:
            # Errore durante la creazione del contesto (es. porta occupata o altro)
            await asyncio.sleep(2)
            
        finally:
            # 🧹 PULIZIA TOTALE
            # Chiudiamo il vecchio protocollo prima di ricominciarne uno nuovo
            if protocol:
                try:
                    await protocol.shutdown()
                except:
                    pass
            
            # Piccola pausa prima di riprovare a connettersi
            if not is_connected:
                await asyncio.sleep(3)

# --- MAIN ---
async def main():
    print("--- 🏥 HOSPITAL IOT AUTO-DISCOVERY SYSTEM ---")
    print(f"Sistema attivo con Watchdog (Timeout: {TIMEOUT_SECONDS}s).")
    print("Puoi staccare e riattaccare i sensori liberamente.")
    
    tasks = []
    for i in range(MAX_ROOMS):
        room_num = i + 1
        port = BASE_PORT + i
        room_id = f"room{room_num}"
        tasks.append(asyncio.create_task(monitor_room_task(room_id, port)))
    
    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[SYSTEM] Spegnimento completato.")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()