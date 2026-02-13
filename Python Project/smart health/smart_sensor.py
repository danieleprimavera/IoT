import asyncio
import random
import aiocoap.resource as resource
import aiocoap
import sys

# Colori
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"
CYAN = "\033[96m"

class HeartRateResource(resource.ObservableResource):
    def __init__(self, room_name):
        super().__init__()
        self.bpm = 70
        self.room_name = room_name

    async def render_get(self, request):
        return aiocoap.Message(payload=str(self.bpm).encode('ascii'))

    def update_state(self):
        # Range 45-130 per testare sia HEAT (<60) che COOLING (>100)
        self.bpm = random.randint(45, 130)
        print(f"[{self.room_name.upper()}] Battito rilevato: {self.bpm} bpm")
        self.updated_state()
        try:
            # Aggiornamento ogni 3 secondi
            asyncio.get_running_loop().call_later(3, self.update_state)
        except RuntimeError:
            pass 

async def find_free_port_and_start():
    """
    Tenta di avviare il sensore sulla prima porta CoAP libera
    partendo dalla 5683 (Standard CoAP).
    """
    BASE_PORT = 5683
    MAX_RETRIES = 10 # Supporta fino a 10 stanze (5683 -> 5693)

    for i in range(MAX_RETRIES):
        current_port = BASE_PORT + i
        room_name = f"room{i+1}" # room1, room2...
        
        root = resource.Site()
        # Passiamo il nome stanza alla risorsa per log più belli
        sensor = HeartRateResource(room_name)
        root.add_resource(['heartrate'], sensor)

        print(f"Tentativo avvio come {room_name} su porta {current_port}...")
        
        try:
            # Se questa riga non fallisce, la porta è libera!
            await aiocoap.Context.create_server_context(root, bind=('127.0.0.1', current_port))
            
            print(f"\n{GREEN}✅ SENSORE ATTIVO!{RESET}")
            print(f"   Stanza Assegnata: {CYAN}{room_name.upper()}{RESET}")
            print(f"   Porta CoAP:       {current_port}")
            print(f"   Resource:         coap://127.0.0.1:{current_port}/heartrate")
            print("----------------------------------------------------")
            
            sensor.update_state()
            await asyncio.get_running_loop().create_future() # Loop infinito
            return # Esce dalla funzione se ha successo

        except OSError:
            # Porta occupata, continua il ciclo e prova la prossima
            print(f"❌ Porta {current_port} occupata. Provo la successiva...")
            continue
            
    print(f"\n{RED}ERRORE CRITICO: Nessuna porta libera trovata nel range!{RESET}")

if __name__ == "__main__":
    try:
        asyncio.run(find_free_port_and_start())
    except KeyboardInterrupt:
        print("\nSensore spento.")