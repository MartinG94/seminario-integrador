# Spec 005 — Sanciones originadas en reuniones y solicitudes (SCRUM-50 / S3-06)

## Contexto y Alcance

Permitir que las autoridades competentes (Comisión Directiva y Autoridades de Subcomisiones) transformen la asistencia y solicitudes aprobadas en propuestas disciplinarias y expedientes trazables. Se formalizan las reuniones institucionales obligatorias, el control procesal de plazos de convocatoria y reporte conforme al Reglamento Interno (Arts. 83, 85, 95, 99 y 100), el registro de asistencia mediante el patrón Strategy (manual y biométrico extensible), la escala reglamentaria de puntos (admitiendo múltiplos de 0.5 e incluyendo 1.5), el régimen de acumulación atómica 3:1 para apercibimientos, y la apertura de oficio de expedientes sin alterar saldos de puntos mediante `UPDATE` manual en MySQL.

Documentos rectores innegociables:
- [`docs/constitution.md`](../../docs/constitution.md) y [`AGENTS.md`](../../AGENTS.md) (Regla 3: Cero sentencias UPDATE/DELETE manuales en MySQL sobre saldos).
- [`docs/gestion-proyecto/notasPO.md`](../../docs/gestion-proyecto/notasPO.md) (Sección "Pantalla: Eventos y Asistencia", "Llamados de atención y Felicitaciones", y lineamientos del 07/10/2026).
- Reglamento Interno de Disciplina AVEIT 2026 (Arts. 83, 85, 95, 99 y 100).

---

## Historias de Usuario

**Como** autoridad competente (Comisión Directiva o Responsable de Subcomisión),  
**quiero** convocar reuniones institucionales obligatorias y reportar la asistencia de los socios convocados,  
**para que** el sistema compute automáticamente las inasistencias y tardanzas según los plazos reglamentarios.

**Como** sistema disciplinario de AVEIT,  
**quiero** verificar los plazos de publicación previa (2 días hábiles) y de reporte (72 horas hábiles),  
**para que** solo se generen propuestas de sanción válidas y se extinga la potestad punitiva en reuniones extemporáneas.

**Como** integrante del Tribunal de Disciplina o Comisión Directiva,  
**quiero** que cada tres apercibimientos acumulados consoliden automáticamente un expediente de -1.0 punto neto sin aplicar fracciones directas,  
**para que** se respete la regla de acumulación 3:1 con trazabilidad inmutable y sin escritura manual en el saldo del socio.

---

## Criterios de Aceptación (EARS)

- **CA1 — Validación de Publicación y Reporte en Días Hábiles:**
  - *Publicación Previa (Art. 95):* Cuando se programa y publica una reunión o actividad de carácter obligatorio y sancionable, el sistema valida que medien al menos dos (2) días hábiles completos entre la publicación formal y la hora de inicio del evento, computados mediante el servicio de calendario institucional único (`Holiday` / `compute_business_deadline`).
  - *Reporte de Asistencia (Art. 99):* Cuando se eleva el informe de asistencia a la Comisión Directiva, el sistema valida que la presentación se realice dentro de las setenta y dos (72) horas hábiles administrativas (equivalentes a 3 días hábiles completos) posteriores a la finalización del evento. Si la fecha de finalización no fue fijada (`fin_at` es nulo), el plazo preclusivo se computa a partir de la hora de cierre efectivo reportada o, subsidiariamente, desde la fecha y hora de inicio del evento.
- **CA2 — Invalidez Sancionatoria ante Incumplimiento de Requisitos:**
  - Cuando una reunión o actividad no cumple con los dos días hábiles de antelación en su convocatoria o el reporte de asistencia se eleva superando las 72 horas hábiles, el sistema declara el evento como `NO_SANCIONABLE`.
  - El sistema permite registrar y conservar la asistencia para fines informativos y estadísticos, pero **inhibe taxativamente la apertura de expedientes disciplinarios o el cómputo de apercibimientos**.
