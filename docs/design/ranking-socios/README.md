# Guía de Diseño Visual: Padrón General y Ranking de Puntos (`ranking-socios`)

Artefactos generados mediante **Stitch MCP** y revisados bajo los principios de **Better Design** (`get-ui-principle`, `get-ux-principle`, `get-review-rules`, `check-comprehension`) para el rediseño integral de la pantalla `ranking-socios` de **SGD-AVEIT**.

---

## 1. Archivos Disponibles en este Directorio

- **`ranking-socios-mockup.png`**: Captura visual en alta resolución (2560x2048) generada por Stitch MCP con el layout completo de Material Dashboard PRO, tarjeta con encabezado flotante institucional en Azul Noche AVEIT (`#151846`), barra de herramientas de filtros, tabla de 8 columnas, filas coloreadas por umbral de alerta disciplinaria y paginación reglamentaria.
- **`ranking-socios-mockup.html`**: Maqueta interactiva standalone en HTML/Tailwind con los tokens institucionales de `DESIGN.md`.
- **`README.md`**: Este documento de especificación y guía de transferencia para los siguientes hitos de implementación.

---

## 2. Decisiones de Interfaz y Tokens de Diseño

Conforme a las Notas del PO (`docs/gestion-proyecto/notasPO.md`), `DESIGN.md` y la auditoría de Better Design:

### 2.1. Eliminación de Elementos Obsoletos / Ruido Visual
- **Supresión de la tarjeta "Pautas del Régimen Disciplinario"**: Se elimina por completo el card superior estático de 3 chips informativos, dejando espacio inmediato para el encabezado flotante y los filtros.
- **Supresión de la columna "Reconciliación"**: No se expone en la vista de usuario la columna de diferencias de auditoría contable (se conserva el campo en la API backend para compatibilidad de pruebas).
- **Limpieza de la celda de Saldo**: Se remueve el badge "Habilitado Regular" y el sufijo "pts". La celda muestra exclusivamente el valor numérico con signo y dos decimales (`+4.50`, `0.00`, `-7.00`, `-10.50`), alineado a la derecha con cifras tabulares (`font-variant-numeric: tabular-nums`).

### 2.2. Cabecera de Tabla (8 Columnas Ordenables)
Las 8 columnas canónicas son:
1. **Posición**: Número entero con el ranking fijo del socio calculado sobre el padrón total por saldo descendente (desempate por Apellido y Nombre). Permanece inmutable al filtrar o reordenar por otra columna.
2. **Socio**: Nombre y Apellido del socio (con avatar con iniciales).
3. **N° de Socio**: Legajo numérico (ej. 1042, 1089), con ordenamiento numérico.
4. **Categoría**: Chip discreto `ACTIVO` (azul institucional) o `PASIVO` (gris neutro).
5. **Grupo**: Código de grupo (ej. G34, G57, G58, G60, G62, G63), con ordenamiento numérico.
6. **Subcomisión**: Subcomisión asignada (o `"Sin Subcomisión"` para socios Juniors de 1.° y 2.° año social).
7. **Saldo**: Valor numérico alineado a la derecha, en verde si $\ge 0$, gris oscuro si $-7 < \text{saldo} < 0$, ámbar si $-10 < \text{saldo} \le -7$, y rojo si $\text{saldo} \le -10$.
8. **Acciones**: Botón "Ver detalle" que abre el modal `ExpedientesSocioDialogComponent`.

### 2.3. Resaltado Normativo de Filas por Umbral de Sanción
Definido en la constante centralizada `RANKING_THRESHOLDS = { cese: -10, alerta: -7 }`:
- **Fila Normal** (`saldo > -7`): Fondo blanco estándar, hover suave.
- **Fila en Alerta Preventiva (`.row-alerta`)** (`-10 < saldo <= -7`): Fondo ámbar tenue (`rgba(245, 158, 11, 0.08)`) con borde lateral izquierdo sólido de 4px (`#F59E0B`). Incluye soporte auditivo/accesible con texto `sr-only` ("Alerta preventiva").
- **Fila Pasible de Cese Estatutario (`.row-cese`)** (`saldo <= -10`): Fondo rojo suave (`rgba(239, 68, 68, 0.08)`) con borde lateral izquierdo sólido de 4px (`#EF4444`). Incluye soporte auditivo/accesible con texto `sr-only` ("Límite de cese estatutario").

### 2.4. Barra de Herramientas de Filtros
- **Búsqueda Reactiva**: Input con debounce para filtrar por nombre, apellido o legajo.
- **Categoría**: Selector con opciones [Todas, Activo, Pasivo].
- **Subcomisión**: Selector con opciones dinámicas más [Todas, Sin Subcomisión].
- **Grupo**: Selector con grupos únicos ordenados numéricamente (G34, G57, G58, G60, G62, G63...).
- **Filas por Página**: Selector con opciones [10, 25, 50, 100, Todas].
- **Botón Limpiar**: Restablece los filtros a su estado inicial.

### 2.5. Paginación y Contador
- Texto: `Mostrando X–Y de N socios`.
- Botones accesibles de navegación: Primero (`«`), Anterior (`‹`), Números de página, Siguiente (`›`), Último (`»`).
- Cuando se selecciona "Todas", se ocultan los controles de página y la tabla activa cabecera fija (`position: sticky`).

---

## 3. Validación de Principios Better Design

1. **Tabular Numbers & Typography**: Las columnas numéricas (Posición, N° de Socio, Grupo y Saldo) implementan `tabular-nums` para evitar saltos ópticos durante el escaneo vertical o cambios de página.
2. **Hold Content Between Two Edges**: El nombre y metadatos se alinean a la izquierda; los saldos y cifras se alinean rígidamente a la derecha para escaneo instantáneo.
3. **Comprehension Check**: Superado con 0 errores críticos y 0 serios. Foco de acción único y unívoco por fila: "Ver detalle".
