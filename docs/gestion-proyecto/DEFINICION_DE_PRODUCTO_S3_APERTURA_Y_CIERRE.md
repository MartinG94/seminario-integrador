# DEFINICIÓN DE PRODUCTO — SPRINT 3 (APERTURA Y CIERRE)
## Sistema de Gestión del Tribunal de Disciplina y Premiaciones de A.V.E.I.T. (SGD-AVEIT)

**Cátedra:** Seminario Integrador — Curso 3K2 — Ciclo Lectivo 2026  
**Carrera:** Ingeniería en Sistemas de Información / ADUSI — UTN FRC  
**Equipo de Proyecto:** Grupo Nº 04  
**Product Owner:** Diego Gabriel Sánchez (Nº Socio: 87414)  
**Scrum Master:** Lucas Martín Guillén (Nº Socio: 85194)  
**Iteración:** Sprint 3 (08/10/2026 al 20/10/2026)  
**Documento Fuente:** Complemento operativo para el Plan de Proyecto / Definición de Producto en Google Drive

---

## PARTE I: DEFINICIÓN DE PRODUCTO — S3 APERTURA

### 1.1. Propósito y Visión del Incremento de Producto en el Sprint 3

El **Sprint 3** tiene por meta consolidar el subsistema de **Descargos Reglamentarios, Plazos Preclusivos y Custodia de Evidencias**, completando la bilateralidad procesal exigida por el Estatuto Social de A.V.E.I.T. y el Reglamento Procesal 2026 (Artículos 12 y 16 bis). 

Habiendo alcanzado en el Sprint 2 la apertura de expedientes con numeración correlativa única (T01) y la máquina de estados procesales, el incremento del Sprint 3 permite a los socios involucrados ejercer su derecho de defensa en tiempo y forma, mientras que otorga a las autoridades institucionales (Comisión Directiva y Tribunal de Disciplina) herramientas precisas para la gestión de urgencias, la fiscalización de asistencias a eventos y la custodia probatoria con reserva legal.

---

### 1.2. Requerimientos Funcionales (RF) del Incremento (Sprint 3)

| Identificador | Nombre del Requerimiento Funcional | Módulo | Descripción Funcional | Trazabilidad Normativa |
| :--- | :--- | :--- | :--- | :--- |
| **RF-08** | Presentación de Justificación Tipificada (Formulario T02) | Descargos | Permitir al socio imputado presentar formalmente su justificación tipificada seleccionando causales reglamentarias predefinidas (laborales, académicas o de fuerza mayor), validando de forma autoritativa en el servidor que la presentación ocurra dentro del plazo perentorio de 5 días hábiles. | Art. 12 inc. b, Art. 16 bis Reg. Procesal 2026 |
| **RF-09** | Presentación de Descargo Extraordinario (Formulario T03) | Descargos | Habilitar la carga de descargo extraordinario con fundamentación libre y circunstanciada ante causales no tabuladas, con control de extensión textual (máx. 4000 caracteres) y auditoría de envío. | Art. 16 bis Reg. Procesal 2026 |
| **RF-10** | Custodia Digital de Evidencia Probatoria Protegida | Evidencias | Proveer un repositorio seguro para adjuntar documentos probatorios (PDF, JPG, PNG) con límite de 5 MB por archivo, validación estricta de encabezados MIME, anonimización criptográfica en disco y control RBAC por objeto (acceso exclusivo para los miembros del TD y el socio presentante, resguardando datos médicos sensibles). | Art. 16 bis Reg. Procesal 2026; Ley 25.326 |
| **RF-14** | Gestión del Calendario Institucional de Días Hábiles | Configuración | Proveer una interfaz administrativa para que las autoridades (CD, TD y Admin) gestionen la lista de feriados nacionales e institucionales inamovibles y trasladables del ciclo 2026, versionando las modificaciones de manera inmutable y recalculando simulaciones de vencimiento. | Art. 12 inc. b; Circular 001/2026 |
| **RF-16** | Clasificación e Indicador Visual de Urgencia en Causas | Expedientes | Incorporar a nivel de causa la graduación de urgencia (`Baja`, `Normal`, `Urgente`) con badges semánticos contrastantes y filtrado dinámico en el tablero Kanban y vistas tabulares, permitiendo priorizar expedientes con impacto institucional inminente. | Directivas PO (07/10/2026); Art. 12 Reg. Procesal |
| **RF-17** | Gestión de Eventos, Asistencias y Sanciones Trazables | Asistencias | Permitir a la Comisión Directiva programar reuniones institucionales y actividades de voluntariado con 2 días hábiles de antelación mínima, registrar la asistencia nominal con motivos circunstanciados mediante patrón Strategy (Manual/Biométrico) y transformar inasistencias injustificadas en expedientes o apercibimientos (acumulación 3:1). | Art. 95 Estatuto AVEIT; Directivas PO |
| **RF-18** | Detalle Oficial del Expediente según Formato Canónico del TD | Sala TD | Presentar a los miembros del Tribunal de Disciplina la vista integral del expediente conforme a la estructura forense histórica: Cabecera, Responsables 1, 2 y 3 identificados por Grupo social (Gxx), Reglamentos respaldantes y tabla de Imputados con estado de justificación. | Directivas PO (07/10/2026); Formato Imagen 2 TD |

