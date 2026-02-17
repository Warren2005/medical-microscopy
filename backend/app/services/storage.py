"""
MinIO (S3-compatible) object storage client wrapper.

Provides:
- Image upload/download
- Presigned URL generation for direct client access
- Bucket management
- Health check
"""

import io
from datetime import timedelta
from typing import Optional

from minio import Minio

from app.core.config import settings
from app.core.logging_config import logger


class StorageService:
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ):
        self._endpoint = endpoint
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket = bucket
        self._secure = secure
        self._client: Optional[Minio] = None

    def connect(self):
        self._client = Minio(
            self._endpoint,
            access_key=self._access_key,
            secret_key=self._secret_key,
            secure=self._secure,
        )
        # Create bucket if it doesn't exist
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)
            logger.info("Created MinIO bucket", extra={"bucket": self._bucket})
        logger.info(
            "Connected to MinIO",
            extra={"endpoint": self._endpoint, "bucket": self._bucket},
        )

    def disconnect(self):
        # MinIO client is stateless HTTP — no cleanup needed
        logger.info("Disconnected from MinIO")

    def health_check(self) -> bool:
        return self._client.bucket_exists(self._bucket)

    def upload_image(
        self, object_name: str, data: bytes, content_type: str = "image/jpeg"
    ) -> str:
        self._client.put_object(
            self._bucket,
            object_name,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return object_name

    def get_presigned_url(
        self, object_name: str, expiry: timedelta = timedelta(hours=1)
    ) -> str:
        return self._client.presigned_get_object(
            self._bucket, object_name, expires=expiry
        )

    def get_image(self, object_name: str) -> bytes:
        response = self._client.get_object(self._bucket, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()


storage_service = StorageService(
    endpoint=settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    bucket=settings.minio_bucket,
    secure=settings.minio_secure,
)
