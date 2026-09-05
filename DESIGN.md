---
name: "AVEIT Design System 2026 - Módulo Tribunal de Disciplina"
version: "2.0.0"
description: "Sistema de diseño canónico e institucional de AVEIT (UTN FRC) para la plataforma web y el Módulo Tribunal de Disciplina y Premiaciones (SGD-AVEIT). Integra el Manual de Marca Oficial AVEIT 2026 con la plantilla técnica Material Dashboard PRO Angular (Creative Tim v2.4 / Angular 9 + Angular Material 8 + Bootstrap Material Design 4) bajo la especificación DESIGN.md de Google Labs y WCAG 2.2 AA."
colors:
  primary: "#151846"
  accent: "#6E9DDC"
  tint: "#B3D3E4"
  surface: "#F2EEE9"
  surface-card: "#FFFFFF"
  surface-elevated: "#FFFFFF"
  surface-sidebar: "#1A2035"
  brand-black: "#111827"
  text-primary: "#151846"
  text-secondary: "#475569"
  text-inverse: "#FFFFFF"
  text-sidebar: "#CBD5E1"
  text-sidebar-muted: "#94A3B8"
  border-main: "#E2E8F0"
  border-focus: "#6E9DDC"
  success: "#15803D"
  warning: "#92400E"
  danger: "#B91C1C"
  info: "#0369A1"
  rose: "#BE185D"
  purple: "#6B21A8"
typography:
  display:
    fontFamily: "Archivo Black, sans-serif"
    fontSize: "40px"
    fontWeight: "900"
    lineHeight: "1.1"
  h1:
    fontFamily: "Garet, Montserrat, sans-serif"
    fontSize: "32px"
    fontWeight: "700"
    lineHeight: "1.2"
  h2:
    fontFamily: "Montserrat, Roboto, sans-serif"
    fontSize: "24px"
    fontWeight: "600"
    lineHeight: "1.3"
  h3:
    fontFamily: "Montserrat, Roboto, sans-serif"
    fontSize: "20px"
    fontWeight: "600"
    lineHeight: "1.4"
  subtitle:
    fontFamily: "Roboto, Arimo, sans-serif"
    fontSize: "16px"
    fontWeight: "500"
    lineHeight: "1.5"
  body:
    fontFamily: "Roboto, sans-serif"
    fontSize: "14px"
    fontWeight: "400"
    lineHeight: "1.6"
  caption:
    fontFamily: "Roboto, sans-serif"
    fontSize: "12px"
    fontWeight: "400"
    lineHeight: "1.4"
  button:
    fontFamily: "Roboto, Montserrat, sans-serif"
    fontSize: "14px"
    fontWeight: "500"
    lineHeight: "1.2"
rounded:
  none: "0px"
  xs: "3px"
  sm: "4px"
  md: "8px"
  lg: "12px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  "2xl": "48px"
  "3xl": "64px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: "10px 24px"
  button-secondary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.primary}"
    rounded: "{rounded.xs}"
    padding: "10px 24px"
  button-round:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "12px 28px"
  button-outline:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.primary}"
    rounded: "{rounded.xs}"
    padding: "10px 24px"
  button-info:
    backgroundColor: "{colors.info}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: "10px 24px"
  button-success:
    backgroundColor: "{colors.success}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: "10px 24px"
  button-warning:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: "10px 24px"
  button-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: "10px 24px"
  button-rose:
    backgroundColor: "{colors.rose}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: "10px 24px"
  card:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "20px"
  card-institutional:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: "24px"
  card-header-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: "15px"
  card-header-info:
    backgroundColor: "{colors.info}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: "15px"
  card-header-success:
    backgroundColor: "{colors.success}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: "15px"
  card-header-warning:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: "15px"
  card-header-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: "15px"
  card-header-rose:
    backgroundColor: "{colors.rose}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: "15px"
  card-header-purple:
    backgroundColor: "{colors.purple}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: "15px"
  sidebar:
    backgroundColor: "{colors.surface-sidebar}"
    textColor: "{colors.text-sidebar}"
    padding: "0px"
  sidebar-item-active:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.xs}"
    padding: "10px 15px"
  sidebar-label-muted:
    backgroundColor: "{colors.surface-sidebar}"
    textColor: "{colors.text-sidebar-muted}"
    padding: "4px 15px"
  page-container:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
  navbar:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.primary}"
    padding: "10px 24px"
  badge-accent:
    backgroundColor: "{colors.tint}"
    textColor: "{colors.primary}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  badge-status-creado:
    backgroundColor: "{colors.tint}"
    textColor: "{colors.primary}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  badge-status-justificando:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  badge-status-enrevision:
    backgroundColor: "{colors.info}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  badge-status-poremitir:
    backgroundColor: "{colors.purple}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  badge-status-mailpendiente:
    backgroundColor: "{colors.rose}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  badge-status-emitido:
    backgroundColor: "{colors.success}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  badge-status-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  input-field:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.xs}"
    padding: "10px 12px"
  footer:
    backgroundColor: "{colors.brand-black}"
    textColor: "{colors.surface}"
    padding: "24px 24px"
  metadata-label:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-secondary}"
    padding: "2px 0px"
  dropdown-menu:
    backgroundColor: "{colors.surface-elevated}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.xs}"
    padding: "8px 0px"
  focus-indicator:
    backgroundColor: "{colors.border-focus}"
    textColor: "{colors.text-primary}"
    padding: "2px"
  border-container:
    backgroundColor: "{colors.border-main}"
    textColor: "{colors.text-primary}"
    padding: "1px"
  card-stats:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.md}"
    padding: "15px 20px"
