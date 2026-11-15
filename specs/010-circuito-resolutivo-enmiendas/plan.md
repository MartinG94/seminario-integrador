# Plan Técnico: Circuito Resolutivo Oficial, Exclusión Fundada, Corrección de Puntaje Final y Enmiendas Trazables

> **Clave Jira:** `SCRUM-89` (Macro 01)  
> **Subtareas:** `SCRUM-99`, `SCRUM-100`, `SCRUM-101`, `SCRUM-102`, `SCRUM-103`  
> **Sprint:** 5 Consolidado  
> **Documento de Requerimientos:** [`specs/010-circuito-resolutivo-enmiendas/spec.md`](spec.md)

---

## 1. Arquitectura y Módulos de la Solución

```
backend/
├── expedientes/
│   ├── models.py                     # Modelo EnmiendaResolucion + campos puntaje_ratificado y exclusión en DescargoExpediente
│   ├── migrations/
│   │   └── 0026_circuito_resolutivo_enmiendas.py
│   ├── services/
│   │   ├── causal_resolution_service.py # Persistencia de puntaje_ratificado en decide()
│   │   ├── exclusion_service.py         # Servicio de exclusión fundada y cierre administrativo si es último
│   │   ├── resolution_service.py        # Firma con selector de suplencia, emisión con EmailOutbox idempotente
│   │   └── enmienda_service.py          # Circuito de enmienda, versión 2 y contra-asientos Opción B
│   ├── serializers/
│   │   ├── visor_serializers.py         # Serialización de puntaje_ratificado, flags de exclusión
│   │   └── resolution_serializers.py    # Serialización de firmas y enmiendas
│   ├── views/
│   │   ├── resolution_views.py          # Endpoints de resolución, firma, emisión y enmienda
│   │   └── exclusion_views.py           # Endpoint de exclusión fundada
│   └── urls.py                          # Rutas REST
└── tests/
    └── expedientes/
        ├── test_causal_resolution_service.py
        ├── test_exclusion_involucrado.py
        ├── test_resolution_service.py
        ├── test_resolution_api.py
        └── test_enmienda_resolucion.py

frontend/
└── src/app/gestionar-expedientes/
    ├── gestionar-expedientes.component.ts     # getPuntajeFinalInvolucrado corregido, exclusión, enmienda, modal firma
    ├── gestionar-expedientes.component.html   # Botón excluir, socio tachado, selector suplente en firma, botón enmendar
    └── gestionar-expedientes.component.spec.ts# Tests Jasmine actualizados
```

---

## 2. Esquema DDL y Modelos

### 2.1. Alteraciones en `DescargoExpediente` (`expedientes_descargo`)
```python
# backend/expedientes/models.py
puntaje_ratificado = models.CharField(max_length=20, null=True, blank=True)
esta_excluido = models.BooleanField(default=False, db_index=True)
motivo_exclusion = models.TextField(blank=True, default="")
excluido_por = models.ForeignKey(
    settings.AUTH_USER_MODEL,
    null=True,
    blank=True,
    on_delete=models.PROTECT,
    related_name="exclusiones_involucrados",
)
excluido_at = models.DateTimeField(null=True, blank=True)
```

### 2.2. Modelo `EnmiendaResolucion` (`expedientes_enmienda_resolucion`)
```python
class EnmiendaResolucion(models.Model):
    expediente = models.ForeignKey(Expediente, on_delete=models.PROTECT, related_name="enmiendas")
    resolucion_anterior = models.ForeignKey("Resolucion", on_delete=models.PROTECT, related_name="enmiendas_posteriores")
    resolucion_nueva = models.OneToOneField("Resolucion", on_delete=models.PROTECT, related_name="origen_enmienda")
    motivo_enmienda = models.TextField()
    solicitado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "expedientes_enmienda_resolucion"
        ordering = ["-created_at"]
```

---

## 3. Contratos de API REST

1. **Excluir Involucrado:**
   - `POST /api/v1/expedientes/<id>/involucrados/<socio_id>/excluir/`
   - Permiso: `IsAuthenticated`, `CanTransitionExpedientes` (rol `TD`)
   - Payload: `{"motivo": "Exclusión fundada por error formal de imputación..."}`
   - Respuesta: `200 OK` con datos actualizados del involucrado y estado del expediente.

2. **Firmar Resolución (con Suplencia):**
   - `POST /api/v1/expedientes/<id>/resolucion/firmar/`
   - Permiso: `IsAuthenticated`, `CanTransitionExpedientes` (rol `TD`)
   - Payload opcional: `{"es_suplente": true | false}` (si se omite, se infiere del padrón)
   - Respuesta: `200 OK` con la resolución y lista de firmantes actualizada.

3. **Emitir Resolución Oficial:**
   - `POST /api/v1/expedientes/<id>/resolucion/emitir/`
   - Efecto: Calcula hash SHA-256, estado `ISSUED`, expediente a `EMITIDO`, despacha correos vía `EmailOutbox` con idempotencia.

4. **Enmendar Resolución Emitida:**
   - `POST /api/v1/expedientes/<id>/enmendar/`
   - Permiso: `IsAuthenticated`, `CanTransitionExpedientes` (rol `TD`)
   - Payload: `{"motivo_enmienda": "...", "considerandos": "...", "nuevos_puntajes": [{"socio_id": 1, "puntaje": -1.0}]}`
   - Respuesta: `201 Created` con la nueva resolución borrador (`version=2`), expediente pasa a `PENDIENTE_CORREOS`.
