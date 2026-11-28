# Registro de Decisiones de Arquitectura (ADR) — SGD-AVEIT

Este directorio contiene el registro cronológico y formal de las Decisiones Arquitectónicas de Relevancia (**Architectural Decision Records - ADR**) adoptadas para la plataforma del Sistema de Gestión Disciplinaria de la Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos (**SGD-AVEIT**).

Cada ADR documenta una decisión técnica crítica, sus motivaciones normativas e ingenieriles, las alternativas descartadas y sus consecuencias operativas.

---

## Índice de Decisiones

| Identificador | Título | Fecha | Estado | Trazabilidad Jira |
| :---: | :--- | :---: | :---: | :---: |
| [**ADR-001**](ADR-001-consumo-padron-institucional.md) | Estrategia de Consumo del Padrón Institucional y Capa Anticorrupción de Sólo Lectura | 2026-09-19 | **Aceptado** | `SCRUM-37` (`S1-04`) |

> **Nota de decisiones arquitectónicas implementadas posteriormente (sin archivo ADR individual; documentadas en sus `specs/*/plan.md`):**
> - Patrón Transactional Outbox de notificaciones (`backend/notifications/models.py`: `EmailOutbox`, `EmailAttachment`).
> - Patrón Strategy de asistencia y acumulación 3:1 (`specs/005-sanciones-reuniones-solicitudes/plan.md`).
> - Eliminación de votación nominal y adopción de firma colegiada en `Resolucion.firmantes` (`specs/010-circuito-resolutivo-enmiendas/plan.md`).
> - Libro mayor inmutable `InsertOnly` (`AsientoLibroMayor` + `PuntajeAplicado`) (`specs/011-libro-mayor-mis-expedientes-publicacion/plan.md`).
> - Panel de Administración auditable de parámetros y miembros TD (`specs/012-panel-administracion/plan.md`).

---

## Estructura de un ADR

Cada documento adhiere a la estructura simplificada del estándar internacional **MADR (Markdown Architectural Decision Records)**:
1. **Contexto y Planteo del Problema:** Fuerzas en juego y restricciones normativas.
2. **Fuerzas Impulsoras (Decision Drivers):** Principios que guían la resolución.
3. **Alternativas Evaluadas:** Opciones analizadas con justificación explícita de descarte.
4. **Decisión Adoptada:** Arquitectura, patrones de diseño y esquemas aprobados.
5. **Estrategia de Observabilidad y Resiliencia:** Tolerancia a fallos y monitoreo.
6. **Consecuencias:** Beneficios obtenidos y trade-offs aceptados con mitigación.
7. **Registro de Aprobaciones:** Firma y homologación formal de roles responsables (Dev, Product Owner, Cátedra).
