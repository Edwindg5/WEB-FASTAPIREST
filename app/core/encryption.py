"""Servicio de cifrado AES-256-GCM (Patrón: Encrypt Filter)."""
import os
import base64
import secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionService:
    """Cifra/descifra datos sensibles con AES-256-GCM."""

    def __init__(self):
        key_b64 = os.getenv("ENCRYPTION_KEY")
        if key_b64:
            self.key = base64.b64decode(key_b64)
        else:
            self.key = AESGCM.generate_key(bit_length=256)
            generated = base64.b64encode(self.key).decode()
            print(
                f"[WARNING] ENCRYPTION_KEY no configurada. "
                f"Clave generada (guardar en .env): ENCRYPTION_KEY={generated}"
            )

    def encrypt(self, plain_text: str) -> str:
        """Cifra texto con AES-256-GCM. Retorna base64 (nonce + ciphertext)."""
        nonce = secrets.token_bytes(12)
        aesgcm = AESGCM(self.key)
        ct = aesgcm.encrypt(nonce, plain_text.encode("utf-8"), None)
        return base64.b64encode(nonce + ct).decode("utf-8")

    def decrypt(self, cipher_text: str) -> str:
        """Descifra texto cifrado con AES-256-GCM desde base64."""
        raw = base64.b64decode(cipher_text)
        nonce, ct = raw[:12], raw[12:]
        aesgcm = AESGCM(self.key)
        return aesgcm.decrypt(nonce, ct, None).decode("utf-8")

    def anonymize_email(self, email: str) -> str:
        """Enmascara email: 'usuario@dominio.com' → 'u***@dominio.com'."""
        if "@" not in email:
            return "***"
        local, domain = email.split("@", 1)
        return f"{local[0]}***@{domain}"

    def anonymize_phone(self, phone: str) -> str:
        """Enmascara teléfono mostrando solo los últimos 4 dígitos."""
        digits = "".join(c for c in str(phone) if c.isdigit())
        if len(digits) >= 4:
            return f"***{digits[-4:]}"
        return "***"


encryption_service = EncryptionService()
