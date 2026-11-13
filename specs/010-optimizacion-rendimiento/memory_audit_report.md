# Informe de Auditoría de Rendimiento y Memoria (T-87.19)
**Épica:** SCRUM-87 (MACRO-06: Optimización Integral de Rendimiento: RAM, CPU y Base de Datos)  
**Fecha:** 13 de Noviembre de 2026  
**Rama:** `feature/SCRUM-87-optimizacion-rendimiento`  
**Objetivo:** Verificación empírica de ciclo de vida, prevención de fugas RxJS/DOM, estabilidad en estado estable (`Heap Delta <= 0.5 MB` en 10 ciclos tras estabilización JIT) y `0` nodos DOM desconectados (RNF-03).

---

## 1. Resumen Ejecutivo de Mediciones (Chrome Headless + CDP)

La verificación se ejecutó directamente contra el bundle de producción compilado (`npx ng build --configuration production`, `BUILD_EXIT=0`), servido por HTTP local con respuestas de API simuladas en el mismo origen (`/api/v1/*`) e instrumentado mediante Chrome DevTools Protocol (`Page`, `Runtime`, `Performance.getMetrics`, `HeapProfiler.collectGarbage`, `HeapProfiler.takeHeapSnapshot`) a lo largo de **20 ciclos completos** (100 transiciones de ruta) recorriendo las 5 vistas principales:

1. `#/ranking-socios` (`<mat-paginator>` verificado en DOM)
2. `#/gestionar-expedientes` + cambio a pestaña `LISTA EN TABLA` (`<mat-paginator>` verificado en DOM)
3. `#/mis-expedientes` (`<mat-paginator>` verificado en DOM)
4. `#/eventos-asistencia` + cambio a pestaña `MIS EVENTOS` (`<mat-paginator>` verificado en DOM)
5. `#/reportes`

### Métricas Medidas vs Criterios de Aceptación

| Métrica Evaluada | Umbral Requerido (RNF-03) | Resultado Medido (Chrome CDP) | Estado |
| :--- | :--- | :--- | :---: |
| **Heap Memory Delta (estado estable, Ciclos 10 -> 20)** | $\le 0.50\text{ MB}$ | **$+0.2515\text{ MB}$** (`9.564 MB -> 9.816 MB`) | **CUMPLIDO** |
| **Heap Memory Delta (Ciclos 2 -> 10, incl. warmup JIT V8)** | Informativo (incl. compilación JIT) | **$+0.9912\text{ MB}$** (`8.573 MB -> 9.564 MB`) | **JUSTIFICADO (V8 JIT)** |
| **Retención neta objetos JS de app (`Array` + `Object`, Ciclos 2 -> 20)** | Sin crecimiento lineal anómalo | **$+4,372\text{ bytes}$** (`+138 Array`, `+85 Object` en 90 navegaciones) | **CUMPLIDO** |
| **Nodos DOM Desconectados (`Detached *` vía Heap Snapshot)** | $0$ nodos huérfanos | **$0$ en Ciclo 2 / $0$ en Ciclo 20** (`delta = 0`) | **CUMPLIDO** |
| **Nodos DOM Vivos (`Performance.Nodes`)** | Estabilidad entre ciclos | **$469 -> 469$** (`delta = 0`) | **CUMPLIDO** |
| **Event Listeners Vivos (`Performance.JSEventListeners`)** | Estabilidad entre ciclos | **$69 -> 69$** (`delta = 0`) | **CUMPLIDO** |
| **Errores de consola y excepciones JS (`Runtime`)** | $0$ errores | **$0$ console errors / $0$ runtime exceptions** | **CUMPLIDO** |
| **Suite Karma Ciclo de Vida y Unitaria (`ChromeHeadless`)** | $100\%$ verde | **$664 / 664\text{ SUCCESS}$** (`0` warnings) | **CUMPLIDO** |

---

## 2. Desglose de Telemetría CDP por Ciclo y Constructor