- **CA3 — Escala Reglamentaria Decimal con 0.5 y 1.5:**
  - Cuando se generan propuestas sancionatorias por inasistencia o impuntualidad, el sistema aplica exclusivamente la escala decimal con paso de 0.5 en formato `Decimal` (prohibiendo tipos `float` o fracciones continuas):
    - Falta injustificada a Reunión Ordinaria de Subcomisión: **-1.0 punto** (Art. 85.b).
    - Falta injustificada a Reunión Extraordinaria aprobada por CD: **-1.5 puntos** (Art. 85.b).
    - Falta injustificada a Asamblea Ordinaria o Extraordinaria: **-2.0 puntos** (Art. 85.c).
    - Falta injustificada a Actividad de Mantenimiento / Voluntariado: **-1.0 punto por defecto**, o el puntaje personalizado definido en `puntos_sancion` para la actividad (Art. 85.a/d).
    - Tardanza grave (> 30 min) o retiro anticipado grave (> 30 min): **-0.5 puntos** (Art. 100.b/d).
    - Tardanza leve (15-30 min) o retiro anticipado leve: **Apercibimiento / llamado de atención** (Art. 100.a/c).
- **CA4 — Régimen de Acumulación Atómica de Apercibimientos 3:1:**
  - Cuando un socio incurre en un apercibimiento o llamado de atención, el sistema registra y acumula el contador en la entidad preexistente `atencionFelicitacion` (PK `nroSocio`) sin modificar el saldo de puntos (los apercibimientos no son ±0,33 ni ±0,5).
  - Cuando un socio acumula tres (3) llamados de atención pendientes (`llamadosAtencion >= 3`), el sistema consolida la terna generando automáticamente un expediente formal por **-1.0 punto** neto una sola vez y descuenta 3 del contador (`llamadosAtencion -= 3`) para impedir dobles cómputos. De manera simétrica, cada tres (3) felicitaciones acumulan un mérito de **+1.0 punto**.
- **CA5 — Cero Sentencias UPDATE Manuales y Flujo Formal:**
  - Cuando se procesa el cierre de un evento con socios sancionables, el sistema genera de oficio expedientes en estado `CREADO` (`EXP-NNNN/YYYY`).
  - Ninguna operación de eventos o acumulación escribe o modifica directamente la columna `saldo` en la base de datos MySQL (cumplimiento estricto de la Regla Innegociable 3 y ADR-001). El impacto en el saldo solo ocurrirá cuando el Tribunal de Disciplina sustancie la causa y emita la resolución final colegiada.
- **CA6 — Flexibilidad de Convocatoria a Individuos (Grupos, Subcomisiones, Estado Social y Listas Personalizadas):**
  - Cuando una autoridad convoca a una reunión o actividad con fecha y hora, el sistema permite definir la nómina de convocados (persistida en `tribunal_evento_convocado`) bajo cuatro modalidades:
    1. **Por Grupo Social Completo (`GRUPO`):** Convocatoria masiva a todos los socios pertenecientes a una cohorte específica (ej. todo el grupo `G58`, o `G55`–`G60`).
    2. **Por Subcomisión Completa (`SUBCOMISION`):** Convocatoria masiva a todos los socios asignados a una subcomisión reglamentaria (ej. toda la Subcomisión de `Cómputos`, `Finanzas`, etc.).
    3. **Por Estado Social (`ESTADO_SOCIAL`):** Convocatoria masiva por tramo de carrera social (`JUNIORS` de 1° a 3° año social, o `SENIORS` de 4° año en adelante).
    4. **Por Listas Personalizadas / Ad-Hoc de Gente (`PERSONALIZADA`):** Convocatoria a una nómina ad-hoc mediante búsqueda y selección reactiva de socios (estilo Select2) por nombre, apellido o legajo.
- **CA7 — Notificación Automática por Correo Electrónico y Ciclo de Vida de 6 Estados (Art. 95 R.I.):**
  - El ciclo de vida del evento contempla 6 estados formales: `CREADO`, `NOTIFICADO`, `EN_CURSO`, `ABIERTO`, `FINALIZADO` y `ANULADO`.
  - Cuando una reunión o actividad institucional es notificada (al crearse con `notificar=True` o mediante la acción `/notificar/`), el sistema despacha de manera automática una notificación individual por correo electrónico a cada uno de los socios citados a través del servicio transaccional Outbox (`EmailDispatcherService`), y envía correos de disculpas si un evento notificado se anula (`/anular/`).
  - El correo notifica formalmente la citación con asunto claro, fecha, hora de inicio, lugar/modalidad (sede, externa o link virtual), tolerancia, carácter del evento (`OBLIGATORIA Y SANCIONABLE` o `NO SANCIONABLE`) y enlace seguro directo a la plataforma, cumplimentando la notificación exigida por el Art. 95 del Reglamento Interno.
