# Inventario de Auditoría — Grupo `repo-auxiliar`

> **Modo de relevamiento:** Solo lectura sobre código, git y `auditoria/registro-canonico.md`.  
> **Archivos auditados:** 6 (alcance exacto del grupo `repo-auxiliar`).

---

## Resumen rápido

| Archivo | Líneas | Última mod. | Clasificación | Quién lo lee | Si desaparece |
|---|---:|---|---|---|---|
| `.github/ISSUE_TEMPLATE/reporte_incidencia.md` | 24 | 2026-09-06 | 4. Vigente | Equipo | Nada |
| `.github/ISSUE_TEMPLATE/tarea_sprint.md` | 21 | 2026-09-06 | 3. Redundante / incompleto | Equipo | Nada |
| `backend/README.md` | 82 | 2026-09-19 | 3. Incompleto | Equipo / Cátedra | Alguien se equivoca |
| `frontend/CHANGELOG.md` | 151 | 2026-09-06 | 1. Residuo de fabricación | Nadie | Nada |
| `frontend/LICENSE.md` | 21 | 2026-09-06 | 4. Vigente (2. Pocas líneas — aviso legal MIT) | Nadie / Auditoría legal | Alguien se equivoca |
| `frontend/README.md` | 251 | 2026-09-26 | 1. Residuo de fabricación | Nadie / Equipo | Nada |

---

## 1. `.github/ISSUE_TEMPLATE/reporte_incidencia.md`

- **Ruta:** `.github/ISSUE_TEMPLATE/reporte_incidencia.md`
- **Líneas:** 24
- **Última modificación:** `2026-09-06`
- **Tema que cubre:** Plantilla de GitHub Issues para reportar defectos o comportamientos anómalos en SGD-AVEIT.
- **Quién lo lee:** equipo.
- **Qué pasa si desaparece:** nada.
- **Clasificación:** `4. Vigente` (archivo breve de 24 líneas; no contiene información errónea respecto del stack actual `Backend / Frontend Angular / Base de Datos / Docker`, aunque al borrarlo no se rompe nada ni nadie se equivoca porque GitHub permite crear issues sin plantilla y la gestión de sprints corre en Jira).
- **Contradicciones con el registro:** Ninguna.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:** Ninguna.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:** Ninguna.
- **Referencias rotas:** Ninguna.

---

## 2. `.github/ISSUE_TEMPLATE/tarea_sprint.md`

- **Ruta:** `.github/ISSUE_TEMPLATE/tarea_sprint.md`
- **Líneas:** 21
- **Última modificación:** `2026-09-06`
- **Tema que cubre:** Plantilla de GitHub Issues para crear tareas técnicas o historias de usuario de Sprint con criterios de DoD.
- **Quién lo lee:** equipo.
- **Qué pasa si desaparece:** nada.
- **Clasificación:** `3. Redundante con AGENTS.md` (este archivo queda desactualizado respecto de `AGENTS.md` y `backend/Dockerfile` en la versión de Python y en la convención de identificadores de tareas).
- **Contradicciones con el registro:**
  - **Versión de Python:** El documento exige `Python 3.11 type hints` (línea 16). El código productivo (`backend/Dockerfile:4`, `FROM python:3.12-slim-bookworm`) y `AGENTS.md` establecen **Python 3.12** (en el entorno local `backend/.venv` persisten artefactos `.pyc` compilados con `cpython-311`).
  - **Identificador de historias:** El documento utiliza el formato `[US-XX]` (línea 4), mientras que el registro canónico muestra que desde los Sprints 3–5 el seguimiento y las historias implementadas se identifican mayoritariamente con claves `SCRUM-XX` de Jira (coexistiendo con `US-XX` históricos).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:** Ninguna.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:** Ninguna.
- **Referencias rotas:** Ninguna (`AGENTS.md` y `DESIGN.md` existen en la raíz del repositorio).

---

## 3. `backend/README.md`

