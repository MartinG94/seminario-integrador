# Aclaraciones del PO — Año social y categorías (SCRUM-77)

## Fuentes y alcance

| ID | Fuente y localizador |
|---|---|
| SRC77-PO-01 | Captura de conversación entregada por el usuario: mensajes del PO entre 23:03 y 23:10. La captura no muestra fecha del intercambio. |
| SRC77-PO-02 | Versión escrita corregida remitida por el usuario como respuesta del PO: preguntas 1–4, desde «G57: No debe contemplarse en esta escala» hasta «Senior: 3.° año en adelante», seguida de «Esta es la correcta, la anterior no». Es la versión vigente. |
| SRC77-BASE-01 | Constitución del baseline, commit 0596c64a1002fd06f135733c7090ae4480f7351f, principio 8: Pasivo en años 1–3 y Activo en 4–6. [Antecedente conservado](../../docs/constitution.md#antecedentes); la constitución activa queda alineada con el PO en TS77.30. |
| SRC77-CODE-01 | [Modelo Socio](../../backend/socios/models.py), social_year y category_for_social_year: TS77.31 incorpora EX_TRAVELER/año nulo explícito fuera de la escala; TS77.32 calcula JUNIOR en años 1/2 y SENIOR en 3–6. TS77.33 implementa el recálculo histórico local mediante [migración 0004](../../backend/socios/migrations/0004_recalculate_social_categories.py). |

Este registro incorpora la respuesta al pendiente DP77-01 y el cambio transversal de clasificación solicitado por el PO. La versión previa que asignaba 7.º año a G57 fue retirada expresamente por el usuario: no se usa para requisitos, validaciones ni fixtures. La instrucción de actualizar todo el sistema se conserva como requisito: no acredita que el cambio ya esté implementado. No modifica las Notas del PO originales ni el seguimiento macro.

## Reglas confirmadas

| ID | Regla | Origen | Evidencia | Estado |
|---|---|---|---|---|
| RN77-01 | Para el corte social actual, G57 es socio exviajero y queda fuera de la escala; G58 corresponde a 6.º año, G59 a 5.º y G60 a 4.º. G63 corresponde a 1.º como referencia. | Explícito | SRC77-PO-02, respuesta 1 corregida | Confirmado por el PO, remitido por el usuario. |
| RN77-02 | El pase de año se hace efectivo en la asamblea de recambio de autoridades. No tiene fecha fija, aunque suele celebrarse en febrero. | Explícito | SRC77-PO-01, 23:09–23:10; SRC77-PO-02, respuesta 2 | Confirmado. |
| RN77-03 | Todos los integrantes de un mismo grupo comparten el mismo año social, sin excepciones particulares; G57 se contempla como exviajero fuera de la escala, conforme a la respuesta 1. | Explícito | SRC77-PO-02, respuestas 1 y 3 | Confirmado. |
| RN77-04 | La categoría depende únicamente del año social: Junior para 1.º–2.º y Senior desde 3.º en adelante. La denominación Activo/Pasivo debe actualizarse en todo el sistema. | Explícito | SRC77-PO-01, 23:07–23:09; SRC77-PO-02, respuesta 4 | Confirmado; implementación transversal verificada/auditada en TS77.37, CA77-08 cerrado. |

| Grupo | Año social del corte confirmado | Clasificación / condición confirmada |
|---|---:|---|
| G57 | Fuera de la escala | Exviajero; fuera de la clasificación Junior/Senior |
| G58 | 6 | Senior |
| G59 | 5 | Senior |
| G60 | 4 | Senior |
| G63, referencia | 1 | Junior |

La tabla corresponde al corte de esta consulta y debe versionarse con el catálogo. No fija una equivalencia perpetua grupo/año ni permite programar el pase automáticamente el 1 de enero o en una fecha elegida de febrero. La fuente confirma el evento institucional, no solicita implementar su administración automática en SCRUM-77.

## Requisito transversal

| ID | Enunciado | Evidencia | Estado |
|---|---|---|---|
| RF77-PO-01 | Actualizar clasificación, denominaciones y representación de socios en backend, contratos, frontend y documentación activa para cumplir RN77-01/04, incluyendo G57 exviajero sin asignarle un año de la escala. | SRC77-PO-02, respuestas 1 y 4 corregidas | Implementada y verificada/auditada en TS77.30–43; DEP77-02 cerrado en TS77.37. Carga posterior G57 verificada en TS77.11 con marcador explícito y año nulo. |

La categoría social y la vigencia de cuenta continúan siendo conceptos separados. La nueva categoría no autoriza por sí sola cambios de roles, facultades procesales, permisos de firma ni saldos: cualquier regla dependiente deberá contrastarse con su requisito propio durante la revisión de impacto.

## Diferencias frente al baseline

| ID | Diferencia | Fuentes | Consecuencia y estado |
|---|---|---|---|
| CF77-01 | Baseline Pasivo 1–3 / Activo 4–6 frente a Junior 1–2 / Senior 3+. | SRC77-BASE-01, SRC77-CODE-01 y RN77-04 | Cerrado: documentación, cálculo/recálculo, lectores/filtros, T01/JWT, identidad de legajo y SPA alineados en TS77.30–43. 932 pruebas backend y 202 frontend verdes, auditoría integral TS77.37 aprobada y CA77-08 cerrado. Se conservan snapshots y aliases históricos de entrada. |
| CF77-02 | El socio operativo del baseline requiere social_year entre 1 y 6 y sólo tiene categorías PASSIVE/ACTIVE; G57 exviajero queda fuera de esa escala. | SRC77-CODE-01 y RN77-01 | Cerrado: EX_TRAVELER/año nulo local y metadato institucional explícito, lectores/T01/legajo/SPA coherentes, sin años 0/7 ni condición inferida desde NULL. UNKNOWN separado. Auditoría TS77.37 aprobada; la carga de G57 conserva TS77.11. |

## Pendientes y cobertura

- DP77-01 queda cerrado: las cuatro respuestas están confirmadas por escrito.
- DP77-02 cerrado: [catálogo v1](../../docs/gestion-proyecto/CATALOGO_DATOS_DEMO_SCRUM-77.md) aceptado tras auditoría TS77.37, con 16 identidades/cuatro por grupo, rangos/referencias fijados y 62 oráculos verdes. Carga/manifiesto/conciliación posteriores verificados en TS77.08–19: 162 referencias, corte confirmado y persistencia sin reseed. [Evidencia](tasks.md#verificación-de-ts770827).
- DEP77-02/CA77-08 cerrados: adecuación global implementada, verificada y auditada en TS77.37 antes de aceptar TS77.07. CF77-01/02 resueltos; el seed conserva el corte confirmado.
- La compatibilidad D77-04–08 quedó implementada en TS77.30–43. TS77.43 y TS77.35/36 resuelven identidad del legajo, caché/contratos y UI/datos demo existentes; TS77.37 audita transversalmente y precede a la aceptación TS77.07. Evidencia histórica: 932 pruebas backend y 202 frontend verdes (0 errores), cobertura 94,72% y build correcto, en [tasks.md](tasks.md#verificación-de-ts774335363707). La carga posterior y regresión de 996 casos están en el [cierre TS77.08–27](tasks.md#verificación-de-ts770827). No se reinterpretan RN77-01–04 ni se modifica notasPO.md.
- No queda una pregunta pendiente al PO sobre la correspondencia actual, la fecha del avance, las excepciones o el corte Junior/Senior. La respuesta no define acceso, permisos ni efectos de futuros pases a exviajero; la revisión de impacto debe registrar cualquier decisión necesaria, sin asumir que exviajero implica cuenta deshabilitada.
- TS77.29 resolvió la representación y compatibilidad en el [informe técnico](../../docs/gestion-proyecto/IMPACTO_COMPATIBILIDAD_SOCIOS_SCRUM-77.md); TS77.30 alinea documentación activa. [DP77-FAC-01](../../docs/constitution.md#facultades-pendientes) conserva pendiente la regla de elegibilidad/firma en sus propias US, sin bloquear clasificación ni modificar RN77-01–04.
