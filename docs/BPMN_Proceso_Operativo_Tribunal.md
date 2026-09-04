# MODELADO OPERATIVO DE PROCESOS DE NEGOCIO (BPMN 2.0)
## Módulo Unificado de Tribunal de Disciplina y Premiaciones (SGD-AVEIT)

---

### DATOS DEL DOCUMENTO Y CONTROL DE VERSIONES

| Atributo | Especificación |
| :--- | :--- |
| **Organización** | Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos (A.V.E.I.T.) - UTN FRC |
| **Sistema** | SGD-AVEIT |
| **Proceso Modelado** | Proceso Integral de Gestión Disciplinaria, Descargos, Cómputo de Puntos y Balances |
| **Estándar** | OMG BPMN 2.0 / Ficha Institucional ASI - UTN FRC / Modelo Canónico BPMN-IR |
| **Fecha de Emisión** | 03/09/2026 |
| **Versión** | 1.0.0 (Primera Iteración) |

---

## 1. FICHA DE PROCESO DE NEGOCIO INSTITUCIONAL

# FICHA DE PROCESO: Gestión Integral del Régimen Disciplinario y Premiaciones

### 1.1. Identificación y Alcance
| Atributo | Especificación |
| :--- | :--- |
| **Nombre del Proceso** | Gestión Integral del Régimen Disciplinario, Justificaciones y Premiaciones |
| **Dueño del Proceso (Owner)** | Presidente del Tribunal de Disciplina |
| **Tipo de Proceso** | Proceso de Soporte, Gobierno y Control Institucional (Core Disciplinario) |
| **Objetivo** | Tramitar el ciclo completo de causas disciplinarias y de reconocimiento al mérito en sus 6 estados oficiales, administrando los plazos preclusivos de 5 días hábiles, recepcionando justificaciones unificadas (con certificados o descargos extraordinarios), posibilitando la votación y firma colegiada de los jueces, computando de forma inmutable los saldos de puntos (+/-), disparando alertas preventivas (7 pts) y críticas de cese (10 pts), y generando los balances de auditoría interna. |
| **Disparador (Trigger)** | Cierre administrativo de un evento institucional obligatorio con inasistencias detectadas o recepción de Formulario T01 formal con Hoja de Anexo por autoridad habilitada. |
| **Límite Inicial** | Detección de falta/mérito o registro formal de solicitud de puntos. |
| **Límite Final** | Publicación de la resolución firmada, impacto inalterable en el saldo de puntos y emisión de balances cuatrimestrales de auditoría. |
| **Cliente(s) del Proceso** | Masa Societaria de AVEIT (Socios Juniors y Seniors), Comisión Directiva, Asamblea General. |
| **Productos / Salidas** | 1. Expediente disciplinario tramitado y resuelto formalmente.<br>2. Resolución Oficial con estructura reglamentaria y firma digital de 3 jueces.<br>3. Saldo de puntos del socio actualizado de forma auditada e inmutable.<br>4. Alertas escalonadas (Amarilla a los 7 pts y Roja a los 10 pts) despachadas.<br>5. Balances Cuatrimestrales de Auditoría Interna consolidados en PDF/Excel. |

---

### 1.2. Matriz de Proveedores e Insumos (SIPOC)
| Proveedor / Entidad | Insumo / Información Suministrada | Propósito en el Proceso |
| :--- | :--- | :--- |
| `Módulo de Eventos & Asistencia` | Acta de cierre con inasistencias registradas ("pasar el dedo"). | Disparar causas automáticas por faltas a eventos obligatorios. |
| `Autoridades Habilitadas (CD/Subcomisiones/Equipos)` | Formulario T01 + Hoja Anexo circunstanciada. | Iniciar formalmente causas de sanción o reconocimiento al mérito. |
| `Socio Imputado / Postulado` | Formulario Unificado de Justificación con certificado o descargo libre. | Ejercer el derecho reglamentario a defensa dentro del plazo preclusivo. |
| `Tribunal de Disciplina` | Votos nominales fundados, considerandos y firmas colegiadas. | Deliberar y emitir sentencia obligatoria e irrecurrible. |
| `Servicio de Reloj del Sistema` | Temporizador de cinco (5) días hábiles (excluye fines de semana y feriados). | Controlar la preclusión temporal objetiva del período de descargo. |

---