### 2.1. Evolución de `JSHeapUsedSize` post-GC (`HeapProfiler.collectGarbage`)

| Punto de Medición | `JSHeapUsedSize` (MB) | `JSHeapTotalSize` (MB) | `Nodes` | `JSEventListeners` | `Detached Nodes` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Ciclo 2** (pos-warmup inicial) | `8.573` (`8,989,316 B`) | `9.50` | `469` | `69` | `0` |
| **Ciclo 3** | `8.972` (`9,408,024 B`) | `9.75` | `457` | `68` | — |
| **Ciclo 5** | `9.162` (`9,607,064 B`) | `9.75` | `469` | `69` | — |
| **Ciclo 7** | `9.296` (`9,747,560 B`) | `10.00` | `469` | `69` | — |
| **Ciclo 10** (corte estado estable) | `9.564` (`10,028,716 B`) | `10.25` | `469` | `69` | — |
| **Ciclo 15** | `9.722` (`10,194,116 B`) | `10.25` | `469` | `69` | — |
| **Ciclo 20** | `9.816` (`10,292,460 B`) | `10.50` | `469` | `69` | `0` |

### 2.2. Diff de Constructores en V8 Heap Snapshot (`Ciclo 2 -> Ciclo 20`)

El diferencial de instantáneas de heap de Chrome confirmó que más del $90\%$ del incremento acumulado desde el arranque correspondió a estructuras internas de optimización JIT de V8 y métricas del propio navegador, descartando fugas en componentes Angular o servicios RxJS:
- **Código JIT y metadatos internos de V8:** `system / InstructionStream` (`+769,472 B`), `system / TrustedByteArray` (`+219,072 B`), `system / ProtectedFixedArray` (`+83,204 B`), `system / WeakArrayList` (`+73,104 B`), `system / Code` (`+59,904 B`), `system / FeedbackVector` (`+52,348 B`).
- **Observadores nativos de Chrome:** `PerformanceResourceTiming` (`+28,424 B`), `DOMRectReadOnly` (`+24,640 B`), `LayoutShift` (`+19,000 B`), `LayoutShiftAttribution` (`+8,800 B`), `NavigationHistoryEntry` (`+7,488 B`).
- **Objetos JS de aplicación:** `Array` (`+2,208 B` / `+138` instancias), `Object` (`+2,164 B` / `+85` instancias).

---

## 3. Mecanismos Verificados

1. **Desuscripción RxJS y cancelación HTTP (`takeUntil(this.destroy$)` + `ngOnDestroy`):** Verificado en componentes principales, shell (`NavbarComponent`, `SidebarComponent`, `AdminLayoutComponent`) y modales (`ReglamentosComponent`, `ExpedientesSocioDialogComponent`), cancelando requests pendientes al desmontar.
2. **Aislamiento de timers, `PerfectScrollbar` y `ObjectURL`:** `interval(1000)` en `MisExpedientesComponent` corre fuera de `NgZone` (`runOutsideAngular`) y reingresa a zona solo cuando existe un plazo activo; `activeTimers`, `activeObjectUrls`, listeners globales y `scrollLock.reset()` se limpian deterministamente en `ngOnDestroy()`.
3. **Eliminación de `ngDoCheck()`, `OnPush`, memoización y `trackBy`:** Cero ocurrencias de `ngDoCheck` en `frontend/src/app`; `ChangeDetectionStrategy.OnPush`, `trackBy` puros y cacheo por clave en getters calientes (`SolicitarPuntosComponent`, `AsistenciaEventoComponent`, `ReportesComponent`, `RankingSociosComponent`, `GestionarExpedientesComponent`, `MisExpedientesComponent`).
4. **Tests automatizados (`frontend/src/app/utils/lifecycle-memory.spec.ts`):** Verifican cierre de `destroy$`, cancelación de peticiones HTTP abiertas, limpieza de `activeTimers` y llamada a `scrollLock.reset()` al destruir los 13 componentes auditados.
