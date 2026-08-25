# Estándar y Plantilla de Especificación de Casos de Uso (CU)
## Sistema de Gestión del Tribunal de Disciplina y Premiaciones (SGD-AVEIT)
### Cátedra: Seminario Integrador — Curso 3K2 — UTN FRC

---

## 📌 Guía de Uso del Estándar

Este documento establece la estructura oficial y obligatoria para la especificación detallada de los **Casos de Uso (CU)** del proyecto **SGD-AVEIT**.

### Principios clave para el equipo:
1. **Granularidad adecuada:** Cada caso de uso debe representar una meta de negocio completa y con valor para un actor (evitar micro-casos de uso como *"Presionar botón"* o *"Validar correo"*).
2. **Numeración y Trazabilidad:** Todo CU debe identificarse con la nomenclatura `CU-XX` y vincularse con sus respectivas **Reglas de Negocio (`RN-XX`)**, **Pantallas/Prototipos (`UI-XX`)** y **Endpoints de Backend (`API-XX`)**.
3. **Claridad en la interacción:** El Flujo Principal debe redactarse en pasos numerados secuenciales, distinguiendo explícitamente la acción del **Actor** de la respuesta del **Sistema**.
4. **Tratamiento exhaustivo de excepciones:** Especificar siempre los flujos alternativos (caminos secundarios válidos) y los flujos de error/excepción (cancelaciones, faltas de datos, plazos vencidos, falta de permisos).

---

# 📄 [PLANTILLA EN BLANCO — COPIAR Y PEGAR]

*(Copiar a partir del siguiente bloque para cada nuevo Caso de Uso a documentar)*

