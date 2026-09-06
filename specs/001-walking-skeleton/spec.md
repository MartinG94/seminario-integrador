# Spec 001 — Walking Skeleton: Autenticación, Roles RBAC, Padrón y Ranking Oficial de Puntos

## Contexto y objetivo
Establecer la base arquitectónica operativa del sistema SGD-AVEIT y la primera integración punta a punta (*Walking Skeleton*) entre la base de datos MySQL, el backend en Django REST Framework y la SPA en Angular 14. Resuelve la autenticación unificada de la masa societaria y autoridades, el control de acceso basado en roles (RBAC) y la consulta transparente del ranking oficial de puntos (+/-) y legajo disciplinario de los ~515 socios activos de AVEIT.

## Usuarios / actores
- **Socio Activo (Junior / Senior):** Consulta su perfil, categoría social y posición en el ranking.
- **Tribunal de Disciplina (TD):** Accede al ranking completo con filtros por subcomisión y al buscador de legajos.
- **Comisión Directiva (CD):** Supervisa el estado de puntos de la totalidad del padrón.
- **Administrador de Cómputos:** Gestiona credenciales y roles iniciales.

## Historias de usuario
- **US-01:** Como socio o autoridad de AVEIT, quiero autenticarme con mis credenciales institucionales y que el sistema identifique mi rol y categoría estatutaria (Junior/Senior), para acceder de forma segura a las funciones que me competen.
- **US-02:** Como integrante del TD o CD, quiero consultar el ranking oficial consolidado de puntos (+/-) de los ~515 socios filtrando por categoría y subcomisión, para auditar el desempeño disciplinario y de méritos.
- **US-03:** Como miembro del TD o CD, quiero buscar a cualquier socio por nombre, apellido, legajo o subcomisión y visualizar su legajo integral, para acceder de inmediato a sus antecedentes y saldo neto.
- **US-04:** Como socio activo, quiero visualizar mi posición personal en el ranking y verificar mi saldo neto acumulado de puntos.

## Requisitos funcionales (criterios de aceptación en EARS)
- **RF-01-WS:** CUANDO un usuario envía credenciales válidas (legajo/email y contraseña) al endpoint de autenticación, EL SISTEMA genera un par de tokens JWT (access y refresh) y retorna el perfil de usuario con su rol RBAC y categoría social (Junior/Senior).
- **RF-02-WS:** SI las credenciales son inválidas o la cuenta se encuentra inactiva, ENTONCES EL SISTEMA rechaza la autenticación retornando código HTTP 401 Unauthorized sin revelar el motivo específico de rechazo.
- **RF-03-WS:** MIENTRAS un usuario mantenga una sesión autenticada con rol `TD`, `CD` o `ADMIN`, EL SISTEMA permite consultar la nómina completa del padrón ordenada por saldo neto de puntos (+/-) con paginación y filtros por subcomisión y categoría (Junior/Senior).
- **RF-04-WS:** CUANDO se ejecuta una búsqueda por texto en el legajo de socios (nombre, apellido o número de legajo), EL SISTEMA devuelve las coincidencias en menos de 500 ms con coincidencia insensible a mayúsculas y acentos.
- **RF-05-WS:** SI un socio con rol estándar intenta acceder a vistas o endpoints de administración reservados al TD o CD, ENTONCES EL SISTEMA deniega el acceso con código HTTP 403 Forbidden.
- **RF-06-WS:** EL SISTEMA garantiza la unicidad del número de legajo y calcula el saldo neto de puntos mediante agregación transaccional sobre el histórico de sanciones y premios aprobados.

## Requisitos no funcionales
- **RNF-01 (Performance):** Tiempo de respuesta del endpoint de ranking <= 500 ms (P95) con carga completa del padrón.
- **RNF-02 (Usabilidad Mobile-First):** La tabla de ranking y la tarjeta de perfil deben adaptarse fluidamente a viewports de 360px a 414px sin desborde horizontal.
- **RNF-04 (Seguridad):** Autenticación mediante tokens JWT con expiración de 60 minutos para access token y hashing seguro de contraseñas con Argon2 o PBKDF2.

## Casos límite
- **Búsqueda sin coincidencias:** Debe mostrar un estado vacío informativo con diseño AVEIT ("No se encontraron socios para el criterio especificado").
- **Empates en puntaje:** Ordenamiento secundario determinista por apellido y nombre en orden alfabético.
- **Socios sin sanciones ni premios:** Saldo neto neutro `0.0` puntos con distintivo visual estándar.
- **Caracteres con diacríticos:** Búsqueda tolerante a acentos (ej. "Sanchez" encuentra "Sánchez").

## Fuera de alcance
- Tramitación o creación de solicitudes T01 con hoja de anexo (corresponde a Spec 002 / Sprint 2).
- Presentación de descargos T02 y T03 (corresponde a Spec 003 / Sprint 3).
- Sesiones de deliberación y votación del TD (corresponde a Spec 004 / Sprint 4).

## Criterios de finalización
1. 100% de los requisitos funcionales (RF-01-WS a RF-06-WS) con pruebas unitarias y de integración pasando en verde (`pytest`).
2. Pruebas de componentes en Angular pasando exitosamente (`ng test`).
3. Demostración manual completa del flujo: Login -> Vista de Ranking con filtros -> Detalle de Legajo.
