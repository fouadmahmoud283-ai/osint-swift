"""Object storage adapter for evidence documents (S3/MinIO)."""

import hashlib
import json
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, Optional
from uuid import UUID

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from ..config import settings
from ..utils.logging import get_logger

logger = get_logger(__name__)


class ObjectStorage:
    """
    Adapter for S3-compatible object storage.
    Handles storing and retrieving evidence documents.
    """
    
    def __init__(self) -> None:
        """Initialize S3 client."""
        self.client = boto3.client(
            's3',
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = settings.s3_bucket_name
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """Ensure the evidence bucket exists, create if it doesn't."""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket '{self.bucket_name}' exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.info(f"Creating bucket '{self.bucket_name}'")
                try:
                    self.client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Bucket '{self.bucket_name}' created successfully")
                except ClientError as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    raise
            else:
                logger.error(f"Error checking bucket: {e}")
                raise
    
    def generate_object_key(
        self,
        job_id: UUID,
        source_type: str,
        evidence_id: UUID,
        extension: str = "json"
    ) -> str:
        """
        Generate a structured object key for evidence storage.
        
        Format: evidence/{source_type}/{date}/{job_id}/{evidence_id}.{extension}
        """
        date_prefix = datetime.utcnow().strftime("%Y/%m/%d")
        return f"evidence/{source_type}/{date_prefix}/{job_id}/{evidence_id}.{extension}"
    
    def store_evidence(
        self,
        object_key: str,
        content: bytes,
        content_type: str = "application/json",
        metadata: Optional[Dict[str, str]] = None
    ) -> tuple[str, int]:
        """
        Store evidence document in object storage.
        
        Args:
            object_key: S3 object key
            content: Document content as bytes
            content_type: MIME type
            metadata: Optional metadata tags
        
        Returns:
            Tuple of (checksum, file_size_bytes)
        """
        # Calculate checksum
        checksum = hashlib.sha256(content).hexdigest()
        file_size = len(content)
        
        # Prepare metadata
        s3_metadata = metadata or {}
        s3_metadata.update({
            'checksum': checksum,
            'ingested-at': datetime.utcnow().isoformat(),
        })
        
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=content,
                ContentType=content_type,
                Metadata=s3_metadata,
            )
            
            logger.info(
                f"Stored evidence: {object_key}",
                extra={
                    'object_key': object_key,
                    'size_bytes': file_size,
                    'checksum': checksum
                }
            )
            
            return checksum, file_size
            
        except ClientError as e:
            logger.error(f"Failed to store evidence: {e}", extra={'object_key': object_key})
            raise
    
    def store_json_evidence(
        self,
        object_key: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, str]] = None
    ) -> tuple[str, int]:
        """Store JSON evidence document."""
        content = json.dumps(data, indent=2, default=str).encode('utf-8')
        return self.store_evidence(
            object_key=object_key,
            content=content,
            content_type="application/json",
            metadata=metadata
        )
    
    def retrieve_evidence(self, object_key: str) -> bytes:
        """
        Retrieve evidence document from object storage.
        
        Args:
            object_key: S3 object key
        
        Returns:
            Document content as bytes
        """
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            content = response['Body'].read()
            
            logger.info(
                f"Retrieved evidence: {object_key}",
                extra={'object_key': object_key, 'size_bytes': len(content)}
            )
            
            return content
            
        except ClientError as e:
            logger.error(f"Failed to retrieve evidence: {e}", extra={'object_key': object_key})
            raise
    
    def retrieve_json_evidence(self, object_key: str) -> Dict[str, Any]:
        """Retrieve and parse JSON evidence document."""
        content = self.retrieve_evidence(object_key)
        return json.loads(content.decode('utf-8'))
    
    def verify_checksum(self, object_key: str, expected_checksum: str) -> bool:
        """
        Verify the integrity of stored evidence.
        
        Args:
            object_key: S3 object key
            expected_checksum: Expected SHA-256 checksum
        
        Returns:
            True if checksum matches, False otherwise
        """
        try:
            content = self.retrieve_evidence(object_key)
            actual_checksum = hashlib.sha256(content).hexdigest()
            
            matches = actual_checksum == expected_checksum
            
            if not matches:
                logger.warning(
                    f"Checksum mismatch for {object_key}",
                    extra={
                        'object_key': object_key,
                        'expected': expected_checksum,
                        'actual': actual_checksum
                    }
                )
            
            return matches
            
        except ClientError as e:
            logger.error(f"Failed to verify checksum: {e}", extra={'object_key': object_key})
            return False
    
    def delete_evidence(self, object_key: str) -> None:
        """Delete evidence document from object storage."""
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            logger.info(f"Deleted evidence: {object_key}", extra={'object_key': object_key})
        except ClientError as e:
            logger.error(f"Failed to delete evidence: {e}", extra={'object_key': object_key})
            raise


# Global object storage instance
object_storage = ObjectStorage()