```markdown
# CU-XX: [Nombre del Caso de Uso en Verbo Infinitivo + Objeto]

## 1. Ficha Técnica

| Atributo | Detalle |
| :--- | :--- |
| **Identificador** | CU-XX |
| **Nombre** | [Nombre del Caso de Uso] |
| **Módulo / Subsistema** | [Módulo 1: Tramitación / Módulo 2: Deliberación / Módulo 3: Puntos / Módulo 4: Portal / Módulo 5: Balances] |
| **Actor Principal** | [Actor que inicia la interacción: Socio Junior / Socio Senior / Miembro del TD / Autoridad de Subcomisión / Comisión Directiva / Sistema] |
| **Actores Secundarios** | [Otros actores que intervienen o reciben notificaciones] |
| **Propósito / Objetivo** | [Descripción breve de una o dos oraciones sobre qué logra el actor con este caso de uso] |
| **Tipo de Ejecución** | [En línea (Web/Mobile) / Asíncrono / Automático por Cron Job / Por Lote (Batch)] |
| **Frecuencia de Uso** | [Muy alta (Diaria) / Alta (Semanal) / Periódica (Quincenal / Mensual) / Eventual / Cuatrimestral] |
| **Estado de Madurez** | [Borrador / En Revisión / Aprobado / Implementado] |

---

## 2. Precondiciones
*El sistema y el entorno deben satisfacer las siguientes condiciones antes de iniciar el caso de uso:*
1. [Precondición 1: ej. El usuario debe haber iniciado sesión con credenciales válidas y rol X].
2. [Precondición 2: ej. El expediente debe encontrarse en estado 'X'].

---

## 3. Disparador (Trigger)
* [Evento inicial que dispara el caso de uso: ej. El usuario hace clic en el botón "Nuevo Descargo" o se cumple el plazo del cron job].

---

## 4. Flujo Principal (Camino Feliz / Happy Path)

| Paso | Actor | Sistema |
| :---: | :--- | :--- |
| **1** | [Acción del actor: ej. Accede a la sección X y solicita realizar Y]. | |
| **2** | | [Respuesta del sistema: ej. Recupera datos de BD y presenta la interfaz UI-XX con los campos A, B, C]. |
| **3** | [Acción del actor: ej. Completa los campos requeridos y presiona "Guardar / Confirmar"]. | |
| **4** | | [Validación del sistema: ej. Valida las reglas RN-01 y RN-02]. |
| **5** | | [Persistencia y efectos colaterales: ej. Inserta el registro en MySQL de forma transaccional, genera log de auditoría y encola notificación por correo]. |
| **6** | | [Feedback al usuario: ej. Muestra mensaje de éxito emergente y redirige a la vista de detalle]. |

---

## 5. Flujos Alternativos (Caminos secundarios válidos)

### 5.1. [FA-XX.1: Nombre del Flujo Alternativo 1]
- **Condición de activación:** En el paso `[N]` del Flujo Principal, ocurre `[Condición]`.
- **Secuencia de pasos:**
  1. [Paso 1 del flujo alternativo].
  2. [Paso 2 del flujo alternativo].
  3. El flujo continúa en el paso `[N+1]` del Flujo Principal (o finaliza con éxito).

---

## 6. Flujos de Excepción / Manejo de Errores

### 6.1. [FE-XX.1: Error de Validación o Datos Incompletos]
- **Condición de activación:** En el paso `[N]` del Flujo Principal, `[Falla validación X]`.
- **Secuencia de pasos:**
  1. El sistema resalta los campos con error y bloquea el envío.
  2. El sistema muestra mensaje informativo: *"El archivo adjunto excede el tamaño máximo permitido (10 MB)"*.
  3. El flujo retorna al paso `[N-1]` para que el actor subsane el error.

### 6.2. [FE-XX.2: Intento de Acción Fuera de Plazo Preclusivo (RN-XX)]
- **Condición de activación:** En el paso `[N]`, el sistema detecta que han transcurrido más de 5 días hábiles.
- **Secuencia de pasos:**
  1. El sistema deniega la operación.
  2. Registra el intento fallido en el log de auditoría.
  3. Muestra alerta: *"El plazo legal para presentar este formulario ha precluido"*.
  4. El caso de uso finaliza sin modificar el estado del expediente.

---

## 7. Postcondiciones

### 7.1. Postcondición de Éxito
- [Estado final en la Base de Datos: ej. Registro insertado con ID único, estado actualizado a 'X'].
- [Pistas de Auditoría: Log inalterable generado con fecha, hora, IP y usuario].
- [Efectos colaterales: Notificación por email enviada/encolada].

### 7.2. Postcondición de Fallo
- El estado del sistema y de la base de datos permanece inalterado (Rollback transaccional).
- Se registra el evento de error en el log del servidor.

---

## 8. Reglas de Negocio Asociadas (RN)

| Código RN | Nombre de la Regla | Descripción |
| :--- | :--- | :--- |
| **RN-XX** | [Nombre Regla] | [Enunciado formal y estricto de la regla que rige este comportamiento]. |

---

## 9. Requerimientos No Funcionales y de Seguridad
- **Disponibilidad y Responsive:** La pantalla debe ser 100% operable desde smartphones (pantallas desde 360px de ancho).
- **Seguridad y Autorización:** Validación de token JWT / sesión activa y comprobación de rol en el backend (no solo validación en frontend).
- **Auditoría:** Toda modificación debe registrar `created_at`, `created_by_user_id` e `ip_address`. Prohibida la eliminación física (`DELETE`); utilizar borrado lógico o transacciones acumulativas.
- **Tiempo de Respuesta:** Tiempo de procesamiento y respuesta de API inferior a 800 ms.

---

## 10. Mapeo a Prototipos de UI y Endpoints de Backend

| Elemento | Referencia / Identificador | Descripción |
| :--- | :--- | :--- |
| **Pantalla / Interfaz** | `UI-XX` | [Nombre de la pantalla o modal en prototipo / wireframe] |
| **API Endpoint** | `POST /api/v1/[recurso]` | [Controlador o servicio encargado de procesar la solicitud] |
```

---

# 📚 EJEMPLO MODELO COMPLETO

A continuación se incluye un ejemplo completamente desarrollado según la plantilla oficial para servir como guía de referencia a todo el equipo:

---

# CU-01: Solicitar Apertura de Expediente de Sanción o Premiación (Formulario T01 / Anexo)

## 1. Ficha Técnica

| Atributo | Detalle |
| :--- | :--- |
| **Identificador** | CU-01 |
| **Nombre** | Solicitar Apertura de Expediente de Sanción o Premiación (Formulario T01 / Anexo) |
| **Módulo / Subsistema** | Módulo 1: Tramitación Procesal y Formularios Digitales |
| **Actor Principal** | Autoridad Competente (Presidente/Vice de Subcomisión, Miembro de CD, Miembro de TD) |
| **Actores Secundarios** | Socio(s) Imputado(s)/Postulado(s), Miembros del Tribunal de Disciplina, Sistema de Correo |
| **Propósito / Objetivo** | Permitir que una autoridad estatutariamente habilitada inicie formalmente un pedido de sanción o premiación ante el TD completando el Formulario T01 y su Hoja de Anexo circunstanciada. |
| **Tipo de Ejecución** | En línea (Plataforma Web / Responsive Mobile) |
| **Frecuencia de Uso** | Periódica (cada vez que ocurra una falta, inasistencia, omisión de tareas o mérito extraordinario) |
| **Estado de Madurez** | Aprobado para Especificación |

