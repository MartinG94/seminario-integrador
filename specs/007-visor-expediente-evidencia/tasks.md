# Tareas — Spec 007: Visor Autorizado de Expedientes y Evidencia Probatoria (US S4-01 / SCRUM-51)

- [x] **TS4-01.1 Modelo y Migración de Auditoría de Consulta (Backend TDD):** Implementar modelo `AuditoriaConsultaExpediente` inmutable en `backend/expedientes/models.py` y migración `0017_auditoria_consulta_expediente.py` dependiente de `0016`.
- [x] **TS4-01.2 Serializador Visor, Verificación SHA-256 y Protección Médica (Backend TDD):** Implementar `ExpedienteVisorSerializer` con cabecera TD, los 3 jueces con grupo Gxx, timeline cronológico, verificación de integridad SHA-256, enmascaramiento de datos médicos para terceros y rotulado de "Plazo vencido sin descargo".
- [x] **TS4-01.3 Endpoint REST Visor con Auditoría Automática (Backend TDD):** Implementar `ExpedienteVisorView` en `backend/expedientes/views/visor_views.py` protegido con `IsImputadoOrTribunal` y registro inmutable en base de datos.
- [x] **TS4-01.4 Suite de Tests Backend (`test_visor_expediente.py`):** Cobertura completa de CA1, CA2, CA3 y CA4.
- [x] **TS4-01.5 Servicio Frontend y DTOs (`ExpedienteApiService`):** Declarar interfaces tipadas y método `obtenerVisorExpediente` en `frontend/src/app/services/expediente-api.service.ts`.
- [x] **TS4-01.6 Componente Frontend `VisorExpedienteComponent` (Angular):** Crear vista de pantalla completa con cabecera canónica TD, 3 jueces con cohorte Gxx, acordeón T01, tabla de involucrados con evidencias e integridad SHA-256, rotulado de plazo vencido, timeline vertical y botón de retorno.
- [x] **TS4-01.7 Enrutamiento y Botones de Acceso en Gestión:** Registrar ruta en `admin-layout.routing.ts`, declarar en `admin-layout.module.ts`, e incorporar botón "Sustanciar / Visor" en tabla y Kanban de `gestionar-expedientes`.
- [x] **TS4-01.8 Suite de Tests Frontend (`visor-expediente.component.spec.ts`):** Tests unitarios en Karma/Jasmine para la vista dedicada.
- [x] **TS4-01.9 Verificación Integral y Consistencia PO:** Chequeo estricto contra `notasPO.md` y preparación de instrucciones manuales para el usuario en bash.
