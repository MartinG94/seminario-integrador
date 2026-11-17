# Tareas de Implementación: Circuito Resolutivo Oficial, Exclusión Fundada, Corrección de Puntaje Final y Enmiendas Trazables

> **Historia Macro:** `SCRUM-89` (Macro 01 — 15 SP)  
> **Subtareas Jira:** `SCRUM-99`, `SCRUM-100`, `SCRUM-101`, `SCRUM-102`, `SCRUM-103`  
> **Spec de Referencia:** [`specs/010-circuito-resolutivo-enmiendas/spec.md`](spec.md)  
> **Plan Técnico:** [`specs/010-circuito-resolutivo-enmiendas/plan.md`](plan.md)

---

## Desglose Atómico de Tareas (<30 minutos)

- [x] **T10.1 (SCRUM-101) Persistencia de `puntaje_ratificado` en Backend [TDD]:**  
      Agregar columna `puntaje_ratificado = models.CharField(max_length=20, null=True, blank=True)` en `DescargoExpediente`, generar migraciones `0027_descargo_puntaje_ratificado.py`, `0028_descargo_exclusion_involucrado.py` y `0029_enmienda_resolucion.py`, persistir el valor en `CausalResolutionService.decide` y exponerlo en `visor_serializers.py` y `DescargoDetalleSerializer`.  
      *Hecho cuando:* Tests en `test_causal_resolution_service.py` y `test_visor_expediente.py` confirman persistencia y recuperación del valor tras guardar.

- [x] **T10.2 (SCRUM-101) Sincronización de Puntaje Ratificado en Frontend [TDD]:**  
      Corregir `getPuntajeFinalInvolucrado` y `formatPuntajeFinal` en `gestionar-expedientes.component.ts` para leer prioritariamente `fila.descargo?.puntaje_ratificado`.  
      *Hecho cuando:* Recargar la vista o reabrir el expediente conserva el puntaje calificado (-1.5, Llamado de Atención, Felicitación) y los tests de Jasmine pasan en verde.

- [x] **T10.3 (SCRUM-102) Dominio y Servicio de Exclusión Fundada [TDD]:**  
      Agregar campos de exclusión en `DescargoExpediente`, crear `ExclusionInvolucradoService.excluir_involucrado` con validación de rol `TD`, motivo obligatorio (>= 10 chars), despacho de email por `EmailOutbox` al socio y al solicitante, y si no quedan más involucrados activos, cierre administrativo directo a `EMITIDO` con resolución sin efecto (Decisión PO 12/11/2026).  
      *Hecho cuando:* Suite de tests en `test_exclusion_involucrado.py` pasa en verde cubriendo exclusión parcial y exclusión del último involucrado con cierre automático.

- [x] **T10.4 (SCRUM-102) Endpoint REST y UI de Exclusión en Angular [TDD]:**  
      Implementar endpoint `POST /api/v1/expedientes/<id>/involucrados/<socio_id>/excluir/` protegido con `CanTransitionExpedientes`. En el frontend, agregar botón "Excluir Socio" para rol `TD`, modal de motivo y visualización tachada con badge `Excluido`.  
      *Hecho cuando:* Un miembro del TD excluye a un socio desde la interfaz, la tabla se actualiza reactivamente y las acciones de sanción se bloquean para ese socio.

- [x] **T10.5 (SCRUM-99) Firma Colegiada por Año Social con Inferencia y Selector de Suplencia [TDD]:**  
      En `resolution_service.py`, soportar inferencia automática de condición Titular/Suplente desde padrón (`idTipoSocio == 11` o `ComposicionTribunal`) y selector opcional `es_suplente` en el payload de firma; estampar etiqueta canónica `[N° de Socio] - [Nombre y Apellido] - [Gxx] [(Sup.)]`. En el frontend, agregar selector visible en el modal de firma para tribunal ad-hoc (Art. 95).  
      *Hecho cuando:* Tests en `test_resolution_service.py` y `test_resolution_api.py` validan estampado de `(Sup.)`, rechazo de año duplicado y completitud de firmas de 4.º, 5.º y 6.º año.

- [x] **T10.6 (SCRUM-100) Emisión Oficial y Despacho Idempotente sin Duplicados [TDD]:**  
      En `emitir_resolucion`, generar hash SHA-256 inmutable de los contenidos, pasar a `EMITIDO` y despachar correos vía `EmailDispatcherService.create_or_get_outbox` hacia imputados, CD y TD con claves de idempotencia únicas (`resolucion-emision-{id}-{destinatario}`). Garantizar ausencia de datos médicos.  
      *Hecho cuando:* La suite de tests confirma que no se generan correos duplicados en `EmailOutbox` aun reintentando la emisión.

- [x] **T10.7 (SCRUM-103) Modelo y Servicio de Enmienda con Contra-asientos Opción B [TDD]:**  
      Crear modelo `EnmiendaResolucion`, endpoint `POST /api/v1/expedientes/<id>/enmendar/` preservando el número canónico `RESOLUCIÓN N/YYYY` (Art. 19), retorno a `PENDIENTE_CORREOS` para nueva firma colegiada, y al emitirse registrar en el libro mayor (`tribunal_puntajeaplicado` / `PuntajeAplicado`) la reversión íntegra y el nuevo asiento definitivo (Opción B del PO).  
      *Hecho cuando:* Tests en `test_enmienda_resolucion.py` verifican la trazabilidad de enmienda, las dos transacciones en el libro mayor sin UPDATEs y la inmutabilidad de la resolución anterior.

- [x] **T10.8 (SCRUM-103) Flujo de Enmienda en Frontend y Verificación Integral [TDD]:**  
      En `GestionarExpedientesComponent`, agregar acción "Enmendar Resolución" para expedientes en `Emitido`, modal para motivo y nuevos considerandos/puntos, y retorno reactivo al estado de firmas. Ejecutar suites completas (`pytest`, `Karma`, `ruff`) y corroborar consistencia con `notasPO.md`.  
      *Hecho cuando:* Todos los tests pasan con 0 errores y el flujo E2E de enmienda funciona de punta a punta.
