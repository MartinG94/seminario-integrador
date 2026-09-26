---
name: "AVEIT Design System 2026 - Material Dashboard PRO Edition"
version: "2.0.0"
description: "Sistema de diseño canónico e institucional de AVEIT (Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos - UTN FRC). Fusiona la identidad oficial del Manual de Marca 2026 con los patrones visuales y ergonómicos de Material Dashboard PRO Angular 2 (tarjetas con cabeceras flotantes, elevaciones sombreadas, paleta semántica de alto contraste y soporte integral de Modo Oscuro bajo WCAG 2.2 AA)."
colors:
  primary: "#151846"
  accent: "#6E9DDC"
  tint: "#B3D3E4"
  surface: "#F2EEE9"
  surface-card: "#FFFFFF"
  surface-elevated: "#FFFFFF"
  brand-black: "#000000"
  text-primary: "#151846"
  text-secondary: "#334155"
  text-inverse: "#FFFFFF"
  border-main: "#D1D5DB"
  border-focus: "#6E9DDC"
  success: "#15803D"
  warning: "#92400E"
  danger: "#B91C1C"
  info: "#0369A1"
  dark-surface: "#0F172A"
  dark-surface-card: "#1E293B"
  dark-surface-elevated: "#334155"
  dark-text-primary: "#F8FAFC"
  dark-text-secondary: "#94A3B8"
  dark-border-main: "#334155"
  gradient-primary-start: "#151846"
  gradient-primary-end: "#242A68"
  gradient-info-start: "#0284C7"
  gradient-info-end: "#0369A1"
  gradient-success-start: "#16A34A"
  gradient-success-end: "#15803D"
  gradient-warning-start: "#D97706"
  gradient-warning-end: "#B45309"
  gradient-danger-start: "#DC2626"
  gradient-danger-end: "#B91C1C"
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
    fontFamily: "Montserrat, sans-serif"
    fontSize: "24px"
    fontWeight: "600"
    lineHeight: "1.3"
  h3:
    fontFamily: "Montserrat, sans-serif"
    fontSize: "20px"
    fontWeight: "600"
    lineHeight: "1.4"
  subtitle:
    fontFamily: "Arimo, Roboto, sans-serif"
    fontSize: "16px"
    fontWeight: "500"
    lineHeight: "1.5"
  body:
    fontFamily: "Roboto, sans-serif"
    fontSize: "15px"
    fontWeight: "400"
    lineHeight: "1.6"
  caption:
    fontFamily: "Arimo, Roboto, sans-serif"
    fontSize: "12px"
    fontWeight: "400"
    lineHeight: "1.4"
  button:
    fontFamily: "Montserrat, sans-serif"
    fontSize: "13px"
    fontWeight: "600"
    lineHeight: "1.2"
rounded:
  none: "0px"
  sm: "4px"
  md: "8px"
  lg: "12px"
  xl: "16px"
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
    rounded: "{rounded.sm}"
    padding: "10px 20px"
  button-secondary:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: "10px 20px"
  button-round:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "10px 24px"
  button-outline:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.primary}"
    rounded: "{rounded.sm}"
    padding: "10px 20px"
  card:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: "20px"
  card-floating-header:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.md}"
    padding: "16px 20px"
  badge-accent:
    backgroundColor: "{colors.tint}"
    textColor: "{colors.primary}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  badge-status-success:
    backgroundColor: "{colors.success}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  badge-status-warning:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  badge-status-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  badge-status-info:
    backgroundColor: "{colors.info}"
    textColor: "{colors.text-inverse}"
    rounded: "{rounded.full}"
    padding: "4px 12px"
  input-field:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.sm}"
    padding: "10px 14px"
  navbar:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.primary}"
    padding: "14px 24px"
  sidebar:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.text-inverse}"
    padding: "20px 16px"
  footer:
    backgroundColor: "{colors.brand-black}"
    textColor: "{colors.surface}"
    padding: "32px 24px"
  modal-dialog:
    backgroundColor: "{colors.surface-elevated}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.lg}"
    padding: "24px"
  input-focus:
    backgroundColor: "{colors.border-focus}"
    textColor: "{colors.text-primary}"
    padding: "2px"
  container-border:
    backgroundColor: "{colors.border-main}"
    textColor: "{colors.text-secondary}"
    padding: "1px"
  card-dark:
    backgroundColor: "{colors.dark-surface-card}"
    textColor: "{colors.dark-text-primary}"
    rounded: "{rounded.lg}"
    padding: "20px"
  page-dark:
    backgroundColor: "{colors.dark-surface}"
    textColor: "{colors.dark-text-secondary}"
    padding: "24px"
  modal-dark:
    backgroundColor: "{colors.dark-surface-elevated}"
    textColor: "{colors.dark-text-primary}"
    rounded: "{rounded.lg}"
    padding: "24px"
  border-dark:
    backgroundColor: "{colors.dark-border-main}"
    textColor: "{colors.dark-text-primary}"
    padding: "1px"
