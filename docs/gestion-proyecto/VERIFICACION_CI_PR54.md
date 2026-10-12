# Verificación de CI — PR #54

Fecha: 12/10/2026. Referencia: [PR #54](https://github.com/MartinG94/seminario-integrador/pull/54), SCRUM-77 / TS77.47. El usuario autorizó corregir los fallos de integración continua y mantener la PR abierta, sin merge.

## Causa y corrección

El [run inicial de pull request](https://github.com/MartinG94/seminario-integrador/actions/runs/38314352466) terminó con 934 pruebas backend aprobadas y 130 errores MySQL 1044. Ruff y formato pasaron. Frontend aprobó sus 278 pruebas y el build; se comprobó el resultado del paso de tests, que tiene `continue-on-error` heredado.

Las fixtures de infraestructura crean bases aisladas con los prefijos `test_scrum77_bootstrap_` y `test_scrum77_ddl_` y un sufijo UUID. CI sólo concedía acceso a la base temporal de Django. El fallo se reprodujo con el mismo usuario y configuración de MySQL, sin usar permisos de administración para ejecutar pytest.

La [corrección fe468b8](https://github.com/MartinG94/seminario-integrador/commit/fe468b8561044dce38b9b81cff2bae9a66a1818b) añade grants para las dos familias temporales y escapa los guiones bajos de los tres nombres de base. Sólo el sufijo de las bases scratch admite comodín. El [manual de MySQL 8.0](https://dev.mysql.com/doc/refman/8.0/en/grant.html) documenta el escape de guiones bajos en grants de base; la reproducción confirmó `partial_revokes=0`.

La corrección mantiene el usuario `aveit_test`, el alcance de los checks, las pruebas y las reglas de negocio de la spec y del PO. No cambia dependencias, migraciones ni datos de la demo.

## Reproducción local

Se utilizó un proyecto Docker separado, `sgd-aveit-pr54-ci-repro`, con MySQL 8.0.46, almacenamiento tmpfs, sin puertos publicados y checkout montado en sólo lectura. Las sentencias de permiso se extrajeron del workflow corregido. Al terminar se retiraron únicamente su contenedor y su red.

| Control | Resultado |
| --- | --- |
| Permisos originales sobre las dos familias scratch | Dos denegaciones MySQL 1044 esperadas |
| Permisos corregidos: crear base, tabla InnoDB y retirar cada base propia | Dos familias habilitadas |
| Nombres ajenos o con sustituciones de los guiones bajos | Cuatro denegaciones esperadas |
| Pytest focal con el usuario restringido de CI | 9 aprobadas, 0 errores, 13,15 s |

El set focal ejecutó `test_scrum77_legacy_ddl.py`, el upgrade Junior que preserva filas/ediciones/contador y el contrato HTTP del catálogo contra MySQL. Los seis controles de permisos posteriores a la corrección terminaron sin resultados inesperados.

## Verificación remota

Los cuatro checks de fe468b8 terminaron `completed/success`. Se verificaron los logs y el resultado de cada paso, incluidos los tests frontend.

| Evento | Run | Backend | Frontend | Build |
| --- | --- | --- | --- | --- |
| Pull request | [38316123126](https://github.com/MartinG94/seminario-integrador/actions/runs/38316123126) | 1064 aprobadas, 618,17 s | 278 aprobadas | 28.525 ms |
| Push | [38316117765](https://github.com/MartinG94/seminario-integrador/actions/runs/38316117765) | 1064 aprobadas, 574,61 s | 278 aprobadas | 32.296 ms |

Cero errores u omisiones. Ruff y formato globales aprobados; ambos builds tienen hash `3d29677bcd1038fa`. La PR continúa abierta hacia main, sin merge. La ampliación de saldo solicitada durante la verificación deberá comprobar nuevamente los checks de su último commit.

## Auditoría

El subagente independiente aprobó el diff del workflow y los resultados remotos: grants de base acotados, escapes conservados por el heredoc y pytest con el usuario restringido. No se conceden privilegios globales ni `GRANT OPTION`. TS77.47 queda verificada para fe468b8.
