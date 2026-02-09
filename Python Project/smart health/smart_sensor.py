import asyncio
import random
import aiocoap.resource as resource
import aiocoap

class HeartRateResource(resource.ObservableResource):
    def __init__(self):
        super().__init__()
        self.bpm = 70

    async def render_get(self, request):
        # Risponde alla richiesta GET standard
        return aiocoap.Message(payload=str(self.bpm).encode('ascii'))

    def update_state(self):
        # Simula il cambio del battito cardiaco
        self.bpm = random.randint(60, 110)
        print(f"[SENSORE] Nuovo BPM rilevato: {self.bpm}")
        
        # FONDAMENTALE: Notifica gli observer che il valore è cambiato
        self.updated_state()
        
        # Riprogramma il prossimo aggiornamento tra 2 secondi
        # FIX: Usa get_running_loop() invece di get_event_loop()
        try:
            asyncio.get_running_loop().call_later(2, self.update_state)
        except RuntimeError:
            pass # Il loop è stato chiuso

async def main():
    root = resource.Site()
    sensor = HeartRateResource()
    
    # Mappa la risorsa all'URL "heartrate"
    root.add_resource(['heartrate'], sensor)

    # Avvia il ciclo di aggiornamento dati ORA CHE IL LOOP ESISTE
    sensor.update_state()

    # FIX WINDOWS: Specificare bind=('127.0.0.1', 5683) è obbligatorio su Windows
    # altrimenti crasha cercando di bindare su "any address"
    await aiocoap.Context.create_server_context(root, bind=('127.0.0.1', 5683))
    
    print("[SENSORE] Smart Bedside Monitor avviato su coap://127.0.0.1:5683/heartrate")

    # Mantieni il server attivo
    await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Sensore spento.")