- **Ruta:** `backend/README.md`
- **Líneas:** 82
- **Última modificación:** `2026-09-19`
- **Tema que cubre:** Guía técnica de puesta en marcha local, ejecución de tests, endpoints iniciales, usuarios demo y auditoría de seguridad del backend Django/DRF.
- **Quién lo lee:** equipo (y cátedra si inspecciona la carpeta `backend/`).
- **Qué pasa si desaparece:** alguien se equivoca (es la única guía dentro de `backend/` sobre `seed_demo`, `01-test-db-grants.sql` y la convivencia con un MySQL local en el puerto 3306; aunque actualmente también induce a error por un comando roto y por reflejar solo el alcance de Spec 001).
- **Clasificación:** `3. Incompleto` (promete documentar la puesta en marcha, endpoints y auditoría del backend SGD-AVEIT, pero quedó congelado en la Spec 001 Walking Skeleton del 19/09/2026 y no cubre los módulos posteriores; parcialmente redundante en setup general con `README.md` y `AGENTS.md`, quedando desactualizado `backend/README.md`).
- **Contradicciones con el registro:**
  - **Identificador de login:** El documento describe el acceso solo por `Legajo` (líneas 72–78) con contraseña `Aveit-Demo-2026!`. El registro canónico (§2 y §3) y `backend/accounts/serializers.py:38-55` indican autenticación por **N.º de Socio** (`numero_socio`), además de `legajo`, `username` o `email` (y contraseña opcional en el `LoginSerializer` actual para pruebas).
  - **Usuarios creados por `seed_demo`:** El documento lista 5 usuarios demo (líneas 72–78). El código (`backend/socios/management/commands/seed_demo.py:19-27, 70`) crea **7 usuarios demo** (agrega `409953` y `415327`, ambos `SOCIO`) y además ejecuta `seed_production_data`.
  - **Eventos de auditoría de seguridad:** El documento afirma que `accounts/audit.py` diferencia 4 eventos (`AUTH_SUCCESS`, `AUTH_FAILURE`, `ACCESS_GRANTED`, `ACCESS_DENIED`, línea 82). El código (`backend/accounts/audit.py:21`) incluye además un quinto evento: `ROLE_CHANGED`.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:** Ninguna (los 4 endpoints que documenta están implementados; `GET /api/v1/socios/` efectivamente exige `TD`, `CD`, `ADMIN` mediante `IsTribunalOrDirectiva` en `backend/socios/views.py:97`).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - De toda la API definida en `backend/core/urls.py` y verificada como `implementada` en el registro canónico (§2), el documento omite:
    - Healthchecks (`/api/health/`, `/api/v1/padron/health/`).
    - Capa anticorrupción Padrón Institucional (`/api/v1/padron/`).
    - Consulta de Legajo Integral (`/api/v1/socios/<pk>/legajo/`).
    - Ranking Oficial (`/api/v1/ranking/`, `/api/ranking/`).
    - Módulo completo de Expedientes (`/api/v1/expedientes/`: solicitudes T01, ciclo de 6 estados, tablero, calendario institucional, descargos T02/T03 y evidencia, visor autorizado, resolución causal T02, valoración T03, composición del tribunal, apelación T01, editor/PDF/firma colegiada de resoluciones, exclusión de involucrados, enmiendas, libro mayor, publicación protegida, ABM de reglamentos y reportes).
    - Eventos y asistencia (`/api/v1/eventos/`).
    - Notificaciones / Outbox (`/api/v1/notifications/`) y management commands operativos (`process_email_queue`, `close_expired_deadlines`, `seed_production_data`, `seed_eventos_asistencias`).
    - Administración de parámetros y miembros TD (`/api/v1/admin/`, `/api/v1/parametros/`).
  - No documenta la ejecución del backend mediante el servicio `backend` de `docker-compose.yml` (solo cubre `docker compose up -d db` + ejecución local en `.venv`).
- **Referencias rotas:**
  - Línea 18: `cp .env.example .env` luego de `cd backend` (línea 12). El archivo `backend/.env.example` **no existe** (solo existe `.env.example` en la raíz del repositorio).

