# Plan Técnico — Spec 007: Visor Autorizado de Expedientes y Evidencia Probatoria (US S4-01 / SCRUM-51)

## Arquitectura y Componentes

### 1. Modelo de Datos y Persistencia Backend
- **Modelo:** `AuditoriaConsultaExpediente` en `backend/expedientes/models.py`.
- **Tabla:** `expedientes_auditoria_consulta`.
- **Migración:** `backend/expedientes/migrations/0017_auditoria_consulta_expediente.py` dependiente de `0016_merge_20261021_0916`.

### 2. Serialización y Lógica de Dominio
- **Módulo:** `backend/expedientes/serializers/visor_serializers.py`.
- **Serializer Principal:** `ExpedienteVisorSerializer`.
- **Funciones de Dominio:**
  - `check_evidencia_integrity(ev: EvidenciaDescargo) -> tuple[bool, bool]`
  - `es_causal_medica(causal: str, texto: str) -> bool`
  - `tiene_acceso_medico(user, socio_imputado_id: int) -> bool`
  - `obtener_responsables_td() -> list[dict]`
  - `construir_timeline(expediente: Expediente) -> list[dict]`

### 3. Endpoint REST DRF
- **Vista:** `ExpedienteVisorView(APIView)` en `backend/expedientes/views/visor_views.py`.
- **Ruta:** `GET /api/v1/expedientes/<int:pk>/visor/`.
- **Permisos:** `[IsAuthenticated, IsImputadoOrTribunal]`.
- **Auditoría:** Inserción automática en `AuditoriaConsultaExpediente` con IP, rol y user-agent.

### 4. Capa Frontend (Angular 14.2 / Material Dashboard PRO)
- **Servicio:** `ExpedienteApiService.obtenerVisorExpediente(expedienteId: number): Observable<ExpedienteVisorData>`.
- **Componente:** `VisorExpedienteComponent` en `frontend/src/app/gestionar-expedientes/visor-expediente/`.
- **Rutas:** `/gestionar-expedientes/:id/visor` protegida por `TribunalGuard`.
- **Acceso:** Botón "Sustanciar / Visor" en tabla y Kanban de `gestionar-expedientes`.
- **Diseño:** Full responsive (Mobile-First 375px), WCAG 2.2 AA, notificaciones 10s globales.