### 1.3. Recursos del Proceso
* **Recursos Humanos (Roles y Carriles)**:
  - `Socio`: Consulta causas personales y carga descargos en el formulario unificado.
  - `Autoridad Solicitante`: Carga solicitudes T01, administra eventos y realiza check-in digital.
  - `Jueces del Tribunal de Disciplina (3)`: Revisan pruebas, deliberan, votan y firman colegiadamente.
* **Recursos Tecnológicos**:
  - Plataforma Web Responsive Mobile SGD-AVEIT (Frontend React/Tailwind).
  - Backend en Python con endpoints REST y control transaccional.
  - Motor de Base de Datos MySQL (tablas: expedientes, justificaciones, ledger de puntos, eventos).
  - Servidor de correo SMTP institucional para acuses y cédulas.

---

### 1.4. Formularios y Documentos Estructurados
* **Formulario T01 con Hoja Anexo:** Solicitud de puntos (+/-) con fundamentación fáctica, fechas y testigos.
* **Formulario Unificado de Justificaciones (T02/T03):** Interfaz unificada que conmuta entre *Justificación con Certificado* (motivos de salud, examen o laborales con comprobante obligatorio) y *Descargo Extraordinario* (exposición libre).
* **Cédula de Votación Nominal:** Registro individual de votos de los tres jueces intervinientes.
* **Resolución Oficial:** Documento formal estructurado en VISTOS, CONSIDERANDOS y RESOLUCIÓN con firmas digitales.
* **Balance Cuatrimestral de Disciplina:** Informe oficial consolidado con estadísticas y rankings.

---

### 1.5. Reglas de Negocio Clave (RN)
* **RN-01:** Plazo preclusivo de 5 días hábiles a partir de la notificación de apertura de causa.
* **RN-02:** Bloqueo automático irreversible del botón de justificación al expirar el temporizador.
* **RN-05:** Carga obligatoria de al menos un comprobante digital al seleccionar causal tipificada en el formulario unificado.
* **RN-08:** Inhibición automática del juez del TD que tenga conflicto de interés y convocatoria del juez suplente.
* **RN-09:** Aprobación de resoluciones por mayoría calificada (mínimo 2 de 3 votos).
* **RN-11:** Firma colegiada tripartita requerida para la validez y publicación del fallo.
* **RN-12:** Prohibición absoluta de alterar saldos mediante sentencias directas (`UPDATE`); solo movimientos por ledger inmutable.
* **RN-13 y RN-14:** Disparo automático de Alerta Preventiva a los -7 puntos y Alerta Crítica Roja de Cese a los -10 puntos.

---

### 1.6. Indicadores de Desempeño (KPIs)
| ID | Indicador | Fórmula | Frecuencia | Meta |
| :---: | :--- | :--- | :---: | :---: |
| **KPI-01** | Tasa de Descargos en Término | `(Justificaciones Presentadas <= 5 días / Total Causas) * 100` | Mensual | `≥ 85%` |
| **KPI-02** | Tiempo Medio de Dictamen | `Promedio(Fecha_Firma_Resolucion - Fecha_Cierre_Descargos)` | Mensual | `≤ 5 días` |
| **KPI-03** | Integridad de Saldos | `(Movimientos de Puntos con Resolución Asociada / Total Movimientos) * 100` | Continuo | `100%` |
| **KPI-04** | Detección Oportuna de Cese | `(Alertas Rojas Emitidas / Total Socios con Saldo <= -10 pts) * 100` | Continuo | `100%` |

---

## 2. REPRESENTACIÓN CANÓNICA INTERMEDIA: BPMN-IR (JSON)

