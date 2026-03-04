from __future__ import annotations

import os
import streamlit as st
from dotenv import load_dotenv

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

from blob_service import BlobStorageService
from card_parser import extract_from_ocr_text

load_dotenv()

AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER", "uploads")
AZURE_DI_ENDPOINT = os.getenv("AZURE_DI_ENDPOINT", "")
AZURE_DI_KEY = os.getenv("AZURE_DI_KEY", "")

st.set_page_config(page_title="Credit Card Analyzer (Safe Demo)", layout="centered")
st.title("💳 Credit Card Analyzer (Safe Demo)")
st.caption("Extracts only masked info (last4) and validates *format* (Luhn + expiry). Do not use with real cards.")

if not (AZURE_STORAGE_CONNECTION_STRING and AZURE_DI_ENDPOINT and AZURE_DI_KEY):
    st.error("Missing env vars. Check .env (connection string, DI endpoint/key).")
    st.stop()

blob = BlobStorageService(AZURE_STORAGE_CONNECTION_STRING, AZURE_STORAGE_CONTAINER)
di = DocumentIntelligenceClient(AZURE_DI_ENDPOINT, AzureKeyCredential(AZURE_DI_KEY))

delete_after_processing = st.checkbox("Delete blob after processing (recommended)", value=True)

uploaded = st.file_uploader("Upload an image (JPG/PNG) with a *test* card", type=["jpg", "jpeg", "png"])

if uploaded:
    content_type = uploaded.type or "application/octet-stream"
    data = uploaded.getvalue()

    st.image(data, caption="Uploaded image", use_container_width=True)

    # Upload to Blob (temporary)
    up = blob.upload_bytes(data=data, content_type=content_type, filename_hint=uploaded.name)

    try:
        # Download back (simulating read from storage)
        img_bytes = blob.download_bytes(up.blob_name)

        # OCR via Document Intelligence
        poller = di.begin_analyze_document(
            model_id="prebuilt-read",
            body=img_bytes,
            content_type=content_type,
        )
        result = poller.result()

        ocr_text = (result.content or "").strip()
        if not ocr_text:
            st.warning("No text detected.")
            st.stop()

        extraction = extract_from_ocr_text(ocr_text)

        st.subheader("Extracted (masked) info")
        st.write(f"**Brand:** {extraction.brand or 'Unknown'}")
        st.write(f"**Last 4:** {extraction.last4 or 'Not found'}")
        st.write(f"**Expiry:** {extraction.expiry or 'Not found'}")
        st.write(f"**Name (heuristic):** {extraction.holder_name or 'Not found'}")

        st.subheader("Validation (format only)")
        st.write(f"**Luhn OK:** {'✅' if extraction.luhn_ok else '❌'}")
        st.write(f"**Expiry OK:** {'✅' if extraction.expiry_ok else '❌'}")

        if extraction.format_valid:
            st.success("Looks valid by format (Luhn + expiry).")
        else:
            st.error("Invalid by format (couldn’t find a valid PAN or expiry).")

        with st.expander("OCR text (for debugging)"):
            st.text(ocr_text[:5000])

    finally:
        if delete_after_processing:
            blob.delete_blob(up.blob_name)