# ecg-web

*[English version](README.md)*

Servizio web per la conversione di file ECG in formato DICOM in immagini grafiche.
Espone un'API REST costruita con [FastAPI](https://fastapi.tiangolo.com/) e delega
il rendering al modulo [dicom-ecg-plot](https://github.com/marcodebe/dicom-ecg-plot),
incluso come git submodule.

## Requisiti

- Python 3.9+
- Git (con supporto ai submodule)

## Installazione

```bash
git clone --recurse-submodules <repo-url>
cd ecg-web

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Se il repository è già stato clonato senza `--recurse-submodules`:

```bash
git submodule update --init
```

## Configurazione

Copia il file di esempio e modifica i valori:

```bash
cp .env.example .env
```

| Variabile      | Default      | Descrizione                                              |
|----------------|--------------|----------------------------------------------------------|
| `AUTH_ENABLED` | `true`       | Abilita/disabilita l'autenticazione via API key          |
| `API_KEYS`     | *(vuoto)*    | Lista di chiavi valide, separate da virgola              |
| `RATE_LIMIT`   | `60/minute`  | Limite richieste per IP (`N/second`, `N/minute`, `N/hour`) |

Per disabilitare l'autenticazione (es. in sviluppo locale):

```ini
AUTH_ENABLED=false
```

## Avvio

```bash
source .venv/bin/activate
uvicorn app.main:app --port 8001 --reload
```

La documentazione interattiva è disponibile su <http://localhost:8001/docs>.

Un client web di esempio è disponibile su <http://localhost:8001/>.

## Autenticazione

Quando `AUTH_ENABLED=true`, ogni richiesta agli endpoint `/api/ecg/*` deve includere
l'header:

```
X-API-Key: <chiave>
```

Le richieste senza chiave o con chiave non valida ricevono `401 Unauthorized`.

## Client web

All'indirizzo `GET /` è disponibile un client web minimale a pagina singola. Permette
di caricare un file DICOM, configurare tutte le opzioni di conversione e visualizzare
il risultato direttamente nel browser. Per i formati immagine (PNG, JPG, SVG) il
risultato è mostrato inline; per tutti i formati è disponibile un link di download.

Non richiede installazione separata: è incluso nel server API.

## Endpoint

### `GET /api/ecg/formats`

Restituisce i valori accettati da tutti i parametri di conversione.

```bash
curl -H "X-API-Key: mykey" http://localhost:8001/api/ecg/formats
```

```json
{
  "layouts": ["3x4_1", "3x4", "6x2", "12x1"],
  "papers": ["a4", "letter"],
  "formats": ["png", "pdf", "svg", "svgz", "tiff", "jpg", "jpeg", "eps", "ps"],
  "defaults": {
    "layout": "3x4_1",
    "paper": "a4",
    "format": "png",
    "minor_grid": false,
    "interpretation": false,
    "mm_mv": 10.0
  }
}
```

---

### `POST /api/ecg/convert`

Converte un file DICOM ECG caricato come `multipart/form-data`.

**Parametri**

| Campo           | Tipo    | Default   | Descrizione                                    |
|-----------------|---------|-----------|------------------------------------------------|
| `file`          | file    | —         | File DICOM ECG *(obbligatorio)*                |
| `layout`        | string  | `3x4_1`   | Layout: `3x4_1`, `3x4`, `6x2`, `12x1`         |
| `paper`         | string  | `a4`      | Formato carta: `a4`, `letter`                  |
| `format`        | string  | `png`     | Formato output (vedi `/api/ecg/formats`)       |
| `minor_grid`    | bool    | `false`   | Griglia minore a 1 mm                          |
| `interpretation`| bool    | `false`   | Mostra il testo di interpretazione automatica  |
| `mm_mv`         | float   | `10.0`    | Scala ampiezza in mm/mV                        |

**Esempio**

```bash
curl -X POST http://localhost:8001/api/ecg/convert \
  -H "X-API-Key: mykey" \
  -F "file=@ecg.dcm" \
  -F "layout=3x4_1" \
  -F "format=pdf" \
  -F "minor_grid=true" \
  -F "interpretation=true" \
  -o ecg.pdf
```

---

### `POST /api/ecg/convert-wado`

Recupera il file ECG da un server PACS tramite WADO e lo converte.
Il server WADO deve essere configurato in `dicom-ecg-plot/ecgconfig.py`.

**Parametri**

Stessi parametri di `/convert`, ma al posto del file:

| Campo        | Tipo   | Descrizione            |
|--------------|--------|------------------------|
| `study_uid`  | string | Study Instance UID     |
| `series_uid` | string | Series Instance UID    |
| `object_uid` | string | SOP Instance UID       |

**Esempio**

```bash
curl -X POST http://localhost:8001/api/ecg/convert-wado \
  -H "X-API-Key: mykey" \
  -F "study_uid=1.2.3.4" \
  -F "series_uid=1.2.3.4.5" \
  -F "object_uid=1.2.3.4.5.6" \
  -F "format=png" \
  -o ecg.png
```

---

### `GET /health`

Verifica che il servizio sia attivo. Non richiede autenticazione.

```bash
curl http://localhost:8001/health
# {"status": "ok"}
```

## Internazionalizzazione (i18n)

I messaggi di errore dell'API vengono restituiti nella lingua richiesta dal client
tramite l'header HTTP standard `Accept-Language`.

Lingue supportate: **`it`** (italiano), **`en`** (inglese, default).

```bash
# Risposta in italiano
curl -H "Accept-Language: it" ...
# → {"detail": "Layout non valido. Valori accettati: ..."}

# Risposta in inglese
curl -H "Accept-Language: en-US,en;q=0.9" ...
# → {"detail": "Invalid layout. Accepted values: ..."}
```

Se l'header è assente o la lingua richiesta non è disponibile, viene usato l'inglese.

**Aggiungere una nuova lingua:** aprire `app/i18n.py` e aggiungere una voce al
dizionario `MESSAGES` con le stesse chiavi di `en`.

## Rate limiting

Il numero massimo di richieste per IP è configurabile tramite `RATE_LIMIT` nel `.env`.
Al superamento del limite il servizio risponde con `429 Too Many Requests`.

Formato: `N/second`, `N/minute`, `N/hour` — es. `30/minute`, `5/second`, `500/hour`.

## Struttura del progetto

```
ecg-web/
├── app/
│   ├── auth.py          # Dipendenza FastAPI per l'autenticazione
│   ├── config.py        # Configurazione via pydantic-settings
│   ├── i18n.py          # Traduzioni e rilevamento lingua da Accept-Language
│   ├── limiter.py       # Istanza globale slowapi
│   ├── main.py          # Applicazione FastAPI
│   ├── routes/
│   │   ├── ecg.py       # Endpoint /convert e /convert-wado
│   │   └── formats.py   # Endpoint /formats
│   └── static/
│       └── index.html   # Client web di esempio (servito su /)
├── dicom-ecg-plot/      # Git submodule
├── .env                 # Configurazione locale (non versionato)
├── .env.example         # Template di configurazione
└── requirements.txt
```

## Esecuzione come servizio systemd

Il file `ecg-web.service` è pronto all'uso.

**1. Copia il progetto** (adatta il percorso se necessario):

```bash
sudo cp -r . /opt/ecg-web
sudo chown -R debe:debe /opt/ecg-web
```

**2. Installa e avvia il servizio:**

```bash
sudo cp /opt/ecg-web/ecg-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now ecg-web
```

**3. Verifica lo stato:**

```bash
systemctl status ecg-web
journalctl -u ecg-web -f
```

Il servizio è in ascolto su `127.0.0.1:8001`. Per esporlo all'esterno, configura
un reverse proxy (nginx, Caddy, …) davanti al servizio.

Se il percorso di deploy o l'utente differiscono dai valori predefiniti nel file
(`/opt/ecg-web`, utente `debe`), modifica `ecg-web.service` prima di copiarlo in
`/etc/systemd/system/`.

## Configurazione nginx

Il file `ecg.galliera.it.conf` contiene un server block nginx pronto all'uso.
Gestisce il redirect HTTP → HTTPS, SSL via Let's Encrypt e il proxy verso
uvicorn su `127.0.0.1:8001`.

**1. Ottieni un certificato SSL** (se non già presente):

```bash
certbot --nginx -d ecg.galliera.it
```

**2. Installa la configurazione:**

```bash
sudo cp ecg.galliera.it.conf /etc/nginx/sites-available/ecg.galliera.it
sudo ln -s /etc/nginx/sites-available/ecg.galliera.it /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## Aggiornare il submodule

```bash
git submodule update --remote dicom-ecg-plot
```

## Licenza

MIT
