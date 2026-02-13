🏥 Smart Health Monitor - IoT Infectious Disease Ward

Intelligent IoT Project - A.A. 2025/2026
Un sistema di monitoraggio ibrido (CoAP + MQTT) per la gestione automatizzata dei parametri vitali e ambientali in reparti ospedalieri critici.

📸 Architettura del Sistema

Il sistema utilizza un'architettura a livelli che integra sensori constrained (vincolati) e attuatori tramite un nodo centrale di elaborazione (Edge Logic).

📝 Descrizione dello Scenario

Il progetto simula una Smart Room in un reparto di malattie infettive. L'obiettivo è monitorare i parametri vitali del paziente e intervenire automaticamente sul sistema HVAC, riducendo l'interazione fisica del personale medico.

🌟 Funzionalità Avanzate

Monitoraggio Multi-Reparto: La dashboard può gestire più stanze simultaneamente.

Auto-Discovery con Approvazione: I nuovi sensori vengono rilevati automaticamente, ma è l'operatore a decidere quando attivarli nel sistema di monitoraggio.

Watchdog in Tempo Reale: Rilevamento immediato dello stato OFFLINE se un sensore smette di inviare dati per più di 10 secondi.

Edge Computing: Il Data Collector analizza i dati localmente (BPM > 100) per attivare l'attuatore HVAC senza attendere input dal cloud.

Digital Twin Dinamico: Visualizzazione reattiva dello stato del paziente (STABLE / CRITICAL / OFFLINE) con grafici ad area e log eventi storici.

🛠️ Tech Stack & Protocolli

Componente      Protocollo       Libreria                Ruolo

Smart Sensor    CoAP (UDP)       aiocoap                 Espone il battito cardiaco come risorsa Observable.

Data Collector  CoAP + MQTT      aiocoap + paho-mqtt     Edge Gateway: Bridge tra rete CoAP e Broker MQTT.

HVAC Actuator   MQTT (TCP)       paho-mqtt               Sottoscrive i comandi ed esegue azioni simulate.

Dashboard       MQTT (Web)       streamlit + plotly      Digital Twin: UI interattiva e gestione stato della sessione.

📂 Struttura del Progetto

📦 smart-health-monitor
 ┣ 📜 smart_sensor.py      # Server CoAP: Genera dati biometrici simulati.
 ┣ 📜 data_collector.py    # Edge Logic: Bridge CoAP-MQTT e decision making.
 ┣ 📜 hvac_actuator.py     # MQTT Client: Simulazione attuatore ambientale.
 ┣ 📜 dashboard.py         # Streamlit UI: Gestione multi-reparto e approvazione.
 ┣ 📜 ui_assets.py         # Asset grafici: CSS personalizzato e template HTML.
 ┣ 📜 architecture.png     # Schema dell'architettura di sistema.
 ┣ 📜 requirements.txt     # Dipendenze del progetto.
 ┗ 📜 README.md            # Documentazione del progetto.

 🚀 Guida all'Esecuzione (Demo Sequence)

Per una corretta simulazione, avvia gli script in questo ordine in terminali separati:

Terminale 1 (Sensore/Paziente): python smart_sensor.py

Terminale 2 (Attuatore/HVAC): python hvac_actuator.py

Terminale 3 (Data Collector): python data_collector.py

Terminale 4 (Dashboard): streamlit run dashboard.py

💡 Come gestire la Dashboard durante la Demo

Attivazione: Al primo avvio, clicca su "✅ Attiva ROOMX" nella sidebar per iniziare il monitoraggio.

Rilevamento Nuovi Nodi: Se aggiungi un nuovo sensore durante l'esecuzione, clicca sul tasto giallo "AGGIORNA LISTA" che apparirà automaticamente.

Simulazione Offline: Spegni il terminale del sensore; dopo 10 secondi la card passerà da "STABLE" a "OFFLINE".

📊 Note sull'Efficienza dell'Architettura
Il sistema evita il fenomeno del polling selvaggio:

Push-based: MQTT invia i dati alla dashboard solo quando ci sono variazioni.

Edge Processing: La logica di allarme è decentralizzata sul Collector, garantendo tempi di risposta rapidi anche in caso di latenza del broker cloud.

👥 Autori

Studente: Daniele Primavera

Matricola: 188567

Anno Accademico: 2025/2026

Corso di Intelligent Internet of Things