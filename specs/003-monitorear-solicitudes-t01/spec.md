# Spec 003 — Monitorear expedientes y solicitudes iniciadas (Mis Solicitudes T01) - SCRUM-75 / PB-04

## Contexto y objetivo
Permitir que las autoridades institucionales con competencia para iniciar solicitudes de puntos y aperturas disciplinarias (Comisión Directiva - CD, Tribunal de Disciplina - TD, y Comisión Fiscalizadora / Subcomisiones) monitoreen el estado procesal y resolución final de sus solicitudes T01 desde la interfaz de usuario, preservando con estricta confidencialidad las deliberaciones internas y votos nominales del TD.

Referencia Jira: [SCRUM-75](https://guillenmartin94.atlassian.net/browse/SCRUM-75) (Épica [SCRUM-29](https://guillenmartin94.atlassian.net/browse/SCRUM-29) EP-02: Apertura y ciclo procesal del expediente).

## Historia de Usuario
**Como** autoridad solicitante (CD / TD / Subcomisión / Fiscalizadora),  
**quiero** consultar la lista y el estado procesal de las solicitudes y expedientes que inicié mediante el Formulario T01,  
**para** monitorear el avance de las solicitudes sin acceder a la deliberación interna reservada del TD.

## Criterios de Aceptación
- **CA1 (Aislamiento de Creador):** Filtra exclusivamente por solicitudes y expedientes donde el usuario autenticado es el creador/solicitante (`solicitante_id == request.user.socio.id`). Ninguna autoridad puede consultar las solicitudes iniciadas por otra.
- **CA2 (Datos Visibles):** Muestra número de expediente/solicitud, fecha de inicio/emisión, socios involucrados (legajo, nombre, subcomisión), título/motivo, causal reglamentaria, estado procesal actualizado y resolución final si está emitida.
- **CA3 (Confidencialidad Estricta del TD):** No expone bajo ningún concepto notas de deliberación interna, votos nominales en curso, proyectos de dictamen ni borradores reservados del Tribunal de Disciplina.
- **CA4 (Control de Acceso RBAC):** Acceso restringido exclusivamente a integrantes habilitados para emitir T01 (`CanCreateT01`: roles `CD`, `TD`, `FISCALIZADORA`). Rechazo con HTTP 403 Forbidden para socios ordinarios.
- **CA5 (Interfaz Responsive e Interacciones):** Panel integrado en `/solicitar-puntos` ("Crear Expediente") con buscador reactivo por texto y filtro por estado.
  - Para borradores (`DRAFT`): opciones de continuar edición en el formulario interactivo o descartar/eliminar borrador.
  - Para emitidos (`ISSUED`): botón para consultar detalle completo en modal de lectura.
- **Vinculación Transaccional:** Al emitir la solicitud T01 (`ISSUED`), se crea atómicamente el `Expediente` en estado `creado` mediante `ExpedienteWorkflowService.open_expediente` y se vincula bidireccionalmente para dar inicio al ciclo procesal del Art. 12.
