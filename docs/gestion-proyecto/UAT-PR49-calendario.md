# UAT — Correcciones del calendario institucional (PR #49)

Fecha: 10/10/2026. Rama: `feature/US-S3-01-calendario-dias-habiles`.

## Acceso

Abrir [Calendario institucional en localhost](http://localhost:4200/#/calendario-institucional). El login dispone de botones de demostración por rol: ADMIN 403655, TD 408917, CD 87414, SOCIO 74907 y FISCALIZADORA 85194.

Angular está servido en el puerto 4200 con el proxy existente; Django y MySQL están activos en Docker. [Healthcheck del backend](http://localhost:8000/api/health/) devuelve estado OK y base conectada.

La implementación y los comandos se ejecutaron en el worktree:

```text
C:\Users\Usuario\.codex\worktrees\calendario-pr49\seminario-integrador
```

UAT aprobada por el usuario el 10/10/2026. La entrega se realiza en la misma rama mediante el [PR #49](https://github.com/MartinG94/seminario-integrador/pull/49), que permanece abierto para revisión, sin merge. El checkout original conserva sus cambios previos.

## Comprobaciones realizadas

| Comprobación | Resultado |
| --- | --- |
| Suite completa backend, MySQL 8 / Django 4.2 | 505 tests aprobados, 0 errores |
| Suite completa Angular / ChromeHeadless | 153 tests aprobados, 0 fallos |
| Reglas de dominio, calendario, API e importación | 85 tests aprobados; cobertura del dominio 99 % |
| Compilación Angular de producción | Aprobada |
| Ruff check y format | Aprobados |
| Migraciones pendientes de generar | Ninguna |
| Auditoría independiente full stack | Cerrada sin hallazgos pendientes |
| HTTP real GET de calendario | 200 para SOCIO, FISCALIZADORA, CD, TD y ADMIN |
| Carga desde la SPA | 16 feriados, sin alerta inicial |
| Lectura como SOCIO desde la SPA | Calendario visible; 0 alertas y 0 botones de alta |
| UX en viewports móviles de 320 y 393 px | Año/Mes en una fila; simulador apilado con inputs de igual ancho y altura; tabla con desplazamiento local |
| UX en escritorio | Año/Mes en una fila; etiquetas e inputs del simulador alineados, ambos inputs de 40 px de alto |
| Formulario de alta | Fecha mínima 10/10/2026; Guardar bloqueado para 09/10 y habilitado para hoy |
| Simulador con Soberanía trasladada | Inicio 20/11/2026 14:30 + 5 hábiles → 30/11/2026 14:30; excluye el 23/11 |

La suite frontend inicialmente se detenía por una interfaz importada como valor en un diálogo anterior. Se corrigió a `import type`. También se actualizaron fixtures de pruebas heredadas: outlet/navegación en vez del título del template inicial, Google Maps aislado sin servicio externo y dependencias de las plantillas de dashboard/layout.

`npm run lint` no está disponible porque la configuración heredada apunta al builder `@angular-devkit/build-angular:tslint`, que no existe en las dependencias instaladas. No se añadieron dependencias. La compilación conserva avisos previos sobre archivos TypeScript no utilizados.

## Casos para la aceptación del usuario

| Caso | Acción | Resultado esperado |
| --- | --- | --- |
| Lectura y acceso | Entrar con cada rol y abrir Calendario institucional | Tabla visible sin alerta roja; Crear Feriado solo para ADMIN/CD/TD |
| Simplificación | Revisar controles y columnas | Año/Mes; Fecha, Denominación, Creado por y Creado el; sin versiones, tipos o condición |
| Orden | Pulsar Fecha dos veces, con todos los meses | Alterna de ascendente a descendente y viceversa |
| Filtros | Seleccionar 2026 / Noviembre | Soberanía figura el 23/11/2026 |
| Retroactividad | Elegir ayer y completar denominación | Guardar deshabilitado; la API también rechaza fechas pasadas |
| Alta y auditoría | Registrar una fecha futura libre con una denominación | Registro inmediato con usuario institucional y hora de creación |
| Impacto inmediato | Simular un plazo que incluya esa fecha, luego registrar el feriado | El siguiente cálculo excluye la fecha; una simulación visible o pendiente se actualiza |
| Duplicados | Intentar un alta de una fecha ya registrada | Mensaje de validación; no se duplica la fila ni aparece un error 500 |
| Zona horaria | Revisar fechas y timestamps desde otro huso horario | El día del feriado no se desplaza; la hora de auditoría/simulador es la institucional |

Los tests backend verifican además que los vencimientos guardados no se recalculan, que el calendario vacío se consulta sin inicialización y que el cliente no puede suplantar el autor ni la fecha de creación.

La sesión ADMIN queda abierta en el navegador para continuar la UAT.

## Ajustes de alineación solicitados durante UAT

Año y Mes ahora usan dos columnas que permanecen en la misma fila. Los campos del simulador se alinean desde arriba y tienen la misma altura, por lo que la ayuda de zona horaria no desplaza Días hábiles. En pantallas pequeñas, los campos del simulador conservan la pila para mostrar la fecha y hora completas.

Se verificó la disposición en localhost en escritorio y a 320/393 px. Tras el cambio se repitieron los 153 tests frontend y la compilación de producción, ambos en verde; la revisión independiente del SCSS no encontró observaciones. Las reglas y los textos mantienen consistencia con las notas del PO.

## Datos y consistencia

El calendario operativo es único. Las tablas anteriores permanecen como evidencia de los expedientes. Los registros iniciales se identifican como Sistema; un registro previo sin autor conocido se muestra como Autor no registrado, sin atribuciones inventadas.

Se corrigieron Güemes al 15/06/2026 y Soberanía al 23/11/2026 únicamente en la carga inicial reconocida, conforme a la aprobación del usuario y a [Cancillería — feriados 2026](https://clond.cancilleria.gob.ar/es/node/1986). La migración conserva los registros institucionales posteriores y los vencimientos históricos.

La alerta original se reprodujo con error MySQL 1146: faltaban tablas de expedientes en la base local. El arranque de Django ahora ejecuta las migraciones antes de servir. La SPA consulta feriados directamente y deja de depender del listado de versiones.

La implementación fue contrastada con las notas del PO al inicio, durante las correcciones y al cierre. Los textos de la pantalla son breves e institucionales y los permisos se verifican en servidor. `notasPO.md` y el seguimiento macro no se modificaron.

## Reanudar el entorno

Desde el worktree:

```powershell
docker compose up -d db backend
cd frontend
npm start -- --host 127.0.0.1 --port 4200
```

Para detener Angular, Ctrl+C en su proceso; para detener los contenedores, `docker compose stop backend db` desde el worktree.
