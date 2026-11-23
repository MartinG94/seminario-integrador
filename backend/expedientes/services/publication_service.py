"""Publicación oficial protegida de resoluciones emitidas (Spec 011, S5-02.3).

Arma un DTO de lista blanca: nunca incluye descargos, causales, comprobantes, rutas de
archivos ni identificadores internos de usuarios, y censura los datos de salud (RF-15 a RF-18).
"""

import hashlib
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

from expedientes.domain.medical_redaction import censurar_datos_salud
from expedientes.models import Resolucion
from socios.models import Role


def calcular_hash_resolucion(resolucion: Resolucion) -> str:
    """Hash de integridad del contenido emitido (mismo criterio que la emisión)."""
    payload = "|".join(
        (
            resolucion.numero_expediente_snapshot,
            resolucion.vistos,
            resolucion.considerandos,
            resolucion.articulos_resolutivos,
            str(resolucion.puntos_finales),
            repr(resolucion.medidas),
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def es_autoridad(user: Any) -> bool:
    """TD, CD y Admin habilitados o staff."""
    if not user or not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    socio = getattr(user, "socio", None)
    return bool(socio and socio.is_enabled and socio.role in (Role.TD, Role.CD, Role.ADMIN))


def firmantes_publicos(firmantes: list[dict] | None) -> list[dict]:
    """Pie de firma sin identificadores internos de usuario (RF-18)."""
    publicos = []
    for firma in firmantes or []:
        anio = firma.get("social_year") or firma.get("anio_social")
        publicos.append(
            {
                "numero_socio": str(firma.get("numero_socio") or ""),
                "nombre": firma.get("full_name") or "",
                "grupo": firma.get("grupo") or "",
                "social_year": int(anio) if anio else None,
                "condicion": firma.get("condicion") or "",
                "etiqueta": firma.get("etiqueta") or firma.get("firma") or "",
                "firmado_at": firma.get("signed_at") or firma.get("firmado_at"),
            }
        )
    return sorted(publicos, key=lambda f: f["social_year"] or 99)


def identificador_resolucion(resolucion: Resolucion) -> str:
    numero = resolucion.numero_expediente_snapshot or resolucion.expediente.numero
    return f"RESOLUCIÓN {numero.replace('EXP-', '').strip()}"


def construir_publicacion(resolucion: Resolucion, user: Any) -> dict[str, Any]:
    """Publicación de una resolución emitida para el lector autorizado (RF-15 a RF-18)."""
    from expedientes.services.ledger_service import LedgerService, imputados_de

    expediente = resolucion.expediente
    autoridad = es_autoridad(user)
    lector = getattr(user, "socio", None)
    impactos = LedgerService.impactos_de_resolucion(resolucion)
    imputados = [
        socio
        for socio in imputados_de(expediente)
        if autoridad or (lector is not None and socio.pk == lector.pk)
    ]
    textos = {
        campo: getattr(resolucion, campo) or ""
        for campo in ("vistos", "considerandos", "articulos_resolutivos")
    }
    textos["titulo"] = expediente.titulo or ""
    censurados = {campo: censurar_datos_salud(texto) for campo, texto in textos.items()}
    reglamentos_originales = list(resolucion.reglamentos_respaldantes or [])
    reglamentos = [
        censurar_datos_salud(r) if isinstance(r, str) else r for r in reglamentos_originales
    ]

    return {
        "identificador": identificador_resolucion(resolucion),
        "expediente_id": expediente.pk,
        "expediente_numero": resolucion.numero_expediente_snapshot or expediente.numero,
        "titulo": censurados["titulo"],
        "version": resolucion.version,
        "fecha_emision": resolucion.issued_at.isoformat() if resolucion.issued_at else None,
        "vistos": censurados["vistos"],
        "considerandos": censurados["considerandos"],
        "articulos_resolutivos": censurados["articulos_resolutivos"],
        "reglamentos_respaldantes": reglamentos,
        "medidas": list(resolucion.medidas or []),
        "firmantes": firmantes_publicos(resolucion.firmantes),
        "impactos": [
            {
                # Sin identificadores internos de usuario (RF-18): sólo el N° de socio.
                "numero_socio": str(socio.numero_socio) if socio.numero_socio is not None else "",
                "nombre": socio.first_name,
                "apellido": socio.last_name,
                "puntos": f"{impactos[socio.pk].puntos:.2f}" if socio.pk in impactos else None,
                "medida": impactos[socio.pk].medida if socio.pk in impactos else None,
            }
            for socio in imputados
        ],
        "contiene_datos_reservados": censurados != textos or reglamentos != reglamentos_originales,
        "contenido_hash": resolucion.contenido_hash,
        "integridad_verificada": bool(resolucion.contenido_hash)
        and calcular_hash_resolucion(resolucion) == resolucion.contenido_hash,
    }


def describir_impacto(puntos: str | None, medida: str | None) -> str:
    """Texto institucional del impacto aplicado (las medidas nunca son puntos)."""
    if medida == "LLAMADO_ATENCION":
        return "Llamado de atención"
    if medida == "FELICITACION":
        return "Felicitación"
    if puntos is None:
        return "Sin movimiento registrado"
    valor = Decimal(puntos)
    if valor == 0:
        return "Sin impacto en puntos"
    return f"{valor:+.2f} puntos".replace(".", ",")


def documento_pdf_publicado(publicacion: dict[str, Any]) -> SimpleNamespace:
    """Adaptador de la publicación censurada al generador de PDF institucional."""
    fecha = publicacion.get("fecha_emision")
    return SimpleNamespace(
        estado="ISSUED",
        es_publicacion=True,
        numero_expediente_snapshot=publicacion["expediente_numero"],
        version=publicacion["version"],
        plantilla_version="",
        issued_at=datetime.fromisoformat(fecha) if fecha else None,
        # Sólo el título censurado: nunca el motivo ni la solicitud originales.
        expediente=SimpleNamespace(
            solicitud_t01=SimpleNamespace(titulo=publicacion["titulo"]), motivo=""
        ),
        vistos=publicacion["vistos"],
        considerandos=publicacion["considerandos"],
        articulos_resolutivos=publicacion["articulos_resolutivos"],
        reglamentos_publicados=publicacion["reglamentos_respaldantes"],
        impactos_publicados=[
            {**impacto, "descripcion": describir_impacto(impacto["puntos"], impacto["medida"])}
            for impacto in publicacion["impactos"]
        ],
        firmantes=publicacion["firmantes"],
        puntos_finales=Decimal("0"),
        contenido_hash=publicacion["contenido_hash"] or "",
        integridad_verificada=publicacion["integridad_verificada"],
    )