---

# AVEIT Design System 2026 — Material Dashboard PRO Edition (`DESIGN.md`)

## 1. Overview y Fundamentos Visuales

Este documento formaliza la **fuente canónica de tokens de diseño y directivas de interfaz de usuario** para la plataforma **SGD-AVEIT** (Sistema de Gestión del Tribunal de Disciplina y Premiaciones) y los productos digitales de la **Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos (AVEIT)** de la Universidad Tecnológica Nacional – Facultad Regional Córdoba (UTN FRC).

El sistema consolida una evolución estética que conjuga la **identidad institucional del Manual de Marca AVEIT 2026** con los estándares ergonómicos y compositivos de **Material Dashboard PRO Angular 2** (Creative Tim), optimizando la legibilidad de datos densos, la fluidez táctil en dispositivos móviles y la alternancia sin fricción entre modos de color claro y oscuro.

### Principios Rectores de Diseño
1. **Identidad Institucional Sólida:** Preserva el Azul Noche AVEIT (`#151846`) como ancla formal de autoridad estatutaria y el Cyan Tecnológico (`#6E9DDC`) como acento interactivo.
2. **Elevación y Jerarquía Visual Material PRO:** Emplea tarjetas con cabeceras flotantes coloreadas (`floating headers`), iconos destacados con gradientes suaves y sombras policromáticas con desenfoque de elevación.
3. **Ergonomía de Datos Densos:** Resuelve tablas de expedientes, matrices de balances y ránkings masivos con tipografías proporcionales legibles y densidades ajustadas sin fatiga visual.
4. **Accesibilidad Universal (WCAG 2.2 AA):** Todo par fondo-texto cumple estrictamente un contraste cromático $\ge 4.5:1$ en texto estándar y $\ge 3.0:1$ en componentes de interfaz.
5. **Lenguaje Institucional sin Sobrecarga Jurídica (Regla Estricta de UI):** La interfaz comunica las directivas en lenguaje natural institucional claro, suprimiendo estrictamente números o citas de leyes y artículos ("Art. XX", "Art. 93", etc.).

### Implementación Técnica en Frontend
La materialización y derivación técnica de estos tokens de diseño en variables Sass y CSS Custom Properties (`:root` y `[data-theme="dark"]`) reside en [`frontend/src/assets/scss/core/_aveit-tribunal.scss`](frontend/src/assets/scss/core/_aveit-tribunal.scss).

---

## 2. Paleta Cromática y Modos de Color

### 2.1. Colores de Marca y Superficies en Modo Claro (Light Mode)

| Token | Hex | Descripción de Uso | Contraste sobre Blanco |
| :--- | :--- | :--- | :---: |
| **`primary`** | `#151846` | Azul noche institucional. Sidebar, encabezados mayores, botones primarios. | **16.6 : 1** (AAA) |
| **`accent`** | `#6E9DDC` | Cyan suave. Acento interactivo, foco, bordes activos. Con texto `primary`: | **6.0 : 1** (AA) |
| **`tint`** | `#B3D3E4` | Ice blue pastel. Badges institucionales, fondos tenues. | **10.6 : 1** (con primary) |
| **`surface`** | `#F2EEE9` | Beige cálido. Fondo global de aplicación (`body`, `page-container`). | Fondo base |
| **`surface-card`** | `#FFFFFF` | Blanco puro. Tarjetas elevadas, modales y formularios. | Fondo contenedor |
| **`text-primary`** | `#151846` | Texto principal continuo en modo claro (reemplaza al negro puro). | **16.6 : 1** (AAA) |
| **`text-secondary`**| `#334155` | Gris pizarra oscuro para subtítulos, fechas y metadatos. | **5.8 : 1** (AA) |
| **`border-main`** | `#D1D5DB` | Gris suave de 1px para delimitación de celdas e inputs. | N/A |

