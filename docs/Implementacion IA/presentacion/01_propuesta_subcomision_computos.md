# Propuesta Técnica: Integración de Motor de Inferencia Ligero (System 1) en SGD-AVEIT

**Destinatario:** Subcomisión de Cómputos — A.V.E.I.T.  
**De:** Equipo de Desarrollo SGD-AVEIT / Product Owner  
**Fecha:** Octubre 2026  
**Carácter:** Documento de Propuesta Técnica y Análisis de Factibilidad  
**Referencias Técnicas:** [`docs/Implementacion IA/01_escenarios_y_casos_de_uso.md`](docs/Implementacion%20IA/01_escenarios_y_casos_de_uso.md) y [`docs/Implementacion IA/02_entrenamiento_datos_y_hardware.md`](docs/Implementacion%20IA/02_entrenamiento_datos_y_hardware.md)  

---

## 1. Resumen Ejecutivo (El Núcleo de la Propuesta)

Colegas de Cómputos: sabemos perfectamente cuál es la primera alarma que salta cuando alguien menciona "poner Inteligencia Artificial" en un sistema en producción: **deuda técnica, dependencias monstruosas en Python, servidores colapsados por falta de GPU y costos de APIs impredecibles**.

Planteamos algo completamente distinto.

No proponemos conectar SGD-AVEIT a un LLM en la nube ni meter librerías de Deep Learning de 4 GB adentro del backend Django. La propuesta concreta es desplegar **Laya**, un motor de decisiones tipadas (*System 1*) no generativo de 322 millones de parámetros, exportado a formato **ONNX cuantizado a INT8**, montado en un **contenedor sidecar independiente** en Docker Compose.

* **Consumo de memoria en el servidor:** Menos de 1.2 GB de RAM.
* **Dependencia de GPU en producción:** Cero. Corre en CPU pura con extensiones AVX2.
* **Latencia por petición:** Entre 40 y 70 milisegundos.
* **Costo mensual recurrente:** $0 (cero pesos, cien por ciento on-premise).
* **Impacto en el backend actual:** Cero modificaciones en el core transaccional; solo una llamada HTTP interna opcional.

---

## 2. Diagnóstico del Flujo Actual y la Oportunidad Técnica

Hoy el backend Django 4.2 LTS gestiona el ciclo de vida del expediente de forma impecable: los estados procesales cambian con bloqueos pesimistas, el libro mayor calcula los saldos sin `UPDATE` destructivos y los correos salen por un Outbox transaccional.

Sin embargo, en el ingreso de datos (el Formulario T01 y la recepción de descargos T02/T03), el sistema procesa cadenas de texto libre como datos mudos. El Tribunal de Disciplina debe leer manualmente relatos largos para decidir dos cosas básicas:
1. Si el asunto es urgente o si puede esperar la sesión ordinaria.
2. Qué artículo del Reglamento Interno de Disciplina 2026 se ajusta a la infracción imputada.

Si dotamos a la API de la capacidad de responder esas dos preguntas en 50 milisegundos con una distribución de probabilidades calibrada, le ahorramos horas de trabajo repetitivo al Tribunal, reducimos el tiempo de respuesta del sistema y mantenemos intacta la integridad de la base de datos.

---

## 3. Arquitectura Propuesta: El Patrón Sidecar

Para que Cómputos mantenga el control absoluto de la infraestructura y no arriesgue la estabilidad del backend, la inferencia corre completamente desacoplada:

```
[ Frontend Angular 14 ]
         │
         ▼ (HTTP JSON)
[ Backend Django 4.2 (DRF) ] ─── (SQL Transaccional) ───► [ MySQL 8.0 ]
         │
         ▼ (HTTP POST /v1/systemone - Red interna Docker)
[ Contenedor Sidecar: laya-service ]
   ├── FastAPI + Uvicorn (2 workers)
   └── ONNX Runtime (INT8 Engine: ~160 MB de pesos)
```

### ¿Por qué esta arquitectura cuida la infraestructura de AVEIT?
1. **Aislamiento de Entorno:** El `requirements.txt` de Django no se toca. Ni PyTorch ni Hugging Face entran al backend. El backend solo usa la librería nativa de peticiones HTTP.
2. **Falla Segura (Fail-Safe):** Si el contenedor `laya-service` se reinicia, se cuelga o se apaga por mantenimiento, **el backend Django no se cae**. La vista captura el timeout con un bloque `try/except` estándar y el formulario T01 sigue funcionando normalmente en modo manual. La IA es un acelerador, nunca un punto único de fallo.
3. **Imágenes Docker Livianas:** El contenedor sidecar parte de `python:3.12-slim`. Con el runtime de ONNX y los pesos cuantizados, la imagen completa ocupa menos de 450 MB en disco.
4. **Despliegue Idéntico en Desarrollo y Producción:** El mismo bloque de servicio corre en la notebook de cualquier desarrollador con `docker compose up -d` sin requerir tarjetas gráficas especiales.

