# Especificación: Circuito Resolutivo Oficial, Exclusión Fundada, Corrección de Puntaje Final y Enmiendas Trazables

> **Clave Jira:** `SCRUM-89` (Macro 01)  
> **Subtareas:** `SCRUM-99`, `SCRUM-100`, `SCRUM-101`, `SCRUM-102`, `SCRUM-103`  
> **Sprint:** 5 Consolidado  
> **Metodología:** Spec-Driven Development (SDD) en notación EARS  
> **Directivas del PO:** Reunión del 12/11/2026

---

## 1. Propósito y Alcance

Cerrar el circuito resolutivo del Tribunal de Disciplina de A.V.E.I.T. asegurando la persistencia exacta del puntaje ratificado, la exclusión fundada de imputados con cierre administrativo cuando no queden imputados, la firma colegiada con distinción de titular y suplente por año social (4.º, 5.º y 6.º), la emisión oficial con hash y despacho sin duplicados en `EmailOutbox`, y el circuito de enmienda trazable con contra-asientos bajo el principio de Cero `UPDATE`/`DELETE`.

---

## 2. Requerimientos Funcionales en Notación EARS

### 2.1. SCRUM-101: Corrección de Bug de Persistencia del Puntaje Final
- **EARS-101.1 (Persistencia del Dictamen):** *CUANDO* un usuario con rol `TD` califica o ratifica un descargo mediante `CausalResolutionService.decide`, *EL SISTEMA DEBE* almacenar directamente el valor en la columna `puntaje_ratificado` del modelo `DescargoExpediente` además de su registro versionado en `DecisionCausalDescargo`.
- **EARS-101.2 (Recuperación en API y Serializers):** *CUANDO* el cliente solicite el detalle del expediente (`GET /api/v1/expedientes/<id>/`), *EL SISTEMA DEBE* retornar en cada descargo de `involucrados` el valor exacto de `puntaje_ratificado` (`float`, `LLAMADO_ATENCION` o `FELICITACION`).
- **EARS-101.3 (Sincronización en UI):** *CUANDO* el usuario recargue la pantalla o abra el detalle de un expediente en estado de revisión o resolución, *EL SISTEMA DEBE* mostrar en la columna "Puntaje Final Asignado" el valor ratificado previamente sin revertir al puntaje pedido original ni a 0.

### 2.2. SCRUM-102: Exclusión Fundada de Involucrados por Rol TD
- **EARS-102.1 (Atribución Exclusiva TD):** *MIENTRAS* un expediente se encuentre en cualquier estado previo a `EMITIDO` (`CREADO`, `JUSTIFICANDO`, `REVISION_RESOLUCION`, `ESPERA_RESOLUCION`, `PENDIENTE_CORREOS`), *SI* un usuario con rol `TD` solicita excluir a un socio imputado con un motivo fundado de al menos 10 caracteres, *EL SISTEMA DEBE* registrar la exclusión inmutablemente marcando al involucrado como excluido.
- **EARS-102.2 (Rechazo a No Autorizados):** *SI* un usuario sin rol `TD` o con motivo menor a 10 caracteres intenta excluir a un socio, *EL SISTEMA DEBE* rechazar la solicitud con error `403 Forbidden` o `400 Bad Request` respectivamente.
- **EARS-102.3 (Efectos sobre el Socio):** *CUANDO* un socio es excluido de la causa, *EL SISTEMA DEBE* desestimar el cómputo de puntos sobre él, eximirlo de presentar descargos, tacharlo visualmente en la tabla de involucrados y despachar una notificación por correo electrónico tanto al socio excluido como al creador/solicitante del expediente.
- **EARS-102.4 (Cierre Administrativo del Último Involucrado):** *CUANDO* la exclusión fundada recaiga sobre el único o último socio involucrado activo de la causa, *EL SISTEMA DEBE* transicionar automáticamente el expediente a `EMITIDO` como causa archivada *"Sin efecto / Causa archivada"*, registrando la justificación en `CambioEstadoExpediente` de forma directa y administrativa sin exigir las tres firmas colegiadas (Decisión PO 12/11/2026).