### 2.2. Colores y Superficies en Modo Oscuro (Dark Mode)

El Modo Oscuro de SGD-AVEIT evita el negro absoluto (`#000000`), implementando tonalidades profundas de azul pizarra (Slate/Navy) para mitigar el deslumbramiento y garantizar confort nocturno durante las sesiones remotas del Tribunal:

| Token | Hex | Rol Semántico en Modo Oscuro | Contraste con Texto Claro |
| :--- | :--- | :--- | :---: |
| **`dark-surface`** | `#0F172A` | Fondo general de la ventana y áreas de trabajo. | Base oscura |
| **`dark-surface-card`** | `#1E293B` | Fondo de tarjetas, tablas densas y paneles Kanban. | **11.8 : 1** (con `dark-text-primary`) |
| **`dark-surface-elevated`**| `#334155` | Diálogos modales, popovers y menús contextuales flotantes. | **8.2 : 1** (con `dark-text-primary`) |
| **`dark-text-primary`** | `#F8FAFC` | Blanco frío de alto contraste para títulos y datos principales. | **14.2 : 1** (AAA) |
| **`dark-text-secondary`** | `#94A3B8` | Gris azulado claro para etiquetas de apoyo y columnas de tabla. | **5.9 : 1** (AA) |
| **`dark-border-main`** | `#334155` | Líneas de división y bordes de inputs en modo oscuro. | Contraste 3:1 |

### 2.3. Semántica de Estados y Alertas Disciplinarias

| Estado | Token Base | Gradiente Material Dashboard PRO | Aplicación Disciplinaria en SGD-AVEIT |
| :--- | :--- | :--- | :--- |
| **Éxito / Aprobado** | `success: #15803D` | `#16A34A` ➔ `#15803D` | Justificación aceptada, saldo positivo de mérito, evento cerrado en término. |
| **Advertencia / Alerta**| `warning: #92400E` | `#D97706` ➔ `#B45309` | Alerta preventiva (-7 puntos), temporizador en últimas 24 horas. |
| **Crítico / Cese** | `danger: #B91C1C` | `#DC2626` ➔ `#B91C1C` | Límite crítico (-10 puntos / pérdida de condición de socio), justificación vencida. |
| **Información / Trámite**| `info: #0369A1` | `#0284C7` ➔ `#0369A1` | Apertura de causa, convocatorias a asamblea, notificaciones de acuse. |
| **Institucional AVEIT** | `primary: #151846` | `#151846` ➔ `#242A68` | Votación colegiada, dictamen de fallo, balance cuatrimestral. |

---

## 3. Tipografía y Escala Jerárquica

| Nivel | Tipografía | Tamaño | Peso | Uso Específico en Material Dashboard PRO |
| :--- | :--- | :---: | :---: | :--- |
| **`display`** | `Archivo Black` | 40px | 900 | Título central del módulo y cifras macro en balances. |
| **`h1`** | `Garet, Montserrat` | 32px | 700 | Título del submódulo activo en la barra superior. |
| **`h2`** | `Montserrat` | 24px | 600 | Cabeceras de tarjetas principales y modales de acción. |
| **`h3`** | `Montserrat` | 20px | 600 | Títulos de columnas Kanban y grupos de formularios. |
| **`subtitle`**| `Arimo, Roboto` | 16px | 500 | Subtítulos descriptivos de causas y filtros de tabla. |
| **`body`** | `Roboto` | 15px | 400 | Texto de expedientes, descargos, inputs y celdas de grilla. |
| **`caption`** | `Arimo, Roboto` | 12px | 400 | Metadatos de auditoría, marcas horarias y leyendas. |
| **`button`** | `Montserrat` | 13px | 600 | Botones de acción, pestañas de vistas y chips. |

