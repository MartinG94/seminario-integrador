# Inventario de Auditoría — `docs-implementacion-ia`

> **Fecha de relevamiento:** 2026-11-28  
> **Modo:** Solo lectura sobre repositorio.  
> **Fuente de verdad contrastada:** `auditoria/registro-canonico.md`, código del repositorio y `docker-compose.yml`.  
> **Archivos auditados:** 6 (total exacto del grupo `docs-implementacion-ia`).  
> **Contexto común:** Los 6 documentos fueron incorporados el `2026-10-14` como entregables de investigación I+D de la tarea `SCRUM-76` (Sprint 3, PR #55). Ninguna funcionalidad de IA descrita en ellos está implementada en `backend/`, `frontend/` ni `docker-compose.yml`, y ninguno corresponde a los 4 entregables obligatorios de la cátedra ni al Manual de Usuario detallados en `auditoria/registro-canonico.md` (§4).

---

## 1. `docs/Implementacion IA/01_escenarios_y_casos_de_uso.md`

- **Ruta:** `docs/Implementacion IA/01_escenarios_y_casos_de_uso.md`
- **Líneas:** 239
- **Última modificación:** `2026-10-14`
- **Tema que cubre:** Propuesta técnica de 4 casos de uso del motor System 1 (Laya), arquitectura de integración mediante contenedor sidecar y lineamientos de gobernanza ética de IA en SGD-AVEIT (`SCRUM-76`).
- **Quién lo lee:** equipo (referencia de I+D para PO y desarrollo).
- **Qué pasa si desaparece:** alguien pregunta (está referenciado en `TASK.md`, `docs/gestion-proyecto/Seguimiento de Proyecto.md` y `docs/Implementacion IA/presentacion/01_propuesta_subcomision_computos.md` como entregable de `SCRUM-76`).
- **Clasificación:** **4. Vigente** (como documento de propuesta/investigación I+D `SCRUM-76`, no como documentación de funcionalidad implementada).
- **Contradicciones con el registro:**
  - *Rol Revisores de Cuentas (línea 239):* menciona *"Revisores de Cuentas"*. El Registro Canónico (§3) indica que en el código el rol RBAC vigente sigue siendo `FISCALIZADORA` (*"Autoridad de Subcomisión / Líder de Equipo"*).
  - *Tablero Kanban (líneas 43, 60, 137):* denomina *"Tablero Kanban"* a la vista del Tribunal; el Registro Canónico (§2 y §3) la identifica como *"tablero de gestión"* en `/gestionar-expedientes`.
  - *Nombre de base de datos y red Docker (líneas 143, 176):* el diagrama nombra la BD MySQL como `sgd_aveit` y el `docker-compose.yml` propuesto usa la red `sgd_network`; en el `docker-compose.yml` real del repositorio la BD por defecto es `aveit_tribunal_dev` y no existe la red `sgd_network`.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - Toda la funcionalidad de IA descrita (`laya-service`, sugerencia de urgencia `score`, sugerencia de artículos `choice`, validación de consistencia en descargos T02/T03 `noul`, detección temprana de flagrancia `noul` y auditoría en `ai_inference_logs`) **no está implementada** en el repositorio ni figura como implementada en el Registro Canónico (§2).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - En los Casos de Uso 1 y 2 no refleja que el sistema ya tiene implementados el clasificador manual de urgencia (`Expediente` / `test_urgencia.py`), el ABM de Reglamentos (`ArticuloReglamento`) y la valoración extraordinaria T03 con vinculación de precedentes (`ValoracionT03`, `SCRUM-53`), verificados como `implementada` en el Registro Canónico (§2).
- **Referencias rotas:**
  - Enlaces Markdown relativos mal resueltos desde `docs/Implementacion IA/` (apuntan a `docs/Implementacion IA/docs/...`, rutas inexistentes, aunque los destinos existen desde la raíz):
    - Líneas 4, 39 y 234: `(docs/gestion-proyecto/notasPO.md)`. Además, la línea 4 cita *"Sección 2, Líneas 144–148"*, cuando la tarea I+D de Laya en `notasPO.md` se encuentra en las líneas **150–153**.
    - Línea 234: `(docs/constitution.md)`.
  - Archivos, servicios y tablas inexistentes en el repositorio: `services/ai_sidecar.py` (línea 142), `./ai-service`, `./ai-service/Dockerfile`, `./ai-service/models` (líneas 165–166, 174), servicio `laya-service` y red `sgd_network` en `docker-compose.yml` (líneas 163, 176), y tabla `ai_inference_logs` (línea 239).

---

## 2. `docs/Implementacion IA/02_entrenamiento_datos_y_hardware.md`

- **Ruta:** `docs/Implementacion IA/02_entrenamiento_datos_y_hardware.md`
- **Líneas:** 202
- **Última modificación:** `2026-10-14`
- **Tema que cubre:** Esquema JSONL de dataset, metodología de curaduría/destilación, hiperparámetros de fine-tuning, requerimientos de hardware y comandos CLI de entrenamiento/exportación ONNX para Laya (`SCRUM-76`).
- **Quién lo lee:** equipo (referencia metodológica de I+D).
- **Qué pasa si desaparece:** alguien pregunta (referenciado en `TASK.md` y `docs/Implementacion IA/presentacion/01_propuesta_subcomision_computos.md` como entregable de `SCRUM-76`).
- **Clasificación:** **4. Vigente** (como guía metodológica de I+D `SCRUM-76`, sin implementación asociada en el repositorio).
- **Contradicciones con el registro:**
  - *Identificador de socio (línea 92):* utiliza *"números de legajo/DNI"*. El Registro Canónico (§3) establece que el identificador canónico en el código es `numero_socio` (`legajo` corresponde únicamente al padrón legado `socio_lista`).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - Todo el pipeline de entrenamiento, evaluación y despliegue de `laya-service` (líneas 152, 166–202) **no está implementado** en el repositorio ni forma parte de las funcionalidades verificadas en el Registro Canónico (§2).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - No aplica al alcance del documento (trata exclusivamente sobre curaduría, entrenamiento y hardware de un motor de inferencia externo).
- **Referencias rotas:**
  - Línea 4: enlace Markdown relativo `(docs/gestion-proyecto/notasPO.md)` mal resuelto desde `docs/Implementacion IA/`; además cita *"Sección 2, Líneas 144–148"*, cuando la tarea I+D de Laya está en las líneas **150–153**.
  - Línea 120: enlace relativo `[\`laya-evals\`](../laya/docs/evals.md)` -> apunta a `docs/laya/docs/evals.md`, **inexistente** en el repositorio (tampoco existe directorio `laya/` en la raíz).
  - Líneas 169–200: módulos CLI y rutas locales inexistentes en el repositorio (`laya.train_cli`, `laya.evals_cli`, `laya.export_onnx`, `./data/dataset_aveit_train.jsonl`, `./data/dataset_aveit_val.jsonl`, `./data/dataset_aveit_test.jsonl`, `./checkpoints/laya-aveit-v1`, `./dist/laya-aveit-onnx-int8`).

---

## 3. `docs/Implementacion IA/03_evaluacion_slm_rag_cag_mag.md`

- **Ruta:** `docs/Implementacion IA/03_evaluacion_slm_rag_cag_mag.md`
- **Líneas:** 161
- **Última modificación:** `2026-10-14`
- **Tema que cubre:** Evaluación comparativa de SLMs (<4B parámetros) frente a Laya (System 1), análisis de paradigmas RAG/CAG/MAG y hoja de ruta de adopción en SGD-AVEIT (`SCRUM-76`).
- **Quién lo lee:** equipo (referencia de I+D).
- **Qué pasa si desaparece:** alguien pregunta (referenciado en `TASK.md` como entregable de `SCRUM-76`).
- **Clasificación:** **4. Vigente** (como estudio de viabilidad I+D `SCRUM-76`, aunque desactualizado en el estado de sprints y contradictorio con la eliminación de la votación del TD).
- **Contradicciones con el registro:**
  - *Votación del Tribunal de Disciplina (líneas 54 y 65):* el diagrama indica `"Entrada del Caso (Hechos + Votación TD)"` y el texto afirma *"Una vez que el Tribunal votó y fijó el puntaje en la Sala"*. El Registro Canónico (§2 y §3; observaciones docentes #23, #24 y #31) establece que la votación nominal fue **eliminada por directiva del PO el 07/10/2026** y reemplazada por el editor unificado de resolución y firma colegiada (`Resolucion.firmantes`).
  - *Fase y sprint actual (líneas 155 y 159):* declara *"Para el MVP y Corto Plazo (Sprint 3 / Actual)"* y *"Fase 1 (MVP — Actual): Despliegue del contenedor sidecar `laya-service`"*. Según el Registro Canónico (§5.3–5.4), el Sprint 3 cerró el 22/10/2026, el Sprint 4 cerró el 03–04/11/2026 y el proyecto se encuentra en Sprint 5 Consolidado, sin haberse desplegado `laya-service`.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - Presenta el despliegue de `laya-service` como *"Fase 1 (MVP — Actual)"* (línea 159), cuando ninguna funcionalidad de IA (Laya, SLMs, RAG, CAG o MAG) está implementada en el repositorio.
  - En §5.3 Vertiente A (líneas 121–125) alude a consulta de precedentes históricos del Tribunal; según el Registro Canónico (§2), el *Repositorio de precedentes y jurisprudencia disciplinaria* (`SCRUM-68` / `SCRUM-125` / `US-19`) está en estado **parcial** (limitado a `AntecedenteT03View` dentro de valoraciones T03).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - En §4.1 (líneas 60–65) describe el flujo de generación de resoluciones sin reflejar el *Editor unificado de Resolución, preview PDF, firma colegiada (4.º/5.º/6.º) y emisión oficial* (`SCRUM-56`, `SCRUM-58`, `SCRUM-89`) ni el *ABM de Reglamentos* (`ArticuloReglamento`) ya implementados en el código (Registro Canónico §2).
- **Referencias rotas:**
  - Enlaces Markdown relativos mal resueltos desde `docs/Implementacion IA/` (apuntan a `docs/Implementacion IA/docs/...`, rutas inexistentes, aunque existen desde la raíz):
    - Líneas 4, 61 y 155: `(docs/gestion-proyecto/notasPO.md)`.
    - Línea 4: `(docs/constitution.md)`.
    - Línea 96: `(docs/analisis-proceso-actual/reglamentos-aveit/)`.
  - Servicio inexistente en el repositorio: `laya-service` (línea 159).

---

## 4. `docs/Implementacion IA/presentacion/01_propuesta_subcomision_computos.md`

- **Ruta:** `docs/Implementacion IA/presentacion/01_propuesta_subcomision_computos.md`
- **Líneas:** 106
- **Última modificación:** `2026-10-14`
- **Tema que cubre:** Memorando de propuesta técnica dirigido a la Subcomisión de Cómputos de AVEIT sobre la arquitectura sidecar, huella de recursos y mantenimiento de Laya (`SCRUM-76`).
- **Quién lo lee:** equipo / nadie (memorando de presentación institucional redactado en Sprint 3; no es entregable de cátedra ni manual de usuario).
- **Qué pasa si desaparece:** alguien pregunta (listado en `TASK.md` y mencionado como entregable de `SCRUM-76` en `docs/gestion-proyecto/Seguimiento de Proyecto.md`).
- **Clasificación:** **3. Redundante con `docs/Implementacion IA/01_escenarios_y_casos_de_uso.md` y `docs/Implementacion IA/02_entrenamiento_datos_y_hardware.md`** (resumen adaptado a formato memorando; este archivo queda desactualizado/desalineado al afirmar la existencia de un script CLI en el repositorio).
- **Contradicciones con el registro:**
  - *Red Docker (línea 83):* afirma que todo el procesamiento ocurre en la red interna `sgd_network`, inexistente en `docker-compose.yml`.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - Línea 76: afirma que el fine-tuning se ejecuta *"con el script CLI del repositorio"*; no existe ningún script CLI de entrenamiento ni código de Laya en el repositorio.
  - Describe el contenedor sidecar `laya-service` y la tabla `ai_inference_logs` (líneas 50, 57, 84, 92), no implementados en el repositorio.
  - *(Nota: la afirmación de línea 29 sobre el backend Django 4.2 LTS —ciclo de vida, libro mayor sin `UPDATE` destructivos y Outbox transaccional— sí corresponde a funcionalidades verificadas como `implementada` en el Registro Canónico §2.)*
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - No aplica (memorando de factibilidad técnica para un componente propuesto no implementado).
- **Referencias rotas:**
  - Enlaces Markdown relativos mal resueltos desde `docs/Implementacion IA/presentacion/` (apuntan a `docs/Implementacion IA/presentacion/docs/Implementacion IA/...`, inexistente):
    - Líneas 7 y 104: `(docs/Implementacion%20IA/01_escenarios_y_casos_de_uso.md)`.
    - Línea 7: `(docs/Implementacion%20IA/02_entrenamiento_datos_y_hardware.md)`.
  - Artefactos inexistentes en el repositorio: contenedor `laya-service` (líneas 50, 57), red `sgd_network` (línea 83), tabla `ai_inference_logs` (línea 84) y *"script CLI del repositorio"* (línea 76).

---

## 5. `docs/Implementacion IA/presentacion/02_propuesta_tribunal_disciplina.md`

- **Ruta:** `docs/Implementacion IA/presentacion/02_propuesta_tribunal_disciplina.md`
- **Líneas:** 100
- **Última modificación:** `2026-10-14`
- **Tema que cubre:** Memorando operativo dirigido al Tribunal de Disciplina de AVEIT sobre las cuatro herramientas de asistencia IA propuestas y garantías de soberanía judicial (`SCRUM-76`).
- **Quién lo lee:** equipo / nadie (memorando de presentación institucional redactado en Sprint 3; no es entregable de cátedra ni manual de usuario).
- **Qué pasa si desaparece:** alguien pregunta (listado en `TASK.md` y mencionado como entregable de `SCRUM-76` en `docs/gestion-proyecto/Seguimiento de Proyecto.md`).
- **Clasificación:** **3. Redundante con `docs/Implementacion IA/01_escenarios_y_casos_de_uso.md` y `docs/Implementacion IA/03_evaluacion_slm_rag_cag_mag.md`** (resumen operativo para el TD; este archivo queda desactualizado respecto del registro canónico por mantener la votación nominal).
- **Contradicciones con el registro:**
  - *Votación nominal (líneas 44, 67 y 77):* afirma *"Una vez que los tres miembros votaron y acordaron la sanción"* (l. 44), *"Una vez que el Tribunal votó nominalmente en la Sala y fijó la sanción por socio"* (l. 67) y *"requiere indefectiblemente el voto explícito y la firma de los integrantes del Tribunal"* (l. 77). Contradice directamente el Registro Canónico (§2 y §3; observaciones docentes #23, #24 y #31), donde consta que la votación nominal fue **eliminada por directiva del PO el 07/10/2026** y sustituida por el editor unificado de resolución y firma colegiada (`Resolucion.firmantes`).
  - *Identificador de socio (línea 89):* menciona *"sus legajos"*; en el Registro Canónico (§3) el identificador canónico en código es `numero_socio`.
  - *Tablero Kanban (líneas 52–53):* usa *"Tablero Kanban"* en lugar de *"tablero de gestión"* (Registro Canónico §2).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - Las cuatro herramientas de asistencia IA presentadas (semáforo de urgencia IA, sugerencia de artículos IA, detección de consistencia en descargos IA y borrador automatizado de considerandos IA) **no están implementadas** en el repositorio.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Al diagnosticar el flujo actual del TD, no refleja las funcionalidades implementadas que ya operan en la Sala del Tribunal (Registro Canónico §2): clasificación manual de urgencia, Visor Autorizado Unificado (`SCRUM-51`), resolución de causal T02 (`SCRUM-52`), valoración extraordinaria T03 con precedentes (`SCRUM-53`), composición y suplencias (`SCRUM-54`) y editor unificado de resolución con preview PDF y firma colegiada (`SCRUM-56` / `SCRUM-58` / `SCRUM-89`).
- **Referencias rotas:**
  - Línea 7: enlace Markdown relativo `(docs/gestion-proyecto/notasPO.md)` mal resuelto desde `docs/Implementacion IA/presentacion/` (apunta a `docs/Implementacion IA/presentacion/docs/gestion-proyecto/notasPO.md`, inexistente).

---

## 6. `docs/Implementacion IA/presentacion/03_propuesta_comision_directiva.md`

- **Ruta:** `docs/Implementacion IA/presentacion/03_propuesta_comision_directiva.md`
- **Líneas:** 89
- **Última modificación:** `2026-10-14`
- **Tema que cubre:** Memorando estratégico dirigido a la Comisión Directiva de AVEIT presentando el impacto institucional, gobernanza, costo cero y pedido de autorización de prueba piloto para Laya (`SCRUM-76`).
- **Quién lo lee:** equipo / nadie (memorando de presentación institucional redactado en Sprint 3; no es entregable de cátedra ni manual de usuario).
- **Qué pasa si desaparece:** alguien pregunta (listado en `TASK.md` y mencionado como entregable de `SCRUM-76` en `docs/gestion-proyecto/Seguimiento de Proyecto.md`).
- **Clasificación:** **3. Redundante con `docs/Implementacion IA/01_escenarios_y_casos_de_uso.md` y `docs/Implementacion IA/presentacion/01_propuesta_subcomision_computos.md`** (resumen estratégico para CD; este archivo queda desactualizado y presenta una contradicción interna con el memorando dirigido a Cómputos).
- **Contradicciones con el registro:**
  - *Rol Revisores de Cuentas (líneas 38, 54–55):* menciona *"Comisión Revisora de Cuentas"* / *"Revisores de Cuentas"*. Según el Registro Canónico (§3), el rol RBAC en el código continúa llamándose `FISCALIZADORA`.
  - *Identificador de socio (línea 66):* refiere a *"legajos"* en lugar de `numero_socio` (Registro Canónico §3).
  - *Validación técnica de Cómputos (línea 76):* afirma *"La Subcomisión de Cómputos validó técnicamente que el modelo corre de forma ultra-liviana en las máquinas actuales del laboratorio"*. No existe evidencia verificable en el repositorio ni en el Registro Canónico (§6), y contradice `docs/Implementacion IA/presentacion/01_propuesta_subcomision_computos.md` (líneas 104–106), donde recién se solicita a Cómputos revisar las especificaciones, levantar el entorno experimental y emitir el visto bueno técnico.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - Describe el funcionamiento del motor Laya, notificaciones prioritarias de riesgo institucional (línea 48) y auditoría de sugerencias (línea 56), ninguno de los cuales está implementado en el repositorio.
  - Solicita desplegar el entorno de pruebas *"durante el transcurso del presente cuatrimestre"* (línea 88) y afirma que *"la solución está completamente diseñada en sus contratos de software, arquitectura de Docker y metodología de datos"* (línea 79), sin existencia de código, Dockerfile ni piloto en el repositorio.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - No aplica (memorando estratégico sobre una propuesta de I+D no implementada).
- **Referencias rotas:**
  - Ninguna (el documento no contiene enlaces Markdown ni rutas de código/archivos).

---

## Decisiones pendientes

1. **Destino de `docs/Implementacion IA/` en el repositorio:** definir si los 3 documentos técnicos (`01` a `03`) correspondientes a la tarea I+D `SCRUM-76` (sin código asociado) permanecen en `docs/` como referencia de investigación futura o se trasladan a `auditoria/archivados/`.
2. **Destino de los 3 memorandos en `docs/Implementacion IA/presentacion/`:** definir si se conservan como registro histórico de los entregables de `SCRUM-76` (citados en `TASK.md` y `Seguimiento de Proyecto.md`) o se archivan por ser redundantes con `01`–`03` y corresponder a un piloto no ejecutado.
3. **Veracidad de la validación de Cómputos:** confirmar con el PO/equipo si la Subcomisión de Cómputos realizó efectivamente la validación en laboratorio afirmada en `presentacion/03_propuesta_comision_directiva.md` (línea 76) o si quedó pendiente según `presentacion/01_propuesta_subcomision_computos.md` (líneas 104–106).
4. **Inconsistencia de votación nominal en documentos I+D:** definir el alcance de consistencia documental frente a las observaciones docentes (#23, #24 y #31 del Registro Canónico) respecto de las menciones a votación del TD en `03_evaluacion_slm_rag_cag_mag.md` y `presentacion/02_propuesta_tribunal_disciplina.md`.
5. **Alcance futuro de IA en el proyecto:** confirmar si la investigación `SCRUM-76` queda cerrada definitivamente fuera del alcance del producto actual o si alguna fase de implementación se registra como pendiente para el traspaso a Sprint 6.