---

## 2. Precondiciones
1. El usuario solicitante debe estar autenticado en la plataforma.
2. El usuario debe poseer un rol con competencia estatutaria para iniciar expedientes:
   - Presidente o Vicepresidente de alguna de las 7 subcomisiones.
   - Miembro titular de Comisión Directiva (CD).
   - Miembro titular o suplente del Tribunal de Disciplina (TD - de oficio).
3. Los socios destinatarios (imputados o postulados) deben figurar como Socios Activos en el padrón de la base de datos (con categoría Junior o Senior identificada).

---

## 3. Disparador (Trigger)
* La autoridad hace clic en el botón **"+ Nuevo Formulario T01"** desde el panel de expedientes o menú lateral.

---

## 4. Flujo Principal (Camino Feliz / Happy Path)

| Paso | Actor | Sistema |
| :---: | :--- | :--- |
| **1** | Hace clic en **"+ Nuevo Formulario T01"**. | |
| **2** | | Valida las atribuciones del usuario (RN-01). Renderiza la interfaz [UI-01: Formulario T01] con el encabezado autocompletado (Datos del solicitante, fecha actual, subcomisión emisora). |
| **3** | Selecciona el **Tipo de Solicitud**: *"Pedido de Sanción"* o *"Pedido de Premiación"*. | |
| **4** | | Carga dinámicamente el catálogo de motivos tipificados según la normativa 2026 (inasistencia a asamblea, omisión de tarea asignada, falta ética / proactividad destacada, evento extraordinario). |
| **5** | Selecciona el o los **Socios Imputados/Postulados** mediante el buscador interactivo (por nombre, apellido, legajo o subcomisión). | |
| **6** | | Valida que los socios seleccionados estén activos y muestra su categoría social (Junior/Senior) y su subcomisión actual. |
| **7** | Selecciona el motivo tipificado y define la **propuesta de puntos** sugerida según la escala reglamentaria. | |
| **8** | Completa la sección **Hoja de Anexo T01**: Redacta el detalle circunstanciado de los hechos (fecha del hecho, contexto, descripción de la falta u omisión, pruebas iniciales). | |
| **9** | *(Opcional)* Adjunta archivos probatorios iniciales (actas de reunión, planillas de asistencia, capturas). | |
| **10**| Revisa el resumen generado y presiona **"Presentar Solicitud T01 ante el TD"**. | |
| **11**| | Valida integridad y obligatoriedad de los datos (RN-02). |
| **12**| | Ejecuta transacción en BD MySQL:<br>1. Genera número correlativo único de expediente (`EXP-2026-XXXX`).<br>2. Registra el expediente en **Estado 1: Expediente Creado**.<br>3. Almacena el formulario T01 y su anexo vinculado al expediente.<br>4. Inserta registro inalterable en la tabla de auditoría (`audit_log`). |
| **13**| | Encola notificaciones automáticas por correo electrónico a los integrantes del TD informando el ingreso de una nueva causa. |
| **14**| | Muestra notificación de éxito (*Toast*: *"Expediente EXP-2026-XXXX creado exitosamente"*) y redirige a la vista de seguimiento del expediente. |

---

## 5. Flujos Alternativos

### 5.1. FA-01.1: Solicitud Colectiva / Grupal (Múltiples socios imputados/premiados)
- **Condición de activación:** En el paso 5, la autoridad selecciona dos o más socios que participaron del mismo hecho o tarea.
- **Secuencia de pasos:**
  1. El sistema valida la lista completa de socios seleccionados.
  2. Permite a la autoridad asignar el mismo motivo y anexo para todos, o individualizar los puntos propuestos para cada integrante.
  3. En el paso 12, el sistema crea un único expediente madre vinculando a todos los socios involucrados de manera individual en la tabla relacional `expediente_socios`.
  4. El flujo continúa en el paso 13.

### 5.2. FA-01.2: Inicio de Expediente de Oficio por el Tribunal de Disciplina
- **Condición de activación:** En el paso 2, el solicitante es un Miembro del Tribunal de Disciplina.
- **Secuencia de pasos:**
  1. El sistema habilita la opción *"Apertura de Oficio por el TD"* omitiendo la selección de subcomisión solicitante.
  2. El flujo continúa en el paso 3 con las causales disciplinarias de actuación directa.

