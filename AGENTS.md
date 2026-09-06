# AGENTS.md — SGD-AVEIT

Guía operativa obligatoria para agentes de Inteligencia Artificial (Antigravity, Copilot, Claude, Gemini CLI) y desarrolladores del equipo. Este proyecto aplica la metodología **Spec-Driven Development (SDD)** inspirada en [mouredev/hello-sdd](https://github.com/mouredev/hello-sdd).

---

## 1. Proyecto

Plataforma web 100% responsive (Mobile-First) para la gestión integral de expedientes disciplinarios, descargos tipificados (T02/T03), votación nominal colegiada del Tribunal de Disciplina y cómputo transaccional inmutable de saldos de puntos de la Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos (**A.V.E.I.T.** - UTN FRC).

- **Backend:** Python 3.11+ con Django 4.2+ LTS y Django REST Framework (DRF).
- **Frontend:** SPA en Angular 14.2+ con TypeScript y Material Dashboard PRO (Angular Material).
- **Base de Datos:** MySQL 8.0 relacional y transaccional (padrón institucional de ~515 socios).
- **Entorno Local:** Orquestación en contenedores mediante `docker-compose.yml`.

---

## 2. Comandos

### Entorno General (Docker Compose)
- Iniciar servicios: `docker compose up -d`
- Detener servicios: `docker compose down`
- Ver logs en vivo: `docker compose logs -f`
- Estado de contenedores: `docker compose ps`

### Backend (Python / Django)
- Migraciones: `docker compose exec backend python manage.py migrate` (o `python manage.py migrate`)
- Crear superusuario: `docker compose exec backend python manage.py createsuperuser`
- Ejecutar tests: `docker compose exec backend pytest -q` (o `pytest -q` con virtualenv activo)
- Cobertura de tests: `docker compose exec backend pytest --cov=. --cov-report=term-missing`
- Linting y formato: `docker compose exec backend ruff check .` y `docker compose exec backend ruff format --check .`

### Frontend (Angular / TypeScript)
- Directorio: `cd frontend-angular`
- Iniciar servidor de desarrollo: `npm start` (disponible en `http://localhost:4200`)
- Compilar para producción: `npm run build`
- Ejecutar tests unitarios: `npm test -- --watch=false --browsers=ChromeHeadless`
- Linting: `npm run lint`

---

## 3. Estilo y Convenciones

- **Lenguaje y Tipado:**
  - Python 3.11+: Type hints obligatorios en todas las funciones, métodos y modelos públicos.
  - TypeScript: Tipado estricto habilitado (`strict: true`), interfaces y DTOs para cada payload de API.
- **Idioma del Código:**
  - Identificadores, nombres de clases, funciones, modelos, campos de BD y commits en **inglés** (ej. `MembershipStatus`, `calculate_balance`, `fetch_records`).
  - Interfaz de usuario, etiquetas, reglamentos, mensajes de error, justificaciones y documentación formal en **español rioplatense institucional** (ej. "Socio Activo", "Expediente Creado", "Formulario T02").
- **Tokens de Diseño:**
  - Prohibido utilizar colores hexadecimales arbitrarios o estilos ad-hoc.
  - Toda interfaz debe consumir las variables canónicas y CSS Custom Properties de [`DESIGN.md`](file:///g:/My%20Drive/Estudios/Seminario/Repositorio/seminario-integrador/DESIGN.md) y [`frontend-angular/src/assets/scss/core/_aveit-tribunal.scss`](file:///g:/My%20Drive/Estudios/Seminario/Repositorio/seminario-integrador/frontend-angular/src/assets/scss/core/_aveit-tribunal.scss).
- **Control de Versiones y Ramas:**
  - Formato de ramas: `feature/US-xx-descripcion-corta`, `fix/issue-descripcion`.
  - Commits semánticos convencionales: `feat: ...`, `fix: ...`, `test: ...`, `docs: ...`.

---

## 4. Reglas Innegociables

1. **Lee `docs/constitution.md` y la spec activa:** Antes de escribir una sola línea de código, revisa la constitución y el archivo `specs/<spec-activa>/spec.md`. Si una decisión no está en la spec, **pregunta antes de asumir**.
2. **Cero sentencias `UPDATE`/`DELETE` manuales en MySQL:** Ninguna operación debe modificar el saldo de puntos de un socio de forma no auditada. Los saldos se recalculan o acreditan mediante eventos de libro mayor transaccional vinculados a una resolución emitida.
3. **Flujo de trabajo SDD estricto:**
   - La spec describe el **QUÉ** y el **POR QUÉ** (requisitos en notación EARS).
   - El plan describe el **CÓMO** (arquitectura, módulos, esquema DDL, alternativas descartadas).
   - Las tareas desglosan el trabajo en unidades verificables de `<30 min`.
   - La implementación se hace **una sola tarea a la vez**, con **tests primero (TDD)**.
4. **Límites de edición:**
   - No toques archivos dentro de `specs/` salvo petición explícita de cambio de requerimiento.
   - No agregues dependencias pesadas a `requirements.txt` o `package.json` sin previa aprobación del Product Owner.
   - Respeta estrictamente los 6 estados del expediente (Art. 12 del Reglamento Procesal 2026).

---

## 5. Al Terminar Cualquier Tarea

1. Ejecuta la suite de pruebas correspondiente (`pytest` o `npm test`).
2. Confirma en tu respuesta que todos los tests pasan en verde (0 errores).
3. Marca la tarea completada con `[x]` en el `tasks.md` de la spec y en [`TASK.md`](file:///g:/My%20Drive/Estudios/Seminario/Repositorio/seminario-integrador/TASK.md).
4. **PÁRATE** y solicita confirmación antes de iniciar la siguiente tarea.