---

## 4. Elevación y Componentes Material Dashboard PRO

### 4.1. Tarjetas con Cabecera Flotante (`Floating Header Cards`)
Característica icónica de Material Dashboard PRO. La tarjeta contiene una cabecera con margen negativo superior (`-20px`), radio redondeado (`8px`) y sombra con difusión del color del tema:
- **Cabecera Primaria (Azul Noche AVEIT):** Gradiente `from-[#151846] to-[#242A68]`, sombra `0 4px 20px 0 rgba(21, 24, 70, 0.28), 0 7px 10px -5px rgba(21, 24, 70, 0.35)`.
- **Cabecera de Alerta (Warning Amber):** Gradiente `from-[#D97706] to-[#B45309]`, sombra `0 4px 20px 0 rgba(217, 119, 6, 0.28), 0 7px 10px -5px rgba(217, 119, 6, 0.35)`.
- **Cabecera Crítica (Danger Red):** Gradiente `from-[#DC2626] to-[#B91C1C]`, sombra `0 4px 20px 0 rgba(220, 38, 38, 0.28), 0 7px 10px -5px rgba(220, 38, 38, 0.35)`.
- **Cabecera Informativa (Info Blue):** Gradiente `from-[#0284C7] to-[#0369A1]`, sombra `0 4px 20px 0 rgba(2, 132, 199, 0.28), 0 7px 10px -5px rgba(2, 132, 199, 0.35)`.

### 4.2. Tarjetas de Estadísticas con Icono Flotante (`Stat Cards`)
Caja de icono cuadrada flotante en la esquina superior izquierda (48x48px o 56x56px) con gradiente temático y sombra, valores numéricos alineados a la derecha y pie de tarjeta con separador sutil y leyenda explicativa.

### 4.3. Grilla Tabular Densa estilo Explorador de Windows
- Filas alternadas con sutil `hover` interactivo.
- Columnas ordenables con indicadores visuales de flecha (▲ / ▼).
- Buscador reactivo integrado en el marco superior.
- Paginación compacta y selectores de densidad.

### 4.4. Tablero Kanban de Estados Procesales
- 5 columnas claramente diferenciadas con contadores de expedientes.
- Tarjetas con estado visual, temporizador regresivo de 5 días hábiles y badge de puntos comprometidos (+/-).
- Acciones directas sobre la tarjeta (revisar, votar, dictaminar).

---

## 5. Reglas de Accesibilidad y Buenas Prácticas (Do's & Don'ts)

### Buenas Prácticas Obligatorias (Do's)
1. **Verificar contraste en ambos modos:** Asegurar que todo texto en modo claro supere 4.5:1 sobre fondo blanco/beige y en modo oscuro sobre slate.
2. **Persistir preferencia de tema:** Almacenar la elección en `localStorage` con clave `aveit_theme` ('light' o 'dark') y aplicar de forma reactiva sin parpadeo (*FOUC*).
3. **Comunicación Institucional Limpia:** Emplear frases como *"Plazo de 5 días hábiles para descargo"*, *"Límite preventivo de sanción"* o *"Límite de cese estatutario"*, sin mencionar números de artículos.
4. **Feedback visual inmediato:** En check-in digital ("pasar el dedo") o carga de certificados, proveer toast notifications con colores semánticos claros.

### Prohibiciones Estrictas (Don'ts)
1. **NO usar citas de artículos en la UI:** Cero mención a "Art. XX", "Art. 93", "Art. 12" en componentes visuales.
2. **NO usar fuentes genéricas de IA como Inter:** Apegarse a la matriz oficial `Montserrat / Roboto / Arimo`.
3. **NO usar negro absoluto (`#000000`) para textos continuos:** Usar siempre `{colors.text-primary}` (`#151846`) en light mode y `{colors.dark-text-primary}` (`#F8FAFC`) en dark mode.
4. **NO permitir envíos ciegos en justificaciones tipificadas:** Si se selecciona causal médica o académica, el botón debe permanecer bloqueado hasta que se adjunte un archivo probatorio.
