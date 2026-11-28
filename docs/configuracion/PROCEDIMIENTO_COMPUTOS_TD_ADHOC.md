# Procedimiento Operativo — Asignación y Revocación de Tribunal Ad-Hoc (Subcomisión de Cómputos)

> **Referencia Normativa:** Estatuto AVEIT Reforma 2026, Arts. 92 y 95; Reglamento Procesal 2026, Art. 24.  
> **Ámbito:** Procedimiento técnico manual ejecutado por la Subcomisión de Cómputos (`Role.ADMIN`) cuando una causa disciplinaria requiere integración ad hoc designada por Asamblea General.

---

## 1. Contexto

Cuando un expediente disciplinario involucra al titular y suplente de un mismo año social (Caso A) o a tres o más integrantes del Tribunal de Disciplina (Caso B), la causa no puede resolverse con el cuerpo ordinario.

La Asamblea General designa a un socio del año social correspondiente para integrar el Tribunal ad hoc. La Subcomisión de Cómputos debe otorgarle temporalmente el rol y permisos en el sistema para que participe en la tramitación y firma de la resolución, y revocar dichos permisos una vez emitida la causa.

---

## 2. Habilitación Temporal del Socio Designado

Una vez comunicada formalmente la designación por Asamblea, el Administrador de Cómputos ejecuta las siguientes operaciones:

### A. Base de Datos Legacy (`socio_lista`)
Se asigna el cargo de Miembro del Tribunal de Disciplina (`idTipoSocio = 10` Titular o `11` Suplente):

```sql
-- Verificar ficha actual del socio designado
SELECT nroSocio, apellido, nombre, anoSocial, idTipoSocio, user_id
FROM socio_lista
WHERE nroSocio = <NRO_SOCIO>;

-- Otorgar cargo de Tribunal de Disciplina
UPDATE socio_lista
SET idTipoSocio = 10
WHERE nroSocio = <NRO_SOCIO>;
```

### B. Aplicación SGD-AVEIT (Panel de Administración `/admin/parametros`)
El alta del rol `TD` en la aplicación **no** se realiza mediante `UPDATE` manual en `socios_socio`, sino desde el Panel de Administración (`/admin/parametros`, `POST /api/v1/admin/usuarios-td/`), que ejecuta `TribunalMemberService` y registra auditoría inmutable en `core_cambio_rol_tribunal` (`TribunalRoleChange`).

---

## 3. Sustanciación y Emisión de la Causa

1. El socio designado inicia sesión con su Número de Socio (`numero_socio`).
2. Posee facultades para acceder a la causa, evaluar justificativos (T02/T03), transicionar el expediente y generar la resolución oficial.
3. Al avanzar el expediente al estado `Pendiente de firma y envío` (`pendiente_correos`), el sistema **estampa inmutablemente** la composición en `expedientes_composicion_tribunal` y sus integrantes en `expedientes_integrante_composicion`, fijando su pie de firma canónico:  
   `[N° de Socio] - [Nombre y Apellido] - [Gxx]`
4. La causa avanza a `Expedientes ya emitidos` (`emitido`).

---

## 4. Revocación Post-Emisión

Una vez que el expediente ha sido emitido, el Administrador de Cómputos restablece la condición ordinaria del socio:

1. **En la aplicación SGD-AVEIT:** revoca el rol `TD` desde `/admin/parametros` (`DELETE /api/v1/admin/usuarios-td/<socio_id>/`), dejando registro auditable en `core_cambio_rol_tribunal`.
2. **En el padrón legado externo (`socio_lista`):**

```sql
-- Restablecer cargo a Socio Ordinario en padrón legado
UPDATE socio_lista
SET idTipoSocio = 12
WHERE nroSocio = <NRO_SOCIO>;
```

> [!NOTE]
> **Preservación Histórica Garantizada:**  
> La revocación de permisos **no altera ni borra** la firma estampada en la resolución emitida. La tabla `expedientes_integrante_composicion` es de sólo-inserción (`InsertOnlyModel`) y preserva de forma permanente la participación del socio designado.
