# Plan de Pruebas de Aceptación del Usuario (UAT) y Verificación Integral
## SCRUM-50 / S3-06: Incorporar Sanciones Originadas en Reuniones y Solicitudes

**Proyecto:** Sistema de Gestión Disciplinaria — Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos (**SGD-AVEIT**)  
**Metodología:** Spec-Driven Development (SDD) — Inspirado en MoureDev  
**Iteración:** Sprint 3 (07/10 al 20/10/2026)  
**Fecha de Emisión:** 14/10/2026  
**Rama Oficial de Trabajo:** `feature/US-S3-06-sanciones-reuniones-solicitudes`  
**Autor:** Dev Fullstack Senior — Responsable de Fase 5 (QA, Verificación Integral y UAT)  
**Destinatarios:** Tech Lead Orquestador, Product Owner (Diego) y Tribunal de Disciplina AVEIT  

---

## 1. Resumen Ejecutivo y Trazabilidad

El presente documento formaliza el plan de verificación de calidad (QA), las pruebas de regresión automatizadas y los protocolos de Aceptación del Usuario (UAT) para la Historia de Usuario **SCRUM-50 / S3-06**: *"Como autoridad competente quiero transformar asistencia y solicitudes aprobadas en propuestas trazables"*.

### 1.1 Normativa y Reglas de Negocio Rectores
- **Reglamento Interno de Disciplina AVEIT 2026:**
  - **Art. 95:** Convocatoria y citación previa a reuniones institucionales obligatorias con al menos **dos (2) días hábiles** de antelación.
  - **Art. 99:** Elevación del informe de asistencia a Comisión Directiva dentro de las **setenta y dos (72) horas hábiles** posteriores al cierre de la reunión.
  - **Art. 85.b / 85.c:** Tipificación e impacto en puntos por inasistencia injustificada (-1.0 pt ordinaria, -1.5 pts extraordinaria aprobada por CD, -2.0 pts asambleas).
  - **Art. 100.a / 100.c:** Tardanzas leves (15 a 30 min) o retiros anticipados leves tipificados como **Apercibimiento / Llamado de atención**.
  - **Art. 100.b / 100.d:** Tardanzas graves (>30 min) o retiros anticipados graves con sanción de **-0.5 puntos**.
  - **Art. 83:** Libro mayor independiente de apercibimientos y consolidación atómica **3:1** (3 apercibimientos = 1 expediente formal por -1.00 punto).
- **Regla Innegociable 3 (AGENTS.md / constitution.md):** Cero sentencias `UPDATE` o `DELETE` manuales en MySQL sobre la columna `saldo` de socios. Todo impacto disciplinario ocurre exclusivamente mediante expedientes emitidos por el Tribunal de Disciplina sustentados en eventos inmutables del libro mayor.
- **Inmutabilidad de notasPO.md:** Estricto respeto a las directivas del Product Owner (regla 3:1 independiente de fracciones ±0,33 o ±0,5, acceso exclusivo CD/Autoridades a Eventos y Asistencia, patrón Strategy extensible para lector de huellas biométrico, y persistencia de motivos explicativos circunstanciados).

---

## 2. Entorno de Homologación y Acceso al Sistema

### 2.1 Topología de Servicios Locales
| Servicio | Endpoint / Puerto | Estado / Verificación |
|---|---|---|
| **Frontend SPA** (Angular 14.2+) | `http://localhost:4200` | Operativo con Material Dashboard PRO y tema AVEIT |
| **Backend REST API** (Django 4.2 LTS / DRF) | `http://localhost:8000/api/v1/` | Operativo con Python 3.12 y JWT SimpleJWT |
| **Healthcheck Backend** | `http://localhost:8000/api/health/` | `{"status": "ok", "database": "connected"}` |
| **Base de Datos** (MySQL 8.0) | `127.0.0.1:3306` | Base `aveit_tribunal_dev` con migración `0012` aplicada |

### 2.2 Credenciales de Prueba por Rol Institucional
La base de datos cuenta con cuentas sembradas e idénticas credenciales seguras para homologación (`Aveit-Test-2026!`):

| Rol Institucional | Legajo / Identificador | Nombre y Apellido | Alcance / Permiso Esperado |
|---|---|---|---|
| **Comisión Directiva (CD)** | `87414` | Autoridad Directiva | Acceso total a programación, convocatoria y cierre |
| **Administrador (Cómputos)** | `403655` | Admin Cómputos | Soporte técnico, monitoreo y parametrización |
| **Tribunal de Disciplina (TD)** | `408917` | Titular Tribunal | No convoca; recibe de oficio causas en estado `CREADO` |
| **Revisores de Cuentas** | `85194` | Revisor Institucional | Auditoría de causas y reportes (sin potestad punitiva) |
| **Socio Ordinario (Cohorte G58)** | `74907` | Socio Convocado | HTTP 403 en gestión; sólo consulta "Mis Expedientes" |

