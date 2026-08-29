import os
import shutil
from typing import Optional
from app.config import settings

try:
    from minio import Minio
    from minio.error import S3Error
    HAS_MINIO = True
except ImportError:
    HAS_MINIO = False


class StorageService:
    """Handles object and image storage across local filesystem and MinIO/S3."""

    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE.lower()
        self.local_upload_dir = settings.TEMP_UPLOAD_DIR
        os.makedirs(self.local_upload_dir, exist_ok=True)

        self.minio_client = None
        if self.storage_type == "minio" and HAS_MINIO:
            try:
                self.minio_client = Minio(
                    endpoint=settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=settings.MINIO_SECURE
                )
                self._ensure_bucket_exists()
            except Exception as e:
                print(f"[!] Warning: Failed to connect to MinIO ({e}). Falling back to local storage.")
                self.storage_type = "local"

    def _ensure_bucket_exists(self):
        """Creates the target bucket in MinIO if it does not already exist."""
        if self.minio_client:
            bucket = settings.MINIO_BUCKET_NAME
            if not self.minio_client.bucket_exists(bucket):
                self.minio_client.make_bucket(bucket)

    def upload_file(self, file_path: str, destination_name: str) -> str:
        """
        Uploads a local image file to either MinIO or the local static storage.
        Returns: Accessible URL or local file path string.
        """
        if self.storage_type == "minio" and self.minio_client:
            try:
                self.minio_client.fput_object(
                    bucket_name=settings.MINIO_BUCKET_NAME,
                    object_name=destination_name,
                    file_path=file_path
                )
                return f"minio://{settings.MINIO_BUCKET_NAME}/{destination_name}"
            except Exception as e:
                print(f"[!] MinIO upload failed: {e}. Falling back to local copy.")

        # Local storage fallback
        dest_path = os.path.join(self.local_upload_dir, destination_name)
        if os.path.abspath(file_path) != os.path.abspath(dest_path):
            shutil.copyfile(file_path, dest_path)
        return dest_path

    def get_file_url(self, file_path_or_key: str) -> Optional[str]:
        """Generates a downloadable/viewable URL or path for stored assets."""
        if file_path_or_key.startswith("minio://") and self.minio_client:
            object_name = file_path_or_key.replace(f"minio://{settings.MINIO_BUCKET_NAME}/", "")
            return self.minio_client.presigned_get_object(
                bucket_name=settings.MINIO_BUCKET_NAME,
                object_name=object_name
            )
        return file_path_or_key


storage_service = StorageService()