---

### 1.3. Criterios de Aceptación Formales (Estándar EARS / Gherkin)

#### CA-RF08.1: Validación perentoria del plazo hábil (Buzzer-beater protection)
* **Escenario:** Socio presenta formulario T02 dentro del plazo establecido.
* **Dado que** el socio autenticado figura como involucrado en el expediente `EXP-XXX/2026`,
* **Y** el expediente se encuentra en estado `EN_PERIODO_DE_JUSTIFICACIONES`,
* **Y** la marca temporal del servidor `now` es estrictamente menor o igual a `plazo_limite_at` (18:00 hs del 5º día hábil),
* **Cuando** el socio envía el Formulario T02 completo con causal válida,
* **Entonces** el servidor persiste el descargo en estado formalmente presentado,
* **Y** devuelve un código HTTP `200 OK` con el número de acuse de recepción.

#### CA-RF08.2: Rechazo autoritativo ante plazo expirado (HTTP 409 Conflict)
* **Escenario:** Socio intenta enviar descargo con el plazo cumplido.
* **Dado que** la marca temporal del servidor supera `plazo_limite_at`,
* **Cuando** el socio intenta enviar cualquier payload de descargo,
* **Entonces** el servidor bloquea la mutación pesimista bajo `transaction.atomic()`,
* **Y** rechaza la solicitud respondiendo con código HTTP `409 Conflict`,
* **Y** el frontend deshabilita inmediatamente los campos y expone el chip "Plazo Expirado".

#### CA-RF10.1: Aislamiento y protección de documentos sensibles (Zero-Leakage)
* **Escenario:** Intento de acceso a comprobantes probatorios médicos por un tercero.
* **Dado que** el socio B no es parte interesada ni integra el Tribunal de Disciplina de la causa,
* **Cuando** el socio B intenta solicitar el endpoint de descarga o previsualización del archivo adjunto `GET /api/v1/expedientes/<id>/evidencias/<file_id>/`,
* **Entonces** el servidor deniega el acceso con código HTTP `403 Forbidden`,
* **Y** registra en el log de auditoría el intento de acceso no autorizado.

---

### 1.4. Casos de Uso del Sistema Impactados en el Sprint 3

1. **CU-05: Presentar Descargo Tipificado / Extraordinario (Formularios T02 y T03):**
   * *Actor Principal:* Socio Imputado.
   * *Precondición:* Expediente en estado `EN_PERIODO_DE_JUSTIFICACIONES` y plazo no vencido.
   * *Flujo Principal:* El socio ingresa a "Mis Expedientes y Descargos", visualiza la causa y el temporizador regresivo, selecciona si presenta T02 (con causales reglamentarias) o T03 (extraordinario libre), adjunta documentación probatoria opcional (PDF/PNG), y envía el formulario. El sistema valida la temporalidad, persiste el descargo y notifica a la mesa de entradas del TD.

2. **CU-06: Configurar Calendario Institucional y Feriados:**
   * *Actor Principal:* Autoridad Habilitada (CD, TD, Admin).
   * *Precondición:* Usuario autenticado con rol administrativo o directivo.
   * *Flujo Principal:* Consulta el calendario del año en curso (2026), ingresa una fecha inhábil excepcional con motivo fundado (ej. Jornada de Limpieza Institucional, asueto), el sistema valida que no sea duplicada ni anterior al día de la fecha, genera una nueva versión auditada de calendario y recalcula los plazos de las simulaciones activas.

3. **CU-13: Gestionar Reuniones, Actividades y Cierre de Asistencias:**
   * *Actor Principal:* Comisión Directiva (`ACT-03`).
   * *Precondición:* Usuario con rol directivo o de administración.
   * *Flujo Principal:* Convocatoria a reunión ordinaria/extraordinaria con al menos 2 días hábiles de anticipación. Registro de asistencias presentes/ausentes con motivo obligatorio por ausente. Cierre de nómina dentro de las 72 horas hábiles; el motor procesa inasistencias y consolida apercibimientos acumulados aplicando la regla 3:1 mediante transacciones inmutables.

