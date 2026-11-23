# Manual de Usuario — SGD-AVEIT

Manual visual interactivo y modular del **Sistema de Gestión del Tribunal de Disciplina y Premiaciones (SGD-AVEIT)** de la Asociación Vocacional de Estudiantes e Ingenieros Tecnológicos (UTN FRC), organizado por módulo y rol de usuario.

Cada módulo HTML en `src/` se maqueta en tamaño **A4 vertical (210 × 297 mm)** siguiendo la línea gráfica oficial de AVEIT y se exporta de forma individual y consolidada a PDF.

---

## Índice de Módulos por Rol

| N.º | Archivo fuente (`src/`) | Módulo / Título | Roles habilitados |
| :-: | :--- | :--- | :--- |
| **01** | `01_Acceso_y_Navegacion.html` | Acceso al Sistema — Ingreso y Navegación | Todos los roles (Socio, Revisores, CD, TD, Admin) |
| **02** | `02_Mis_Expedientes_y_Descargos.html` | Mis Expedientes — Consulta y Descargos | Socio, Revisores, CD, TD, Admin |
| **03** | `03_Reglamentos.html` | Reglamentos — Consulta y Gestión | Lectura: Todos · Alta/Edición: TD, CD, Admin |
| **04** | `04_Ranking_de_Socios.html` | Ranking de Socios — Padrón y Saldos | Todos los roles (con privacidad de alertas) |
| **05** | `05_Calendario_Institucional.html` | Calendario — Días Hábiles y Plazos | Consulta/Simulador: Todos · Feriados: TD, CD, Admin |
| **06** | `06_Crear_Expediente.html` | Crear Expediente — Solicitudes de Puntos | TD, CD, Revisores de Cuentas |
| **07** | `07_Gestionar_Expedientes_TD.html` | Gestionar Expedientes — Sala del Tribunal | TD, CD, Admin (Resolución y Enmienda exclusivas TD) |
| **08** | `08_Eventos_y_Asistencia.html` | Eventos y Asistencia — Convocatorias y Cierre | TD, CD, Revisores, Admin |
| **09** | `09_Reportes_y_Administracion.html` | Reportes y Admin — Balances y Parámetros | Reportes: TD, CD, Revisores, Admin · Admin: solo Admin |

---

## Estructura del Directorio

```text
docs/manual-usuario/
├── README.md                  # Este índice y guía de compilación
├── shared/
│   ├── manual-base.css        # Estilos A4, ondas/cintas AVEIT y componentes UI
│   └── aveit_template.py      # Escudo SVG y constructores HTML UTF-8
├── scripts/
│   ├── render_pdfs.py         # Renderiza src/0*.html -> pdfs/*.pdf + Drive
│   └── merge_pdfs.py          # Combina pdfs/01..09*.pdf en manual único + Drive
├── src/                       # Módulos HTML fuente (01..09)
└── pdfs/                      # PDFs renderizados por módulo y completo
```

---

## Cómo generar los PDFs

Ejecutar desde `c:\git\seminario-integrador\docs\manual-usuario\`:

### 1. Renderizar los 9 módulos HTML a PDF

```powershell
python scripts/render_pdfs.py
```

- Detecta automáticamente **Microsoft Edge** o **Google Chrome** en modo `--headless` (o Playwright como respaldo).
- Genera cada PDF individual en `pdfs/<modulo>.pdf` e imprime el resumen con la cantidad de páginas por módulo.
- Copia automáticamente todos los PDFs a `G:\My Drive\Estudios\Seminario\Manual de Usuario\`.
- Opciones útiles:
  - `python scripts/render_pdfs.py --no-drive` para omitir la copia a Google Drive.
  - `python scripts/render_pdfs.py --pattern "07_*.html"` para renderizar un módulo puntual.

### 2. Unificar los 9 módulos en un único PDF completo

```powershell
python scripts/merge_pdfs.py
```

- Concatena `pdfs/01*.pdf` .. `pdfs/09*.pdf` en orden numérico estricto usando `pypdf` (o `pymupdf` / `PyPDF2`).
- Genera `pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf`.
- Copia automáticamente el archivo unificado a `G:\My Drive\Estudios\Seminario\Manual de Usuario\Manual_Usuario_SGD_AVEIT_Completo.pdf`.
