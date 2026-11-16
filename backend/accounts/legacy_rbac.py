"""
Equivalencia entre el esquema de permisos legado y el RBAC nuevo (CA2).

Fuente de los datos legados:
`docs/analisis-proceso-actual/sistema-actual/descripcion-sistema-actual-legado.md`
(secciones 6.1.3 "Cargos Oficiales" y 7 "Jerarquía de Permisos del Tribunal").

El sistema legado combinaba dos cosas independientes:

1. Tres permisos de Django acumulativos (`tribunal_bajo`, `tribunal_medio`,
   `tribunal_alto`) que sí gobernaban el acceso.
2. Un cargo estatutario en `Socio.tipoSocio` que, según la regla crítica del
   propio relevamiento, **no confería permisos de software automáticamente**.

El esquema nuevo mantiene esa separación: el cargo/categoría del socio es dato
del padrón y el acceso lo determina únicamente `Socio.role`. Este módulo es la
tabla de conversión usada para migrar cuentas del legado, y existe como código
(y no sólo como documentación) para que quede cubierto por tests.
"""

from typing import Final

from socios.models import Role

# Qué roles nuevos satisfacen cada nivel legado. Los niveles legados eran
# acumulativos: todo lo que alcanzaba `tribunal_bajo` lo alcanzaba también
# quien tuviera medio o alto.
LEGACY_PERMISSION_TO_ROLES: Final[dict[str, tuple[str, ...]]] = {
    # Acceso base de cualquier socio autenticado: consultar reglamentos, ver
    # sus propias solicitudes T01 y presentar descargos T02/T03.
    "tribunal_bajo": (
        Role.SOCIO,
        Role.AUTORIDAD_SC,
        Role.REVISORES,
        Role.CD,
        Role.TD,
        Role.ADMIN,
        Role.FISCALIZADORA,
    ),
    # Gestión operativa: eventos, asistencias, hora de fin y filtrado de
    # expedientes. Corresponde a órganos directivos, tribunal y autoridades de subcomisión.
    "tribunal_medio": (Role.CD, Role.TD, Role.AUTORIDAD_SC),
    # Potestad jurisdiccional: dictaminar T01, calificar T02/T03, resolver y
    # firmar disposiciones. Exclusivo del Tribunal de Disciplina.
    "tribunal_alto": (Role.TD,),
}

# Cargos estatutarios legados (`socio_tipoSocio`, IDs 1-15) y el rol RBAC con
# el que se da de alta la cuenta migrada (Refinamiento PO S5 / SCRUM-121).
LEGACY_POSITION_TO_ROLE: Final[dict[int, str]] = {
    1: Role.AUTORIDAD_SC,  # Presidente de Subcomisión
    2: Role.AUTORIDAD_SC,  # Vicepresidente de Subcomisión
    3: Role.CD,  # Presidente de AVEIT
    4: Role.CD,  # Vicepresidente de AVEIT
    5: Role.CD,  # Tesorero
    6: Role.CD,  # Protesorero
    7: Role.CD,  # Secretario de Actas
    8: Role.CD,  # Secretario General
    9: Role.CD,  # Prosecretario
    10: Role.TD,  # Titular del Tribunal de Disciplina
    11: Role.TD,  # Suplente del Tribunal de Disciplina
    12: Role.SOCIO,  # Socio Ordinario
    13: Role.CD,  # Secretario (sujeto a revisión en padrón)
    14: Role.REVISORES,  # Revisor de Cuentas Titular
    15: Role.REVISORES,  # Revisor de Cuentas Suplente
}

# Todos los cargos 1-15 cuentan con asignación formal conforme a SCRUM-121.
UNMAPPED_LEGACY_POSITIONS: Final[dict[int, str]] = {}

DEFAULT_ROLE_FOR_UNMAPPED: Final[str] = Role.SOCIO


def role_for_legacy_position(position_id: int) -> str:
    """Rol RBAC con el que migrar una cuenta según su cargo legado."""
    return LEGACY_POSITION_TO_ROLE.get(position_id, DEFAULT_ROLE_FOR_UNMAPPED)


def satisfies_legacy_permission(role: str, legacy_permission: str) -> bool:
    """Si `role` habilita lo que en el legado exigía `legacy_permission`."""
    return role in LEGACY_PERMISSION_TO_ROLES.get(legacy_permission, ())
