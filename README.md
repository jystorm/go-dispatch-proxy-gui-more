# Go Dispatch Proxy GUI

Interfaccia grafica per il programma a riga di comando `go-dispatch-proxy.exe` https://github.com/extremecoders-re/go-dispatch-proxy.

![image](https://github.com/user-attachments/assets/d80cab43-8cef-496d-afb4-3e4ef4f3d0dc)


## Caratteristiche

- Interfaccia grafica moderna con tema chiaro/scuro
- Rilevamento intelligente delle interfacce di rete fisiche attive (escludendo interfacce virtuali)
- Configurazione completa delle opzioni di go-dispatch-proxy
- Visualizzazione dell'output del proxy in tempo reale
- Avvio/arresto semplificato del proxy

## Requisiti

- Windows (testato su Windows 10/11)
- `go-dispatch-proxy.exe` (deve essere disponibile nel PATH di sistema o nella stessa cartella dell'applicazione)

## Installazione

### Metodo 1: Download dell'eseguibile precompilato

1. Scarica l'ultima versione dell'applicazione dalla sezione [Releases](https://github.com/tuousername/go-dispatch-proxy-gui/releases)
2. Estrai l'archivio ZIP
3. Assicurati che `go-dispatch-proxy.exe` sia nel PATH o nella stessa cartella
4. Esegui `GoDispatchProxyGUI.exe`

### Metodo 2: Compilazione da codice sorgente

1. Clona o scarica questo repository
2. Installa le dipendenze Python:
   ```
   pip install -r requirements.txt
   ```
3. Esegui l'applicazione direttamente:
   ```
   python go_dispatch_proxy_gui.py
   ```
4. Per creare un eseguibile autonomo:
   ```
   pyinstaller go-dispatch-proxy-gui.spec
   ```

## Utilizzo

1. Avviare l'applicazione
2. Selezionare una o più interfacce di rete dalla lista
3. Configurare le opzioni del proxy:
   - **Host**: L'indirizzo IP su cui il proxy ascolterà le connessioni SOCKS (default: 127.0.0.1)
   - **Porta**: La porta su cui il proxy ascolterà le connessioni SOCKS (default: 8080)
   - **Modalità Tunnel**: Attiva la modalità tunnel (funziona come un proxy di bilanciamento del carico trasparente)
   - **Modalità Silenziosa**: Disabilita i messaggi a schermo
4. Cliccare su "Avvia Proxy" per iniziare
5. Visualizzare l'output del proxy nella finestra di destra
6. Cliccare su "Ferma Proxy" per terminare

## Note

- L'applicazione rileva automaticamente solo le interfacce di rete fisiche attivamente connesse
- Vengono escluse le interfacce virtuali (VPN, Docker, VMware, WSL, ecc.) e le interfacce non attive
- Gli indirizzi loopback (127.x.x.x) e link-local (169.254.x.x) vengono filtrati
- Il pulsante "Aggiorna interfacce" permette di aggiornare la lista in caso di modifiche
- Chiudendo l'applicazione si terminerà automaticamente il processo del proxy

## Licenza

[MIT License](LICENSE)