4. **CU-14: Graduar Urgencia de Causa Disciplinaria:**
   * *Actor Principal:* Tribunal de Disciplina / Solicitante Calificado.
   * *Flujo Principal:* Durante la apertura o mediante actualización posterior en el tablero, la autoridad asigna la urgencia de la causa (`Baja`, `Normal`, `Urgente`). El sistema proyecta la distinción visual en las tarjetas Kanban (borde rojo semántico) y habilita el filtrado por prioridad.

---

## PARTE II: DEFINICIÓN DE PRODUCTO — S3 CIERRE

### 2.1. Incorporación Formal de las Directivas Rectoras del PO (Hito 07/10/2026)

Durante el transcurso del Sprint 3 se formalizaron las conclusiones de las reuniones de alineación estratégica entre el Product Owner (**Diego Gabriel Sánchez**), la Subcomisión de Cómputos y el Tribunal de Disciplina (`notasPO.md` del 07/10/2026). Estas directivas redefinieron requerimientos clave que quedan formalmente incorporados a la Definición de Producto:

1. **Simplificación del Juzgamiento y Votación en Sala TD:**
   - **Se descarta definitivamente la votación nominal compleja paso a paso** (voto por voto en pantalla).
   - Se establece en su lugar un **editor unificado de redacción de Resolución** con fijación directa del **Puntaje Final Neto Aplicado** individualizado por socio imputado.
2. **Estandarización Forense de Firmas Colegiadas:**
   - En el pie de firma de las resoluciones emitidas por el Tribunal de Disciplina es **obligatorio distinguir el Grupo Social (Gxx)** de cada integrante interviniente, así como su condición de Titular o Suplente:  
     `[N° Socio] - [Nombre y Apellido] - [Gxx] [(Sup.)]`
3. **Formato Institucional Canónico de Resolución (Ref. Imagen 3 TD):**
   - La emisión documental se ajusta al estándar jurídico canónico del Tribunal: Membrete oficial, fecha y hora de emisión, **VISTO** (normativa reglamentaria citada), **CONSIDERANDO** (valoración probatoria y sana crítica) y **SE RESUELVE** (artículos dispositivos con individualización exacta de sanciones o méritos).
4. **Readecuación Terminológica Institucional:**
   - Se reemplaza en todas las capas del sistema y en la documentación técnica la denominación "Comisión Fiscalizadora" por **"Revisores de Cuentas"** (o **"Revisores"** en interfaces compactas), asegurando estricta concordancia con el Estatuto AVEIT 2026.
5. **Inmutabilidad de la Regla de Acumulación 3:1:**
   - Se ratifica de manera estricta que los llamados de atención y las felicitaciones no aplican descuentos fraccionarios directos (ni ±0,33 ni ±0,5). Se gestionan en un libro mayor transaccional donde cada **tres (3) acumulados consolidan un (1) punto neto** (+1 o -1 respectivamente).

---

### 2.2. Estado del Catálogo de Requerimientos al Cierre del Sprint 3