---

# AVEIT Design System 2026 (`DESIGN.md`)

## Overview

Este documento establece la **fuente de verdad canónica de diseño y tokens** para todos los productos digitales de la **Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos (AVEIT)** de la Universidad Tecnológica Nacional - Facultad Regional Córdoba (UTN FRC), gobernando con máxima fidelidad técnica el **Módulo Tribunal de Disciplina y Premiaciones (SGD-AVEIT)**.

El sistema formaliza la evolución visual definida en el **Manual de Marca Oficial AVEIT 2026** y su integración nativa con la infraestructura de frontend en producción provista por Cómputos, fundamentada en la plantilla técnica **Material Dashboard PRO Angular 2** de Creative Tim ([demo de referencia oficial](https://demos.creative-tim.com/material-dashboard-pro-angular2/#/dashboard)).

### 1. Stack Tecnológico de Producción (Contrato de Ingeniería)
El Módulo Tribunal de Disciplina opera bajo el siguiente stack arquitectónico:
- **Frontend Framework:** Angular `9.1.13` sobre Node.js `16.13.2` (`DockerfileAngular`).
- **Componentes y Primitivas UI:** Angular Material `8.0.1` (`@angular/material`, `@angular/cdk`).
- **Framework CSS Base:** Bootstrap `4.3.1` + Bootstrap Material Design `4.1.2` (`bootstrap-material-design`).
- **Visualización de Datos / Estadísticas:** Chartist `0.11.2` (`chartist-plugin-tooltip`).
- **Programación Reactiva:** RxJS `6.6.7`.
- **Plantilla Base Institucional:** Material Dashboard PRO Angular `v2.3.0` / `v2.4.x` (Creative Tim).
- **Backend de Soporte:** Django `2.2.4` REST Framework (`python:3.5-slim`, MySQL vía `mysqlclient`).
- **Generación y Descarga Documental:** Compilación LaTeX server-side (`texlive-latex-base`) para emisión oficial de formularios y resoluciones en PDF (`imprimirt02`, `imprimirt03`, `imprimirres`, `imprimirdisp`).

### 2. Núcleo Funcional del Tribunal de Disciplina
El diseño visual y la ergonomía de pantalla responden directamente a los procesos estatutarios modelados:
1. **Control de Eventos y Asistencia Biológica:** Registro de huellas (`Asistente`), cálculo automatizado de tolerancias de llegada/salida (leves y graves) y asignación de sanciones base vs. `SancionPersonalizadaEventos`.
2. **Formularios Oficiales Estatutarios:**
   - **T01:** Solicitud formal de sanción o felicitación promovida por una autoridad.
   - **Formulario de Descargo Unificado (T02/T03):** Presentación del descargo del socio dentro del plazo perentorio de 5 días hábiles, unificando la justificación con causal tipificada (enfermedad, examen, laboral, etc.) y el descargo extraordinario en texto libre tipificado como causal **"Otros"**.
3. **Expedientes Disciplinarios (`NN/AAAA`):** Tramitación secuencial a través de los **6 estados oficiales**:
   - `Creado` → `Justificando` (plazo perentorio de 5 días hábiles) → `EnRevision` → `PorEmitir` → `MailPendiente` → `Emitido`.
4. **Disposiciones y Resoluciones:** Vistos y Considerandos (`DatosResolucion`) con cita de hasta 3 artículos reglamentarios y firma colegiada de hasta 3 miembros del Tribunal.
5. **Inalterabilidad y Auditoría de Puntos:** Pista de auditoría inmutable en `PuntajeAplicado` (cada registro vinculado a su expediente) y balance consolidado en `PuntajeGeneral`, con **alarmas estatutarias automáticas en 7 puntos (apercibimiento) y 10 puntos (suspensión)**.

### 3. Principios Fundamentales de Diseño
1. **Identidad Institucional UTN AVEIT:** Rigor visual, sobriedad ingenieril y tipografía jerárquica basada en el Manual de Marca 2026.
2. **Estética Material Dashboard PRO:** Cabeceras flotantes en relieve con desplazamiento negativo (`margin-top: -20px`), sombras con difusión cromática y panel lateral oscuro (`sidebar-dark`).
3. **Accesibilidad Universal (WCAG 2.2 AA / AAA):** Contraste estricto ≥ 4.5:1 en texto estándar y ≥ 3:1 en elementos gráficos interactivos.
4. **Diseño Anti-Slop (Taste Design):** Cero degradados de IA descontrolados, sustitución de negro puro por `#111827`, cero emojis en elementos de control y tipografía orientada a lectura documental densa.

---

## Colors

El sistema cromático fusiona la paleta de identidad del **Manual de Marca AVEIT 2026** con las cabeceras semánticas del sistema **Material Dashboard PRO**, optimizadas para cumplimiento estricto de accesibilidad:

### 1. Colores de Marca AVEIT (Manual 2026)
- **`primary` (`#151846` - Navy Institucional AVEIT):**
  - Azul noche profundo estatutario de la UTN FRC.
  - **Uso:** Cabeceras de tarjetas primarias (`card-header-primary`), botones de acción confirmatoria, navegación principal, badges institucionales.
  - **Contraste:** `16.6:1` sobre fondo blanco (`#FFFFFF`), `14.2:1` sobre beige (`#F2EEE9`) (supera ampliamente WCAG AAA).
- **`accent` (`#6E9DDC` - Celeste Tecnológico):**
  - Cyan suave institucional.
  - **Uso:** Acento interactivo secundario, indicador de foco accesible (`border-focus`), enlaces interactivos.
  - **Contraste:** `6.0:1` combinado con texto `{colors.primary}` (cumple WCAG AA).
- **`tint` (`#B3D3E4` - Ice Blue Pastel):**
  - Azul claro atenuado.
  - **Uso:** Fondo suave de badges de estado `Creado`, microchips informativos y resaltados suaves de filas.
  - **Contraste:** `10.6:1` con texto `{colors.primary}`.
- **`surface` (`#F2EEE9` - Beige Cálido Institucional):**
  - Off-white cálido para el contenedor principal de la aplicación (`page-container`), mitigando la fatiga visual en jornadas de deliberación.
- **`brand-black` (`#111827` - Dark Slate / Sustituto Anti-Slop):**
  - Gris noche profundo que reemplaza al `#000000` puro para evitar dureza visual excesiva. Usado en pie de página institucional (`footer`).

### 2. Superficies y Navegación Dashboard
- **`surface-sidebar` (`#1A2035` - Dark Sidebar Material):**
  - Fondo azul noche profundo característico de la barra lateral de Material Dashboard PRO Angular.
- **`text-sidebar` (`#CBD5E1` - Slate 300):**
  - Texto legible para elementos de menú de navegación lateral (contraste `10.8:1` sobre `#1A2035`, WCAG AAA).
- **`text-sidebar-muted` (`#94A3B8` - Slate 400):**
  - Metadatos, versión del sistema y títulos de categoría en la barra lateral (contraste `6.3:1`, WCAG AA).
- **`surface-card` (`#FFFFFF`):**
  - Superficie blanca para tarjetas modulares, tablas de expedientes y formularios.
- **`surface-elevated` (`#FFFFFF`):**
  - Menús desplegables, cuadros de diálogo y modales con sombra de elevación.
- **`text-primary` (`#151846`):**
  - Tipografía principal de lectura.
- **`text-secondary` (`#475569` - Slate 600):**
  - Etiquetas descriptivas, metadatos y notas al pie (contraste `7.2:1` sobre beige y `9.3:1` sobre blanco).
- **`border-main` (`#E2E8F0`):**
  - Delimitador estructural sutil para tablas y bordes de tarjeta.

### 3. Paleta Semántica Material Dashboard PRO (Cabeceras & Estados del Tribunal)
Las cabeceras desplazadas y los badges de estado emplean tonos calibrados para superar el ratio 4.5:1 con texto blanco `{colors.text-inverse}`:

| Token | Hex | Nombre Funcional | Rol en el Tribunal de Disciplina | Ratio vs. Blanco |
| :--- | :--- | :--- | :--- | :--- |
| **`info`** | `#0369A1` | Info Blue | Expediente `EnRevision`, notificaciones de eventos, filtros activos | `4.90:1` (AA) |
| **`success`** | `#15803D` | Success Green | Expediente `Emitido`, justificación `Aprobada`, asistencia regular | `4.52:1` (AA) |
| **`warning`** | `#92400E` | Amber Warning | Expediente `Justificando` (plazo 5 días), **Alerta Estatutaria 7 Puntos** | `5.95:1` (AA) |
| **`danger`** | `#B91C1C` | Crimson Danger | Justificación `Desaprobada`, falta injustificada, **Suspensión 10 Puntos** | `5.88:1` (AA) |
| **`rose`** | `#BE185D` | Creative Tim Rose | Expediente `MailPendiente` (despacho de cédulas), acciones destacadas | `6.08:1` (AA) |
| **`purple`** | `#6B21A8` | Deliberation Purple | Expediente `PorEmitir` (redacción de Vistos/Considerandos colegiados) | `8.78:1` (AAA) |

### 4. Mapeo Canónico de Estados de Expediente y Alarmas de Puntos

```
┌────────────────────────────────────────────────────────────────────────┐
│                   CICLO DE VIDA DEL EXPEDIENTE                         │
├──────────────┬──────────────────┬─────────────────┬────────────────────┤
│ Estado       │ Token Color      │ Fondo Badge     │ Texto Badge        │
├──────────────┼──────────────────┼─────────────────┼────────────────────┤
│ Creado       │ tint             │ #B3D3E4         │ #151846 (primary)  │
│ Justificando │ warning          │ #92400E         │ #FFFFFF (inverse)  │
│ EnRevision   │ info             │ #0369A1         │ #FFFFFF (inverse)  │
│ PorEmitir    │ purple           │ #6B21A8         │ #FFFFFF (inverse)  │
│ MailPendiente│ rose             │ #BE185D         │ #FFFFFF (inverse)  │
│ Emitido      │ success          │ #15803D         │ #FFFFFF (inverse)  │
└──────────────┴──────────────────┴─────────────────┴────────────────────┘
```

**Semáforo de Sanciones Estatutarias (`PuntajeGeneral`):**
- **0.0 a 6.9 Puntos:** Zona de Regularidad → Indicador `{colors.success}` (`#15803D`).
- **7.0 a 9.9 Puntos:** Apercibimiento Estatutario → Indicador `{colors.warning}` (`#92400E`).
- **10.0+ Puntos:** Suspensión de Derechos y Elección a Asamblea → Indicador `{colors.danger}` (`#B91C1C`).

---

## Typography

El sistema tipográfico combina la tradición geométrica institucional (`Archivo Black`, `Garet`, `Montserrat`) con la tipografía de base de Angular Material y Material Dashboard (`Roboto`), incorporando soporte monoespaciado para expedientes y artículos legales:

| Escala | Familia Tipográfica | Tamaño | Peso | Line-Height | Rol Semántico en el Tribunal de Disciplina |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`display`** | `Archivo Black, sans-serif` | 40px | 900 | 1.1 | Títulos de gran impacto, membretes de apertura y carátulas de dictámenes. |
| **`h1`** | `Garet, Montserrat, sans-serif` | 32px | 700 | 1.2 | Encabezados de módulo institucional ("Tribunal de Disciplina", "Mis Expedientes"). |
| **`h2`** | `Montserrat, Roboto, sans-serif` | 24px | 600 | 1.3 | Títulos de tarjetas principales (`card-title`) y encabezados de panel. |
| **`h3`** | `Montserrat, Roboto, sans-serif` | 20px | 600 | 1.4 | Subtítulos de vista, cabeceras de diálogo y etapas del Wizard procesal. |
| **`subtitle`**| `Roboto, Arimo, sans-serif` | 16px | 500 | 1.5 | Subtítulos de tarjetas (`card-category`), encabezados de tabla de expedientes. |
| **`body`** | `Roboto, sans-serif` | 14px | 400 | 1.6 | Contenido de resoluciones, considerandos, descargo de socios y celdas de tabla. |
| **`caption`** | `Roboto, sans-serif` | 12px | 400 | 1.4 | Marcas temporales, legajos, fechas perentorias y metadatos de firma. |
| **`button`** | `Roboto, Montserrat, sans-serif` | 14px | 500 | 1.2 | Acciones de control, botones de cabecera y pestañas de navegación. |

### Tipografía Técnica y Datos
- **Códigos de Expediente y Puntos:** Para números de expediente (`03/2026`), montos de sanción (`-2.0 pts`), citas de artículos reglamentarios (`Art. 18 Inc. A`) y marcas horarias biométricas, se recomienda la clase `.font-mono` con pila `'JetBrains Mono', 'Roboto Mono', monospace` (`13px`, `font-medium`).

### Iconografía Material Icons (Angular Material)
Se utiliza exclusivamente la fuente oficial `Material Icons` para todas las acciones y estados:
- `gavel`: Tribunal de Disciplina, resoluciones y disposiciones.
- `assignment`: Expedientes y formularios T01 / T02 / T03.
- `timer` / `schedule`: Control de plazo perentorio de 5 días hábiles y tolerancias de eventos.
- `fingerprint`: Registro biométrico de asistencia a eventos.
- `picture_as_pdf`: Descarga de resoluciones compiladas en LaTeX.
- `verified` / `done_all`: Aprobación y firma colegiada de autoridades.
- `warning_amber`: Alerta de acumulación de 7 puntos.
- `block`: Alerta crítica de suspensión de 10 puntos.

---

## Layout

La arquitectura de interfaz adopta el patrón estructural de **Material Dashboard PRO Angular**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SGD-AVEIT - Plataforma de Gestión                                          │
├──────────────┬──────────────────────────────────────────────────────────────┤
│ SIDEBAR      │ TOP NAVBAR (Breadcrumb, Search, Notification Badge, User)    │
│ (260px fijo) ├──────────────────────────────────────────────────────────────┤
│              │ MAIN CONTENT CONTAINER                                       │
│ • Logo AVEIT │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐          │
│ • Mini-User  │  │ Card-Stats 1 │ │ Card-Stats 2 │ │ Card-Stats 3 │ (Grid 12)│
│ • Navegación │  └──────────────┘ └──────────────┘ └──────────────┘          │
│   - Tablero  │  ┌─────────────────────────────────────────────────────────┐ │
│   - T01 Sol. │  │ [Card Header Flotante con Sombra Cromática: -20px top]  │ │
│   - Expedien.│  │ TABLA PRINCIPAL DE EXPEDIENTES / TRIBUNAL KANBAN        │ │
│   - Puntos   │  │                                                         │ │
│   - Reglament│  └─────────────────────────────────────────────────────────┘ │
└──────────────┴──────────────────────────────────────────────────────────────┘
```

1. **Sidebar Navegación (`sidebar`):**
   - Ancho estándar desktop: `260px` fijo a la izquierda.
   - Fondo: `surface-sidebar` (`#1A2035`).
   - Cabecera: Logotipo oficial AVEIT con texto `SGD-AVEIT | Tribunal`.
   - Widget de Perfil: Avatar del usuario activo, nombre, rol estatutario y menú acordeón desplegable.
   - Menú de Enlaces: Iconos `Material Icons` alineados a la izquierda, etiqueta tipográfica `Roboto 14px`, indicador de elemento activo con fondo `{colors.primary}` y radio `3px`.
   - En pantallas móviles (<992px), colapsa automáticamente a menú lateral oculto (off-canvas drawer) activado por botón de hamburguesa.
2. **Top Navbar:**
   - Barra superior flotante o integrada con `backdrop-filter: blur(8px)`.
   - Migas de pan de navegación (`breadcrumb`), buscador universal por socio/legajo/expediente, campana de notificaciones con badge contador y acceso a perfil.
3. **Contenedor Principal (`main-panel`):**
   - Fondo: `{colors.surface}` (`#F2EEE9`) para amortiguar el contraste en pantallas de alta densidad de datos.
   - Relleno perimetral: `padding: 30px 15px` en desktop, `padding: 15px 10px` en móvil.
   - Sistema de grilla: Grilla Bootstrap de 12 columnas (`col-lg-3`, `col-lg-4`, `col-lg-6`, `col-lg-12`).

---

## Elevation & Depth

La identidad tridimensional sigue el sello distintivo de **Material Dashboard PRO** de Creative Tim: **cabeceras desplazadas con sombras difusas coloreadas** que sobresalen por encima del marco de la tarjeta.

### 1. Fórmulas de Sombras para Cabeceras Flotantes (`card-header`)
Las cabeceras flotantes emplean un margen superior negativo de `-20px`, relleno interior de `15px`, radio de `3px` y sombras dobles que proyectan el tono del color temático:

```css
/* Cabecera Primaria - Navy Institucional AVEIT */
.card-header-primary {
  background: linear-gradient(60deg, #151846, #1E2368);
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.14), 0 7px 10px -5px rgba(21, 24, 70, 0.4);
}

/* Cabecera Informativa - Azul Info */
.card-header-info {
  background: linear-gradient(60deg, #0369A1, #0284C7);
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.14), 0 7px 10px -5px rgba(3, 105, 161, 0.4);
}

/* Cabecera Éxito - Verde Cumplimiento / Emitido */
.card-header-success {
  background: linear-gradient(60deg, #15803D, #16A34A);
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.14), 0 7px 10px -5px rgba(21, 128, 61, 0.4);
}

/* Cabecera Advertencia - Ámbar Plazo Perentorio / 7 Puntos */
.card-header-warning {
  background: linear-gradient(60deg, #92400E, #B45309);
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.14), 0 7px 10px -5px rgba(146, 64, 14, 0.4);
}

/* Cabecera Peligro - Rojo Sanción Crítica / 10 Puntos */
.card-header-danger {
  background: linear-gradient(60deg, #B91C1C, #DC2626);
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.14), 0 7px 10px -5px rgba(185, 28, 28, 0.4);
}

/* Cabecera Rose - Frambuesa Despacho Cédulas */
.card-header-rose {
  background: linear-gradient(60deg, #BE185D, #DB2777);
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.14), 0 7px 10px -5px rgba(190, 24, 93, 0.4);
}

/* Cabecera Púrpura - Deliberación y Considerandos */
.card-header-purple {
  background: linear-gradient(60deg, #6B21A8, #7E22CE);
  box-shadow: 0 4px 20px 0 rgba(0, 0, 0, 0.14), 0 7px 10px -5px rgba(107, 33, 168, 0.4);
}
```

### 2. Niveles de Elevación de Contenedores
- **Nivel 0 (Base):** Superficie `{colors.surface}` (`#F2EEE9`).
- **Nivel 1 (Tarjetas estándar):** Fondo blanco `{colors.surface-card}`, borde `1px solid {colors.border-main}`, sombra `0 1px 4px 0 rgba(0, 0, 0, 0.14)`.
- **Nivel 2 (Botones elevados y tarjetas en hover):** Sombra `0 4px 5px 0 rgba(0, 0, 0, 0.14), 0 1px 10px 0 rgba(0, 0, 0, 0.12), 0 2px 4px -1px rgba(0, 0, 0, 0.20)`.
- **Nivel 3 (Modales de deliberación y diálogos):** Sombra `0 24px 38px 3px rgba(0, 0, 0, 0.14), 0 9px 46px 8px rgba(0, 0, 0, 0.12), 0 11px 15px -7px rgba(0, 0, 0, 0.20)`.

---

## Shapes

La geometría de los componentes equilibra el estándar Paper Kit / Material Design:

- **`none` (`0px`):** Líneas divisorias de tablas, reglas horizontales y separadores estructurales.
- **`xs` (`3px`):** Esquinas de botones Material (`btn`), cajas de iconos de cabecera (`.card-icon`), inputs de formulario (`form-control`) y elementos activos del sidebar.
- **`sm` (`4px`):** Contenedores de alerta contextual y tarjetas compactas.
- **`md` (`8px`):** Cuerpo contenedor de las tarjetas principales (`card`) y cuadros de diálogo.
- **`lg` (`12px`):** Paneles institucionales destacados y contenedores bento-box.
- **`full` (`9999px`):** Badges de estado procesal (`badge-pill`), avatares de socio y botones de acción flotante (FAB).

---

## Components

A continuación se especifican los componentes clave adaptados a **Angular Material 8** y **Bootstrap Material Design 4**:

### 1. Tarjetas de Estadísticas del Tribunal (`card-stats`)
Utilizadas en la cabecera del módulo para monitoreo rápido:

```html
<div class="card card-stats">
  <div class="card-header card-header-warning card-header-icon">
    <div class="card-icon">
      <i class="material-icons">schedule</i>
    </div>
    <p class="card-category">Plazos por Vencer (5 días)</p>
    <h3 class="card-title font-mono">4</h3>
  </div>
  <div class="card-footer">
    <div class="stats text-danger">
      <i class="material-icons">warning</i> 2 expedientes vencen hoy
    </div>
  </div>
</div>
```

### 2. Tabla de Expedientes con Cabecera Desplazada
La vista principal de gestión del Tribunal (`/tribunal/expedientes`):

```html
<div class="card">
  <div class="card-header card-header-primary card-header-icon">
    <div class="card-icon">
      <i class="material-icons">gavel</i>
    </div>
    <h4 class="card-title">Expedientes Disciplinarios en Trámite</h4>
    <p class="card-category">Ciclo procesal oficial según Reglamento Interno</p>
  </div>
  <div class="card-body table-responsive">
    <table class="table table-hover">
      <thead class="text-primary font-weight-bold">
        <tr>
          <th>Expediente</th>
          <th>Socio Imputado</th>
          <th>Causa / Origen</th>
          <th>Estado Procesal</th>
          <th>Puntos</th>
          <th class="text-right">Acciones</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td class="font-mono">14/2026</td>
          <td>Gómez, Martín (Leg. 74125)</td>
          <td>Ausencia Asamblea Extraordinaria</td>
          <td><span class="badge badge-status-justificando">Justificando</span></td>
          <td class="font-mono text-danger font-weight-bold">-2.0</td>
          <td class="td-actions text-right">
            <button type="button" rel="tooltip" class="btn btn-info btn-link btn-sm" title="Ver Expediente">
              <i class="material-icons">visibility</i>
            </button>
            <button type="button" rel="tooltip" class="btn btn-success btn-link btn-sm" title="Revisar T02/T03">
              <i class="material-icons">assignment_turned_in</i>
            </button>
            <button type="button" rel="tooltip" class="btn btn-rose btn-link btn-sm" title="Descargar PDF">
              <i class="material-icons">picture_as_pdf</i>
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
```

### 3. Formularios Material con Etiquetas Flotantes (T01, Formulario de Descargo)
Campos interactivos con soporte nativo de Bootstrap Material Design:

```html
<div class="card">
  <div class="card-header card-header-rose">
    <h4 class="card-title">Formulario de Descargo</h4>
    <p class="card-category">Presentación sujeta a plazo perentorio de 5 días hábiles</p>
  </div>
  <div class="card-body">
    <form>
      <div class="row">
        <div class="col-md-6">
          <div class="form-group bmd-form-group">
            <label class="bmd-label-floating">Causal Tipificada (Catálogo Estatutario)</label>
            <select class="form-control" required>
              <option value="1">Enfermedad (con certificado médico)</option>
              <option value="2">Compromiso Laboral Excepcional</option>
              <option value="3">Mesa de Examen Universitario</option>
              <option value="otros">Otros (Descargo extraordinario no tipificado)</option>
            </select>
          </div>
        </div>
        <div class="col-md-6">
          <div class="form-group bmd-form-group">
            <label class="bmd-label-floating">Fecha y Hora del Evento</label>
            <input type="text" class="form-control" value="02/09/2026 19:30" readonly>
          </div>
        </div>
      </div>
      <div class="row mt-3">
        <div class="col-md-12">
          <div class="form-group bmd-form-group">
            <label class="bmd-label-floating">Fundamentación y Aclaraciones del Descargo</label>
            <textarea class="form-control" rows="4"></textarea>
          </div>
        </div>
      </div>
      <!-- Subida de comprobante adjunto -->
      <div class="row mt-3">
        <div class="col-md-12">
          <label class="text-secondary font-weight-bold">Comprobante Adjunto (PDF o JPG, máx. 5MB)</label>
          <div class="fileinput fileinput-new text-center d-block">
            <span class="btn btn-outline-primary btn-round btn-file">
              <span class="fileinput-new">Seleccionar Certificado</span>
              <input type="file" name="justificativo" />
            </span>
          </div>
        </div>
      </div>
      <button type="submit" class="btn btn-primary pull-right">Enviar Formulario de Descargo</button>
    </form>
  </div>
</div>
```

### 4. Pista de Auditoría Inmutable de Puntaje (`PuntajeAplicado`)
Tabla transaccional vinculada a cada movimiento de puntos:

```html
<div class="card">
  <div class="card-header card-header-info card-header-icon">
    <div class="card-icon">
      <i class="material-icons">timeline</i>
    </div>
    <h4 class="card-title">Registro Histórico e Inalterable de Puntos</h4>
    <p class="card-category">Pista de auditoría legal vinculada al expediente de origen</p>
  </div>
  <div class="card-body table-responsive">
    <table class="table">
      <thead>
        <tr>
          <th>Fecha/Hora</th>
          <th>Socio</th>
          <th>Movimiento</th>
          <th>Expediente de Origen</th>
          <th>Saldo Resultante</th>
          <th>Estado Estatutario</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>03/09/2026 10:15</td>
          <td>Pérez, Lucas</td>
          <td class="font-mono text-danger font-weight-bold">-3.0 pts</td>
          <td class="font-mono"><a href="#">Disp. 05/2026 (Exp. 08/2026)</a></td>
          <td class="font-mono font-weight-bold">7.0 pts</td>
          <td><span class="badge badge-warning">Alerta: 7 Puntos (Apercibimiento)</span></td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
```

### 5. Barra de Previsualización y Descarga LaTeX / PDF
Componente para visualización de documentos emitidos:

```html
<div class="alert alert-info alert-with-icon d-flex align-items-center justify-content-between">
  <div class="d-flex align-items-center">
    <i class="material-icons mr-3">picture_as_pdf</i>
    <span><strong>Resolución Oficial Compilada:</strong> Expediente N° 14/2026 listo para despacho con firma colegiada.</span>
  </div>
  <a href="/tribunal/imprimirres/14/" target="_blank" class="btn btn-sm btn-white text-primary font-weight-bold">
    Descargar PDF Oficial
  </a>
</div>
```

---

## Do's and Don'ts

### Qué HACER (Do's)
- **HACER:** Utilizar siempre cabeceras flotantes desplazadas con sombras cromáticas (`.card-header-primary`, `.card-header-info`, etc.) en las tarjetas estructurales del módulo para preservar la coherencia de Material Dashboard PRO.
- **HACER:** Respetar los ratios de contraste WCAG 2.2 AA (mínimo 4.5:1 en texto estándar) asegurando que cualquier badge o botón con texto blanco `{colors.text-inverse}` utilice los colores semánticos normados (`#15803D`, `#92400E`, `#B91C1C`, `#0369A1`, `#BE185D`, `#6B21A8`).
- **HACER:** Destacar en ámbar `{colors.warning}` cualquier expediente en estado `Justificando` cuyo plazo de 5 días hábiles esté próximo a expirar.
- **HACER:** Formatear siempre números de expediente (`NN/AAAA`), artículos reglamentarios y variaciones de puntaje con fuentes monoespaciadas (`font-mono`).
- **HACER:** Incorporar siempre enlace o referencia al PDF oficial generado en LaTeX para resoluciones, formulario de descargo (T02/T03) y disposiciones colegiadas.

### Qué NO HACER (Don'ts)
- **NO HACER:** Emplear negro puro (`#000000`) en fondos o textos; utilizar exclusivamente `{colors.brand-black}` (`#111827`) o `{colors.text-primary}` (`#151846`) conforme a las pautas anti-slop.
- **NO HACER:** Utilizar emojis en botones, cabeceras o tablas procesales; emplear exclusivamente la biblioteca `Material Icons`.
- **NO HACER:** Permitir la edición manual o arbitraria del puntaje consolidado de un socio sin la correspondiente transacción inmutable en `PuntajeAplicado` respaldada por un expediente.
- **NO HACER:** Colocar texto blanco sobre fondo de acento `{colors.accent}` (`#6E9DDC`) o tinte `{colors.tint}` (`#B3D3E4`), ya que no superan el ratio mínimo de 4.5:1.
- **NO HACER:** Crear tarjetas planas sin elevación ni cabecera flotante para paneles de datos principales, lo cual desvirtúa la identidad Material Dashboard PRO de la plataforma.
