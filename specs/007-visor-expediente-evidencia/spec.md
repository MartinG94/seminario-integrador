# Spec 007 — Visor Autorizado de Expedientes y Evidencia Probatoria (US S4-01 / SCRUM-51)

## Contexto y Objetivo

Implementar el **Visor Autorizado de Expedientes y Evidencias** en una **vista dedicada de pantalla completa** para el Tribunal de Disciplina (TD) y la Comisión Directiva (CD) de A.V.E.I.T. El objetivo es brindar un flujo unificado, cronológico e interactivo que permita sustanciar las causas disciplinarias revisando la solicitud formal de apertura (**Formulario T01 + Hoja de Anexo Circunstanciada**), las justificaciones y descargos de cada imputado (**Formularios T02 y T03**), el historial de decisiones sobre causales (integrado con **S4-02**) y los comprobantes probatorios custodiados, garantizando:

1. **Integridad documental y verificación de hashes SHA-256.**
2. **Confidencialidad médica estricta (RBAC por campo/objeto):** acceso restringido exclusivamente a integrantes de **TD**, **CD**, **ADMIN** y al **socio imputado titular** de su propia justificación.
3. **Auditoría inmutable de accesos:** registro en base de datos de quién consulta/abre el expediente en el visor (`AuditoriaConsultaExpediente`) preservando la auditoría de descargas de piezas probatorias (`AuditoriaDescargaEvidencia`).
4. **Detección visual proactiva:** identificación inmediata de evidencias dañadas por discordancia de hash y rotulado explícito de socios con **"Plazo vencido sin descargo"**.
5. **Experiencia de pantalla completa Mobile-First, accesible (WCAG 2.2 AA)** y consistente con el sistema de notificaciones centralizadas (10 segundos, abajo a la derecha).

---

## Historia de Usuario

**Como** vocal del Tribunal de Disciplina o integrante de Comisión Directiva,  
**quiero** acceder a un visor dedicado y cronológico de la causa disciplinaria con sus descargos, evidencias custodiadas y trazabilidad integral,  
**para** sustanciar el expediente con plenas garantías de integridad, confidencialidad médica y auditoría de accesos.

---

## Requisitos en Notación EARS

1. **Ubiquitous (Vista dedicada de pantalla completa):**
   El sistema *debe* proveer una vista de pantalla completa en la ruta `/gestionar-expedientes/:id/visor` accesible para TD, CD y Administrador, exhibiendo la cabecera oficial del TD, la composición de los 3 jueces del Tribunal con cohorte `Gxx`, y la botonera de acciones resolutivas.

2. **Event-driven (Auditoría inmutable de consulta):**
   CUANDO un usuario autorizado consulte un expediente en el visor, el sistema *debe* asentar de forma automática e inmutable un registro en `AuditoriaConsultaExpediente` con usuario, legajo, rol, dirección IP, user-agent y sello de tiempo de servidor.

3. **Ubiquitous (Confidencialidad médica y RBAC por objeto):**
   El sistema *debe* permitir el acceso al visor exclusivamente a integrantes de TD, CD, ADMIN y a los socios imputados en la causa (`IsImputadoOrTribunal`). SI un usuario no autorizado intenta consultar la causa, el sistema *debe* rechazar la solicitud con HTTP `403`. MIENTRAS un socio imputado consulte el expediente, el sistema *debe* enmascarar u ocultar causales y constancias médicas de co-imputados terceros, reservando los diagnósticos médicos exclusivamente para TD, CD, ADMIN y el socio imputado titular.

4. **Event-driven (Detección de integridad SHA-256 y rotulado de plazos):**
   CUANDO se consulten las evidencias del expediente, el sistema *debe* validar en tiempo real el contenido binario custodiado contra el hash `sha256_hash` almacenado, marcando `sha256_valido=False` y `archivo_danado=True` si no concuerdan. SI un socio imputado no presentó descargo habiendo expirado el plazo legal, el sistema *debe* rotularlo explícitamente con `"Plazo vencido sin descargo"`.

5. **State-driven (Línea de tiempo cronológica):**
   El sistema *debe* construir un timeline unificado y ordenado temporalmente de forma ascendente con la apertura formal T01, notificaciones y plazos, presentaciones/retiros de descargos, resoluciones de causal y transiciones de estado.

---

## Criterios de Aceptación (DoD)

- [ ] **CA1 (Línea de tiempo y visor dedicado):** Pantalla completa con cabecera TD, 3 jueces con grupo `Gxx`, y timeline cronológico.
- [ ] **CA2 (Confidencialidad médica estricta):** Ocultamiento de diagnósticos médicos a no autorizados (solo TD, CD y titular).
- [ ] **CA3 (Auditoría inmutable de consulta):** Registro inmutable en `expedientes_auditoria_consulta` al consultar el visor.
- [ ] **CA4 (Integridad SHA-256 y Plazo Vencido):** Flags de archivo dañado ante alteración de hash y rotulado visible de "Plazo vencido sin descargo".
- [ ] **CA5 (Responsive, WCAG y Notificaciones):** UI adaptada a móvil (375px/320px) con tokens de `DESIGN.md` y notificaciones centrales de 10s.
