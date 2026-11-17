# Análisis para Product Owner: Visibilidad y Acceso al Ranking de Socios

**Proyecto:** SGD-AVEIT  
**Fecha:** 25 de Septiembre de 2026  
**Referencia:** Sprint 1 — US-02 / S1-06 / PR #33  
**Destinatario:** Product Owner & Comité de Proyecto  

---

## 1. Resumen Ejecutivo y Veredicto

Al evaluar el funcionamiento de la pantalla **Ranking de Socios**, se detectó un desajuste entre las capas de Backend y Frontend:

* **En el Backend:** El comportamiento actual es el **esperado y formalmente especificado**. El acceso al padrón general y al listado de socios está restringido por diseño institucional exclusivamente a las autoridades (**Tribunal de Disciplina**, **Comisión Directiva** y **Administradores**), respondiendo con `403 Forbidden` a cualquier intento de consulta por parte de un socio ordinario.
* **En el Frontend:** La SPA continúa mostrando el acceso al *"Ranking de Socios"* en la barra lateral para todos los roles. Cuando un socio común ingresa, el servidor rechaza la petición legítimamente por seguridad y la pantalla muestra una tabla vacía sin feedback informativo.

Se requiere una **definición funcional del Product Owner** para determinar si el ranking debe mantenerse reservado a autoridades o abrirse a todo el padrón.

---

## 2. Bases Reglamentarias y Técnicas del Proyecto

### A. Documento Rector de Control de Acceso (`docs/especificaciones/RBAC-SGD-AVEIT.md`)
* **Rol SOCIO (`ACT-01`):** "Consulta de su propio legajo, saldo y expedientes; presentación de descargos T02/T03." *No posee alcance sobre el padrón general ni el ranking de terceros.*
* **Rol FISCALIZADORA (`ACT-04`):** Alcance de SOCIO, más inicio de solicitudes T01 sobre miembros de su subcomisión. *No tiene acceso al padrón general.*
* **Rol CD (`ACT-03`):** "Lo de SOCIO, más ranking consolidado del padrón, inicio de T01 general..."
* **Rol TD (`ACT-02`):** "Lo de SOCIO, más tablero de los 6 estados, buscador integral de legajos, ranking, sustanciación de T02/T03..."
* **Endpoints Protegidos (Sección 4):**
  * `GET /api/v1/socios/`: Autorización reservada a `TD`, `CD`, `ADMIN` (clase de permiso `IsTribunalOrDirectiva`). Ante falta de permisos retorna estrictamente `403 Forbidden`.

### B. Suite de Pruebas Canónica del Backend (`backend/tests/test_rbac.py`)
En las líneas 63 a 73 se define una prueba unitaria obligatoria que falla si un `SOCIO` o `FISCALIZADORA` puede consultar el padrón:

```python
@pytest.mark.parametrize("role", [Role.SOCIO, Role.FISCALIZADORA])
@pytest.mark.django_db
def test_unauthorized_roles_get_403_on_padron(make_socio, authenticate, role):
    socio = make_socio(legajo=f"2000{role}", role=role)
    client = authenticate(socio)
    response = client.get(PADRON_URL)
    assert response.status_code == 403
```

### C. Historias de Usuario y Matriz RACI
* **Historia de Usuario `US-02` (`Seguimiento de Proyecto.md`):**  
  *"Como integrante del TD o CD, quiero consultar el ranking consolidado de puntos (+/-) de los ~515 socios con membresía vigente... para supervisar el estado de cumplimiento y emitir informes ante Asambleas."*
* **Matriz RACI (`PLAN_DE_PROYECTO_SGD_AVEIT.md` - `CU-04`):**  
  * Consultar Ranking General de Socios: **Socio: No** | **Fiscalizadora: No** | **CD: Sí** | **TD: Sí** | **ADMIN: Sí**.

---

## 3. Causa del Comportamiento Observado

1. **Estado previo:** El componente `RankingSociosComponent` consumía datos simulados estáticos en memoria (`TribunalDataService`), sin interactuar con la API ni validar roles de usuario.
2. **Estado actual:** Con la integración a la API real (`SocioApiService.searchSocios` -> `GET /api/v1/socios/`), el backend aplica la seguridad RBAC requerida:
   * Al iniciar sesión como `TD`, `CD` o `ADMIN`: el servidor autoriza la consulta (200 OK) y el ranking muestra los socios.
   * Al iniciar sesión como `SOCIO` o `FISCALIZADORA`: el servidor rechaza la consulta por falta de autorización (403 Forbidden) y la lista se inicializa vacía.