- **CA8 — Campos Mínimos Obligatorios y Fecha de Finalización Opcional:**
  - Al dar de alta un evento, son obligatorios mínimos: `titulo` (`nombre`), `fecha_programada` (`fechaHoraInicio`), `categoria` (`REUNION` o `ACTIVIDAD`), `tipo` (subtipo reglamentario correspondiente) y `modalidad` (`PRESENCIAL_SEDE`, `PRESENCIAL_EXTERNA` o `VIRTUAL`). Para `ACTIVIDAD` es obligatorio consignar `detalle_tarea`.
  - El campo `fecha_fin` (`fechaHoraFin`) es estrictamente **opcional** (`null=True`). La aplicación permite iniciar y gestionar eventos de duración abierta (estado `ABIERTO`) y fijar la hora de finalización con posterioridad (`/fijar-hora-fin/`).
- **CA9 — Distinción Formal entre "Reunión" y "Actividad":**
  - El sistema distingue formalmente a nivel de base de datos, backend y frontend la categoría del evento:
    - `REUNION`: Ámbito deliberativo, reglamentario o asambleario (subtipos: `ORDINARIA`, `EXTRAORDINARIA`, `ASAMBLEA`, `PLENARIO`).
    - `ACTIVIDAD`: Tareas operativas, mantenimiento o voluntariado institucional (subtipos: `MANTENIMIENTO`, `VOLUNTARIADO`, `JORNADA`, `EVENTO_SOCIAL`, `GUARDIA`).
  - Las opciones de tipo se filtran y validan dinámicamente según la categoría elegida, y los impactos disciplinarios se aplican conforme a la tipificación correspondiente.
- **CA10 — Modalidades de Realización y Motivo Circunstanciado en Asistencia:**
  - El sistema soporta tres modalidades de realización:
    1. `PRESENCIAL_SEDE`: Desarrollada en la Sede Central de AVEIT.
    2. `PRESENCIAL_EXTERNA`: Realizada fuera de la sede, requiriendo consignar la dirección o locación en `ubicacion`.
    3. `VIRTUAL`: Realizada por medios telemáticos, requiriendo enlace de videoconferencia (Meet/Zoom/Teams) en `ubicacion`/`enlace_virtual`.
  - En la toma y reporte de asistencia, el creador u organizador puede y debe registrar siempre el `motivo` u observación explicativa circunstanciada para cada socio citado (tanto presentes, tardanzas leves/graves, retiros o ausencias), garantizando que las justificaciones consten formalmente en los expedientes disciplinarios derivados.

---

## Delimitación de Roles y Seguridad (RBAC)

- **Comisión Directiva (`Role.CD`) y Administradores (`Role.ADMIN`):**
  - Acceso total a la pantalla "Eventos y Asistencia" para programar reuniones, convocar socios/grupos y cargar asistencias.
- **Autoridades de Subcomisión / Representantes de Grupo:**
  - Habilitados para convocar y reportar asistencia exclusivamente de sus respectivas subcomisiones o cohortes asignadas.
- **Tribunal de Disciplina (`Role.TD`):**
  - No gestiona convocatorias ni toma de asistencia; recibe de oficio los expedientes generados en estado `CREADO` para su sustanciación y deliberación colegiada.
- **Socios Ordinarios (`Role.SOCIO`):**
  - Acceso restringido a la pantalla y endpoints de gestión de eventos (HTTP 403 Forbidden). Solo pueden visualizar en su portal "Mis Expedientes" las causas notificadas en su contra.

---

## Interfaz de Usuario y Accesibilidad

1. **Tokens de Diseño:** Adhesión estricta a [`DESIGN.md`](../../DESIGN.md) (paleta institucional `#151846`, `#6E9DDC`, card floating headers, bordes suaves de 8px y tipografía Montserrat/Roboto).
2. **Notificaciones al Usuario:** Avisos temporales exclusivamente vía `NotificationService` centralizado (inferior derecho, 10 segundos, botón X accesible, texto plano).
3. **Búsqueda Reactiva de Socios:** Componente de autocompletado reactivo tipo Select2 con búsqueda dinámica por nombre, apellido o legajo, y selector masivo por grupos (`G57`, `G58`, `G59`, `G60`) o subcomisiones.
4. **Patrón Strategy en Frontend:** Selector de modo de captura de asistencia (`Modo Manual` con switches de estado vs `Modo Biométrico` con simulación auditiva y visual).
