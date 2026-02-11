"""Key Management Service for encrypting/decrypting wallet private keys.

Uses local Fernet encryption in dev, AWS KMS in production.
"""

import base64

from cryptography.fernet import Fernet

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)


class KeyManager:
    """Encrypt and decrypt private key material."""

    def __init__(self):
        settings = get_settings()
        self._use_kms = bool(settings.aws_kms_key_id)
        if not self._use_kms:
            key = settings.encryption_key
            if not key:
                raise RuntimeError(
                    "ENCRYPTION_KEY environment variable is not set. "
                    "This is required for encrypting wallet private keys at rest. "
                    "Generate a Fernet key with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())' "
                    "and set it in your .env file."
                )
            self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, plaintext: bytes) -> str:
        """Encrypt raw private key bytes. Returns base64-encoded ciphertext."""
        if self._use_kms:
            return self._kms_encrypt(plaintext)
        ct = self._fernet.encrypt(plaintext)
        return base64.b64encode(ct).decode()

    def decrypt(self, ciphertext: str) -> bytes:
        """Decrypt base64-encoded ciphertext. Returns raw private key bytes."""
        if self._use_kms:
            return self._kms_decrypt(ciphertext)
        ct = base64.b64decode(ciphertext)
        return self._fernet.decrypt(ct)

    def _kms_encrypt(self, plaintext: bytes) -> str:
        """AWS KMS encryption (production)."""
        import boto3

        settings = get_settings()
        client = boto3.client("kms", region_name=settings.aws_region)
        resp = client.encrypt(
            KeyId=settings.aws_kms_key_id,
            Plaintext=plaintext,
        )
        return base64.b64encode(resp["CiphertextBlob"]).decode()

    def _kms_decrypt(self, ciphertext: str) -> bytes:
        """AWS KMS decryption (production)."""
        import boto3

        settings = get_settings()
        client = boto3.client("kms", region_name=settings.aws_region)
        resp = client.decrypt(
            CiphertextBlob=base64.b64decode(ciphertext),
        )
        return resp["Plaintext"]


_km: KeyManager | None = None


def get_key_manager() -> KeyManager:
    global _km
    if _km is None:
        _km = KeyManager()
    return _km