---

## 6. Flujos de Excepción / Manejo de Errores

### 6.1. FE-01.1: Usuario sin Competencia Estatutaria (RN-01)
- **Condición:** El usuario autenticado es un socio ordinario sin cargo de Presidente/Vice de Subcomisión ni rol en CD/TD.
- **Acción:** El sistema bloquea el acceso a la pantalla, registra el intento no autorizado en logs y muestra mensaje de error: *"No posee atribuciones estatutarias para iniciar solicitudes de expediente T01"*.

### 6.2. FE-01.2: Omisión de Campos Obligatorios en Hoja de Anexo (RN-02)
- **Condición:** En el paso 11, la descripción de los hechos posee menos de 20 caracteres o no se seleccionó ningún socio.
- **Acción:** El sistema resalta los campos faltantes en rojo, no ejecuta la persistencia y notifica: *"Debe detallar circunstanciadamente los hechos en la Hoja de Anexo y seleccionar al menos un socio"*.

### 6.3. FE-01.3: Formato o Tamaño de Adjuntos No Permitido
- **Condición:** En el paso 9, el usuario intenta adjuntar un archivo que no es PDF/PNG/JPG o que supera los 10 MB.
- **Acción:** El sistema rechaza el archivo en el cliente y muestra alerta: *"Solo se admiten documentos PDF o imágenes JPG/PNG de hasta 10 MB"*.

---

## 7. Postcondiciones

### 7.1. Postcondición de Éxito
- Se crea un nuevo registro en la tabla `expedientes` con estado `CREADO` (Estado 1) y código autogenerado `EXP-YYYY-XXXX`.
- Se persiste el formulario T01 en `formularios_t01` con su respectivo anexo y archivos vinculados en el storage seguro.
- Se inserta la pista de auditoría en `auditoria_operaciones` (`action='CREATE_EXPEDIENTE'`, `user_id`, `timestamp`, `ip_address`).
- El expediente queda visible en el tablero general del TD listo para ser analizado y dar inicio al período de descargo (CU-02).

### 7.2. Postcondición de Fallo
- Ningún dato es insertado en la base de datos MySQL (Rollback total).
- El usuario permanece en el formulario con sus datos cargados para corregir el inconveniente.

---

## 8. Reglas de Negocio Asociadas (RN)

| Código RN | Nombre de la Regla | Descripción |
| :--- | :--- | :--- |
| **RN-01** | **Competencia de Solicitud T01** | Solo pueden emitir formularios T01: Presidentes/Vices de Subcomisión, miembros de Comisión Directiva y miembros del Tribunal de Disciplina. |
| **RN-02** | **Fundamentación Circunstanciada Obligatoria** | Todo Formulario T01 debe contener obligatoriamente una Hoja de Anexo con la descripción fáctica, fecha y motivación del pedido. |
| **RN-03** | **Unicidad e Inalterabilidad de Expediente** | Una vez generado el número de expediente, el formulario T01 original no puede ser modificado ni sobreescrito; solo podrá recibir anexos o justificaciones posteriores. |
| **RN-04** | **Escala de Puntos 2026** | Los puntos propuestos deben respetar los rangos fijados por la Circular Normativa vigente (fracciones mínimas de 0.5 puntos; faltas leves hasta 2 pts, omisión de tareas hasta 2 pts, faltas graves según escala). |

---

## 9. Requerimientos No Funcionales y de Seguridad
- **Responsive Mobile:** Formulario operable de forma táctil y fluida en teléfonos móviles (Mobile-First).
- **Integridad y Transaccionalidad:** Inserción ACID garantizada en MySQL; no se permiten registros huérfanos.
- **Auditoría inalterable:** Registro estricto del usuario emisor, fecha/hora exacta de recepción e IP.

---

## 10. Mapeo a Prototipos de UI y Endpoints

| Elemento | Identificador | Descripción |
| :--- | :--- | :--- |
| **Prototipo UI** | `UI-01` | Pantalla de Formulario Digital T01 con buscador de socios y editor de Anexo |
| **API Endpoint** | `POST /api/v1/expedientes/solicitud-t01` | Endpoint para creación transaccional del expediente y recepción de datos multipart (adjuntos) |
| **Modelo BD** | Tablas `expedientes`, `expediente_socios`, `formularios_t01`, `adjuntos_expediente`, `auditoria_operaciones` | Estructura relacional de persistencia en MySQL |