---

## 4. `frontend/CHANGELOG.md`

- **Ruta:** `frontend/CHANGELOG.md`
- **Líneas:** 151
- **Última modificación:** `2026-09-06`
- **Tema que cubre:** Historial de versiones (1.0.0 a 2.8.0, 2017–2022) de la plantilla *Material Dashboard Angular* de Creative Tim.
- **Quién lo lee:** nadie.
- **Qué pasa si desaparece:** nada.
- **Clasificación:** `1. Residuo de fabricación` (archivo intacto de la plantilla base de terceros; no es arquitectónico, ni formal del proyecto, ni sirve al repositorio ni a contenido presentable).
- **Contradicciones con el registro:** No menciona a SGD-AVEIT; su contenido corresponde exclusivamente a versiones históricas (2017–2022) de la plantilla comercial externa y no refleja ninguna entrega del proyecto 2026.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:** Ninguna.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:** Ninguna como residuo de plantilla; si se lo interpretara como changelog del frontend de SGD-AVEIT, omite la totalidad de las funcionalidades implementadas en `frontend/src/app/` (registro §2 y §3).
- **Referencias rotas:** Menciona paquetes y elementos de versiones antiguas de la plantilla que no existen en el proyecto actual (por ejemplo, `@agm/core`, `core-js`, `rxjs-compat` en líneas 34–60; página `Upgrade to PRO` en línea 139).

---

## 5. `frontend/LICENSE.md`

- **Ruta:** `frontend/LICENSE.md`
- **Líneas:** 21
- **Última modificación:** `2026-09-06`
- **Tema que cubre:** Texto de la licencia MIT (Copyright 2017 Creative Tim) de la plantilla base utilizada en `frontend/`.
- **Quién lo lee:** nadie (salvo revisión de cumplimiento de licencias de terceros).
- **Qué pasa si desaparece:** alguien se equivoca (la cláusula de la licencia MIT exige conservar el aviso de copyright y permiso en todas las copias o porciones sustanciales del software derivado).
- **Clasificación:** `4. Vigente` / `2. Pocas líneas` (aunque tiene 21 líneas, borrarlo genera incumplimiento de la licencia MIT del template incorporado en `frontend/`).
- **Contradicciones con el registro:**
  - No contradice el registro canónico directamente, pero existe una inconsistencia de licencias en el repositorio: `frontend/LICENSE.md` declara **MIT License (Copyright 2017 Creative Tim)**, mientras que `frontend/package.json:4` declara `"license": "Apache-2.0"` y el `README.md` raíz enlaza a `LICENSE` (Apache-2.0).
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:** Ninguna.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:** Ninguna.
- **Referencias rotas:** Ninguna.

---

## 6. `frontend/README.md`

