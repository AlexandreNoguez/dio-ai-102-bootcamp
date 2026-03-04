import argparse
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

import requests
import trafilatura
from dotenv import load_dotenv


@dataclass
class TranslatorConfig:
    endpoint: str
    key: str
    region: str
    timeout_seconds: int = 30
    max_chars_per_request: int = 45000  # safety below 50k limit
    max_retries: int = 5


def fetch_markdown_from_url(url: str) -> str:
    """
    Extracts main content from a web page and returns Markdown.
    Uses trafilatura which supports output_format="markdown".
    """
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise RuntimeError("Failed to download page content (possibly blocked or requires JS).")

    md = trafilatura.extract(
        downloaded,
        output_format="markdown",
        with_metadata=True,
        include_links=True,
        include_tables=True,
        deduplicate=True,
    )

    if not md:
        raise RuntimeError("Failed to extract main content from the page.")

    return md.strip()


def split_markdown(md: str, max_chars: int) -> List[str]:
    """
    Splits Markdown into chunks <= max_chars, preferring paragraph boundaries.
    """
    parts = md.split("\n\n")
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for p in parts:
        p_len = len(p) + 2  # account for "\n\n"
        if p_len > max_chars:
            # Fallback: hard split if a single paragraph is too large
            text = p
            while len(text) > max_chars:
                chunks.append(text[:max_chars])
                text = text[max_chars:]
            if text:
                chunks.append(text)
            continue

        if current_len + p_len > max_chars and current:
            chunks.append("\n\n".join(current).strip())
            current = [p]
            current_len = p_len
        else:
            current.append(p)
            current_len += p_len

    if current:
        chunks.append("\n\n".join(current).strip())

    return chunks


def translate_chunk_rest(
    cfg: TranslatorConfig,
    text: str,
    to_lang: str,
    from_lang: Optional[str] = None,
) -> str:
    """
    Calls Azure AI Translator (Text Translation) REST API.
    """
    # Translator V3 endpoint shape (works with custom domain too):
    # {endpoint}/translator/text/v3.0/translate?api-version=3.0&to=xx[&from=yy]
    base = cfg.endpoint.rstrip("/")
    url = f"{base}/translator/text/v3.0/translate"
    params = {"api-version": "3.0", "to": to_lang}
    if from_lang:
        params["from"] = from_lang

    headers = {
        "Ocp-Apim-Subscription-Key": cfg.key,
        "Ocp-Apim-Subscription-Region": cfg.region,
        "Content-Type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4()),
    }

    body = [{"Text": text}]

    for attempt in range(cfg.max_retries):
        resp = requests.post(url, params=params, headers=headers, json=body, timeout=cfg.timeout_seconds)

        if resp.status_code == 200:
            data = resp.json()
            # data[0]["translations"][0]["text"]
            return data[0]["translations"][0]["text"]

        # Simple backoff for rate limits / transient errors
        if resp.status_code in (429, 500, 502, 503, 504):
            wait = min(2 ** attempt, 20)
            time.sleep(wait)
            continue

        raise RuntimeError(f"Translator error {resp.status_code}: {resp.text}")

    raise RuntimeError("Translator failed after max retries (rate limit or transient errors).")


def translate_markdown(cfg: TranslatorConfig, md: str, to_lang: str, from_lang: Optional[str]) -> str:
    chunks = split_markdown(md, cfg.max_chars_per_request)
    translated_chunks: List[str] = []

    for i, ch in enumerate(chunks, start=1):
        translated = translate_chunk_rest(cfg, ch, to_lang=to_lang, from_lang=from_lang)
        translated_chunks.append(translated)

    return "\n\n".join(translated_chunks).strip()


def build_frontmatter(source_url: str, target_lang: str) -> str:
    extracted_at = datetime.now(timezone.utc).isoformat()
    return (
        "---\n"
        f"source_url: {source_url}\n"
        f"target_lang: {target_lang}\n"
        f"extracted_at_utc: {extracted_at}\n"
        "---\n\n"
    )


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Extract webpage content as Markdown and translate using Azure AI Translator.")
    parser.add_argument("--url", required=True, help="Web page URL to extract and translate")
    parser.add_argument("--to", required=True, help="Target language (ISO code), e.g. pt, en, es")
    parser.add_argument("--from-lang", default=None, help="Optional source language (ISO). If omitted, Translator will auto-detect.")
    parser.add_argument("--out", default=None, help="Output markdown file path")
    parser.add_argument("--save-original", action="store_true", help="Also save extracted original Markdown next to output")
    args = parser.parse_args()

    key = os.getenv("AZURE_TRANSLATOR_KEY", "").strip()
    region = os.getenv("AZURE_TRANSLATOR_REGION", "").strip()
    endpoint = os.getenv("AZURE_TRANSLATOR_ENDPOINT", "").strip()

    if not key or not region or not endpoint:
        raise RuntimeError("Missing env vars. Set AZURE_TRANSLATOR_KEY, AZURE_TRANSLATOR_REGION, AZURE_TRANSLATOR_ENDPOINT.")

    cfg = TranslatorConfig(endpoint=endpoint, key=key, region=region)

    original_md = fetch_markdown_from_url(args.url)

    translated_md = translate_markdown(cfg, original_md, to_lang=args.to, from_lang=args.from_lang)
    final_md = build_frontmatter(args.url, args.to) + translated_md

    out_path = args.out or f"translated.{args.to}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(final_md)

    if args.save_original:
        with open("extracted.original.md", "w", encoding="utf-8") as f:
            f.write(build_frontmatter(args.url, "original") + original_md)

    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