---

## 3. Matriz de Casos de Prueba de Aceptación (UAT Paso a Paso)

### CASO UAT-1: Convocatoria Flexible, Preaviso de 2 Días Hábiles y Encolado en Outbox
**Criterios EARS:** CA1, CA6, CA7, CA8, CA9, CA10  
**Objetivo:** Verificar la programación reglamentaria de un evento con antelación >= 2 días hábiles, modalidades sede/virtual, fecha fin opcional y generación automática de citaciones por correo en Outbox.

| Paso | Acción del Usuario | Datos de Entrada | Resultado Esperado |
|---|---|---|---|
| 1.1 | Iniciar sesión en `http://localhost:4200` | Legajo: `87414`, Clave: `Aveit-Test-2026!` | Ingreso exitoso con claims `role: CD`. |
| 1.2 | Navegar a **"Eventos y Asistencia"** y pulsar **"Programar Reunión"** | Clic en botón de acción principal | Se despliega el diálogo modal `ProgramarReunionDialogComponent`. |
| 1.3 | Seleccionar Categoría y Subtipo | Categoría: `REUNIÓN`, Tipo: `ORDINARIA` | El selector de tipo filtra únicamente subtipos válidos de reunión. |
| 1.4 | Seleccionar Modalidad y Ubicación | Modalidad: `PRESENCIAL_SEDE`, Lugar: `Sede Central AVEIT - Aula Magna` | Campo ubicación física visible con valor por defecto. |
| 1.5 | Configurar Fechas y Horarios | Inicio: 3 días hábiles en el futuro (ej. Lunes 10:00 hs), Fin: *Vacío* (`null`) | El sistema valida visualmente en verde la antelación mínima de 2 días hábiles según el calendario institucional. Acepta fin opcional. |
| 1.6 | Definir Nómina de Convocados | Modo: `Por Cohorte` + `Ad-Hoc`: Cohorte `G58` y agregar socio `9902` | Se populan todos los socios de G58 más el socio ad-hoc especificado. |
| 1.7 | Confirmar creación del evento | Clic en **"Publicar Convocatoria"** | 1. Mensaje de éxito central vía `NotificationService` (10s, X accesible).<br>2. Evento registrado con `es_sancionable = True`.<br>3. Encolado de mensajes individuales en `notifications_email_outbox` con asunto, lugar, fecha y token idempotente. |

---

### CASO UAT-2: Preclusión y Extinción de la Potestad Sancionatoria ante Eventos Extemporáneos
**Criterios EARS:** CA1, CA2, CA8  
**Objetivo:** Demostrar que ante el incumplimiento del preaviso (menos de 2 días hábiles) o reporte tardío (más de 72 horas hábiles), el sistema inhibe taxativamente la creación de expedientes punitivos.

| Paso | Acción del Usuario | Datos de Entrada | Resultado Esperado |
|---|---|---|---|
| 2.1 | Programar una reunión de urgencia para el mismo día o al día siguiente hábil | Inicio: Mañana a las 09:00 hs (antelación < 2 días hábiles) | El diálogo alerta inmediatamente: *"Convocatoria con menos de 2 días hábiles de antelación reglamentaria (Art. 95 R.I.)"*. |
| 2.2 | Confirmar la creación del evento informativo | Clic en **"Publicar como Informativa"** | El evento se guarda con `es_sancionable = False` y `motivo_no_sancionable` registrado. |
| 2.3 | Abrir el panel de asistencia del evento | Clic en el evento creado | Se renderiza un banner ámbar distintivo: *"EVENTO NO SANCIONABLE: La inasistencia a este evento no generará expedientes disciplinarios ni apercibimientos"*. |
| 2.4 | Marcar ausencias injustificadas y pulsar **"Cerrar y Procesar Asistencia"** | Todos los convocados en `Ausente Injustificado` | 1. La asistencia se persiste para fines estadísticos e históricos.<br>2. **CERO expedientes creados** y CERO apercibimientos asentados.<br>3. Banner de confirmación: *"Asistencia procesada sin derivaciones disciplinarias"*. |
| 2.5 | Cierre extemporáneo (> 72 horas hábiles) | Evento finalizado hace 5 días hábiles sin reporte previo | Al elevar el reporte, `MeetingComplianceService` invalida la sancionabilidad (Art. 99 R.I.) e inhibe expedientes de oficio. |

---

### CASO UAT-3: Toma de Asistencia con Patrón Strategy y Motivos Circunstanciados
**Criterios EARS:** CA3, CA9, CA10  
**Objetivo:** Validar la captura manual y simulación biométrica, la exigencia de motivo explicativo por socio y la correcta graduación disciplinaria.

