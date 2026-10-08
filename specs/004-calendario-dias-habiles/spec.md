# Spec 004 — Configurar calendario institucional de días hábiles (SCRUM-45 / S3-01)

## Contexto y objetivo
Permitir que la administración y autoridades institucionales de AVEIT (Comisión Directiva, Tribunal de Disciplina y Administrador de Cómputos) configuren y gestionen el calendario institucional de días hábiles, feriados nacionales y excepciones procesales. Esto garantiza que el cómputo de plazos perentorios (como los 5 días hábiles previstos en el Art. 12 Inc. 2 del Reglamento Procesal 2026 para la presentación de descargos T02/T03) sea completamente reproducible, determinista, inmutable en el tiempo y auditado.

Referencia Jira: [SCRUM-45](https://guillenmartin94.atlassian.net/browse/SCRUM-45) (Épica [SCRUM-30](https://guillenmartin94.atlassian.net/browse/SCRUM-30) EP-03: Descargos y Plazos Preclusivos).

---

## Historia de Usuario
**Como** administrador autorizado (ADMIN, CD, TD),  
**quiero** mantener los feriados y excepciones del calendario institucional,  
**para que** los plazos procesales sean reproducibles, justos y formalmente auditables.

---

## Criterios de Aceptación (EARS)

- **CA1 (Exclusión de fines de semana y feriados):**
  - Al contabilizar días hábiles para el cómputo de plazos, el sistema excluye automáticamente los sábados (weekday 5) y domingos (weekday 6).
  - Asimismo, se excluyen todas las fechas declaradas como feriados nacionales, asuetos institucionales o días inhábiles en la versión aplicable del calendario.

- **CA2 (Vigencia, Versión y Auditoría):**
  - Cada configuración de calendario posee un identificador de versión secuencial (`version`), rango de vigencia (`vigencia_desde`, `vigencia_hasta`), indicador de versión activa (`activa`), motivo auditado del cambio (`motivo_cambio`), autor (`creado_por`) y estampas temporales (`created_at`, `updated_at`).
  - Cada feriado o excepción asociada posee fecha (`fecha`), denominación (`descripcion`), tipo (`tipo`: NACIONAL, PROVINCIAL, INSTITUCIONAL, EXCEPCION) y estado laborable/inhábil (`es_laborable`).
  - Las versiones publicadas y aplicadas a plazos en curso no pueden modificarse destructivamente ni eliminarse. Todo nuevo ajuste crea una nueva versión de calendario con su correspondiente justificación de auditoría.

- **CA3 (Inmutabilidad y Reproducibilidad de Plazos Iniciados):**
  - Al iniciarse el plazo perentorio de descargo de un expediente (`iniciar_plazo_descargo`), se asocia de forma persistente e inmutable la versión del calendario institucional vigente (`calendario_version_id`).
  - Si con posterioridad se crea una nueva versión del calendario (por ejemplo, por decreto de un nuevo feriado o asueto imprevisto), los expedientes cuyo plazo ya fue iniciado conservan su versión asignada y su fecha/hora límite original (`plazo_limite_at`) sin recálculos que alteren la seguridad jurídica del socio imputado.

- **CA4 (Zona Horaria Oficial America/Argentina/Buenos_Aires):**
  - Todas las operaciones de fecha y hora, almacenamiento y cálculo de vencimientos deben ejecutarse de manera estricta bajo la zona horaria `America/Argentina/Buenos_Aires` (UTC-3).
  - La hora, minuto y segundo de la notificación o evento de despacho (`plazo_inicio_at`) se preservan exactamente en la fecha calculada de vencimiento (`plazo_limite_at`).

- **CA5 (Control de Acceso RBAC en Servidor):**
  - La creación y modificación de versiones y feriados institucionales está restringida a los roles autorizados: `ADMIN`, `CD` y `TD`. Los intentos por parte de roles no autorizados o socios ordinarios son denegados con HTTP 403 Forbidden y registrados en la auditoría de seguridad.
  - La lectura de la versión activa de feriados y el cálculo estimativo de plazos son públicos para cualquier usuario autenticado en el sistema.

- **CA6 (Interfaz Web y Simulación Reactiva):**
  - La SPA provee una interfaz accesible para visualizar los feriados vigentes, el histórico de versiones y agregar excepciones con justificación auditada.
  - Se provee una herramienta interactiva para que las autoridades y socios puedan simular y verificar el cómputo de plazos hábiles ingresando una fecha de inicio y cantidad de días, visualizando los días hábiles intermedios y el instante exacto de vencimiento.
  - El diseño cumple estrictamente con los tokens de `DESIGN.md` (Material Dashboard PRO), tipografía, contrastes WCAG 2.2 AA y disposición Mobile-First.

---

## Criterios de Finalización (DoD)
1. Modelos ORM de versiones de calendario y feriados/excepciones con restricciones de unicidad e integridad referencial.
2. Migración de base de datos con seeder inicial de los feriados oficiales de Argentina 2026 para la versión 1 activa.
3. Vinculación del modelo `Expediente` con la versión del calendario aplicada (`calendario_version`) en `iniciar_plazo_descargo`.
4. Endpoints REST completos con permisos RBAC en servidor y tests de cobertura > 80%.
5. Interfaz de usuario en Angular integrada en la navegación con simulación reactiva de plazos.
6. Suite completa de tests backend (`pytest`) y frontend (`npm test`) pasando en verde.
7. Verificación de consistencia estricta con `docs/gestion-proyecto/notasPO.md`.