- **Ruta:** `frontend/README.md`
- **Líneas:** 251
- **Última modificación:** `2026-09-26`
- **Tema que cubre:** README original promocional y de inicio rápido de la plantilla *Material Dashboard Angular* de Creative Tim.
- **Quién lo lee:** nadie (o un integrante del equipo que busque instrucciones del frontend y se encuentre con la documentación del template externo).
- **Qué pasa si desaparece:** nada (el contenido actual no documenta SGD-AVEIT).
- **Clasificación:** `1. Residuo de fabricación` (archivo de la plantilla base de Creative Tim sin adaptar a SGD-AVEIT; no es arquitectónico, ni formal, ni útil para el repositorio ni presentable para la cátedra).
- **Contradicciones con el registro:**
  - **Identidad del producto:** Presenta la aplicación como *Material Dashboard Angular - Free Bootstrap Material Design Admin* de Creative Tim, no como el frontend de **SGD-AVEIT** (registro §2 y §3).
  - **Versión de Angular:** Afirma *"This project was generated with Angular CLI version 1.0.0 and angular 4.x"* (línea 72). El registro (§3) y `frontend/package.json` confirman **Angular 14.2+** (`@angular/core: ^14.2.0`, `@angular/cli: ~14.2.7`).
  - **Sistema de notificaciones:** Destaca `bootstrap-notify` (`$.notify`) como sistema de notificaciones (línea 16). El registro (§2) verifica que el sistema usa `NotificationCenter` (`frontend/src/app/components/notification-center/`), y `AGENTS.md` prohíbe explícitamente usar `$.notify`.
  - **Instalación y ejecución local:** Indica `npm install` y `ng serve` (líneas 78–79) sin advertir `--legacy-peer-deps` ni el proxy hacia el backend (`proxy.conf.json` / `proxy.docker.conf.json`).
  - **Año de copyright:** Indica `Copyright 2018 Creative Tim` (línea 225), mientras que `frontend/LICENSE.md:3` indica `Copyright (c) 2017 Creative Tim`.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:** Ninguna sobre SGD-AVEIT (solo promociona vistas demo de la plantilla).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Omite por completo la arquitectura y los módulos reales implementados en `frontend/src/app/` y verificados en el registro canónico (§2 y §3): `login`, `mis-expedientes`, `reglamentos`, `solicitar-puntos`, `ranking-socios`, `gestionar-expedientes` (`visor-expediente`, `valoracion-t03-panel`), `calendario-institucional`, `reportes`, `eventos-asistencia` / `pages/eventos/asistencia-evento`, `pages/admin/parametros`, `components/notification-center`, los 55 archivos de tests `*.spec.ts`, el `Dockerfile` y `proxy.docker.conf.json`.
- **Referencias rotas:**
  - En el diagrama `What's included` (líneas 88–188):
    - `angular-cli.json` (línea 92): archivo inexistente (el archivo real es `frontend/angular.json`).
    - `typings` (línea 187): directorio inexistente en `frontend/`.
  - Enlaces internos rotos en `Table of Contents` (líneas 24–35):
    - `[Documentation](#documentation)` (línea 28): no existe encabezado `## Documentation`.
    - `[File Structure](#file-structure)` (línea 29): no existe encabezado `## File Structure` (la sección se titula `### What's included`).
  - Enlaces externos obsoletos o ajenos al proyecto:
    - `https://plus.google.com/+CreativetimPage` (línea 245 — servicio Google+ discontinuado).
    - `https://github.com/tiniestory/material-dashboard-angular2/archive/master.zip` (línea 61 — repositorio externo de terceros).
    - Botón `Deploy to Genezio` apuntando a `https://github.com/creativetimofficial/material-dashboard-angular2` (línea 68).

---

## Decisiones pendientes

1. **Destino de los archivos de plantilla en `frontend/` (`frontend/CHANGELOG.md` y `frontend/README.md`):** Definir si `frontend/CHANGELOG.md` se archiva en `auditoria/archivados/` y si `frontend/README.md` se archiva o se reemplaza por documentación técnica propia del frontend de SGD-AVEIT.
2. **Armonización de licencias en `frontend/` (`frontend/LICENSE.md` vs `frontend/package.json` vs `LICENSE` raíz):** Definir cómo dejar documentada la coexistencia entre la licencia MIT de la plantilla base de Creative Tim (`frontend/LICENSE.md`, cuyo aviso debe conservarse) y la licencia Apache-2.0 declarada en `frontend/package.json` y en la raíz del repositorio.
3. **Alcance y mantenimiento de `backend/README.md`:** Definir si `backend/README.md` se mantiene como guía técnica completa del backend (requiriendo reflejar la API real, el setup con Docker y corregir la referencia a `.env.example`) o si se acota exclusivamente a puesta en marcha y ejecución de tests.
4. **Vigencia de las plantillas de GitHub Issues (`.github/ISSUE_TEMPLATE/reporte_incidencia.md` y `.github/ISSUE_TEMPLATE/tarea_sprint.md`):** Definir si el equipo continuará usando GitHub Issues en paralelo con Jira y, en caso afirmativo, si se alinea `.github/ISSUE_TEMPLATE/tarea_sprint.md` con Python 3.12 y la nomenclatura `SCRUM-XX` o si se archiva.