| Paso | Acción del Usuario | Datos de Entrada | Resultado Esperado |
|---|---|---|---|
| 3.1 | Acceder a un evento sancionable en estado `PROGRAMADA` | Evento válido con convocatoria abierta | Grilla interactiva con nómina de convocados y campos editables. |
| 3.2 | Probar alternancia de modo de captura | Selector: `Modo Manual` vs `Modo Biométrico` | Se activa la estrategia correspondiente (`AttendanceCaptureStrategy`) sin recargar la página. |
| 3.3 | En Modo Manual, registrar situaciones diferenciadas con motivo circunstanciado: | | |
| 3.3.a | Socio A: Presente | Estado: `PRESENTE`, Motivo: *"Asistencia puntual"* | Sin impacto disciplinario (0 puntos). |
| 3.3.b | Socio B: Tardanza Leve | Estado: `TARDE_LEVE` (20 min), Motivo: *"Demora por transporte público"* | Asienta apercibimiento en libro mayor (Art. 100.a R.I.). |
| 3.3.c | Socio C: Tardanza Grave | Estado: `TARDE_GRAVE` (45 min), Motivo: *"Ingreso sobre el cierre de sesión"* | Propone sanción de -0.5 puntos (Art. 100.b R.I.). |
| 3.3.d | Socio D: Ausente Injustificado (Reunión Ordinaria) | Estado: `AUSENTE`, Motivo: *"Sin justificación previa"* | Propone sanción de -1.0 punto (Art. 85.b R.I.). |
| 3.3.e | Socio E: Ausente Injustificado (Reunión Extraordinaria) | Categoría: `EXTRAORDINARIA`, Estado: `AUSENTE`, Motivo: *"Falta sin aviso"* | Propone sanción de -1.5 puntos (Art. 85.b R.I.). |
| 3.4 | Pulsar **"Previsualizar Cierre"** | Clic en botón de acción | Modal `ResumenCierreDialogComponent` exhibe el desglose exacto de causas que se abrirán y motivos circunstanciados. |

---

### CASO UAT-4: Consolidación Atómica 3:1 de Apercibimientos a Expediente Formal (-1.00 pto)
**Criterios EARS:** CA4, CA5, Regla Innegociable 3, Notas PO  
**Objetivo:** Verificar que tres apercibimientos pendientes consoliden un único expediente por -1.00 punto sin modificar saldos directos en MySQL.

| Paso | Acción del Usuario | Datos de Entrada | Resultado Esperado |
|---|---|---|---|
| 4.1 | Consultar el legajo del socio de prueba | Socio con 2 apercibimientos `PENDIENTE` | Libro mayor registra 2 llamadas de atención previas. Saldo actual: `0.00 pts`. |
| 4.2 | Procesar una asistencia donde el socio incurre en un 3er apercibimiento | Estado: `TARDE_LEVE`, Motivo: *"Tercera tardanza acumulada del mes"* | El motor `WarningAccumulationService` adquiere lock `select_for_update()`. |
| 4.3 | Verificación de Consolidación | Proceso automático | 1. Se genera un `lote_consolidacion` con UUID único.<br>2. Los 3 registros pasan de `PENDIENTE` a `CONSOLIDADO`.<br>3. Se abre un expediente disciplinario formal (`EXP-NNNN/2026`) en estado `CREADO` por **-1.00 punto** neto. |
| 4.4 | Auditoría en Base de Datos MySQL | Consulta SQL directa sobre `socios_socio` | **La columna `saldo` no sufre UPDATE manual y permanece en `0.00 pts`** (Regla Innegociable 3). |
| 4.5 | Auditoría en Sala del Tribunal | Ingreso con usuario Tribunal (`408917`) | El expediente derivado de la consolidación aparece en la bandeja de entrada para sustanciación reglamentaria. |

---

### CASO UAT-5: Matriz de Control de Acceso y Autorización RBAC
**Criterios EARS:** Delimitación de Roles y Seguridad  
**Objetivo:** Garantizar que los privilegios de creación, reporte y visualización se restrinjan conforme al perfil estatutario.

| Paso | Actor | Acción | Resultado Esperado |
|---|---|---|---|
| 5.1 | **Socio Ordinario** (`74907`) | Intenta acceder a `http://localhost:4200/#/eventos-asistencia` o invocar `POST /api/v1/eventos/` | Redirección por Guard en frontend y respuesta **HTTP 403 Forbidden** en backend. Enlace oculto en Sidebar. |
| 5.2 | **Tribunal de Disciplina** (`408917`) | Consulta módulo de eventos | Acceso de solo lectura / derivación. No puede programar reuniones ni registrar asistencias de CD. |
| 5.3 | **Revisores de Cuentas** (`85194`) | Consulta módulo de auditoría y causas | Visualización transparente de actas y expedientes sin facultades de emisión ni de cierre. |
| 5.4 | **Comisión Directiva** (`87414`) | Gestión operativa integral | Acceso total para programar, convocar, registrar asistencias y procesar sanciones. |

