# Especificación Normativa de Control de Acceso Basado en Roles (RBAC) — SGD-AVEIT

> **Código de Documento:** `SPEC-RBAC-001`  
> **Versión Normativa:** `2.0.0` (Consolidación Post-Refinamiento Sprint 5 / MACRO-07 / SCRUM-121)  
> **Fecha de Entrada en Vigencia:** 11/11/2026  
> **Autor Institucional:** Equipo Seminario Integrador — En acuerdo vinculante con Diego Sánchez (Product Owner)  
> **Fuentes Rectoras:** Estatuto AVEIT, Reglamento del Proceso Disciplinario (RPD 2026, Arts. 12–26, 95), [`docs/gestion-proyecto/notasPO.md`](file:///c:/Users/terza/Desktop/Current Team Proyects/seminario-integrador/docs/gestion-proyecto/notasPO.md) y Acuerdos de Refinamiento MACRO-07.

---

## 1. Principios Rectores de Seguridad y Autorización

1. **La autorización vinculante reside estrictamente en el Servidor (Backend DRF):**  
   El ocultamiento de botones, pestañas o redirecciones en la Single Page Application (SPA Angular) constituye una optimización de la experiencia de usuario (UX). Toda validación de acceso procesal se ejecuta en el backend en cada petición HTTP. Cualquier invocación manual o directa a un endpoint protegido sin credenciales ni privilegios responderá taxativamente con códigos de error estándar HTTP.
2. **Relectura en Base de Datos en cada Request:**  
   Los permisos del usuario se evalúan releyendo en tiempo de ejecución los campos `Socio.role` y `Socio.is_enabled` directamente desde la base de datos MySQL, descartando la confianza ciega en los claims del token JWT emitido. De este modo, una cesantía, suspensión o cambio de designación estatutaria surte efecto inmediato.
3. **El Cargo Estatutario No Confiere Permisos Técnicos Automáticos:**  
   Conforme a la regla crítica del sistema legado, el cargo estatutario (`tipoSocio`) y la categoría (`ACTIVO` / `PASIVO`) son atributos institucionales del padrón. El control de acceso al software es gobernado exclusivamente por el rol RBAC asignado.
4. **Principio de Menor Privilegio por Defecto:**  
   Django REST Framework está configurado por defecto con `rest_framework.permissions.IsAuthenticated`. Ningún endpoint nuevo queda expuesto anónimamente salvo los mecanismos de autenticación pública (`/api/v1/auth/login/`, `/api/v1/auth/refresh/`).
5. **Diferenciación Semántica de Respuestas ante Falla de Seguridad:**
   * **`401 Unauthorized`:** Petición carente de credenciales JWT, token malformado, vencido o asociado a una cuenta con baja definitiva (`is_enabled=False`).
   * **`403 Forbidden`:** Usuario debidamente autenticado pero cuyo rol RBAC no cuenta con atribuciones para el módulo, o que habiendo sido recusado de un expediente específico intenta ejecutar una acción procesal vedada (`has_object_permission`).

---

## 2. Gobernanza de Roles Institucionales (6 Roles Vigentes)

En cumplimiento de los acuerdos del PO del 07/10/2026 y del Refinamiento de la MACRO-07, **se extingue formalmente la denominación `FISCALIZADORA` como rol RBAC vigente**, dividiéndose en dos roles independientes según su naturaleza estatutaria:

```
[ Antiguo Rol Legado ]
   FISCALIZADORA  ──────┬──►  REVISORES      (Revisores de Cuentas - Control de Legalidad)
                        └──►  AUTORIDAD_SC   (Presidentes/Vices Subcomisión y Líderes de Equipo)
```

| Rol RBAC | Actor Institucional | Atribuciones Procesales y Alcance Operativo |
| :--- | :--- | :--- |
| **`SOCIO`** | **Socio Ordinario** (ACT-01) | Acceso de solo lectura a su propio legajo, saldo histórico de puntos, causas donde figura como imputado o solicitante, reglamentos vigentes y calendario. Facultad operativa acotada a presentar o editar descargos (T02/T03) e interponer apelaciones procesales sobre sus expedientes dentro de los plazos reglamentarios. |
| **`AUTORIDAD_SC`** | **Autoridad de Subcomisión / Líder de Equipo** (ACT-04) | Autoridades ejecutivas de cada una de las 7 subcomisiones. Facultados para iniciar solicitudes disciplinarias T01 exclusivamente sobre integrantes de su propia subcomisión o equipo (Arts. 25 y 26 RPD), y gestionar integralmente los Eventos y Asistencias de su área. |
| **`REVISORES`** | **Revisores de Cuentas** (STK-06) | Órgano estatutario de fiscalización y legalidad. Facultados para auditar expedientes disciplinarios, examinar balances y promover de oficio solicitudes disciplinarias T01 de carácter institucional general (Arts. 22 y 23 RPD). Sin competencia en gestión de asistencias cotidianas. |
| **`CD`** | **Comisión Directiva** (ACT-03) | Órgano de conducción y gobierno ejecutivo de AVEIT. Facultados para iniciar solicitudes T01 de carácter general (Art. 21 RPD), administrar artículos de Reglamentos, convocar y gestionar Eventos y Asistencias institucionales, acceder al Ranking consolidado con visualización de alertas preventivas (-7 puntos) y cese estatutario (-10 puntos). |
| **`TD`** | **Miembro del Tribunal de Disciplina** (ACT-02) | Autoridad jurisdiccional colegiada de AVEIT. Acceso al tablero de los 6 estados procesales, sustanciación y deliberación de expedientes, calificación de descargos T02/T03, redacción, firma y emisión vinculante de Resoluciones, gestión de artículos de Reglamentos y supervisión de Eventos. |
| **`ADMIN`** | **Administrador de Cómputos** (ACT-05) | Soporte técnico, infraestructura, mantenimiento de variables de entorno, copias de seguridad de MySQL y monitoreo de logs de auditoría de seguridad. **Estrictamente neutral y delimitado:** no posee atribuciones funcionales para juzgar causas, deliberar votos, dictar sanciones ni alterar saldos de puntos o registrar asistencias. |

---

## 3. Mapeo de Cargos Estatutarios Legados (`socio_tipoSocio`)

El padrón histórico de AVEIT clasifica a los miembros bajo 15 identificadores estatutarios. La siguiente tabla establece la correspondencia formal y obligatoria para la migración de cuentas y asignación de roles RBAC:

| ID | Cargo Estatutario Legado | Rol RBAC Normativo | Justificación Institucional y Normativa |
| :---: | :--- | :---: | :--- |
| **1** | Presidente de Subcomisión | `AUTORIDAD_SC` | Conducción ejecutiva de subcomisión estatutaria (Art. 25 RPD). |
| **2** | Vicepresidente de Subcomisión | `AUTORIDAD_SC` | Autoridad ejecutiva adjunta de subcomisión (Art. 25 RPD). |
| **3** | Presidente de AVEIT | `CD` | Miembro titular del órgano directivo de AVEIT (Art. 21 RPD). |
| **4** | Vicepresidente de AVEIT | `CD` | Miembro titular del órgano directivo de AVEIT (Art. 21 RPD). |
| **5** | Tesorero | `CD` | Responsable económico-financiero de CD (Art. 21 RPD). |
| **6** | Protesorero | `CD` | Miembro directivo adjunto de Tesorería (Art. 21 RPD). |
| **7** | Secretario de Actas | `CD` | Custodio de libros de actas y gobierno formal (Art. 21 RPD). |
| **8** | Secretario General | `CD` | Máxima coordinación institucional de CD (Art. 21 RPD). |
| **9** | Prosecretario | `CD` | Coordinación adjunta de Secretaría (Art. 21 RPD). |
| **10** | Titular del Tribunal de Disciplina | `TD` | Magistrado titular con voz, voto y firma de resoluciones (Art. 12 RPD). |
| **11** | Suplente del Tribunal de Disciplina | `TD` | Magistrado suplente con facultades ante integración por apartamiento. |
| **12** | Socio Ordinario | `SOCIO` | Miembro sin cargos de conducción; sujeto al régimen ordinario. |
| **13** | Secretario | `CD` *(Con salvedad)* | **Asignado a CD según acuerdo de PO.** *Salvedad de auditoría:* en caso de detectarse durante la depuración del padrón histórico que el cargo corresponde a una secretaría de subcomisión específica, se ajustará caso por caso a `AUTORIDAD_SC`. |
| **14** | Revisor de Cuentas Titular | `REVISORES` | Titular del órgano de fiscalización y legalidad (Arts. 22 y 23 RPD). |
| **15** | Revisor de Cuentas Suplente | `REVISORES` | Suplente del órgano de fiscalización y legalidad (Arts. 22 y 23 RPD). |

---

## 4. Matriz Normativa de Acceso (Pantalla x Acción x Endpoint x Respuestas)

### Referencia de Códigos de Permiso en Tabla:
* **`AUTORIZADO`**: Acción y endpoint habilitados procesalmente.
* **`DENEGADO`**: Acción bloqueada en UI y rechazada por la API (`403 Forbidden`).
* **`401`**: Sin token válido o autenticación.
* **`403`**: Autenticado sin rol suficiente o inhibido por recusación.

---

### 4.1. Módulo: Autenticación, Sesión y Perfil Propio

| Pantalla / Módulo SPA | Acción UI | Roles Autorizados | Roles Denegados | Método y Endpoint REST | Falta Auth | Falta Permiso |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **Login** (`/login`) | Autenticarse | Todos (Público) | Ninguno | `POST /api/v1/auth/login/` | `401` | N/A |
| **Sesión Activa** | Refrescar Token JWT | Todos (con refresh token) | Cuentas `is_enabled=False` | `POST /api/v1/auth/refresh/` | `401` | `401` |
| **Perfil Propio** (Header) | Consultar identidad y rol | `SOCIO`, `AUTORIDAD_SC`, `REVISORES`, `CD`, `TD`, `ADMIN` | Anónimos | `GET /api/v1/auth/me/` | `401` | `403` |

---

### 4.2. Módulo: Mis Expedientes y Descargos (`/mis-expedientes`)

| Pantalla / Módulo SPA | Acción UI | Roles Autorizados | Roles Denegados | Método y Endpoint REST | Falta Auth | Falta Permiso |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **Mis Expedientes** | Ver causas propias | `SOCIO`, `AUTORIDAD_SC`, `REVISORES`, `CD`, `TD`, `ADMIN` | Anónimos | `GET /api/v1/expedientes/mis-expedientes/` | `401` | `403` |
| **Mis Solicitudes T01** | Ver T01 promovidos | `AUTORIDAD_SC`, `REVISORES`, `CD`, `TD` | `SOCIO`, `ADMIN` | `GET /api/v1/expedientes/mis-solicitudes/` | `401` | `403` |
| **Presentar / Editar Descargo** | Cargar o corregir T02/T03 | Solo el **Socio Imputado** titular/coimputado (en plazo) | Terceros ajenos al expediente | `POST /api/v1/expedientes/{id}/descargo/` | `401` | `403` |
| **Historial de Versiones** | Ver historial de su descargo | Socio Imputado y `TD` | Terceros | `GET /api/v1/expedientes/{id}/descargo/versiones/` | `401` | `403` |
| **Apelación de T01** | Interponer recurso (en plazo) | Solo el **Socio Imputado** sobre T01 | Terceros | `POST /api/v1/expedientes/{id}/apelacion/` | `401` | `403` |

---

### 4.3. Módulo: Reglamentos Institucionales (`/reglamentos`)

> [!IMPORTANT]
> **Restricción Expresa del PO:** Todos los roles pueden consultar el articulado vigente. La creación, modificación y baja queda restringida con exclusividad a `TD` y `CD`. Cómputos (`ADMIN`), `REVISORES`, `AUTORIDAD_SC` y `SOCIO` tienen prohibida toda acción mutativa.

| Pantalla / Módulo SPA | Acción UI | Roles Autorizados | Roles Denegados | Método y Endpoint REST | Falta Auth | Falta Permiso |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **Reglamentos** | Ver articulado vigente | `SOCIO`, `AUTORIDAD_SC`, `REVISORES`, `CD`, `TD`, `ADMIN` | Anónimos | `GET /api/v1/expedientes/reglamentos/` | `401` | `403` |
| **Artículos** | Buscar / Filtrar artículos | `SOCIO`, `AUTORIDAD_SC`, `REVISORES`, `CD`, `TD`, `ADMIN` | Anónimos | `GET /api/v1/expedientes/reglamentos/articulos/` | `401` | `403` |
| **Gestión Artículos** | Crear nuevo artículo | `TD`, `CD` | `ADMIN`, `REVISORES`, `AUTORIDAD_SC`, `SOCIO` | `POST /api/v1/expedientes/reglamentos/articulos/` | `401` | `403` |
| **Gestión Artículos** | Modificar artículo | `TD`, `CD` | `ADMIN`, `REVISORES`, `AUTORIDAD_SC`, `SOCIO` | `PUT /api/v1/expedientes/reglamentos/articulos/{id}/` | `401` | `403` |
| **Gestión Artículos** | Eliminar / Desactivar | `TD`, `CD` | `ADMIN`, `REVISORES`, `AUTORIDAD_SC`, `SOCIO` | `DELETE /api/v1/expedientes/reglamentos/articulos/{id}/` | `401` | `403` |

---

### 4.4. Módulo: Apertura de Causas / Formulario T01 (`/solicitar-puntos`)

| Pantalla / Módulo SPA | Acción UI | Roles Autorizados | Roles Denegados | Método y Endpoint REST | Falta Auth | Falta Permiso |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **Formulario T01** | Acceder a la pantalla | `AUTORIDAD_SC`, `REVISORES`, `CD`, `TD` | `SOCIO`, `ADMIN` | Sin endpoint directo (Guard Angular) | N/A | Redirige a 403 |
| **Búsqueda Select2** | Buscar socios imputados | `AUTORIDAD_SC`, `REVISORES`, `CD`, `TD` | `SOCIO`, `ADMIN` | `GET /api/v1/padron/socios/?search=...` | `401` | `403` |
| **Crear Solicitud T01** | Guardar borrador T01 | `AUTORIDAD_SC` *(su área)*, `REVISORES` *(inst.)*, `CD`, `TD` | `SOCIO`, `ADMIN` | `POST /api/v1/expedientes/` | `401` | `403` |
| **Emitir Solicitud T01** | Apertura formal procesal | `AUTORIDAD_SC`, `REVISORES`, `CD`, `TD` | `SOCIO`, `ADMIN` | `POST /api/v1/expedientes/{uuid}/emitir/` | `401` | `403` |
| **Notificar Apertura** | Despachar cédula inicial | `TD`, `CD` | `AUTORIDAD_SC`, `REVISORES`, `ADMIN`, `SOCIO` | `POST /api/v1/expedientes/{id}/despachar-notificacion/` | `401` | `403` |

---

### 4.5. Módulo: Gestión, Tablero y Sala del Tribunal (`/gestionar-expedientes`)

| Pantalla / Módulo SPA | Acción UI | Roles Autorizados | Roles Denegados | Método y Endpoint REST | Falta Auth | Falta Permiso |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **Tablero 6 Estados** | Ver Kanban de causas | `TD`, `CD` | `AUTORIDAD_SC`, `REVISORES`, `ADMIN`, `SOCIO` | `GET /api/v1/expedientes/board/` | `401` | `403` |
| **Listado General** | Ver nómina de expedientes | `TD`, `CD` | `AUTORIDAD_SC`, `REVISORES`, `ADMIN`, `SOCIO` | `GET /api/v1/expedientes/gestion/` | `401` | `403` |
| **Detalle Oficial TD** | Ver expediente completo | `TD`, `CD` | `AUTORIDAD_SC`, `REVISORES`, `ADMIN`, `SOCIO` | `GET /api/v1/expedientes/{id}/` | `401` | `403` |
| **Visor Autorizado** | Ver piezas y evidencias | `TD`, `CD` (Todos los exp.), `SOCIO` (Solo si es imputado) | Terceros ajenos al expediente | `GET /api/v1/expedientes/{id}/visor/` | `401` | `403` |
| **Adjuntar Evidencias** | Subir documentos probatorios | `TD`, `CD`, o **Socio Imputado** | Terceros ajenos al expediente | `POST /api/v1/expedientes/{id}/evidencia/` | `401` | `403` |
| **Descargar Evidencia** | Descargar archivo cifrado | Integrantes con permiso de Visor | Terceros ajenos | `GET /api/v1/expedientes/{id}/evidencia/{uuid}/` | `401` | `403` |
| **Transición de Estado** | Cambiar estado procesal | `TD` *(Exclusivo, no recusado)* | `CD`, `AUTORIDAD_SC`, `REVISORES`, `ADMIN`, `SOCIO` | `PATCH /api/v1/expedientes/{id}/transicionar/` | `401` | `403` |
| **Evaluar Causal T02** | Calificar justificativo T02 | `TD` *(Exclusivo, no recusado)* | `CD`, `AUTORIDAD_SC`, `REVISORES`, `ADMIN`, `SOCIO` | `POST /api/v1/expedientes/{id}/descargos/{d_id}/decisiones/` | `401` | `403` |
| **Adecuación T01** | Dictaminar adecuación | `TD` *(Exclusivo, no recusado)* | Todos los demás roles | `POST /api/v1/expedientes/{id}/adecuaciones/` | `401` | `403` |
| **Composición TD** | Designar suplente/apartar | `TD`, `CD` | `AUTORIDAD_SC`, `REVISORES`, `ADMIN`, `SOCIO` | `POST /api/v1/expedientes/{id}/composicion/` | `401` | `403` |
| **Resolución (Borrador)**| Redactar dictamen unificado| `TD` *(Exclusivo, no recusado)* | Todos los demás roles | `POST /api/v1/expedientes/{id}/resolucion/` | `401` | `403` |
| **Firma de Resolución** | Suscribir formalmente | Miembros intervinientes del `TD` | Quien no integra la sala o fue recusado | `POST /api/v1/expedientes/{id}/resolucion/firmar/` | `401` | `403` |
| **Emitir Resolución** | Publicar y acreditar puntos | `TD` *(Exclusivo con quorum)* | Todos los demás roles | `POST /api/v1/expedientes/{id}/resolucion/emitir/` | `401` | `403` |

---

### 4.6. Módulo: Eventos y Asistencia (`/eventos-asistencia` y `/eventos`)

> [!IMPORTANT]
> **Restricción Expresa del PO:** Acceso habilitado exclusivamente a `CD`, `TD` y `AUTORIDAD_SC`. Quedan estrictamente excluidos `ADMIN` (Cómputos), `REVISORES` y `SOCIO`. La SPA debe bloquear la ruta y el menú; la API debe rechazar con `403 Forbidden`.

| Pantalla / Módulo SPA | Acción UI | Roles Autorizados | Roles Denegados | Método y Endpoint REST | Falta Auth | Falta Permiso |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **Eventos & Asistencia**| Acceder a la pantalla | `CD`, `TD`, `AUTORIDAD_SC` | `ADMIN`, `REVISORES`, `SOCIO` | Sin endpoint directo (Guard Angular) | N/A | Redirige a 403 |
| **Nómina de Eventos** | Listar eventos | `CD`, `TD`, `AUTORIDAD_SC` | `ADMIN`, `REVISORES`, `SOCIO` | `GET /api/v1/eventos/` | `401` | `403` |
| **Detalle de Evento** | Ver asistentes y estado | `CD`, `TD`, `AUTORIDAD_SC` | `ADMIN`, `REVISORES`, `SOCIO` | `GET /api/v1/eventos/{id}/` | `401` | `403` |
| **Crear Evento** | Programar actividad/reunión | `CD`, `TD`, `AUTORIDAD_SC` *(área)* | `ADMIN`, `REVISORES`, `SOCIO` | `POST /api/v1/eventos/` | `401` | `403` |
| **Editar Evento** | Reprogramar / Modificar | `CD`, `TD`, `AUTORIDAD_SC` *(área)* | `ADMIN`, `REVISORES`, `SOCIO` | `PUT /api/v1/eventos/{id}/` | `401` | `403` |
| **Anular Evento** | Cancelar convocatoria | `CD`, `TD`, `AUTORIDAD_SC` *(área)* | `ADMIN`, `REVISORES`, `SOCIO` | `DELETE /api/v1/eventos/{id}/` | `401` | `403` |
| **Carga de Asistencia** | Registrar presentes/ausentes| `CD`, `TD`, `AUTORIDAD_SC` *(área)* | `ADMIN`, `REVISORES`, `SOCIO` | `POST /api/v1/eventos/{id}/asistencias/` | `401` | `403` |
| **Procesar Asistencias**| Aplicar 3:1 y aperturas | `CD`, `TD`, `AUTORIDAD_SC` | `ADMIN`, `REVISORES`, `SOCIO` | `POST /api/v1/eventos/{id}/procesar-asistencias/`| `401`| `403` |

---

### 4.7. Módulo: Ranking de Socios y Libro Mayor (`/ranking-socios`)

> [!NOTE]
> **Directiva del PO:** El socio ordinario puede ver la tabla con su saldo en números de colores y ordenarla libremente. Se eliminan chips de pautas reglamentarias, "Habilitado Regular" y botones "Mayor sanción". El ranking es de acceso institucional general para socios autenticados.

| Pantalla / Módulo SPA | Acción UI | Roles Autorizados | Roles Denegados | Método y Endpoint REST | Falta Auth | Falta Permiso |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **Ranking General** | Ver tabla y ordenar columnas| `SOCIO`, `AUTORIDAD_SC`, `REVISORES`, `CD`, `TD`, `ADMIN` | Anónimos | `GET /api/v1/ranking/` | `401` | `403` |
| **Alertas de Umbral** | Alertas de -7 y -10 puntos | `CD`, `TD` | `SOCIO`, `AUTORIDAD_SC`, `REVISORES`, `ADMIN` | Incluido en DTO de gestión | N/A | Oculto en UI |
| **Detalle de Puntos** | Ver movimientos de un socio | `TD`, `CD`, `REVISORES` | `SOCIO` (de terceros), `ADMIN` | `GET /api/v1/expedientes/socios/{id}/apercibimientos/`| `401`| `403` |

---

### 4.8. Módulo: Calendario Institucional (`/calendario-institucional`)

| Pantalla / Módulo SPA | Acción UI | Roles Autorizados | Roles Denegados | Método y Endpoint REST | Falta Auth | Falta Permiso |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **Calendario** | Consultar días hábiles | `SOCIO`, `AUTORIDAD_SC`, `REVISORES`, `CD`, `TD`, `ADMIN` | Anónimos | `GET /api/v1/expedientes/calendario/feriados/` | `401` | `403` |
| **Cálculo de Plazos** | Calcular vencimiento hábil | `SOCIO`, `AUTORIDAD_SC`, `REVISORES`, `CD`, `TD`, `ADMIN` | Anónimos | `GET /api/v1/expedientes/calendario/calcular-plazo/` | `401` | `403` |
| **Parámetros Feriados** | Configurar feriados | `ADMIN`, `CD`, `TD` | `SOCIO`, `AUTORIDAD_SC`, `REVISORES` | `POST /api/v1/expedientes/calendario/feriados/` | `401` | `403` |

---

### 4.9. Módulo: Reportes y Balances (`/reportes`)

> [!NOTE]
> **Directiva del PO:** El módulo se encuentra temporalmente en pausa hasta definir con el Tribunal de Disciplina los indicadores exactos requeridos. Normativamente se delimita su acceso para evitar filtraciones de datos sensibles.

| Pantalla / Módulo SPA | Acción UI | Roles Autorizados | Roles Denegados | Método y Endpoint REST | Falta Auth | Falta Permiso |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **Reportes & Balance** | Acceder a la pantalla | `TD`, `CD`, `REVISORES` | `SOCIO`, `AUTORIDAD_SC`, `ADMIN` | Sin endpoint directo (Guard Angular) | N/A | Redirige a 403 |
| **Métricas T01** | Consultar estadísticas T01 | `TD`, `CD`, `REVISORES` | `SOCIO`, `AUTORIDAD_SC`, `ADMIN` | `GET /api/v1/expedientes/reportes/t01/` | `401` | `403` |
| **Métricas Asistencias**| Estadísticas de asistencia | `TD`, `CD`, `REVISORES` | `SOCIO`, `AUTORIDAD_SC`, `ADMIN` | `GET /api/v1/expedientes/reportes/reuniones/` | `401` | `403` |
| **Exportar CSV** | Descargar balance auditable | `TD`, `CD`, `REVISORES` | `SOCIO`, `AUTORIDAD_SC`, `ADMIN` | `GET /api/v1/expedientes/reportes/exportar-csv/` | `401` | `403` |

---

### 4.10. Módulo: Despacho y Cola de Notificaciones (`notifications`)

| Pantalla / Módulo SPA | Acción UI | Roles Autorizados | Roles Denegados | Método y Endpoint REST | Falta Auth | Falta Permiso |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **Disparo Interno** | Encolar email transaccional | Servicios de dominio backend | Llamadas directas de clientes | `POST /api/v1/notifications/email/` | `401` | `403` (Solo API interna / Celery) |
| **Reintento de Cola** | Forzar reintento manual | `ADMIN` (Cómputos) | `SOCIO`, `AUTORIDAD_SC`, `REVISORES`, `CD`, `TD` | `POST /api/v1/notifications/email/retry/` | `401` | `403` |

---

## 5. Perspectiva Inversa: Resumen de Atribuciones por Rol

```
                  ┌──────────────────────────────────────────────┐
                  │                 SOCIO                        │
                  │  - Consulta causas propias y presenta T02/T03│
                  │  - Solo lectura: Ranking, Reglam., Calendario│
                  └──────────────────────┬───────────────────────┘
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
   ┌───────────────────────────┐                   ┌───────────────────────────┐
   │       AUTORIDAD_SC        │                   │         REVISORES         │
   │ - Solicitudes T01 su área │                   │ - Auditoría de causas     │
   │ - Gestión Eventos de área │                   │ - Apertura T01 instituc.  │
   │ - Sin acceso a Sala TD    │                   │ - Excluido de Eventos     │
   └─────────────┬─────────────┘                   └─────────────┬─────────────┘
                 │                                               │
                 └───────────────────────┬───────────────────────┘
                                         ▼
   ┌───────────────────────────────────────────────────────────────────────────┐
   │                                  CD                                       │
   │ - Gobierno institucional y apertura de T01 general (Art. 21)              │
   │ - Gestión de Eventos y Asistencias de AVEIT                               │
   │ - Edición de Reglamentos institucionales y alertas de saldos (-7 / -10)   │
   └─────────────────────────────────────┬─────────────────────────────────────┘
                                         ▼
   ┌───────────────────────────────────────────────────────────────────────────┐
   │                                  TD                                       │
   │ - Plenas facultades jurisdiccionales y tablero de los 6 estados procesales│
   │ - Calificación de descargos T02/T03, redacción, firma y emisión de Fallos │
   │ - Edición de Reglamentos, supervisión de eventos y cómputo de sanciones   │
   └───────────────────────────────────────────────────────────────────────────┘
   ┌───────────────────────────────────────────────────────────────────────────┐
   │                             ADMIN (CÓMPUTOS)                              │
   │ - Infraestructura, backups MySQL, variables de entorno y logs de auditoría│
   │ - ESTRICTAMENTE NEUTRAL: Sin facultades procesales, sin juzgamiento ni    │
   │   alteración de puntos o registro de asistencias.                         │
   └───────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Estados Operativos y Control de Acceso por Objeto

### 6.1. Cuenta Deshabilitada / Cesantía (`is_enabled=False`) vs. `Socio Suspendido`
Conforme al acuerdo de refinamiento con el PO:
* **`is_enabled=False` (Cesanteado / Expulsado / Baja definitiva):** Se produce el bloqueo integral de credenciales. La API rechaza cualquier intento de login o invocación con `401 Unauthorized`. La cuenta no tiene acceso alguno al software.
* **`Socio Suspendido` (Sanción procesal temporal o límite de puntos):** El socio **mantiene acceso a la SPA en modo solo lectura a `/mis-expedientes`**, a efectos de conocer el estado de sus causas, leer la resolución sancionatoria y ejercer su derecho constitucional de apelación dentro del plazo legal. Se bloquea cualquier otra acción activa en el sistema.

### 6.2. Recusación o Apartamiento de Miembro del Tribunal (`has_object_permission`)
En concordancia con el Art. 95 del Estatuto de AVEIT, Art. 24 del RPD y la Spec 007 (`specs/007-apartamiento-suplencia/`):
* Si un miembro titular o suplente del Tribunal de Disciplina resulta imputado, solicitante o manifiesta conflicto de interés en un expediente determinado, se activa la inhibición a nivel de objeto (`IsNotInvolvedInExpediente`).
* **Permiso concedido:** Mantiene visibilidad de **solo lectura** en el Visor de la causa (`GET /api/v1/expedientes/{id}/visor/`), para garantizar la transparencia procesal.
* **Prohibición absoluta (`403 Forbidden`):** Queda estrictamente inhabilitado para votar, suscribir resoluciones (`POST /resolucion/firmar/`), transicionar el expediente (`PATCH /transicionar/`) o calificar causales de descargo. Dichas facultades se transfieren al suplente legalmente incorporado.

---

## 7. Brecha de Implementación (Gap Analysis: Normativa vs. Código Actual)

Para guiar la ejecución de la subtarea técnica [SCRUM-122](https://aveit.atlassian.net/browse/SCRUM-122) sin introducir desvíos ni alterar código prematuramente, se detallan las discrepancias identificadas entre esta matriz normativa y el estado del repositorio:

| Componente | Estado Actual en Código | Requisito Normativo Aprobado por el PO | Acción Requerida en SCRUM-122 |
| :--- | :--- | :--- | :--- |
| **Enum de Roles** | `Role` en `backend/socios/models.py` posee `FISCALIZADORA`. | Se divide en `REVISORES` y `AUTORIDAD_SC`. `FISCALIZADORA` se extingue. | Migración de datos y esquema en Django (`Role.TextChoices`). |
| **Permiso Reglamentos** | `CanManageReglamentos` incluye `Role.ADMIN`. | Creación y edición exclusiva de `TD` y `CD`. `ADMIN` es solo lectura. | Remover `ADMIN` de `CanManageReglamentos.allowed_roles`. |
| **Permiso Eventos** | `CanManageEventos` incluye `Role.ADMIN` y `Role.FISCALIZADORA`. `list` y `retrieve` son públicos autenticados. | Exclusivo `CD`, `TD` y `AUTORIDAD_SC`. `ADMIN`, `REVISORES` y `SOCIO` excluidos. | Reemplazar `allowed_roles` y proteger `get_permissions` completo. |
| **Cargos Estatutarios** | `backend/accounts/legacy_rbac.py` deja 13, 14 y 15 sin mapear. | Cargos 1 y 2 $\rightarrow$ `AUTORIDAD_SC`; 14 y 15 $\rightarrow$ `REVISORES`; 13 $\rightarrow$ `CD`. | Actualizar `LEGACY_POSITION_TO_ROLE` en código y tests de migración. |
| **Frontend 403** | Redirección estándar a login o notificación transitoria. | Vista dedicada de pantalla completa "Acceso Denegado" con botón a `/mis-expedientes`. | Crear componente Angular para error 403 y actualizar Guards. |
| **Recusación TD** | `IsNotInvolvedInExpediente` bloquea todo acceso si está involucrado. | Permite lectura en Visor; solo bloquea acciones de voto, firma y resolución. | Separar validación en `has_object_permission` diferenciando métodos `SAFE_METHODS`. |
