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
  - Renderizar badge semántico compacto (icono opcional) en las tarjetas Kanban y destacar tarjetas con urgencia "Urgente".
  - Incorporar columna "Urgencia" con ordenamiento en la tabla explorer.  
  - Incorporar selector de urgencia en el modal de detalle para integrantes del TD.  
  *Hecho cuando:* Pruebas unitarias de `gestionar-expedientes.component.spec.ts` validan ordenamiento, filtrado y renderizado de badges.

- [x] **TS3-07.6 Verificación Integral, Cobertura y Consistencia con PO:**  
  Ejecutar suite completa de backend (`pytest`) y frontend (`Karma`). Validar consistencia con `notasPO.md` (07/10/2026), `DESIGN.md` y verificar ejecución en local.

## Corrección de Observaciones del PO — PR #50

- [x] **TS3-07.7 Urgencia en origen (TDD):** Selector en Crear Expediente / Solicitud T01, DTOs tipados, preservación al guardar/retomar/resetear, herencia y snapshot de emisión; regresiones de apertura directa y validación API. Verificado: 57 pruebas backend y 30 del formulario Angular en verde.
- [x] **TS3-07.8 Tarjeta Kanban simplificada (TDD):** Solo ID, urgencia, puntos, título/motivo y fecha; ID sin quiebres, badges compactos y tokens canónicos, conservando acceso al detalle. Verificado: 18 pruebas del componente Angular en verde, incluidas las seis etapas y acceso por teclado.
- [x] **TS3-07.9 Verificación y UAT:** 490 pruebas backend/MySQL y 151 frontend/Karma en verde (0 errores), compilación de producción correcta, Ruff y migraciones verificados, notas del PO y Seguimiento preservados, auditoría full stack independiente sin hallazgos pendientes. UAT funcional y visual comprobada en escritorio y móvil (375 px); aplicación activa en http://localhost:4201. El lint frontend no se puede ejecutar por la configuración TSLint heredada del proyecto.


- [x] **TS3-07.10 Selección visual de urgencia (TDD):** Tres casillas coloreadas de selección única, Normal por defecto y bloqueo durante carga/emisión. 32 pruebas del formulario y 153 de la suite Angular en verde (0 errores), build correcto y auditoría independiente sin hallazgos bloqueantes. Verificación real de guardado, reanudación y emisión; Tab, flechas, Espacio, foco visible y reflow a 320/375 px sin desborde del control. Localhost:4201 activo para UAT. UAT aprobada por el usuario el 10/10/2026.
