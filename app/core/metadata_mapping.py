"""Metadatos de campos sensibles por tabla (Patrón: Metadata Mapping)."""

SENSITIVE_FIELDS: dict[str, list[str]] = {
    "usuarios": ["email", "telefono", "correo"],
    "pagos": ["mp_payment_id", "detalle_pago"],
    "sensores": ["provisioning_token"],
}

ANONYMIZE_FUNCTIONS: dict[str, str] = {
    "email": "anonymize_email",
    "correo": "anonymize_email",
    "telefono": "anonymize_phone",
    "mp_payment_id": "anonymize_token",
    "provisioning_token": "anonymize_token",
    "detalle_pago": "anonymize_token",
}


def is_sensitive(table: str, field: str) -> bool:
    """Indica si un campo de una tabla es sensible."""
    return field in SENSITIVE_FIELDS.get(table, [])
