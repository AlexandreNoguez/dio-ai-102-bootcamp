from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Optional

from azure.storage.blob import BlobServiceClient, ContentSettings


@dataclass(frozen=True)
class UploadResult:
    blob_name: str
    url: str


class BlobStorageService:
    def __init__(self, connection_string: str, container_name: str) -> None:
        self._bsc = BlobServiceClient.from_connection_string(connection_string)
        self._container = self._bsc.get_container_client(container_name)
        try:
            self._container.create_container()
        except Exception:
            # Container already exists or cannot be created; ignore for simplicity.
            pass

    def upload_bytes(
        self,
        data: bytes,
        content_type: str,
        filename_hint: Optional[str] = None,
    ) -> UploadResult:
        # NOTE: Use a random name to avoid leaking original file names.
        ext = ""
        if filename_hint and "." in filename_hint:
            ext = "." + filename_hint.split(".")[-1].lower()

        blob_name = f"{uuid.uuid4().hex}{ext}"
        blob_client = self._container.get_blob_client(blob_name)

        blob_client.upload_blob(
            data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )

        return UploadResult(blob_name=blob_name, url=blob_client.url)

    def download_bytes(self, blob_name: str) -> bytes:
        blob_client = self._container.get_blob_client(blob_name)
        return blob_client.download_blob().readall()

    def delete_blob(self, blob_name: str) -> None:
        blob_client = self._container.get_blob_client(blob_name)
        try:
            blob_client.delete_blob()
        except Exception:
            pass