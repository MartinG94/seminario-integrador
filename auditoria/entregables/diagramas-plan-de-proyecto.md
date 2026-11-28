# Diagramas Requeridos — Plan de Proyecto (`SGD-AVEIT`)

> **Entregable:** `C:\Users\terza\Desktop\workshop\Seminario\Documentación Actual Humana\Entregables\02_Plan_de_Proyecto_SGD_AVEIT.html`  
> **Versión:** `v2.1.0` (`28/11/2026`)  
> **Criterio:** No se incluyeron diagramas inline ni aproximaciones en texto; cada figura figura en el documento con su marcador `[DIAGRAMA: nombre]` para ser insertada como imagen exportada en alta resolución.

| # | Marcador en el documento | Ubicación | Propósito visual | Fuente recomendada para generarlo |
|---|---|---|---|---|
| 1 | `[DIAGRAMA: Flujo de trabajo Scrumban y entregas incrementales]` | §5 · Pág. 5 (Figura 1) | Mostrar el flujo del tablero Scrumban (Backlog → In Progress [WIP ≤ 4] → Peer Code Review [WIP ≤ 3] → Testing [WIP ≤ 3] → Done), ceremonias quincenales y corte de entregas (MVP en Sprint 2 + Releases). | `docs/gestion-proyecto/Seguimiento de Proyecto.md` (§2.1.1 y §2.1.3) y tablero Jira del equipo. |
| 2 | `[DIAGRAMA: Arquitectura de integración y capa anticorrupción con padrón legado MySQL]` | §11.1 · Pág. 14 (Figura 2) | Ilustrar la arquitectura de monolito modular contenerizado (Docker Compose): SPA Angular 14.2+ (Material) → API REST Django 4.2 LTS / DRF (JWT + RBAC) → Capa Anticorrupción Read-Only hacia tablas legadas MySQL + tablas propias de dominio (Libro Mayor InsertOnly, Evidencias, Outbox SMTP). | `docs/arquitectura/` y estructura real de módulos (`backend/padron/`, `backend/accounts/`, `backend/expedientes/`, `backend/ranking/`, `backend/notifications/`, `docker-compose.yml`). |
| 3 | `[DIAGRAMA: Cronograma macro e hitos de entregas incrementales]` | §12 · Pág. 16 (Figura 3) | Visualizar el roadmap adaptable del segundo cuatrimestre 2026 (Sprint 0 → Sprint 1–2 Corte MVP → Sprint 3 Release 2 → Sprint 4 Release 3 → Release 4 / Evolución) alineado al calendario de cátedra. | `docs/gestion-proyecto/Seguimiento de Proyecto.md` (Story Map y Roadmap adaptable) y §7 / §12 de este Plan de Proyecto. |
