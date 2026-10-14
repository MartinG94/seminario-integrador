# Propuesta Operativa: Asistencia Inteligente y Optimización del Proceso Disciplinario

**Destinatario:** Miembros Titulares y Suplentes del Tribunal de Disciplina — A.V.E.I.T.  
**De:** Equipo de Desarrollo SGD-AVEIT / Product Owner  
**Fecha:** Octubre 2026  
**Carácter:** Propuesta de Mejora de Procesos y Asistencia Operativa al Tribunal  
**Referencias Normativas:** [`docs/gestion-proyecto/notasPO.md`](docs/gestion-proyecto/notasPO.md), Estatuto Social AVEIT 2026 y Reglamento Procesal Disciplinario 2026  

---

## 1. El Propósito Central: Proteger el Tiempo y el Juicio del Tribunal

Estimados miembros del Tribunal: juzgar la conducta de un par dentro de una asociación como AVEIT es una de las tareas institucionales más delicadas y desgastantes. Exige templanza, ecuanimidad y un conocimiento minucioso de cada artículo reglamentario.

Hoy, gran parte de la energía y el tiempo de ustedes no se destina a deliberar sobre la justicia del caso, sino a **tareas operativas repetitivas**:
* Leer denuncias desordenadas para determinar si un caso amerita una reunión de urgencia o puede esperar.
* Rastrear entre decenas de páginas del Reglamento Interno de Disciplina cuál es el artículo exacto que tipifica la conducta.
* Cotejar declaraciones extensas de descargos (Formularios T02 y T03) contra el relato inicial para detectar contradicciones evidentes.
* Redactar a mano la estructura formal de los considerandos (el VISTO y CONSIDERANDO) de cada resolución.

La propuesta que ponemos a consideración de este cuerpo no viene a reemplazar el criterio de ustedes. Viene a hacer exactamente lo contrario: **eliminar la carga burocrática y los cuellos de botella del proceso para que el Tribunal recupere el foco en lo sustancial: evaluar los hechos con justicia y ecuanimidad**.

---

## 2. Enfoque de Procesos: Dónde Están los Cuellos de Botella Hoy

Desde una mirada de ingeniería de procesos y flujo de valor, el ciclo de vida de un expediente disciplinario presenta tres demoras críticas:

```
[ Ingreso de Denuncia T01 ]
         │
         ▼ (Cuello de Botella 1: Triage manual y lectura completa para fijar urgencia)
[ Apertura y Notificación ] ─── (Plazo preclusivo: 5 días hábiles) ───► [ Recepción Descargo T02/T03 ]
                                                                                   │
                                                                                   ▼ (Cuello de Botella 2: Comparación forense y búsqueda de artículos)
                                                                         [ Sesión de Sala del TD ]
                                                                                   │
                                                                                   ▼ (Cuello de Botella 3: Redacción manual de considerandos)
                                                                         [ Resolución Formal Firmada ]
```

1. **Cuello de Botella 1 (Triage de Entrada):** Cuando ingresan varias solicitudes T01 en una misma semana, las causas urgentes (agresiones, riesgo patrimonial o peligro de prescripción procesal) quedan mezcladas con faltas menores en la misma lista. El TD pierde días valiosos antes de advertir la gravedad de un hecho.
2. **Cuello de Botella 2 (Tipificación Normativa):** La búsqueda del artículo aplicable depende de la memoria o la experiencia de quien instruye la causa. Esto introduce variabilidad: dos casos similares pueden terminar tipificados bajo artículos distintos según quién redacte la acusación.
3. **Cuello de Botella 3 (Confección del Proyecto de Fallo):** Una vez que los tres miembros votaron y acordaron la sanción, pasar la deliberación a la estructura canónica de resolución formal insume entre 45 minutos y dos horas de redacción técnica por expediente.

---

## 3. Las Cuatro Herramientas de Asistencia Propuestas

Para atacar estos tres cuellos de botella sin introducir riesgos de arbitrariedad, proponemos integrar cuatro asistencias consultivas en el sistema:

### 3.1. Clasificador y Semáforo de Urgencia en el Tablero Kanban
Al registrarse una denuncia o solicitud T01, el motor analiza el relato del hecho y el anexo de testigos, y sugiere en la tarjeta del tablero un nivel de urgencia (`Baja`, `Normal` o `Urgente`) con un porcentaje de certeza.
* **Lo que gana el Tribunal:** Visibilidad inmediata de las causas críticas apenas abren la pantalla, permitiendo priorizar audiencias o solicitar medidas preventivas a Comisión Directiva sin demoras.

### 3.2. Sugerencia no Vinculante de Artículos Reglamentarios
En la pantalla de apertura, el sistema despliega el artículo más probable del Reglamento de Disciplina (ej. *"Art. 12: Custodia de bienes institucionales - 86% de coincidencia"*), junto con un resumen de los criterios que fundamentan esa sugerencia.
* **Lo que gana el Tribunal:** Estandarización y repetibilidad. El instructor no empieza de una hoja en blanco; puede aceptar la sugerencia con un clic o rechazarla y seleccionar cualquier otro artículo del catálogo oficial.