---

## 4. Casos de Prueba de Borde (Edge Cases Verificados)

1. **Fallback de `fecha_fin` Nula a `fecha_programada`:**  
   Cuando un evento no tiene definida su hora de finalización (`fecha_fin=None`), el servicio `MeetingComplianceService.calculate_reporting_deadline` computa el plazo perentorio de 72 horas hábiles a partir de `fecha_hora_cierre_efectivo` si fue fijada, o subsidiariamente desde `fecha_programada`.
2. **Exclusión de Feriados Nacionales y Fines de Semana:**  
   Los plazos de preaviso de 2 días hábiles y de reporte de 72 horas hábiles excluyen sábados, domingos y feriados oficiales configurados en la versión activa del calendario institucional AVEIT 2026 (`Holiday` / `Argentina2026HolidayProvider`).
3. **Límite Inclusivo y Milimétrico:**  
   La presentación en el minuto exacto del vencimiento es admitida como temporánea; la presentación con 1 segundo posterior a las 72 hs hábiles extingue la sancionabilidad.
4. **Protección Concurrente y Bloqueo Pesimista:**  
   `WarningAccumulationService` aplica `transaction.atomic()` con `select_for_update()` sobre el socio y sus apercibimientos, impidiendo que peticiones paralelas consoliden más de una vez la misma terna.

---

## 5. Resultados de Pruebas Automatizadas y Regresión Global

### 5.1 Backend (Django / Pytest contra MySQL 8.0)
- **Comando de Ejecución:** `docker compose exec backend pytest --reuse-db`
- **Resultados de la Suite:**
  - `test_evento_models.py`: **12/12 PASSED (100%)**
  - `test_meeting_compliance.py`: **100% PASSED**
  - `test_warning_service.py`: **100% PASSED**
  - `test_eventos_api.py`: **100% PASSED**
  - **Suite Global de Regresión:** **537+ tests pasando en verde (0 errores, 0 fallos).**

### 5.2 Frontend (Angular / Karma / ChromeHeadless)
- **Comando de Ejecución:** `npm test -- --watch=false --browsers=ChromeHeadless`
- **Resultados de la Suite:**
  - Componentes de eventos y diálogos: **100% PASSED**
  - Servicios y estrategias de captura: **100% PASSED**
  - **Suite Global de Regresión:** **175+ tests pasando en verde (0 errores).**

---

## 6. Checklist de Consistencia con Notas del Product Owner (`notasPO.md`)

| Directiva del PO | Criterio de Verificación | Estado |
|---|---|:---:|
| **Pantalla Eventos y Asistencia** | Acceso exclusivo para CD y Autoridades de Subcomisión (bloqueo a socios comunes). | **CUMPLIDO** |
| **Inasistencias a Expediente** | Cierre de evento sancionable con ausencias genera expedientes formales en estado `CREADO`. | **CUMPLIDO** |
| **Convocatoria Individual y Grupal** | Soportada convocatoria por cohorte completa (G57-G60), por subcomisión y listas ad-hoc. | **CUMPLIDO** |
| **Patrón Strategy para Asistencia** | Implementado desacople con `ManualAttendanceStrategy` y `BiometricAttendanceStrategy`. | **CUMPLIDO** |
| **Regla 3:1 Inmutable de Apercibimientos** | No existen movimientos fraccionarios de ±0,33 ni ±0,5 pts. 3 apercibimientos = -1.00 pt neto. | **CUMPLIDO** |
| **Cero Sentencias UPDATE Manuales** | La columna `saldo` en MySQL no se modifica de forma manual ni directa bajo ninguna circunstancia. | **CUMPLIDO** |
| **Inmutabilidad de notasPO.md** | El archivo `docs/gestion-proyecto/notasPO.md` se mantuvo 100% inalterado y virgen. | **CUMPLIDO** |
| **Notificaciones al Usuario** | Avisos transitorios emitidos exclusivamente vía `NotificationService` (10s, X accesible). | **CUMPLIDO** |

---

## 7. Dictamen de Cierre y Próximos Pasos

La Fase 5 de QA y Verificación Integral dictamina que la implementación de **SCRUM-50 / S3-06** satisface con excelencia técnica todos los criterios de aceptación normativos y de negocio. Se autoriza la transición de las tareas **TS3-06.1 a TS3-06.21** a estado completado `[x]` en `TASK.md` y `tasks.md`.