---

## 4. Matriz de Comportamiento por Rol

| Rol en Sesión | Acceso en Backend (`GET /api/v1/socios/`) | Comportamiento Actual en Pantalla | Diagnóstico Técnico |
| :--- | :--- | :--- | :--- |
| **TD** (Tribunal de Disciplina) | `200 OK` | Visualiza ranking completo y puede abrir legajos. | **Correcto** conforme a especificación. |
| **CD** (Comisión Directiva) | `200 OK` | Visualiza ranking completo y puede abrir legajos. | **Correcto** conforme a especificación. |
| **ADMIN** (Administrador Cómputos) | `200 OK` | Visualiza ranking completo y puede abrir legajos. | **Correcto** conforme a especificación. |
| **SOCIO** (Socio Ordinario) | `403 Forbidden` | Visualiza la tabla vacía sin mensaje explicativo. | **Backend correcto; UX inconsistente.** |
| **FISCALIZADORA** (Subcomisión) | `403 Forbidden` | Visualiza la tabla vacía sin mensaje explicativo. | **Backend correcto; UX inconsistente.** |

---

## 5. Opciones para Decisión del Product Owner

### Opción A — Respetar estrictamente el RBAC de la Spec (Recomendada)
> El ranking de mérito y sanciones es concebido como una **herramienta de supervisión disciplinaria e institucional interna**, reservada para las autoridades estatutarias.

* **Ventajas:**
  * Preserva al 100% la confidencialidad de las sanciones y legajos disciplinarios de los asociados (Art. 12 del Reglamento Procesal 2026).
  * No requiere modificar el backend ni altera la suite de pruebas unitarias canónicas (`test_rbac.py`).
  * Respeta los contratos vigentes de la arquitectura SDD del Sprint 1.
* **Acciones técnicas a ejecutar:**
  1. **Frontend:** Filtrar el ítem *"Ranking de Socios"* en `sidebar.component.ts` para mostrarlo exclusivamente si el usuario tiene rol `TD`, `CD` o `ADMIN`.
  2. **Frontend:** Implementar un `CanActivate` Guard en las rutas de Angular (`admin-layout.routing.ts`) que redirija a `/mis-expedientes` si un socio intenta acceder manualmente por URL.
  3. **Frontend:** Mostrar un aviso institucional de acceso restringido en lugar de una tabla vacía ante un 403.

---

### Opción B — Publicar el Ranking para Todo el Padrón
> El ranking es concebido como una **herramienta de transparencia e incentivo social**, permitiendo a cualquier socio consultar la tabla general de posiciones de méritos y sanciones.

* **Ventajas:**
  * Estimula la participación y visibilidad de las contribuciones positivas de los socios en la asociación.
  * Brinda acceso simétrico a la tabla de posiciones a todos los usuarios autenticados.
* **Implicancias y advertencias:**
  * **Exposición pública de sanciones:** Los socios podrían visualizar las quitas de puntos y sanciones de sus pares.
  * **Protección de legajos individuales (Regla CA4):** Aunque la tabla fuera pública, por secreto disciplinario ningún socio puede abrir el legajo de otro socio. En consecuencia, las filas no deberían permitir clic para abrir el modal, salvo que sea el propio legajo del usuario logueado.
* **Acciones técnicas a ejecutar:**
  1. **Backend:** Modificar la clase de permisos de `PadronListView` en Django para permitir a cualquier usuario autenticado (`IsAuthenticated`).
  2. **Backend:** Actualizar la prueba canónica `tests/test_rbac.py` para adecuarla al nuevo criterio.
  3. **Frontend:** Deshabilitar la apertura del modal al hacer clic en filas de otros socios cuando el usuario tenga rol `SOCIO`.
  4. **Documentación:** Actualizar la especificación `RBAC-SGD-AVEIT.md` y la matriz de casos de uso del Sprint 1.

---

## 6. Recomendación del Equipo de Desarrollo

Se sugiere aprobar la **Opción A**, garantizando la privacidad de los antecedentes disciplinarios y manteniendo plena coherencia con la arquitectura de seguridad y los criterios de aceptación ya aprobados para el Sprint 1.
