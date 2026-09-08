# CU-XX: [Nombre del Caso de Uso en Verbo Infinitivo + Objeto]

## 1. Ficha Técnica

| Atributo | Detalle |
| :--- | :--- |
| **Identificador** | CU-XX |
| **Nombre** | [Nombre del Caso de Uso] |
| **Módulo / Subsistema** | [Módulo 1: Tramitación / Módulo 2: Deliberación / Módulo 3: Puntos / Módulo 4: Portal / Módulo 5: Balances] |
| **Actor Principal** | [Actor que inicia la interacción: Socio Pasivo / Socio Activo / Miembro del TD / Autoridad de Subcomisión / Comisión Directiva / Sistema] |
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
