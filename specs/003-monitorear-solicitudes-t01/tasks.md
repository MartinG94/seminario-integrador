# Tareas — Spec 003: SCRUM-75 / PB-04 (Monitorear Solicitudes T01)

- [x] **T1. Modelo y Vinculación T01 ➔ Expediente:** Vincular `SolicitudT01` con `Expediente` (campo `expediente = OneToOneField(Expediente, ...)`). Al emitir solicitud en `EmitirT01Serializer.save()`, abrir atómicamente el `Expediente` mediante `ExpedienteWorkflowService.open_expediente` asociando socios involucrados y motivo.
- [x] **T2. Serializer y Queryset Sanitizado para Monitoreo (Backend TDD):** Implementar `MisSolicitudesT01Serializer` sanitizado excluyendo deliberaciones, notas y votos del TD (CA2, CA3).
- [x] **T3. Endpoint REST `GET /api/v1/expedientes/mis-solicitudes/` (Backend TDD):** Implementar vista protegida con `CanCreateT01`, filtrado estricto por `solicitante = request.user.socio`, filtros por estado y buscador textual (CA1, CA4, CA5). Pruebas de permisos y aislamiento.
- [ ] **T4. Servicio Angular y DTOs (`ExpedienteApiService`):** Definir interfaces DTOs y métodos en `ExpedienteApiService` para listar solicitudes iniciadas y eliminar borradores. Tests unitarios en Jasmine.
- [ ] **T5. Componente e Interfaz de Usuario ("Mis Solicitudes T01" en `SolicitarPuntosComponent`):** Incorporar panel inferior reactivo en `solicitar-puntos` con buscador, filtro de estados, tabla responsive y acciones de reanudación y descarte de borradores (CA5).
- [ ] **T6. Modal de Detalle Resumido y Trazabilidad:** Incorporar diálogo modal para visualizar la solicitud emitida con su estado procesal y resolución final sin datos reservados del TD (CA2, CA3).
- [ ] **T7. Suite Integral de Pruebas, Verificación y Consistencia:** Ejecutar suite backend (`pytest`), frontend (`npm test`), linters y corroborar consistencia con `notasPO.md`.
