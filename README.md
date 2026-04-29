# ecg-web

*[Versione italiana](README.it.md)*

Web service for converting ECG files in DICOM format to graphic images.
Exposes a REST API built with [FastAPI](https://fastapi.tiangolo.com/) and delegates
rendering to the [dicom-ecg-plot](https://github.com/marcodebe/dicom-ecg-plot) module,
included as a git submodule.

## Requirements

- Python 3.9+
- Git (with submodule support)

## Installation

```bash
git clone --recurse-submodules <repo-url>
cd ecg-web

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If the repository was already cloned without `--recurse-submodules`:

```bash
git submodule update --init
```

## Configuration

Copy the example file and edit the values:

```bash
cp .env.example .env
```

| Variable       | Default      | Description                                               |
|----------------|--------------|-----------------------------------------------------------|
| `AUTH_ENABLED` | `true`       | Enable/disable API key authentication                     |
| `API_KEYS`     | *(empty)*    | Comma-separated list of valid API keys                    |
| `RATE_LIMIT`   | `60/minute`  | Per-IP request limit (`N/second`, `N/minute`, `N/hour`)   |

To disable authentication (e.g. for local development):

```ini
AUTH_ENABLED=false
```

## Running

```bash
source .venv/bin/activate
uvicorn app.main:app --port 8001 --reload
```

Interactive API documentation is available at <http://localhost:8001/docs>.

A browser-based demo client is served at <http://localhost:8001/>.

## Authentication

When `AUTH_ENABLED=true`, every request to `/api/ecg/*` endpoints must include the header:

```
X-API-Key: <key>
```

Requests without a key or with an invalid key receive `401 Unauthorized`.

## Web client

A minimal single-page client is served at `GET /`. It provides a form to upload a
DICOM file, configure all conversion options, and view the result directly in the
browser. For image formats (PNG, JPG, SVG) the output is displayed inline; for all
formats a download link is provided.

No installation or separate server is needed — it is bundled with the API.

## Endpoints

### `GET /api/ecg/formats`

Returns all accepted values for conversion parameters.

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

Converts an uploaded DICOM ECG file via `multipart/form-data`.

**Parameters**

| Field           | Type    | Default   | Description                                       |
|-----------------|---------|-----------|---------------------------------------------------|
| `file`          | file    | —         | DICOM ECG file *(required)*                       |
| `layout`        | string  | `3x4_1`   | Layout: `3x4_1`, `3x4`, `6x2`, `12x1`            |
| `paper`         | string  | `a4`      | Paper format: `a4`, `letter`                      |
| `format`        | string  | `png`     | Output format (see `/api/ecg/formats`)            |
| `minor_grid`    | bool    | `false`   | Draw 1 mm minor grid lines                        |
| `interpretation`| bool    | `false`   | Show automated ECG interpretation text            |
| `mm_mv`         | float   | `10.0`    | Amplitude scale in mm/mV                          |

**Example**

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

Fetches an ECG from a PACS server via WADO and converts it.
The WADO server must be configured in `dicom-ecg-plot/ecgconfig.py`.

**Parameters**

Same as `/convert`, but instead of a file:

| Field        | Type   | Description            |
|--------------|--------|------------------------|
| `study_uid`  | string | Study Instance UID     |
| `series_uid` | string | Series Instance UID    |
| `object_uid` | string | SOP Instance UID       |

**Example**

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

Checks that the service is running. Does not require authentication.

```bash
curl http://localhost:8001/health
# {"status": "ok"}
```

## Internationalisation (i18n)

API error messages are returned in the language requested by the client via the
standard `Accept-Language` HTTP header.

Supported languages: **`it`** (Italian), **`en`** (English, default).

```bash
# Response in Italian
curl -H "Accept-Language: it" ...
# → {"detail": "Layout non valido. Valori accettati: ..."}

# Response in English
curl -H "Accept-Language: en-US,en;q=0.9" ...
# → {"detail": "Invalid layout. Accepted values: ..."}
```

If the header is absent or the requested language is not available, English is used.

**Adding a new language:** open `app/i18n.py` and add an entry to the `MESSAGES`
dictionary with the same keys as `en`.

## Rate limiting

The maximum number of requests per IP is configurable via `RATE_LIMIT` in `.env`.
When the limit is exceeded the service responds with `429 Too Many Requests`.

Format: `N/second`, `N/minute`, `N/hour` — e.g. `30/minute`, `5/second`, `500/hour`.

## Project structure

```
ecg-web/
├── app/
│   ├── auth.py          # FastAPI dependency for authentication
│   ├── config.py        # Configuration via pydantic-settings
│   ├── i18n.py          # Translations and Accept-Language detection
│   ├── limiter.py       # Global slowapi instance
│   ├── main.py          # FastAPI application
│   ├── routes/
│   │   ├── ecg.py       # /convert and /convert-wado endpoints
│   │   └── formats.py   # /formats endpoint
│   └── static/
│       └── index.html   # Browser demo client (served at /)
├── dicom-ecg-plot/      # Git submodule
├── .env                 # Local configuration (not versioned)
├── .env.example         # Configuration template
└── requirements.txt
```

## Updating the submodule

```bash
git submodule update --remote dicom-ecg-plot
```

## License

MIT