---

## 4. Eficiencia de Cómputo: Números Concretos sobre la Mesa

Hablemos en términos de hardware y recursos de cómputo reales:

| Métrica Técnica | Enfoque Descartado (LLM Generativo Local / Cloud) | Enfoque Propuesto (Laya System 1 ONNX INT8) |
| :--- | :--- | :--- |
| **Arquitectura de Red** | Autorregresiva (*decoder* con bucle token por token) | Codificador bidireccional (*single forward pass*) |
| **Tiempo de Inferencia** | 1.500 a 4.000 ms | **40 a 75 ms en CPU** |
| **Huella en Memoria RAM** | 6 a 16 GB VRAM/RAM dedicada | **~1.1 GB RAM total del proceso** |
| **Cálculo de Gradientes** | Ingestion masiva de contexto | Inferencia estática compilada |
| **Dependencia de Internet** | Crítica (riesgo de caída de API o cambios de términos) | **Cero (funciona aislado sin salida a internet)** |
| **Alucinación Factual** | Probabilidad real de inventar artículos reglamentarios | **0% (solo clasifica sobre opciones cerradas)** |

El entrenamiento del modelo no se ejecuta en el servidor de AVEIT. El fine-tuning se hace previamente en una computadora de escritorio con GPU (demorando entre 15 y 25 minutos con el script CLI del repositorio), se exporta el archivo `model.onnx` cuantizado y se monta en el contenedor como un volumen de solo lectura.

---

## 5. Trazabilidad, Seguridad y Gobernanza de Datos

Desde la óptica de administración de sistemas y auditoría:
* **Privacidad de Datos:** Ningún dato de socios, relatos de faltas disciplinarias ni resoluciones viaja fuera del servidor local de AVEIT. Todo el procesamiento ocurre en la red interna de Docker (`sgd_network`).
* **Auditoría de Inferencia:** Cada sugerencia emitida por el modelo se registra en una tabla técnica dedicada (`ai_inference_logs`) que almacena el hash del texto de entrada, el tiempo de respuesta en milisegundos y el vector de probabilidades devuelto. Esto permite a Cómputos monitorear la latencia y la precisión sin mezclar logs técnicos con el expediente judicial.
* **Cero Impacto en Puntos:** El microservicio no tiene credenciales de acceso a la base de datos MySQL. No puede leer el padrón ni modificar saldos. Su única función es recibir un string JSON y responder otro string JSON tipado.

---

## 6. Despeje de Dudas y Objeciones Clave de Cómputos

### "Ya tenemos suficiente trabajo manteniendo los servicios actuales. ¿Quién mantiene esto si algo falla?"
El mantenimiento operativo es prácticamente nulo. El contenedor sidecar es un servicio *stateless* (sin estado): no tiene base de datos propia, no retiene sesiones y no acumula temporales. Si el contenedor falla, Docker lo reinicia en 3 segundos (`restart: unless-stopped`). Si se decide darlo de baja, basta con comentar 12 líneas en el `docker-compose.yml` y el sistema sigue operando como siempre.

### "¿Qué pasa si se actualiza el Reglamento de Disciplina? ¿Hay que reprogramar la red de cero?"
No. Las opciones de clasificación (`criteria`) se le pasan al modelo en el payload de cada petición HTTP. Si el Tribunal agrega un artículo nuevo o cambia una descripción, solo se actualiza el archivo de configuración JSON de criterios, sin necesidad de reentrenar la red para cambios menores. Para reentrenamientos estructurales, se dispone de un script por línea de comandos que compila el nuevo checkpoint en minutos.

### "¿Por qué no usar simplemente un clasificador clásico como Naive Bayes o TF-IDF con Scikit-Learn?"
Los clasificadores por bolsas de palabras o n-gramas fallan estrepitosamente ante la sinonimia y el lenguaje jurídico informal. Si un socio escribe *"el imputado se quedó con la llave del pañol y no la devolvió"* y el reglamento habla de *"negligencia en la custodia de bienes institucionales"*, un TF-IDF no encuentra coincidencias léxicas. Laya comprende la semántica profunda del texto a nivel contextual mediante un transformer moderno (mmBERT), pero sin la pesadez ni la lentitud de un modelo generativo.

---

## 7. Próximos Pasos Recomendados para Cómputos

1. **Revisión del Código y Especificaciones:** Inspeccionar el contrato de API y los esquemas en [`docs/Implementacion IA/01_escenarios_y_casos_de_uso.md`](docs/Implementacion%20IA/01_escenarios_y_casos_de_uso.md).
2. **Levantamiento Experimental:** Probar el contenedor sidecar en una rama aislada de desarrollo y verificar el consumo de CPU y memoria con `docker stats`.
3. **Visto Bueno Técnico:** Emitir el dictamen de factibilidad de Cómputos para habilitar la prueba piloto en conjunto con el Tribunal de Disciplina.