```json
{
  "process": [
    {
      "type": "startEvent",
      "id": "start_disciplinario",
      "label": "Hecho pasible de sanción o mérito detectado",
      "lane": "Lane_Autoridad"
    },
    {
      "type": "exclusiveGateway",
      "id": "gw_origen_causa",
      "label": "¿Origen de la actuación disciplinaria?",
      "has_join": true,
      "lane": "Lane_Autoridad",
      "branches": [
        {
          "condition": "Cierre de Evento Obligatorio (Inasistencia)",
          "path": [
            {
              "type": "userTask",
              "id": "task_cerrar_evento",
              "label": "Confirmar cierre formal de evento institucional",
              "lane": "Lane_Autoridad"
            },
            {
              "type": "serviceTask",
              "id": "task_detectar_ausentes",
              "label": "Detectar socios sin check-in y crear causas automáticas",
              "lane": "Lane_Sistema"
            }
          ]
        },
        {
          "condition": "Solicitud Manual de Puntos (Formulario T01)",
          "path": [
            {
              "type": "userTask",
              "id": "task_cargar_t01",
              "label": "Completar Formulario T01 con Hoja de Anexo",
              "lane": "Lane_Autoridad"
            },
            {
              "type": "businessRuleTask",
              "id": "task_validar_facultades",
              "label": "Verificar facultades estatutarias de la autoridad",
              "lane": "Lane_Sistema"
            }
          ]
        }
      ]
    },
    {
      "type": "serviceTask",
      "id": "task_crear_expediente",
      "label": "Crear expediente formal y notificar acuse al socio",
      "lane": "Lane_Sistema"
    },
    {
      "type": "serviceTask",
      "id": "task_iniciar_timer_5dias",
      "label": "Iniciar temporizador preclusivo de 5 días hábiles",
      "lane": "Lane_Sistema"
    },
    {
      "type": "exclusiveGateway",
      "id": "gw_resolucion_descargo",
      "label": "¿Respuesta del socio dentro del plazo?",
      "has_join": true,
      "lane": "Lane_Socio",
      "branches": [
        {
          "condition": "Presenta Justificación con Certificado",
          "path": [
            {
              "type": "userTask",
              "id": "task_justificar_certificado",
              "label": "Completar causal y adjuntar comprobante médico o de examen",
              "lane": "Lane_Socio"
            },
            {
              "type": "serviceTask",
              "id": "task_guardar_justificacion",
              "label": "Almacenar comprobantes con sello de tiempo UTC",
              "lane": "Lane_Sistema"
            }
          ]
        },
        {
          "condition": "Presenta Descargo Extraordinario",
          "path": [
            {
              "type": "userTask",
              "id": "task_descargo_libre",
              "label": "Exponer hechos extraordinarios en formulario",
              "lane": "Lane_Socio"
            },
            {
              "type": "serviceTask",
              "id": "task_guardar_descargo",
              "label": "Almacenar descargo extraordinario en base de datos",
              "lane": "Lane_Sistema"
            }
          ]
        },
        {
          "condition": "Vencimiento del Plazo (Sin Respuesta)",
          "path": [
            {
              "type": "intermediateCatchEvent",
              "id": "timer_5dias_vencido",
              "label": "Expiración de las 120 horas hábiles",
              "eventDefinition": "timerEventDefinition",
              "lane": "Lane_Sistema"
            },
            {
              "type": "serviceTask",
              "id": "task_preclusion_plazo",
              "label": "Bloquear formulario y registrar preclusión procesal",
              "lane": "Lane_Sistema"
            }
          ]
        }
      ]
    },
    {
      "type": "serviceTask",
      "id": "task_estado_en_revision",
      "label": "Actualizar expediente a 'Justificaciones en revisión'",
      "lane": "Lane_Sistema"
    },
    {
      "type": "userTask",
      "id": "task_examinar_pruebas",
      "label": "Examinar pruebas y antecedentes jurisprudenciales",
      "lane": "Lane_Tribunal"
    },
    {
      "type": "userTask",
      "id": "task_votar_nominal",
      "label": "Registrar votación nominal fundada de los 3 jueces",
      "lane": "Lane_Tribunal"
    },
    {
      "type": "businessRuleTask",
      "id": "task_verificar_mayoria",
      "label": "Verificar mayoría absoluta reglamentaria (>= 2/3)",
      "lane": "Lane_Sistema"
    },
    {
      "type": "userTask",
      "id": "task_redactar_resolucion",
      "label": "Redactar Vistos, Considerandos y Resolución final",
      "lane": "Lane_Tribunal"
    },
    {
      "type": "parallelGateway",
      "id": "gw_fork_firmas",
      "label": "Recolección simultánea de firmas colegiadas",
      "lane": "Lane_Sistema",
      "branches": [
        [
          {
            "type": "userTask",
            "id": "task_firma_juez1",
            "label": "Firmar digitalmente resolución (Juez 1)",
            "lane": "Lane_Tribunal"
          }
        ],
        [
          {
            "type": "userTask",
            "id": "task_firma_juez2",
            "label": "Firmar digitalmente resolución (Juez 2)",
            "lane": "Lane_Tribunal"
          }
        ],
        [
          {
            "type": "userTask",
            "id": "task_firma_juez3",
            "label": "Firmar digitalmente resolución (Juez 3)",
            "lane": "Lane_Tribunal"
          }
        ]
      ]
    },
    {
      "type": "serviceTask",
      "id": "task_impactar_puntos",
      "label": "Impactar movimiento transaccional en ledger inmutable",
      "lane": "Lane_Sistema"
    },
    {
      "type": "serviceTask",
      "id": "task_publicar_resolucion",
      "label": "Publicar resolución y notificar a partes y CD",
      "lane": "Lane_Sistema"
    },
    {
      "type": "businessRuleTask",
      "id": "task_evaluar_umbrales",
      "label": "Evaluar saldo neto contra umbrales (7 y 10 puntos)",
      "lane": "Lane_Sistema"
    },
    {
      "type": "exclusiveGateway",
      "id": "gw_alertas_disciplinarias",
      "label": "¿Saldo acumulado alcanza límites reglamentarios?",
      "has_join": false,
      "lane": "Lane_Sistema",
      "branches": [
        {
          "condition": "Saldo >= 10 Puntos Negativos (Límite Crítico)",
          "path": [
            {
              "type": "sendTask",
              "id": "task_alerta_roja",
              "label": "Emitir Alerta Roja Crítica de Pérdida de Condición de Socio",
              "lane": "Lane_Sistema"
            },
            {
              "type": "endEvent",
              "id": "end_cese_estatutario",
              "label": "Fin: Trámite de cese estatutario disparado",
              "lane": "Lane_Sistema"
            }
          ]
        },
        {
          "condition": "Saldo >= 7 Puntos Negativos (Alerta Preventiva)",
          "path": [
            {
              "type": "sendTask",
              "id": "task_alerta_amarilla",
              "label": "Emitir Alerta Preventiva Amarilla al socio y CD",
              "lane": "Lane_Sistema"
            },
            {
              "type": "endEvent",
              "id": "end_alerta_preventiva",
              "label": "Fin: Advertencia preventiva registrada",
              "lane": "Lane_Sistema"
            }
          ]
        },
        {
          "condition": "Saldo < 7 Puntos (Régimen Ordinario)",
          "path": [
            {
              "type": "endEvent",
              "id": "end_regular",
              "label": "Fin: Expediente concluido y saldo actualizado",
              "lane": "Lane_Sistema"
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 3. DIAGRAMA OPERATIVO EN MERMAID.JS

```mermaid
flowchart TB
    %% ==============================================================
    %% POOL: SISTEMA DE GESTIÓN DISCIPLINARIA (SGD-AVEIT)
    %% ==============================================================
    subgraph Pool_SGD ["Pool: SGD-AVEIT - Gestión Integral del Tribunal de Disciplina"]

        %% CARRIL 1: AUTORIDADES SOLICITANTES
        subgraph Lane_Autoridad ["Lane: Autoridades Solicitantes (CD / Subcomisiones / Líderes)"]
            Start_Discip((("○ Inicio: Falta o Mérito Detectado")))
            Gw_Origen{"¿Origen de Causa?"}
            Task_CierreEvento["Confirmar Cierre de Evento Obligatorio"]
            Task_CargaT01["Completar Formulario T01 con Hoja de Anexo"]
        end

        %% CARRIL 2: SOCIO
        subgraph Lane_Socio ["Lane: Socio Imputado / Postulado"]
            Gw_DescargoChoice{"¿Modalidad de Descargo?"}
            Task_JustifCert["Cargar Justificación con Certificado Digital"]
            Task_DescargoLibre["Completar Descargo Extraordinario"]
        end

        %% CARRIL 3: TRIBUNAL DE DISCIPLINA
        subgraph Lane_Tribunal ["Lane: Miembros del Tribunal de Disciplina"]
            Task_ExamPruebas["Examinar Pruebas, Descargos y Antecedentes"]
            Task_VotoNominal["Registrar Votación Nominal Fundada (3 Jueces)"]
            Task_RedactarRes["Redactar Vistos, Considerandos y Resolución"]
            Task_FirmaJ1["Firmar Digitalmente (Juez 1)"]
            Task_FirmaJ2["Firmar Digitalmente (Juez 2)"]
            Task_FirmaJ3["Firmar Digitalmente (Juez 3)"]
        end

        %% CARRIL 4: SERVICIOS Y AUTOMATIZACIONES BACKEND
        subgraph Lane_Sistema ["Lane: Sistema SGD-AVEIT (Servicios Backend y Daemons)"]
            Task_DetectAusentes["Detectar Ausentes y Crear Causas"]
            Task_ValFacultades["Validar Facultades de la Autoridad"]
            Gw_JoinOrigen{"(+) Convergencia Origen"}
            Task_CrearExp["Crear Expediente y Enviar Notificación"]
            Task_StartTimer["Iniciar Temporizador de 5 Días Hábiles"]
            Task_SaveJustif["Registrar Justificación con Sello Temporal"]
            Task_SaveDescargo["Registrar Descargo con Sello Temporal"]
            Timer_5d((("◎ Espera: Timer 5 Días Hábiles")))
            Task_Preclusion["Bloquear Formulario por Vencimiento de Plazo"]
            Gw_JoinDescargo{"(+) Convergencia Descargos"}
            Task_SetReview["Actualizar Estado a 'Justificaciones en Revisión'"]
            Task_ValMayoria["Verificar Mayoría Calificada (>= 2/3)"]
            Gw_ForkFirmas{"(+) Fork Firmas Colegiadas"}
            Gw_JoinFirmas{"(+) Join Firmas Completas"}
            Task_Ledger["Impactar Movimiento en Ledger Inmutable"]
            Task_Publicar["Publicar Fallo y Notificar a Partes"]
            Task_EvalUmbral["Evaluar Saldo contra Umbrales de Puntos"]
            Gw_Threshold{"¿Umbral Crítico?"}
            Task_AlertRed["Emitir Alerta Roja Crítica de Cese Estatutario"]
            End_Red((("● Fin: Cese Disparado (10 pts)")))
            Task_AlertYellow["Emitir Alerta Preventiva Amarilla al Socio"]
            End_Yellow((("● Fin: Advertencia (7 pts)")))
            End_Ok((("● Fin: Causa Resuelta")))
        end

    end

    %% ==============================================================
    %% SECUENCIA DE CONTROL
    %% ==============================================================
    Start_Discip --> Gw_Origen
    Gw_Origen -- "Inasistencia a Evento" --> Task_CierreEvento --> Task_DetectAusentes --> Gw_JoinOrigen
    Gw_Origen -- "Solicitud Manual T01" --> Task_CargaT01 --> Task_ValFacultades --> Gw_JoinOrigen

    Gw_JoinOrigen --> Task_CrearExp --> Task_StartTimer --> Gw_DescargoChoice

    Gw_DescargoChoice -- "Causal con Certificado" --> Task_JustifCert --> Task_SaveJustif --> Gw_JoinDescargo
    Gw_DescargoChoice -- "Descargo Extraordinario" --> Task_DescargoLibre --> Task_SaveDescargo --> Gw_JoinDescargo
    Gw_DescargoChoice -- "Sin Respuesta en Término" --> Timer_5d --> Task_Preclusion --> Gw_JoinDescargo

    Gw_JoinDescargo --> Task_SetReview --> Task_ExamPruebas --> Task_VotoNominal --> Task_ValMayoria
    Task_ValMayoria --> Task_RedactarRes --> Gw_ForkFirmas

    Gw_ForkFirmas --> Task_FirmaJ1 --> Gw_JoinFirmas
    Gw_ForkFirmas --> Task_FirmaJ2 --> Gw_JoinFirmas
    Gw_ForkFirmas --> Task_FirmaJ3 --> Gw_JoinFirmas

    Gw_JoinFirmas --> Task_Ledger --> Task_Publicar --> Task_EvalUmbral --> Gw_Threshold

    Gw_Threshold -- "Saldo <= -10 pts" --> Task_AlertRed --> End_Red
    Gw_Threshold -- "Saldo <= -7 pts" --> Task_AlertYellow --> End_Yellow
    Gw_Threshold -- "Saldo > -7 pts" --> End_Ok

    %% ==============================================================
    %% ESTILOS VISUALES
    %% ==============================================================
    classDef startEvent fill:#15803D,stroke:#14532D,color:#fff,stroke-width:2px;
    classDef endEvent fill:#B91C1C,stroke:#7F1D1D,color:#fff,stroke-width:2px;
    classDef timerEvent fill:#D97706,stroke:#B45309,color:#fff,stroke-width:2px;
    classDef gateway fill:#FEF3C7,stroke:#D97706,color:#000,stroke-width:2px;
    classDef userTask fill:#DBEAFE,stroke:#1E40AF,color:#0F172A,stroke-width:1px;
    classDef serviceTask fill:#F1F5F9,stroke:#64748B,color:#0F172A,stroke-width:1px;

    class Start_Discip startEvent;
    End_Red,End_Yellow,End_Ok class:endEvent;
    Timer_5d class:timerEvent;
    Gw_Origen,Gw_JoinOrigen,Gw_DescargoChoice,Gw_JoinDescargo,Gw_ForkFirmas,Gw_JoinFirmas,Gw_Threshold class:gateway;
    Task_CierreEvento,Task_CargaT01,Task_JustifCert,Task_DescargoLibre,Task_ExamPruebas,Task_VotoNominal,Task_RedactarRes,Task_FirmaJ1,Task_FirmaJ2,Task_FirmaJ3 class:userTask;
    Task_DetectAusentes,Task_ValFacultades,Task_CrearExp,Task_StartTimer,Task_SaveJustif,Task_SaveDescargo,Task_Preclusion,Task_SetReview,Task_ValMayoria,Task_Ledger,Task_Publicar,Task_EvalUmbral,Task_AlertRed,Task_AlertYellow class:serviceTask;
