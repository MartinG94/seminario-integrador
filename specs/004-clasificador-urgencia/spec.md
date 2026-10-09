# Spec 004 — Clasificador e Indicador Visual de Urgencia en Expedientes (SCRUM-78 / S3-07)

## Contexto y Objetivo

Permitir que el Tribunal de Disciplina (TD) y las autoridades clasifiquen y visualicen el nivel de urgencia (`Baja`, `Normal`, `Urgente`) de las causas disciplinarias y de mérito, tanto en el modelo de dominio, API REST, tarjetas del tablero Kanban y tabla densa de *Gestionar Expedientes*, para priorizar la sustanciación de causas críticas y de gravedad institucional.

- **Referencia Jira:** [SCRUM-78](https://guillenmartin94.atlassian.net/browse/SCRUM-78) (S3-07).
- **Referencia Rectoral:** [Notas del PO (07/10/2026, Sección 2: Gestión y Tablero de Expedientes)](../../docs/gestion-proyecto/notasPO.md).
- **Sistema de Diseño:** [DESIGN.md](../../DESIGN.md) (Material Dashboard PRO Angular 2 / WCAG 2.2 AA).

---

## Historia de Usuario

**Como** integrante del Tribunal de Disciplina (TD) o autoridad habilitada,  
**quiero** clasificar y visualizar de forma inmediata el nivel de urgencia de los expedientes disciplinarios mediante badges semánticos en el tablero Kanban y en la grilla de causas,  
**para** priorizar la resolución y tratamiento de aquellas causas graves o que requieren intervención procesal urgente.

---

## Requisitos en Notación EARS

1. **Ubiquitous (Atributo de Dominio):**  
   El sistema *debe* mantener un atributo de urgencia procesal (`urgencia`) en el modelo `Expediente`, restringido estrictamente a los valores canónicos: `baja` (Baja), `normal` (Normal) y `urgente` (Urgente), con valor por defecto `normal`.

2. **Event-driven (Visualización en Tarjetas Kanban):**  
   CUANDO el usuario consulte el tablero Kanban de estados procesales,  
   el sistema *debe* renderizar en cada tarjeta un indicador visual (badge semántico) con el nivel de urgencia y su respectivo icono accesible:
   - `urgente`: Badge rojo de peligro (`badge-mat-danger` con token `{colors.danger}`, icono `priority_high` o `bolt`).
   - `normal`: Badge azul/informativo (`badge-mat-info` con token `{colors.info}`).
   - `baja`: Badge verde/atenuado (`badge-mat-success` con token `{colors.success}`).

3. **Event-driven (Visualización y Orden en Grilla Tabular):**  
   CUANDO el usuario acceda a la vista de tabla en *Gestionar Expedientes*,  
   el sistema *debe* incluir una columna explícita "Urgencia" con su badge semántico correspondiente, permitiendo ordenamiento bidireccional (ascendente/descendente) por dicho criterio.

4. **Event-driven (Filtrado por Urgencia):**  
   CUANDO el usuario seleccione un nivel de urgencia en la barra de herramientas de filtros,  
   el sistema *debe* filtrar sincrónica y reactivamente las causas mostradas tanto en el tablero Kanban como en la tabla de datos, soportando el parámetro `urgencia` en el endpoint `/api/v1/expedientes/board/` y `/api/v1/expedientes/`.

5. **Event-driven (Actualización de Urgencia por el TD):**  
   CUANDO un usuario autenticado con rol `TD` o `ADMIN` actualice la urgencia de un expediente (a través del endpoint `PATCH /api/v1/expedientes/<id>/` o desde el modal de detalle del expediente),  
   el sistema *debe* validar el nuevo nivel, persistir el cambio en la base de datos y devolver la representación actualizada. Usuarios sin permisos de gestión del TD verán rechazada la modificación con HTTP 403 Forbidden.

6. **State-driven (Priorización en Tarjetas Urgentes):**  
   MIENTRAS una causa se encuentre clasificada como `urgente`,  
   su tarjeta Kanban *debe* contar con un destacado visual perceptible (borde o acento de advertencia) para facilitar el escaneo visual rápido en el tablero colegiado.

---

## Criterios de Aceptación (DoD)

- [x] **CA1 (Persistencia y Migración):** Campo `urgencia` agregado en `Expediente` con choices `baja`, `normal`, `urgente` e índice en base de datos. Migración generada y aplicable sin pérdida de datos.
- [x] **CA2 (API REST y Serialización):** `BoardExpedienteSerializer` y `ExpedienteListSerializer` exponen `urgencia` y `urgencia_display`. El endpoint `PATCH /api/v1/expedientes/<id>/` permite modificar la urgencia validando roles (`IsTribunalOrDirectiva`).
- [x] **CA3 (Filtro en Backend y Frontend):** `ExpedienteFilter` soporta `urgencia`. En la UI de *Gestionar Expedientes*, la barra de filtros incluye selector de urgencia sincronizado con el backend y con fallback en memoria.
- [x] **CA4 (Indicadores Visuales en Kanban y Tabla):** Badges semánticos según tokens de `DESIGN.md` renderizados en las tarjetas del Kanban y en la grilla tabular con ordenamiento por columna.
- [x] **CA5 (Modal de Detalle y Edición TD):** El modal de detalle del expediente exhibe la urgencia y permite a los integrantes del TD actualizarla directamente con feedback visual inmediato.
- [x] **CA6 (Tests Automatizados en Verde):** Tests unitarios y de integración de backend (`pytest`) y tests unitarios de frontend (`Karma`) pasando al 100% con 0 errores.