| Requerimiento / Ítem | Estado de Implementación | Cobertura de Verificación |
| :--- | :---: | :--- |
| **RF-08 (Formulario T02 Tipificado y Resolución Causal)** | **100% Completado** | Validado con suite unitaria backend y componentes reactivos en frontend (`SCRUM-83` y `SCRUM-52` / PR #59 integrados a `main`). |
| **RF-09 (Formulario T03 Extraordinario y Versionado)** | **100% Completado** | PR #58 integrado a `main`. Límite de 5000 caracteres, versionado inmutable `DescargoVersion` y retiro lógico auditado. |
| **RF-10 (Custodia de Evidencias)** | **100% Completado** | PR #53 integrado a `main`. Validado aislamiento RBAC por objeto, validación de magic bytes y sanitización MIME. |
| **RF-14 (Calendario Institucional)** | **100% Completado** | PR #49 integrado a `main`. 16 feriados oficiales 2026 cargados, API REST y simulador interactivo verificados. |
| **RF-16 (Clasificador de Urgencia y Socios Múltiples)** | **100% Completado** | PR #50 y PR #57 integrados a `main`. Selector en T01, badges Kanban, filtros de tabla y modal de socios múltiples operativos. |
| **RF-17 (Eventos, Asistencias y Sanciones 3:1)** | **100% Completado** | PR #56 integrado a `main`. Ciclo de vida de eventos en 6 estados, patrón Strategy, consolidación 3:1 y 812 tests backend en verde. |
| **RF-18 (Sala TD: Detalle Canónico)** | **100% Completado** | PR #60 (`SCRUM-81`) integrado a `main`. Detalle canónico con Cabecera, Responsables 1, 2 y 3 con Grupo social, Reglamentos y tabla de imputados con estados de justificación. |
| **T01 Grupo + Anexo y Ranking Anidado** | **100% Completado** | PR #51 (`SCRUM-80`) y PR #52 (`SCRUM-82`) integrados a `main` con ordenamiento múltiple y modal de causas por socio. |
| **I+D Asistencia IA (Laya)** | **100% Completado** | PR #55 (`SCRUM-76`) integrado a `main`. Documento técnico de viabilidad de SLMs locales entregado a CD, TD y Cómputos. |
| **Padrón y Seed Data MySQL (G57 a G60)** | **100% Completado** | Poblamiento de base de datos (`SCRUM-77`) con cohortes reales y casos testigo para testing de integración. |

---

### 2.3. Matriz de Trazabilidad Bidireccional (Actualizada al Hito IOC)

```mermaid
flowchart LR
    subgraph Normativa ["Normativa AVEIT"]
        Estatuto["Estatuto 2026 (Art. 95)"]
        RegProc["Reglamento Procesal (Arts. 12 y 16 bis)"]
        NotasPO["Directivas PO (07/10/2026)"]
    end

    subgraph Requerimientos ["Definición de Producto"]
        RF08["RF-08: T02 Tipificado"]
        RF09["RF-09: T03 Extraordinario"]
        RF10["RF-10: Evidencias Seguras"]
        RF14["RF-14: Calendario Hábiles"]
        RF16["RF-16: Clasificador Urgencia"]
        RF17["RF-17: Asistencias y Sanciones"]
        RF18["RF-18: Sala TD y Resolución"]
    end

    subgraph CasosDeUso ["Casos de Uso del Sistema"]
        CU05["CU-05: Presentar Descargo"]
        CU06["CU-06: Configurar Calendario"]
        CU13["CU-13: Gestionar Reuniones"]
        CU14["CU-14: Graduar Urgencia"]
    end

    RegProc --> RF08
    RegProc --> RF09
    RegProc --> RF10
    RegProc --> RF14
    NotasPO --> RF16
    Estatuto --> RF17
    NotasPO --> RF18

    RF08 --> CU05
    RF09 --> CU05
    RF10 --> CU05
    RF14 --> CU06
    RF17 --> CU13
    RF16 --> CU14
```

---

### 2.4. Release Plan y Transición hacia el Sprint 4

Al concluir el Sprint 3 con el **100% del alcance completado e integrado en `main` (36/36 Story Points — 14 de 14 ítems en estado *Finalizado*)**, la plataforma SGD-AVEIT alcanza una madurez funcional sólida que habilita el inicio formal de la fase de **Sustanciación y Resolución Colegiada (Sprint 4: 22/10 al 03/11, 19 Story Points comprometidos)**:

* **Sprint 4 (`SCRUM-51`, `SCRUM-53`, `SCRUM-54`, `SCRUM-56` y `SCRUM-70`):**
  * **`SCRUM-51` (S4-01 - 5 SP):** Visor autorizado unificado para revisar cronológicamente T01, T02/T03 y evidencias probatorias con auditoría de consultas sensibles.
  * **`SCRUM-53` (S4-03 - 3 SP):** Valoración de descargos extraordinarios T03 mediante antecedentes emitidos y sana crítica.
  * **`SCRUM-54` (S4-04 - 3 SP):** Gestión de apartamiento por conflicto de interés y suplencia estatutaria (3 titulares y 3 suplentes por grupos Activos 4.º, 5.º y 6.º, sin recusación conforme Art. 93).
  * **`SCRUM-56` (S4-06 - 3 SP):** Editor unificado de resolución oficial con estructura reglamentaria (`VISTO / CONSIDERANDO / SE RESUELVE`) y fijación de puntaje final neto aplicado por socio sin votación nominal.
  * **`SCRUM-70` (PB-02 - 5 SP):** Tramitación de apelación y adecuación del Formulario T01 conforme al Art. 14 del Reglamento Procesal 2026.

---
*Documento aprobado y formalizado para la Cátedra de Seminario Integrador — Ciclo Lectivo 2026.*