```

---

## 4. AUDITORÍA DE CALIDAD Y MATRIZ DE PREVENCIÓN DE ANTI-PATRONES (AP-01 A AP-12)

| Anti-Patrón | Descripción y Criterio OMG | Estado en Especificación | Cumplimiento Técnico |
| :---: | :--- | :---: | :--- |
| **AP-01** | *Sequence Flow entre Pools* | **CORRECTO (Ausente)** | Todos los flujos de secuencia se mantienen confinados dentro de la Pool `SGD-AVEIT`. |
| **AP-02** | *Message Flow intra-Pool* | **CORRECTO (Ausente)** | No se usan flujos de mensaje entre los carriles internos (`Lane_Socio`, `Lane_Tribunal`, etc.). |
| **AP-03** | *Compuertas Asimétricas* | **CORRECTO (Ausente)** | Las bifurcaciones `gw_origen_causa`, `gw_resolucion_descargo` y `gw_fork_firmas` cuentan con convergencias balanceadas. |
| **AP-04** | *Nombres Ambiguos en Tareas* | **CORRECTO (Ausente)** | El 100% de las tareas está etiquetado con la fórmula imperativa `[Verbo en Infinitivo] + [Objeto Directo]`. |
| **AP-05** | *Condiciones Ocultas en XOR* | **CORRECTO (Ausente)** | Todas las ramas salientes de compuertas exclusivas poseen etiquetas booleanas claras y excluyentes. |
| **AP-06** | *Sumideros Muertos (Deadlocks)* | **CORRECTO (Ausente)** | Cada ruta de ejecución culmina inequívocamente en un evento de fin tipado (`End_Red`, `End_Yellow`, `End_Ok`). |
| **AP-07** | *Confusión Rol vs Organización* | **CORRECTO (Ausente)** | La Asociación se modela en una única Pool y los roles institucionales se delimitan en carriles (Lanes). |
| **AP-08** | *Ramas Paralelas Vacías* | **CORRECTO (Ausente)** | Cada rama del fork de firmas paralelas (`gw_fork_firmas`) contiene una tarea de firma unívoca (`task_firma_juezX`). |
| **AP-09** | *Redirecciones Colgantes* | **CORRECTO (Ausente)** | El modelo JSON BPMN-IR no contiene punteros `next` hacia identificadores inexistentes. |
| **AP-10** | *Ambigüedad de Automatización* | **CORRECTO (Ausente)** | Se diferencian estrictamente las tareas humanas (`userTask`) de las tareas automáticas del servidor (`serviceTask` y `businessRuleTask`). |
| **AP-11** | *Compuertas Inclusivas sin Default* | **CORRECTO (Ausente)** | Solo se emplean bifurcaciones exclusivas disjuntas y forks paralelos incondicionales. |
| **AP-12** | *Omisión de End Event en Excepción* | **CORRECTO (Ausente)** | Las rutas de cese estatutario (-10 pts) y advertencia preventiva (-7 pts) finalizan formalmente en eventos de fin dedicados. |

---
*Especificación elaborada para la Cátedra de Seminario Integrador - UTN FRC - Ciclo Lectivo 2026.*
