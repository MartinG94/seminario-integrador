# Tareas — Clasificador e Indicador Visual de Urgencia en Expedientes (SCRUM-78 / S3-07)

Tareas atómicas estimadas en `<30 minutos` bajo metodología SDD y TDD.

---

## Tareas de Implementación

- [x] **TS3-07.1 Modelo y Migración de Urgencia (Backend TDD):**  
  Incorporar `UrgenciaExpedienteEnum` (`baja`, `normal`, `urgente`) y el campo `urgencia` con default `normal` en `Expediente` (y `SolicitudT01`). Crear migración de Django y verificar aplicación en SQLite/MySQL.  
  *Hecho cuando:* Tests unitarios de modelo validan valores aceptados, default `normal` y rechazo de valores inválidos.

- [x] **TS3-07.2 Serialización y Filtro por Urgencia en API REST (Backend TDD):**  
  Actualizar `BoardExpedienteSerializer` y `ExpedienteListSerializer` para incluir `urgencia` y `urgencia_display`. Agregar filtro por urgencia en `ExpedienteFilter`.  
  *Hecho cuando:* Tests de integración de `BoardExpedientesView` validan presencia de `urgencia` y respuesta filtrada ante `?urgencia=urgente`.

- [x] **TS3-07.3 Endpoint PATCH de Actualización de Urgencia (Backend TDD):**  
  Implementar actualización parcial de urgencia en `ExpedienteDetailView` (`PATCH /api/v1/expedientes/<id>/`), protegida por `IsTribunalOrDirectiva`.  
  *Hecho cuando:* Tests de API confirman actualización exitosa para usuarios con rol TD (200 OK), validación de campos inválidos (400) y rechazo para usuarios no autorizados (403).

- [x] **TS3-07.4 DTOs, Mapeo y Servicio en Frontend (Angular TDD):**  
  Actualizar interfaces `BoardCaseDTO` y `Expediente` con `urgencia: NivelUrgencia`. Actualizar `TribunalDataService.mapearBoardCaseAExpediente()` y agregar `actualizarUrgencia()`.  
  *Hecho cuando:* Tests unitarios de servicio en Karma verifican mapeo y llamada HTTP PATCH.

- [x] **TS3-07.5 Indicadores Visuales y Filtro en Tablero Kanban y Tabla (Frontend):**  
  En `gestionar-expedientes`:  
  - Agregar selector de filtro por urgencia en la barra de herramientas.  
  - Renderizar badge semántico con icono en las tarjetas Kanban y destacar tarjetas con urgencia "Urgente".  
  - Incorporar columna "Urgencia" con ordenamiento en la tabla explorer.  
  - Incorporar selector de urgencia en el modal de detalle para integrantes del TD.  
  *Hecho cuando:* Pruebas unitarias de `gestionar-expedientes.component.spec.ts` validan ordenamiento, filtrado y renderizado de badges.

- [x] **TS3-07.6 Verificación Integral, Cobertura y Consistencia con PO:**  
  Ejecutar suite completa de backend (`pytest`) y frontend (`Karma`). Validar consistencia con `notasPO.md` (07/10/2026), `DESIGN.md` y verificar ejecución en local.

