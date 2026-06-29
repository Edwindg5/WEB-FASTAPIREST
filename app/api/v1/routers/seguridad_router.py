"""Router de demostración de cifrado (Parte 4)."""
from fastapi import APIRouter

from app.core.encryption import encryption_service

router = APIRouter(prefix="/seguridad", tags=["Seguridad — Demo Cifrado"])


@router.get("/demo-cifrado", summary="Demostración del flujo de cifrado AES-256-GCM")
async def demo_cifrado():
    dato_original = "9611234567"
    dato_cifrado = encryption_service.encrypt(dato_original)
    dato_descifrado = encryption_service.decrypt(dato_cifrado)
    dato_anonimizado = encryption_service.anonymize_phone(dato_original)

    return {
        "dato_original": dato_original,
        "dato_cifrado": dato_cifrado,
        "dato_descifrado": dato_descifrado,
        "dato_anonimizado": dato_anonimizado,
        "patron_dto": "Solo recibe nombre, email, password del cliente",
        "patron_mapper": "Transforma DTO a Entity interna",
        "patron_entity": "Entidad con todos los campos incluidos sensibles",
        "patron_metadata_mapping": "Marca telefono como campo sensible",
        "patron_repository": "Única vía de acceso a BD con RLS",
        "patron_interceptor": "Middleware intercepta request/response",
        "patron_encrypt_filter": "AES-256 antes de guardar en BD",
        "patron_anon_filter": "Enmascara datos al retornar al cliente",
    }
