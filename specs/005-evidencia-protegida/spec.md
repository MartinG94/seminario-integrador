# Spec 005 — Adjuntar y Custodiar Evidencia Protegida (SCRUM-48 / S3-04)

## Contexto y Objetivo

Permitir que los socios imputados en un expediente disciplinario puedan adjuntar comprobantes probatorios (certificados médicos, constancias académicas, comprobantes laborales o pasajes) desde dispositivos móviles o de escritorio de forma protegida, garantizando la custodia segura, la trazabilidad inmutable y el cumplimiento estatutario del Régimen Disciplinario de A.V.E.I.T.

- **Referencia Jira:** [SCRUM-48](https://guillenmartin94.atlassian.net/browse/SCRUM-48) (S3-04).
- **Referencia Rectoral:** [Notas del PO (07/10/2026 y 27/09/2026)](../../docs/gestion-proyecto/notasPO.md).
- **Plan de Implementación Aprobado:** `plan_us_s3_04_evidencia_protegida.md`.
- **Sistema de Diseño:** [DESIGN.md](../../DESIGN.md) (Material Dashboard PRO Angular 2 / WCAG 2.2 AA).
- **Normativa Procesal:** Art. 12 Inc. 2 y Art. 102 del Reglamento Interno 2026.

---

## Historia de Usuario

**Como** socio imputado en un expediente disciplinario en período de justificaciones,  
**quiero** adjuntar comprobantes probatorios digitales (PDF o imágenes) al presentar o corregir mi descargo reglamentario,  
**para** respaldar mi justificación de inasistencia o descargo fáctico dentro del plazo perentorio de 5 días hábiles, asegurando su custodia confidencial y auditoría ante el Tribunal de Disciplina.

---

## Requisitos en Notación EARS

1. **Ubiquitous (Formatos, Tamaño y Límites Técnicos):**  
   El sistema *debe* soportar exclusivamente archivos en formato PDF (`application/pdf`), JPEG (`image/jpeg`) y PNG (`image/png`), con un tamaño máximo estricto de 5 MB (5.242.880 bytes) por archivo.

2. **Event-driven (Cupos de Documentos por Modalidad):**  
   CUANDO el socio presente un descargo:
   - Para el **Formulario T02 (Justificación Tipificada con Certificado)**: el sistema *debe* admitir entre 1 (mínimo obligatorio) y 3 (máximo) documentos adjuntos.
   - Para el **Formulario T03 (Descargo Libre / Extraordinario)**: el sistema *debe* admitir entre 0 y 5 (máximo) documentos adjuntos.

3. **Event-driven (Validación de Cabeceras Binarias y Metadatos):**  
   CUANDO un archivo sea enviado para su custodia:
   - El sistema *debe* inspeccionar las cabeceras binarias reales (*magic bytes*) del contenido para prevenir ataques de spoofing y verificar consistencia con el tipo MIME declarado.
   - El sistema *debe* extraer y registrar la extensión original en minúsculas, el nombre sanitizado contra *path traversal* y el hash SHA-256 inmutable de los bytes.

4. **Ubiquitous (Custodia en Base de Datos y Aislamiento por Objeto):**  
   El sistema *debe* persistir el contenido íntegro del archivo de forma serializada en la base de datos relacional MySQL (`LONGBLOB` / `models.BinaryField`), sin almacenamiento residual en el sistema de archivos del servidor. La deserialización y entrega en streaming *debe* requerir autenticación forzada y autorización por objeto (`IsImputadoOrTribunal`), reservada al socio imputado titular de la causa y a los miembros del Tribunal de Disciplina, Comisión Directiva y Administrador.

5. **Event-driven (Auditoría Inmutable de Descargas):**  
   CADA VEZ QUE un usuario consulte o descargue un comprobante probatorio,  
   el sistema *debe* asentar una fila inmutable en la tabla de auditoría con la identificación del usuario, su legajo, su rol, la fecha y hora institucional, la dirección IP de origen y el identificador de la evidencia.

6. **State-driven (Preservación Histórica ante Correcciones en Plazo):**  
   MIENTRAS el plazo perentorio de 5 días hábiles permanezca abierto y el socio modifique su descargo adjuntando nueva documentación,  
   el sistema *debe* preservar en la base de datos las versiones documentales previamente aportadas marcándolas con `es_vigente = False`, impidiendo cualquier pérdida de trazabilidad probatoria histórica.

7. **Event-driven (Advertencia Estatutaria Art. 102 en Frontend):**  
   CUANDO la interfaz de presentación de descargos sea desplegada,  
   el sistema *debe* mostrar de manera destacada, accesible e institucional el texto del Art. 102 del Reglamento Interno:  
   *"Aviso Reglamentario (Art. 102): La aceptación digital de esta constancia certifica su recepción en término, pero no exime de la obligación de presentar el certificado médico original físico cuando sea requerido formalmente por el Tribunal de Disciplina."*

8. **State-driven (Cierre Pesimista por Plazo o Estado Procesal):**  
   SI el plazo perentorio ha vencido (`now > plazo_limite_at`) O el expediente ya no se encuentra en estado `justificando`,  
   el sistema *debe* rechazar cualquier intento de carga o modificación de comprobantes con HTTP `409 Conflict`.

---

## Criterios de Aceptación (DoD)

- [ ] **CA1 (Límites y Formatos):** PDF, JPG, JPEG, PNG <= 5 MB; T02: 1 a 3 comprobantes; T03: 0 a 5 comprobantes.
- [ ] **CA2 (Validación Real y Metadatos):** Detección de magic bytes, hash SHA-256, sanitización de nombre y rechazo de spoofing.
- [ ] **CA3 (Custodia en BD y RBAC por Objeto):** Almacenamiento en `BinaryField` MySQL, endpoint protegido con `IsImputadoOrTribunal`, rechazo 401 a anónimos y 403 a terceros.
- [ ] **CA4 (Auditoría de Descarga):** Registro inmutable en `AuditoriaDescargaEvidencia` por cada acceso con streaming seguro (`nosniff`).
- [ ] **CA5 (Advertencia Art. 102 e Interfaz Responsive):** Advertencia legal visible en modal de descargo, selector de archivos múltiples, previsualización, modal de detalle con descarga segura y notificaciones centrales de 10s.
- [ ] **CA6 (Preservación Histórica):** Reenvíos en plazo conservan documentos previos con `es_vigente = False`.
- [ ] **CA7 (Suites en Verde):** 100% de tests backend (`pytest`) y frontend (`Karma`) pasando en verde sin regresiones.
