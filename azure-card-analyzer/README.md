# Credit Card Analyzer (Safe Demo) — Streamlit + Azure Document Intelligence

This is a **safe demo** that reads an uploaded image, runs OCR using **Azure AI Document Intelligence (prebuilt-read)**,
extracts card-like fields, and validates only the **format** (Luhn + expiry plausibility).

⚠️ Security note:
- Do **not** use real credit card data.
- The app **does not display** the full card number (PAN) and recommends deleting blobs after processing.
- “Valid” here means **format-valid**, not “authorized/active”.

## Tech
- streamlit
- azure-ai-documentintelligence
- azure-storage-blob
- python-dotenv

## Setup

1) Create `.env` from `.env.example` and fill:
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_STORAGE_CONTAINER`
- `AZURE_DI_ENDPOINT`
- `AZURE_DI_KEY`

2) Install dependencies:
```bash
pip install -r requirements.txt