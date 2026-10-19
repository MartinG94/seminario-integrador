# Tareas Técnicas — Spec 005: Adjuntar y Custodiar Evidencia Protegida (SCRUM-48 / S3-04)

Desglose de tareas atómicas de implementación (<30 min) conforme a la metodología Spec-Driven Development (SDD) y TDD.

---

- [x] **TS3-04.1 Dominio y Validación Binaria (Magic Bytes, Hash, Sanitización) [TDD]:**  
  Implementar `backend/expedientes/domain/evidence_validator.py` con validación estricta de magic bytes (PDF, JPEG, PNG), límite de 5 MB, sanitización de nombre contra path traversal, cálculo SHA-256 y control de cupos (T02 máx 3, T03 máx 5).  
  *Hecho cuando:* Tests unitarios en `backend/tests/expedientes/test_evidence_validator.py` pasando 100% en verde.

- [x] **TS3-04.2 Modelos ORM, Persistencia BLOB y Auditoría de Descargas [TDD]:**  
  Implementar `EvidenciaDescargo` y `AuditoriaDescargaEvidencia` en `backend/expedientes/models.py`. Generar migración Django.  
  *Hecho cuando:* Tests de persistencia, unicidad, integridad y preservación histórica (`es_vigente = False`) pasando 100% en verde.

- [x] **TS3-04.3 Servicio de Aplicación y Serializadores:**  
  Implementar `EvidenceService` en `backend/expedientes/services/evidence_service.py` y serializadores `EvidenciaMetadataSerializer` en `backend/expedientes/serializers.py`. Adaptar `PresentarDescargoSerializer`.  
  *Hecho cuando:* Tests de servicio y serializadores pasando 100% en verde.

- [x] **TS3-04.4 Endpoints REST de Carga y Descarga Segura Auditada [TDD]:**  
  Implementar `EvidenciaUploadView` y `EvidenciaDownloadView` en `backend/expedientes/views.py`, registrar rutas en `backend/expedientes/urls.py`, aplicar permiso por objeto `IsImputadoOrTribunal`, auditoría de descargas y headers `nosniff`.  
  *Hecho cuando:* Tests de integración de API pasando 100% en verde (subida 201, descarga 200, 400 formatos/cupos, 403 ajenos, 401 anónimos, 409 fuera de plazo).

- [x] **TS3-04.5 Servicio Frontend y DTOs (`ExpedienteApiService`) [TDD]:**  
  Agregar métodos `subirEvidencias` y `descargarEvidencia` con DTOs en `frontend/src/app/services/expediente-api.service.ts`.  
  *Hecho cuando:* Tests unitarios en Jasmine pasando 100% en verde.

- [x] **TS3-04.6 Componente Frontend `MisExpedientes` (Adjuntos Múltiples, Art. 102 y Descarga Segura):**  
  Integrar en `mis-expedientes.component.html` y `.ts`: selector múltiple con límites de 3 (T02) y 5 (T03), advertencia estatutaria visible Art. 102, previsualización/eliminación de adjuntos, visualización en modal de detalle de causa con descarga directa y notificaciones globales de 10s.  
  *Hecho cuando:* Tests en Karma/Jasmine pasando 100% en verde y renderizado responsive verificado.

- [x] **TS3-04.7 Verificación Integral, Cobertura, Linters y Consistencia PO:**  
  Ejecutar suite completa de backend (`pytest`) y frontend (`Karma`), linters (`ruff check/format`), verificar inmutabilidad de `notasPO.md` y consistencia con las directivas del PO.