### 3.3. Detección de Consistencia en Descargos (T02 / T03)
Cuando el socio imputado presenta su descargo, el sistema realiza una comparación semántica rápida contra la denuncia original e indica:
* Si el socio admite expresamente los hechos imputados.
* Si introduce contradicciones directas con las declaraciones de testigos consignadas en la Hoja de Anexo.
* **Lo que gana el Tribunal:** Un resumen de discrepancias que guía el interrogatorio de los miembros durante la deliberación.

### 3.4. Borrador Automatizado de Considerandos (VISTO y CONSIDERANDO)
Una vez que el Tribunal votó nominalmente en la Sala y fijó la sanción por socio, el sistema genera en dos segundos el texto preliminar formal de la resolución (encabezado canónico, resumen de hechos acreditados y mención de artículos violados).
* **Lo que gana el Tribunal:** Los miembros solo leen, ajustan matices de redacción y firman. El tiempo administrativo de redacción por resolución baja de una hora a diez minutos.

---

## 4. Garantías Innegociables: Soberanía Judicial y Presunción de Inocencia

El mayor temor que suscita la palabra "algoritmo" en un ámbito disciplinario es la pérdida de la dimensión humana. Por eso, dejamos fijadas cuatro garantías institucionales que están grabadas en el diseño mismo del software:

1. **Carácter 100% no vinculante (Human-in-the-Loop):** La IA no tiene voto, no tiene firma y no tiene autoridad. Cada sugerencia de urgencia o de artículo es una recomendación en pantalla que el Tribunal puede ignorar o modificar libremente sin justificar ante el sistema.
2. **Cero automatización en la imposición de sanciones:** Ningún socio puede ser sancionado, amonestado ni apercibido por una decisión automática. El cómputo y acreditación de puntos requiere indefectiblemente el voto explícito y la firma de los integrantes del Tribunal.
3. **Imposibilidad de alucinación reglamentaria:** El clasificador utilizado (Laya) opera sobre un conjunto cerrado de artículos preexistentes del Reglamento Interno 2026. Es matemáticamente imposible que el modelo invente artículos, sanciones o normas que no estén en los textos vigentes de AVEIT.
4. **Respeto absoluto al debido proceso:** La existencia de sugerencias de IA en el sistema no altera los plazos de 5 días hábiles para el descargo ni la confidencialidad de la deliberación interna del Tribunal.

---

## 5. Despeje de Dudas y Objeciones Clave del Tribunal

### "¿Qué pasa si un socio sancionado impugna el fallo diciendo que 'lo juzgó una computadora'?"
El expediente y la resolución formal no contienen rastros de autoría automática. Lo que valida legal y estatutariamente una sanción es la resolución firmada al pie por los tres miembros del Tribunal (con indicación de año social y condición de titular o suplente, según el Art. 12 del Reglamento Procesal 2026). La IA actúa como un procesador de texto avanzado o un buscador inteligente que asiste a quien redacta; la potestad sancionatoria emana pura y exclusivamente de los miembros humanos electos.

### "¿El modelo no puede tener sesgos contra ciertos grupos o socios?"
Para evitar cualquier sesgo de afinidad o cohorte, el modelo es ciego a los nombres de los involucrados, sus legajos y su grupo social (G57, G58, etc.). El texto que analiza el motor pasa anonimizado: solo evalúa la descripción fáctica de la conducta denunciada frente a las definiciones técnicas de las faltas reglamentarias.

### "¿Esto nos obliga a cambiar nuestra forma de trabajar o de sesionar?"
En absoluto. El Tribunal sigue sesionando exactamente igual. La única diferencia visible es que en el sistema encontrarán campos precompletados con sugerencias inteligentes que les ahorrarán tiempo de tipeo y búsqueda. Si el Tribunal considera que una sugerencia no es adecuada, la descarta en un segundo con el teclado o el mouse.

---

## 6. Conclusión y Propuesta de Trabajo Conjunto

Desde la perspectiva de la mejora continua de procesos, esta herramienta no viene a vigilar ni a condicionar la labor del Tribunal, sino a jerarquizarla. Un Tribunal liberado de la pesadez de buscar artículos y tipear considerandos es un Tribunal que puede dedicar más tiempo a escuchar a los socios, evaluar los atenuantes con serenidad y emitir fallos de mayor calidad institucional.

Proponemos realizar una **prueba piloto cerrada de 30 días**, utilizando casos simulados o expedientes ya resueltos de años anteriores, para que los propios integrantes del Tribunal evalúen la precisión de las sugerencias y definan si la herramienta les aporta el valor y la comodidad que esperamos antes de activarla en producción.