### 2.3. SCRUM-99: Firma Colegiada por Año Social (4.º, 5.º y 6.º)
- **EARS-99.1 (Representación de Cohortes Activas):** *CUANDO* se genere un borrador de resolución, *EL SISTEMA DEBE* habilitar la suscripción de exactamente tres firmas correspondientes a los años sociales 4.º, 5.º y 6.º (socios Activos).
- **EARS-99.2 (Inferencia y Ajuste de Suplencia):** *CUANDO* un integrante del TD proceda a firmar, *EL SISTEMA DEBE* precargar automáticamente su condición de Titular o Suplente desde el padrón institucional (`idTipoSocio == 11` o `ComposicionTribunal`), permitiendo ajustar manualmente dicha condición en la pantalla de firma para conformaciones ad-hoc bajo el Art. 95 del Estatuto (Decisión PO 12/11/2026).
- **EARS-99.3 (Formato Canónico de Pie de Firma):** *EL SISTEMA DEBE* estampar la firma con el formato canónico `[N° de Socio] - [Nombre y Apellido] - [Gxx] [(Sup.)]`.
- **EARS-99.4 (Unicidad de Año):** *SI* un usuario intenta firmar por un año social que ya fue firmado previamente, *EL SISTEMA DEBE* rechazar la operación con `400 Bad Request` indicando que dicho año social ya cuenta con firma registrada.

### 2.4. SCRUM-100: Emisión Oficial de Resolución y Despacho sin Duplicados
- **EARS-100.1 (Sello Criptográfico e Inmutabilidad):** *CUANDO* se completen las tres firmas colegiadas reglamentarias, *EL SISTEMA DEBE* generar el hash SHA-256 de los contenidos resolutivos, sellar la resolución en estado `ISSUED` y pasar el expediente a `EMITIDO`.
- **EARS-100.2 (Despacho Idempotente Outbox):** *CUANDO* se emita la resolución oficial, *EL SISTEMA DEBE* encolar atómicamente en `EmailOutbox` los correos de notificación dirigidos a los socios involucrados, a la Comisión Directiva (`cd@aveit.org`) y al Tribunal de Disciplina (`td@aveit.org`), utilizando claves de idempotencia únicas (`resolucion-emision-{id}-{destinatario}`) para impedir envíos duplicados ante reintentos.
- **EARS-100.3 (Protección de Confidencialidad):** *EL SISTEMA DEBE* asegurar que las notificaciones generales y la carátula pública de la resolución no expongan diagnósticos médicos reservados.

### 2.5. SCRUM-103: Enmienda Trazable de Resoluciones Emitidas y Contra-Asiento
- **EARS-103.1 (Apertura de Enmienda):** *MIENTRAS* un expediente se encuentre en estado `EMITIDO` con resolución oficial vigente, *SI* un miembro del TD solicita enmendarla fundadamente por error material o hecho sobreviniente, *EL SISTEMA DEBE* crear una nueva resolución enlazada (`version = 2`), transicionar el expediente a `PENDIENTE_CORREOS` y exigir una nueva firma colegiada de los tres años sociales.
- **EARS-103.2 (Numeración Canónica Art. 19):** *EL SISTEMA DEBE* mantener el número oficial de la resolución idéntico al del expediente (`RESOLUCIÓN N/YYYY`), versionando internamente la enmienda sin crear números paralelos ni sufijos `-ENM-1` (Decisión PO 12/11/2026).
- **EARS-103.3 (Contra-asiento bajo Opción B):** *CUANDO* la resolución enmendada sea suscripta por los 3 años sociales y emitida, *EL SISTEMA DEBE* registrar en el libro mayor de puntos (`tribunal_puntajeaplicado` / `PuntajeAplicado`):
  1. Un asiento de reversión íntegra por el monto opuesto del movimiento original (*"Reversión íntegra de Res. N/YYYY por Enmienda"*).
  2. Un asiento nuevo definitivo por el valor rectificado (*"Asiento definitivo Res. N/YYYY (Versión rectificada)"*).
  Queda prohibido cualquier `UPDATE` o `DELETE` sobre registros contables existentes.
