# Guía de Pull Requests

Esta guía establece el formato mínimo para crear y revisar Pull Requests (PR) del proyecto SGD-AVEIT. Su objetivo es que cada cambio sea comprensible, trazable y verificable antes de integrarse.

## Regla obligatoria

**Todo Pull Request debe incluir una descripción.** No se aprobarán ni integrarán PR sin ella, aunque el cambio sea pequeño.

La descripción debe ser **clara, concisa, breve y redactada como una lista de ítems**. Debe indicar qué cambia y, cuando sea necesario para comprender el aporte, por qué se realiza. Si corresponde, también debe incluir la historia de usuario, tarea o incidencia relacionada.

## Nombre del Pull Request

El título debe seguir este formato:

```text
<tipo>(<alcance opcional>): <descripción breve>
```

- Usar el tipo en minúsculas.
- Escribir una descripción concreta y breve, sin punto final.
- El alcance es opcional y representa el módulo afectado, por ejemplo: `backend`, `frontend`, `auth` o `docs`.

Ejemplos:

```text
feat(auth): agregar autenticación con JWT
fix(ranking): corregir ordenamiento ante empates
docs: actualizar guía de instalación local
chore: actualizar configuración de desarrollo
```

## Tipos permitidos

| Tipo | Cuándo usarlo | Ejemplo |
| --- | --- | --- |
| `feat` | Incorpora una funcionalidad nueva para el usuario. | `feat(socios): agregar filtro por subcomisión` |
| `fix` | Corrige un defecto o comportamiento incorrecto. | `fix(login): validar cuenta inactiva` |
| `docs` | Modifica únicamente documentación. | `docs: agregar guía de Pull Requests` |
| `test` | Agrega o ajusta pruebas sin cambiar funcionalidad productiva. | `test(ranking): cubrir empates de puntaje` |
| `refactor` | Reorganiza código sin alterar su comportamiento externo. | `refactor(api): extraer servicio de búsqueda` |
| `chore` | Realiza mantenimiento técnico, configuración o tareas auxiliares. | `chore: actualizar archivos de configuración` |
| `build` | Cambia dependencias, empaquetado o proceso de compilación. | `build(frontend): ajustar configuración de producción` |
| `ci` | Cambia automatizaciones de integración o despliegue continuo. | `ci: ejecutar pytest en GitHub Actions` |
| `perf` | Mejora el rendimiento sin cambiar el resultado funcional. | `perf(search): optimizar consulta de socios` |
| `style` | Aplica formato o cambios visuales sin modificar la lógica. | `style(frontend): alinear espaciados de la tabla` |
| `revert` | Revierte un cambio previamente integrado. | `revert: revertir feat(auth): agregar autenticación con JWT` |

## Descripción obligatoria

La sección **Descripción** debe cumplir estas pautas:

- Usar una lista de ítems; no redactar párrafos extensos.
- Expresar una sola modificación relevante por ítem.
- Comenzar cada ítem con un verbo de acción, por ejemplo: `Agrega`, `Corrige`, `Actualiza`, `Documenta` o `Refactoriza`.
- Mantener cada ítem en una oración breve y verificable.
- Describir el resultado del cambio y evitar detalles internos que no aporten a la revisión.
- No repetir el título ni incluir cambios que no formen parte del PR.
- No inventar pruebas, referencias ni resultados que no puedan verificarse.

Ejemplo de una descripción correcta:

```md
## Descripción

- Agrega la nomenclatura convencional para los títulos de Pull Requests.
- Define la descripción obligatoria como una lista breve de cambios verificables.
- Incorpora una plantilla reutilizable para el equipo de desarrollo.
```

Copiar y completar esta plantilla en cada PR:

```md
## Descripción

- <!-- Cambio relevante 1. -->
- <!-- Cambio relevante 2. -->

## Referencia

<!-- Jira, historia de usuario, tarea o incidencia. Si no aplica, indicar "No aplica". -->

## Verificación

- [ ] Pruebas automatizadas ejecutadas y en verde.
- [ ] Validación manual realizada, si aplica.
- [ ] No se incluyen secretos, datos sensibles ni cambios ajenos al alcance.

## Evidencia visual

<!-- Capturas o video para cambios de interfaz. Si no aplica, indicar "No aplica". -->
```

No incluir resultados de pruebas o validaciones que aún no se hayan realizado; en ese caso, indicarlo como pendiente.

## Uso por asistentes de desarrollo

Antes de sugerir un PR, los asistentes deben consultar esta guía. Su propuesta debe incluir:

1. Un título con la nomenclatura definida en [Nombre del Pull Request](#nombre-del-pull-request).
2. Una descripción clara, concisa y breve, confeccionada como una lista de ítems.
3. Un único cambio verificable por ítem, redactado con un verbo de acción.
4. Los demás apartados de la plantilla cuando el desarrollador solicite la descripción completa del PR.

Cuando un desarrollador solicite solamente una **descripción de PR**, el asistente debe entregar un bloque listo para copiar con este formato:

```md
## Descripción

- [Primer cambio relevante y verificable.]
- [Segundo cambio relevante y verificable.]
```

El asistente debe basar los ítems en los cambios reales de la rama o en la información proporcionada por el desarrollador. La respuesta no debe contener introducciones, conclusiones ni explicaciones adicionales, salvo que sean solicitadas.

Si no se conoce una referencia, una prueba ejecutada o una evidencia visual, se debe indicarlo como `No aplica` o `Pendiente`; nunca debe inventarse esa información.

## Condiciones para solicitar revisión

Antes de asignar revisores, la persona autora debe verificar que:

- la rama está actualizada respecto de la rama base definida por el equipo;
- el PR contiene un único cambio coherente y no mezcla trabajo no relacionado;
- las pruebas aplicables pasan en verde;
- los cambios de interfaz fueron verificados en vista móvil y de escritorio;
- no hay secretos, credenciales ni datos reales sensibles de socios;
- la descripción y la referencia de trabajo están completas.

## Revisión e integración

- Todo PR requiere la aprobación de al menos una persona del equipo distinta de su autoría.
- Los comentarios de revisión deben resolverse o acordarse antes de integrar.
- No se permite integrar un PR con pruebas fallando.
- No se permite hacer `push` directo a `main` ni a `develop`.
- La persona autora es responsable de que el cambio cumpla la spec activa, la constitución del proyecto y los criterios de aceptación asociados.
