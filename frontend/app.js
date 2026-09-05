/**
 * SGD-AVEIT - Módulo de Tribunal de Disciplina y Premiaciones
 * Lógica de la Aplicación Frontend e Interactividad
 * Cumplimiento estricto: Cero mención a números de leyes o artículos ("Art. XX").
 */

(function () {
  'use strict';

  // =========================================================================
  // 1. ESTADO DE LA APLICACIÓN Y DATOS INICIALES
  // =========================================================================

  const STORAGE_KEY = 'sgd_aveit_tribunal_data_v2';

  // Actores disponibles para la simulación interactiva
  const ACTORS = {
    socio: {
      id: 'socio',
      nombre: 'Lucas Guillén',
      legajo: '85194',
      categoria: 'Socio Ordinario (Junior - 2º Año)',
      subcomision: 'Cómputos',
      rol: 'Socio',
      avatar: 'LG'
    },
    juez1: {
      id: 'juez1',
      nombre: 'Nicolás Rosales',
      legajo: '408917',
      categoria: 'Juez del Tribunal (Senior - 4º Año)',
      subcomision: 'Tribunal de Disciplina',
      rol: 'Juez TD',
      avatar: 'NR'
    },
    cd: {
      id: 'cd',
      nombre: 'Diego Sánchez',
      legajo: '87414',
      categoria: 'Comisión Directiva (Senior - 5º Año)',
      subcomision: 'Mesa Directiva',
      rol: 'Comisión Directiva',
      avatar: 'DS'
    },
    autoridad: {
      id: 'autoridad',
      nombre: 'Lucas Gastiaburu',
      legajo: '74907',
      categoria: 'Presidente de Subcomisión (Senior - 4º Año)',
      subcomision: 'Cómputos',
      rol: 'Autoridad',
      avatar: 'LG'
    }
  };

  // Estados procesales oficiales consolidados (5 Estados)
  const ESTADOS = {
    creado: {
      id: 'creado',
      nombre: 'Expediente Creado',
      badgeClass: 'badge-mat-info',
      icon: 'file_copy'
    },
    justificando: {
      id: 'justificando',
      nombre: 'En período de justificaciones',
      badgeClass: 'badge-mat-warning',
      icon: 'schedule'
    },
    revision_resolucion: {
      id: 'revision_resolucion',
      nombre: 'En revisión y resolución',
      badgeClass: 'badge-mat-primary',
      icon: 'gavel'
    },
    pendiente_firma: {
      id: 'pendiente_firma',
      nombre: 'Pendiente de firma y envío',
      badgeClass: 'badge-mat-rose',
      icon: 'history_edu'
    },
    emitido: {
      id: 'emitido',
      nombre: 'Expedientes ya emitidos',
      badgeClass: 'badge-mat-success',
      icon: 'verified'
    }
  };

  // Datos base representativos
  const DEFAULT_DATA = {
    currentActorId: 'juez1',
    activeSubmodule: 'gestionar-expedientes',
    expedientesViewMode: 'kanban', // 'kanban' o 'explorer'
    theme: localStorage.getItem('aveit_theme') || 'light',
    
    // Lista de Expedientes
    expedientes: [
      {
        id: 'EXP-2026-042',
        socio: 'Lucas Guillén',
        legajo: '85194',
        subcomision: 'Cómputos',
        categoria: 'Junior (2º Año)',
        motivo: 'Inasistencia a Asamblea General Ordinaria',
        tipoPuntos: 'sancion',
        puntos: -2.0,
        estado: 'justificando',
        fechaApertura: '03/09/2026 10:30',
        horasPlazoRestantes: 68, // Plazo de 5 días hábiles
        origen: 'Cierre de Asamblea General',
        autoridadSolicitante: 'Comisión Directiva',
        justificacion: null,
        votos: { juez1: null, juez2: null, juez3: null },
        firmas: { juez1: false, juez2: false, juez3: false },
        considerando: ''
      },
      {
        id: 'EXP-2026-038',
        socio: 'Luis Urviola',
        legajo: '409953',
        subcomision: 'Mantenimiento',
        categoria: 'Junior (1º Año)',
        motivo: 'Omisión de turno de limpieza general en sede',
        tipoPuntos: 'sancion',
        puntos: -2.0,
        estado: 'revision_resolucion',
        fechaApertura: '30/08/2026 14:00',
        horasPlazoRestantes: 0,
        origen: 'Reporte de Subcomisión de Mantenimiento',
        autoridadSolicitante: 'Presidente de Mantenimiento',
        justificacion: {
          tipo: 'T02 (Causal con Certificado)',
          causal: 'Enfermedad debidamente certificada',
          archivoNombre: 'certificado_medico_urviola.pdf',
          observaciones: 'Presento certificado de atención en Hospital de Urgencias por gastroenteritis aguda con reposo de 48 hs.',
          fechaEnvio: '01/09/2026 18:22'
        },
        votos: { juez1: 'aprobar', juez2: null, juez3: null },
        firmas: { juez1: false, juez2: false, juez3: false },
        considerando: 'Habiendo evaluado el certificado médico emitido por profesional con matrícula vigente, se constata la imposibilidad física de asistencia al turno asignado.'
      },
      {
        id: 'EXP-2026-035',
        socio: 'Axel Villegas',
        legajo: '403655',
        subcomision: 'Cómputos',
        categoria: 'Senior (3º Año)',
        motivo: 'Desarrollo extraordinario del nuevo servidor institucional',
        tipoPuntos: 'premio',
        puntos: 3.0,
        estado: 'pendiente_firma',
        fechaApertura: '26/08/2026 11:15',
        horasPlazoRestantes: 0,
        origen: 'Solicitud Formulario de Reconocimiento',
        autoridadSolicitante: 'Presidente de Cómputos',
        justificacion: null,
        votos: { juez1: 'aprobar', juez2: 'aprobar', juez3: 'aprobar' },
        firmas: { juez1: true, juez2: true, juez3: false },
        considerando: 'Visto el informe técnico de migración de servidores y la dedicación superior a 40 horas no remuneradas para el despliegue del sistema web, corresponde otorgar reconocimiento extraordinario.'
      },
      {
        id: 'EXP-2026-029',
        socio: 'Tomas Augusto Quiroz',
        legajo: '415327',
        subcomision: 'Organización y Eventos',
        categoria: 'Junior (2º Año)',
        motivo: 'Coordinación destacada en campaña de la Gran Rifa Anual',
        tipoPuntos: 'premio',
        puntos: 2.0,
        estado: 'emitido',
        fechaApertura: '18/08/2026 09:00',
        horasPlazoRestantes: 0,
        origen: 'Solicitud Formulario de Reconocimiento',
        autoridadSolicitante: 'Comisión Directiva',
        justificacion: null,
        votos: { juez1: 'aprobar', juez2: 'aprobar', juez3: 'aprobar' },
        firmas: { juez1: true, juez2: true, juez3: true },
        considerando: 'Se reconoce formalmente la dedicación y liderazgo en la fiscalización de talonarios y logística de recaudación.'
      },
      {
        id: 'EXP-2026-045',
        socio: 'Mateo Fernández',
        legajo: '89102',
        subcomision: 'Relaciones Institucionales',
        categoria: 'Junior (1º Año)',
        motivo: 'Inasistencia injustificada a Reunión Ordinaria de Socios',
        tipoPuntos: 'sancion',
        puntos: -1.0,
        estado: 'creado',
        fechaApertura: '04/09/2026 19:40',
        horasPlazoRestantes: 120,
        origen: 'Cierre de Asistencia Digital',
        autoridadSolicitante: 'Comisión Directiva',
        justificacion: null,
        votos: { juez1: null, juez2: null, juez3: null },
        firmas: { juez1: false, juez2: false, juez3: false },
        considerando: ''
      },
      {
        id: 'EXP-2026-041',
        socio: 'Sofía Romero',
        legajo: '88310',
        subcomision: 'Prensa y Difusión',
        categoria: 'Junior (2º Año)',
        motivo: 'Retiro anticipado sin aviso en jornada de difusión',
        tipoPuntos: 'sancion',
        puntos: -0.5,
        estado: 'justificando',
        fechaApertura: '02/09/2026 16:10',
        horasPlazoRestantes: 18,
        origen: 'Reporte de Subcomisión de Prensa',
        autoridadSolicitante: 'Presidente de Prensa y Difusión',
        justificacion: null,
        votos: { juez1: null, juez2: null, juez3: null },
        firmas: { juez1: false, juez2: false, juez3: false },
        considerando: ''
      },
      {
        id: 'EXP-2026-022',
        socio: 'Agustín Benítez',
        legajo: '79214',
        subcomision: 'Gestión Social y Ambiental',
        categoria: 'Senior (4º Año)',
        motivo: 'Reincidencia continuada en omisión de tareas estatutarias',
        tipoPuntos: 'sancion',
        puntos: -2.0,
        estado: 'emitido',
        fechaApertura: '10/08/2026 11:00',
        horasPlazoRestantes: 0,
        origen: 'Solicitud Formal Comisión Directiva',
        autoridadSolicitante: 'Comisión Directiva',
        justificacion: null,
        votos: { juez1: 'rechazar', juez2: 'rechazar', juez3: 'rechazar' },
        firmas: { juez1: true, juez2: true, juez3: true },
        considerando: 'Verificada la reiterada falta de compromiso y acumulación de apercibimientos formales, se ratifica la sanción solicitada.'
      }
    ],

    // Padrón de Socios y Ranking General
    socios: [
      { id: '1', nombre: 'Diego Sánchez', legajo: '87414', categoria: 'Senior (5º Año)', subcomision: 'Mesa Directiva', saldo: 6.5, felicitaciones: 4, llamadosAtencion: 0, estado: 'regular' },
      { id: '2', nombre: 'Lucas Gastiaburu', legajo: '74907', categoria: 'Senior (4º Año)', subcomision: 'Cómputos', saldo: 5.0, felicitaciones: 3, llamadosAtencion: 0, estado: 'regular' },
      { id: '3', nombre: 'Tomas Augusto Quiroz', legajo: '415327', categoria: 'Junior (2º Año)', subcomision: 'Organización y Eventos', saldo: 4.5, felicitaciones: 3, llamadosAtencion: 1, estado: 'regular' },
      { id: '4', nombre: 'Axel Villegas', legajo: '403655', categoria: 'Senior (3º Año)', subcomision: 'Cómputos', saldo: 3.5, felicitaciones: 2, llamadosAtencion: 0, estado: 'regular' },
      { id: '5', nombre: 'Nicolás Rosales', legajo: '408917', categoria: 'Senior (4º Año)', subcomision: 'Tribunal de Disciplina', saldo: 3.0, felicitaciones: 2, llamadosAtencion: 0, estado: 'regular' },
      { id: '6', nombre: 'Camila López', legajo: '88240', categoria: 'Junior (1º Año)', subcomision: 'Recursos Humanos', saldo: 1.5, felicitaciones: 1, llamadosAtencion: 0, estado: 'regular' },
      { id: '7', nombre: 'Martín Gómez', legajo: '86104', categoria: 'Junior (2º Año)', subcomision: 'Prensa y Difusión', saldo: 0.5, felicitaciones: 1, llamadosAtencion: 1, estado: 'regular' },
      { id: '8', nombre: 'Lucas Guillén', legajo: '85194', categoria: 'Junior (2º Año)', subcomision: 'Cómputos', saldo: 0.0, felicitaciones: 1, llamadosAtencion: 1, estado: 'regular' },
      { id: '9', nombre: 'Sofía Romero', legajo: '88310', categoria: 'Junior (2º Año)', subcomision: 'Prensa y Difusión', saldo: -0.5, felicitaciones: 0, llamadosAtencion: 1, estado: 'regular' },
      { id: '10', nombre: 'Mateo Fernández', legajo: '89102', categoria: 'Junior (1º Año)', subcomision: 'Relaciones Institucionales', saldo: -1.0, felicitaciones: 0, llamadosAtencion: 2, estado: 'regular' },
      { id: '11', nombre: 'Luis Urviola', legajo: '409953', categoria: 'Junior (1º Año)', subcomision: 'Mantenimiento', saldo: -2.0, felicitaciones: 0, llamadosAtencion: 2, estado: 'regular' },
      { id: '12', nombre: 'Julián Castro', legajo: '84102', categoria: 'Senior (3º Año)', subcomision: 'Relaciones Institucionales', saldo: -4.5, felicitaciones: 1, llamadosAtencion: 3, estado: 'regular' },
      { id: '13', nombre: 'Franco Varela', legajo: '83119', categoria: 'Senior (3º Año)', subcomision: 'Organización y Eventos', saldo: -7.5, felicitaciones: 0, llamadosAtencion: 4, estado: 'alerta_amarilla' },
      { id: '14', nombre: 'Agustín Benítez', legajo: '79214', categoria: 'Senior (4º Año)', subcomision: 'Gestión Social y Ambiental', saldo: -10.5, felicitaciones: 0, llamadosAtencion: 6, estado: 'limite_rojo' },
      { id: '15', nombre: 'Valeria Morales', legajo: '78401', categoria: 'Senior (5º Año)', subcomision: 'Mantenimiento', saldo: -11.0, felicitaciones: 0, llamadosAtencion: 7, estado: 'limite_rojo' }
    ],

    // Eventos Institucionales con Control de Asistencia
    eventos: [
      {
        id: 'EVT-101',
        nombre: 'Asamblea General Ordinaria Cuatrimestral',
        tipo: 'Asamblea Obligatoria',
        fecha: '05/09/2026',
        horario: '18:00 - 21:00',
        lugar: 'Aula Magna UTN FRC',
        estado: 'en_curso',
        totalConvocados: 40,
        presentes: 33,
        ausentes: 7,
        listaAusentes: [
          { nombre: 'Lucas Guillén', legajo: '85194', subcomision: 'Cómputos' },
          { nombre: 'Mateo Fernández', legajo: '89102', subcomision: 'Relaciones Inst.' },
          { nombre: 'Sofía Romero', legajo: '88310', subcomision: 'Prensa' },
          { nombre: 'Franco Varela', legajo: '83119', subcomision: 'Eventos' },
          { nombre: 'Julián Castro', legajo: '84102', subcomision: 'Relaciones Inst.' },
          { nombre: 'Camila López', legajo: '88240', subcomision: 'RRHH' },
          { nombre: 'Martín Gómez', legajo: '86104', subcomision: 'Prensa' }
        ]
      },
      {
        id: 'EVT-102',
        nombre: 'Jornada Solidaria y Mantenimiento Edilicio',
        tipo: 'Mantenimiento General',
        fecha: '06/09/2026',
        horario: '09:00 - 13:00',
        lugar: 'Sede Social AVEIT',
        estado: 'programado',
        totalConvocados: 25,
        presentes: 0,
        ausentes: 25,
        listaAusentes: []
      },
      {
        id: 'EVT-100',
        nombre: 'Reunión Plenaria de Subcomisiones',
        tipo: 'Reunión Ordinaria',
        fecha: '28/08/2026',
        horario: '19:30 - 21:00',
        lugar: 'Sala de Conferencias AVEIT',
        estado: 'cerrado',
        totalConvocados: 35,
        presentes: 31,
        ausentes: 4,
        listaAusentes: []
      }
    ]
  };

  // Cargar estado inicial
  function loadState() {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        return Object.assign({}, DEFAULT_DATA, JSON.parse(saved));
      }
    } catch (e) {
      console.warn('Error al leer datos locales, usando predeterminados', e);
    }
    return JSON.parse(JSON.stringify(DEFAULT_DATA));
  }

  let state = loadState();

  function saveState() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      console.error('Error al guardar estado', e);
    }
  }

  // =========================================================================
  // 2. GESTIÓN DE TEMA (MODO OSCURO / MODO CLARO)
  // =========================================================================

  function initTheme() {
    const html = document.documentElement;
    if (state.theme === 'dark') {
      html.classList.add('dark');
    } else {
      html.classList.remove('dark');
    }
    updateThemeToggleUI();
  }

  function toggleTheme() {
    state.theme = state.theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('aveit_theme', state.theme);
    initTheme();
    saveState();
    showToast(`Modo ${state.theme === 'dark' ? 'Oscuro' : 'Claro'} activado`, 'info');
  }

  function updateThemeToggleUI() {
    const btn = document.getElementById('theme-toggle-btn');
    if (!btn) return;
    if (state.theme === 'dark') {
      btn.innerHTML = '<i class="fas fa-sun text-yellow-400 text-lg"></i>';
      btn.setAttribute('title', 'Cambiar a Modo Claro');
    } else {
      btn.innerHTML = '<i class="fas fa-moon text-slate-600 text-lg"></i>';
      btn.setAttribute('title', 'Cambiar a Modo Oscuro');
    }
  }

  // =========================================================================
  // 3. ENRUTAMIENTO Y RENDERIZADO DE SUBMÓDULOS
  // =========================================================================

  function navigateTo(submoduleName) {
    state.activeSubmodule = submoduleName;
    saveState();

    // Actualizar items activos en sidebar Material PRO
    document.querySelectorAll('.sidebar-nav-item').forEach(el => {
      if (el.dataset.submodule === submoduleName) {
        el.classList.add('active');
      } else {
        el.classList.remove('active');
      }
    });

    // Actualizar título de la vista y breadcrumb en topbar
    const titleEl = document.getElementById('page-title');
    const breadcrumbEl = document.getElementById('breadcrumb-section');
    const titles = {
      'mis-expedientes': 'Mis Expedientes',
      'gestionar-expedientes': 'Gestión de Expedientes — Tribunal de Disciplina',
      'reportes': 'Reportes y Balance Cuatrimestral de Disciplina',
      'ranking': 'Ranking General y Padrón de Socios',
      'solicitar-puntos': 'Solicitar Premios o Sanciones (Formulario Oficial)',
      'eventos': 'Eventos Institucionales y Control de Asistencia Digital'
    };
    const breadcrumbs = {
      'mis-expedientes': 'Mis Expedientes',
      'gestionar-expedientes': 'Tribunal de Disciplina',
      'reportes': 'Reportes y Balances',
      'ranking': 'Ranking de Socios',
      'solicitar-puntos': 'Solicitudes',
      'eventos': 'Eventos & Asistencia'
    };
    if (titleEl) {
      titleEl.textContent = titles[submoduleName] || 'Tribunal de Disciplina';
    }
    if (breadcrumbEl) {
      breadcrumbEl.textContent = breadcrumbs[submoduleName] || 'Tribunal de Disciplina';
    }

    renderCurrentSubmodule();
  }

  function renderCurrentSubmodule() {
    const container = document.getElementById('submodule-content');
    if (!container) return;

    switch (state.activeSubmodule) {
      case 'mis-expedientes':
        renderMisExpedientes(container);
        break;
      case 'gestionar-expedientes':
        renderGestionarExpedientes(container);
        break;
      case 'reportes':
        renderReportes(container);
        break;
      case 'ranking':
        renderRanking(container);
        break;
      case 'solicitar-puntos':
        renderSolicitarPuntos(container);
        break;
      case 'eventos':
        renderEventos(container);
        break;
      default:
        renderGestionarExpedientes(container);
    }
  }

  // =========================================================================
  // 4. SUBMÓDULO 1: MIS EXPEDIENTES
  // =========================================================================

  function renderMisExpedientes(container) {
    const currentActor = ACTORS[state.currentActorId];
    // Causas donde el socio actual está involucrado
    const causasPropias = state.expedientes.filter(exp => exp.socio.toLowerCase() === currentActor.nombre.toLowerCase() || exp.legajo === currentActor.legajo);

    let html = `
      <div class="space-y-6">
        <!-- Tarjetas Material Dashboard PRO Stat Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="card-mat card-stats">
            <div class="card-header-icon header-primary">
              <i class="material-icons">account_circle</i>
            </div>
            <p class="card-category">Socio Autenticado</p>
            <h3 class="card-title">${currentActor.nombre}</h3>
            <div class="card-footer">
              <div class="stats flex items-center justify-between w-full">
                <span><i class="material-icons text-sm">badge</i> Legajo Nº ${currentActor.legajo} · ${currentActor.categoria}</span>
                <span class="text-emerald-500 font-medium flex items-center gap-1"><i class="material-icons text-sm">verified</i> Padrón Activo</span>
              </div>
            </div>
          </div>

          <div class="card-mat card-stats">
            <div class="card-header-icon header-info">
              <i class="material-icons">account_balance_wallet</i>
            </div>
            <p class="card-category">Saldo Neto de Puntos</p>
            <h3 class="card-title ${getSaldoColorClass(getSocioSaldo(currentActor.legajo))}">
              ${formatPuntos(getSocioSaldo(currentActor.legajo))}
            </h3>
            <div class="card-footer">
              <div class="stats flex items-center justify-between w-full">
                <span><i class="material-icons text-sm">warning_amber</i> Límite Advertencia: <strong>-7.0 pts</strong></span>
                <span><i class="material-icons text-sm">error_outline</i> Límite Cese: <strong>-10.0 pts</strong></span>
              </div>
            </div>
          </div>

          <div class="card-mat card-stats">
            <div class="card-header-icon header-warning">
              <i class="material-icons">folder_open</i>
            </div>
            <p class="card-category">Causas en Trámite</p>
            <h3 class="card-title text-[var(--text-main)]">${causasPropias.length}</h3>
            <div class="card-footer">
              <div class="stats text-amber-600 font-medium flex items-center">
                <i class="material-icons text-sm">timer</i> Plazo para presentar justificación: 5 días hábiles
              </div>
            </div>
          </div>
        </div>

        <!-- Listado de Causas Propias con Cabecera Flotante Material PRO -->
        <div class="card-mat mt-8">
          <div class="card-header-full header-primary flex items-center justify-between">
            <div>
              <h4 class="card-title">Mis Expedientes Disciplinarios y Reconocimientos</h4>
              <p class="card-category">Consulta tus causas, plazos preclusivos y presenta tu descargo o certificado</p>
            </div>
            <span class="badge-mat badge-mat-info">
              ${causasPropias.length} ${causasPropias.length === 1 ? 'causa' : 'causas'} registradas
            </span>
          </div>

          <div class="card-body p-6 pt-8">
    `;

    if (causasPropias.length === 0) {
      html += `
        <div class="text-center py-12">
          <div class="w-16 h-16 rounded-full bg-emerald-100 dark:bg-emerald-950/40 text-emerald-600 flex items-center justify-center mx-auto mb-4 text-2xl shadow-sm">
            <i class="material-icons text-3xl">verified_user</i>
          </div>
          <h4 class="text-lg font-bold text-[var(--text-main)]">Sin expedientes activos</h4>
          <p class="text-sm text-[var(--text-muted)] max-w-md mx-auto mt-1">
            No posees causas disciplinarias pendientes ni trámites en curso. Tu legajo asociativo se encuentra plenamente regular.
          </p>
          <button onclick="window.cambiarActorSimulado('socio')" class="btn-mat btn-white mt-4 text-xs">
            <i class="material-icons text-sm mr-1">sync</i> Simular como Socio con Causa Abierta
          </button>
        </div>
      `;
    } else {
      html += `
        <div class="space-y-4">
      `;

      causasPropias.forEach(exp => {
        const estadoInfo = ESTADOS[exp.estado] || ESTADOS.creado;
        const puedeJustificar = exp.estado === 'justificando' && exp.horasPlazoRestantes > 0;
        const plazoExpirado = exp.estado === 'justificando' && exp.horasPlazoRestantes <= 0;

        html += `
          <div class="p-5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] hover:border-[var(--color-accent)] transition-all shadow-sm">
            <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div class="space-y-1.5">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-mono text-xs font-bold bg-slate-100 dark:bg-slate-800 text-[var(--text-main)] px-2.5 py-1 rounded">
                    ${exp.id}
                  </span>
                  <span class="badge-mat ${estadoInfo.badgeClass}">
                    <i class="material-icons text-xs">${estadoInfo.icon}</i> ${estadoInfo.nombre}
                  </span>
                  <span class="text-xs font-bold px-2 py-0.5 rounded ${exp.tipoPuntos === 'premio' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-400' : 'bg-rose-100 text-rose-700 dark:bg-rose-950/50 dark:text-rose-400'}">
                    ${exp.tipoPuntos === 'premio' ? '+' : ''}${exp.puntos} puntos
                  </span>
                </div>
                <h4 class="text-base font-bold text-[var(--text-main)] mt-1">${exp.motivo}</h4>
                <p class="text-xs text-[var(--text-muted)]">
                  Origen: ${exp.origen} · Solicitado por: <strong>${exp.autoridadSolicitante}</strong> · Apertura: ${exp.fechaApertura}
                </p>
              </div>

              <!-- Temporizador y Acciones de Descargo -->
              <div class="flex flex-col items-start md:items-end gap-2.5">
                ${exp.estado === 'justificando' ? `
                  <div class="flex items-center gap-2 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50 px-3 py-1.5 rounded text-xs text-amber-800 dark:text-amber-300 font-mono">
                    <i class="material-icons text-sm ${plazoExpirado ? 'text-rose-500' : 'text-amber-500'}">timer</i>
                    <span>Plazo de 5 días hábiles: <strong>${formatHorasRestantes(exp.horasPlazoRestantes)}</strong></span>
                  </div>
                ` : ''}

                ${exp.justificacion ? `
                  <div class="flex items-center gap-1.5 text-xs text-emerald-600 font-medium">
                    <i class="material-icons text-sm">done_all</i> Descargo presentado (${exp.justificacion.tipo})
                  </div>
                ` : ''}

                <div class="flex items-center gap-2">
                  <button onclick="window.verDetalleExpediente('${exp.id}')" class="btn-mat btn-white text-xs py-1.5 px-3">
                    <i class="material-icons text-sm mr-1">visibility</i> Ver Causa
                  </button>

                  ${puedeJustificar && !exp.justificacion ? `
                    <button onclick="window.abrirModalJustificacion('${exp.id}')" class="btn-mat btn-warning text-xs py-1.5 px-3.5">
                      <i class="material-icons text-sm mr-1">upload_file</i> Presentar Justificación
                    </button>
                  ` : ''}

                  ${plazoExpirado && !exp.justificacion ? `
                    <button disabled class="btn-mat bg-slate-300 dark:bg-slate-700 text-slate-500 text-xs py-1.5 px-3 cursor-not-allowed">
                      <i class="material-icons text-sm mr-1">lock</i> Plazo Expirado
                    </button>
                  ` : ''}
                </div>
              </div>
            </div>
          </div>
        `;
      });

      html += `</div>`;
    }

    html += `
          </div>
        </div>
      </div>
    `;

    container.innerHTML = html;
  }

  // =========================================================================
  // 5. SUBMÓDULO 2: GESTIONAR EXPEDIENTES (TRIBUNAL DE DISCIPLINA)
  // =========================================================================

  function renderGestionarExpedientes(container) {
    const isKanban = state.expedientesViewMode === 'kanban';

    let html = `
      <div class="space-y-6">
        <!-- Barra de Control y Selector de Vistas Material PRO -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[var(--bg-card)] p-4 rounded-lg border border-[var(--border-color)] shadow-sm">
          <div class="flex items-center gap-3">
            <div class="flex rounded-md border border-[var(--border-color)] p-1 bg-slate-100 dark:bg-slate-800">
              <button onclick="window.setExpedientesViewMode('kanban')" class="px-3.5 py-1.5 text-xs font-semibold rounded transition-all ${isKanban ? 'bg-[var(--color-primary)] text-white shadow' : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'}">
                <i class="material-icons text-sm mr-1 align-middle">view_week</i> Tablero de Estados (Kanban)
              </button>
              <button onclick="window.setExpedientesViewMode('explorer')" class="px-3.5 py-1.5 text-xs font-semibold rounded transition-all ${!isKanban ? 'bg-[var(--color-primary)] text-white shadow' : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'}">
                <i class="material-icons text-sm mr-1 align-middle">table_rows</i> Vista Detalle (Explorador)
              </button>
            </div>
            <span class="text-xs text-[var(--text-muted)] hidden lg:inline">
              | 5 estados reglamentarios
            </span>
          </div>

          <!-- Buscador con Material Underline y Botón de Nueva Causa -->
          <div class="flex items-center gap-3">
            <div class="mat-search-wrapper">
              <input type="text" id="expedientes-search-input" oninput="window.filtrarExpedientes(this.value)" placeholder="Buscar expediente, socio o motivo..." 
                class="mat-search-input text-xs">
              <i class="material-icons text-slate-400 text-sm">search</i>
            </div>
            <button onclick="window.navigateTo('solicitar-puntos')" class="btn-mat btn-primary text-xs py-2">
              <i class="material-icons text-sm mr-1">add</i> Nueva Causa
            </button>
          </div>
        </div>

        <!-- Contenedor dinámico según vista seleccionada -->
        <div id="expedientes-view-container">
          ${isKanban ? renderKanbanBoardHtml() : renderExplorerTableHtml()}
        </div>
      </div>
    `;

    container.innerHTML = html;
  }

  // Vista Kanban Material PRO (5 Columnas Consolidadas)
  function renderKanbanBoardHtml(filtro = '') {
    const expFiltrados = filtrarExpedientesData(filtro);

    let html = `<div class="kanban-board-mat">`;

    // Las 5 columnas oficiales consolidadas
    const columnas = [
      { id: 'creado', nombre: '1. Expediente Creado', badgeClass: 'header-info', icon: 'file_copy' },
      { id: 'justificando', nombre: '2. En período de justificaciones', badgeClass: 'header-warning', icon: 'schedule' },
      { id: 'revision_resolucion', nombre: '3. En revisión y resolución', badgeClass: 'header-primary', icon: 'gavel' },
      { id: 'pendiente_firma', nombre: '4. Pendiente de firma y envío', badgeClass: 'header-rose', icon: 'history_edu' },
      { id: 'emitido', nombre: '5. Expedientes ya emitidos', badgeClass: 'header-success', icon: 'verified' }
    ];

    columnas.forEach(col => {
      const items = expFiltrados.filter(e => e.estado === col.id);

      html += `
        <div class="kanban-col-mat">
          <div class="flex items-center justify-between pb-3 mb-3 border-b border-[var(--border-color)]">
            <span class="text-xs font-bold text-[var(--text-main)] flex items-center gap-1.5">
              <i class="material-icons text-sm text-[var(--color-accent)]">${col.icon}</i> ${col.nombre}
            </span>
            <span class="text-xs bg-slate-200 dark:bg-slate-700 px-2 py-0.5 rounded-full font-bold text-[var(--text-main)]">
              ${items.length}
            </span>
          </div>

          <div class="space-y-3 overflow-y-auto max-h-[720px] pr-1">
      `;

      if (items.length === 0) {
        html += `
          <div class="text-center py-8 text-xs text-[var(--text-muted)] border border-dashed border-[var(--border-color)] rounded p-4">
            Sin causas en esta etapa
          </div>
        `;
      } else {
        items.forEach(item => {
          const esSancion = item.tipoPuntos === 'sancion';
          html += `
            <div class="kanban-card-mat" onclick="window.verDetalleExpediente('${item.id}')">
              <div class="flex items-center justify-between mb-1.5">
                <span class="font-mono text-xs font-bold text-blue-600 dark:text-blue-400">${item.id}</span>
                <span class="text-xs font-bold ${esSancion ? 'text-rose-600' : 'text-emerald-600'}">
                  ${item.puntos > 0 ? '+' : ''}${item.puntos} pts
                </span>
              </div>
              <h5 class="text-xs font-bold text-[var(--text-main)] line-clamp-2 mb-1">${item.motivo}</h5>
              <p class="text-[11px] text-[var(--text-muted)] mb-2 flex items-center gap-1">
                <i class="material-icons text-xs">person</i> ${item.socio} (${item.subcomision})
              </p>

              ${item.estado === 'justificando' ? `
                <div class="text-[11px] bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 p-2 rounded flex items-center justify-between mb-2 font-mono">
                  <span class="flex items-center gap-1"><i class="material-icons text-xs">timer</i> Plazo:</span>
                  <strong>${formatHorasRestantes(item.horasPlazoRestantes)}</strong>
                </div>
              ` : ''}

              ${item.justificacion ? `
                <div class="text-[11px] bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 p-1.5 rounded flex items-center gap-1 mb-2">
                  <i class="material-icons text-xs">attachment</i> Justificación cargada
                </div>
              ` : ''}

              ${item.estado === 'revision_resolucion' ? `
                <div class="mt-2 pt-2 border-t border-[var(--border-color)]">
                  <button onclick="event.stopPropagation(); window.abrirModalVotacion('${item.id}')" class="w-full btn-mat btn-info text-[11px] py-1">
                    <i class="material-icons text-xs mr-1">how_to_vote</i> Votar y Dictaminar
                  </button>
                </div>
              ` : ''}

              ${item.estado === 'pendiente_firma' ? `
                <div class="mt-2 pt-2 border-t border-[var(--border-color)]">
                  <button onclick="event.stopPropagation(); window.abrirModalFirma('${item.id}')" class="w-full btn-mat btn-rose text-[11px] py-1">
                    <i class="material-icons text-xs mr-1">history_edu</i> Firmar Resolución
                  </button>
                </div>
              ` : ''}

              ${item.estado === 'emitido' ? `
                <div class="mt-2 pt-1 text-[11px] text-emerald-600 font-semibold flex items-center justify-between">
                  <span>Resolución Emitida</span>
                  <i class="material-icons text-sm">verified</i>
                </div>
              ` : ''}
            </div>
          `;
        });
      }

      html += `
          </div>
        </div>
      `;
    });

    html += `</div>`;
    return html;
  }

  // Vista Detalle Material PRO (Estilo Explorador de Windows)
  let sortField = 'id';
  let sortAsc = false;

  function renderExplorerTableHtml(filtro = '') {
    const expFiltrados = filtrarExpedientesData(filtro);

    // Ordenamiento por columna
    expFiltrados.sort((a, b) => {
      let valA = a[sortField] || '';
      let valB = b[sortField] || '';
      if (typeof valA === 'string') valA = valA.toLowerCase();
      if (typeof valB === 'string') valB = valB.toLowerCase();
      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });

    let html = `
      <div class="card-mat mt-4">
        <div class="card-header-full header-primary flex items-center justify-between">
          <div>
            <h4 class="card-title">Inventario Procesal de Expedientes</h4>
            <p class="card-category">Grilla densa con ordenamiento bidireccional y trazabilidad de causas</p>
          </div>
          <span class="badge-mat badge-mat-info">
            ${expFiltrados.length} expedientes
          </span>
        </div>

        <div class="card-body p-4 pt-6">
          <div class="explorer-table-container">
            <table class="table-mat">
              <thead>
                <tr>
                  <th onclick="window.sortExplorer('id')" class="cursor-pointer select-none">
                    Expediente ${sortField === 'id' ? (sortAsc ? '▲' : '▼') : ''}
                  </th>
                  <th onclick="window.sortExplorer('socio')" class="cursor-pointer select-none">
                    Socio Involucrado ${sortField === 'socio' ? (sortAsc ? '▲' : '▼') : ''}
                  </th>
                  <th onclick="window.sortExplorer('subcomision')" class="cursor-pointer select-none">
                    Subcomisión ${sortField === 'subcomision' ? (sortAsc ? '▲' : '▼') : ''}
                  </th>
                  <th onclick="window.sortExplorer('motivo')" class="cursor-pointer select-none">
                    Carátula / Motivo ${sortField === 'motivo' ? (sortAsc ? '▲' : '▼') : ''}
                  </th>
                  <th onclick="window.sortExplorer('puntos')" class="cursor-pointer select-none">
                    Puntos ${sortField === 'puntos' ? (sortAsc ? '▲' : '▼') : ''}
                  </th>
                  <th onclick="window.sortExplorer('estado')" class="cursor-pointer select-none">
                    Estado Procesal ${sortField === 'estado' ? (sortAsc ? '▲' : '▼') : ''}
                  </th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
      `;

    if (expFiltrados.length === 0) {
      html += `
        <tr>
          <td colspan="7" class="text-center py-8 text-xs text-[var(--text-muted)]">
            No se encontraron expedientes con los criterios ingresados.
          </td>
        </tr>
      `;
    } else {
      expFiltrados.forEach(exp => {
        const estadoInfo = ESTADOS[exp.estado] || ESTADOS.creado;
        const esSancion = exp.tipoPuntos === 'sancion';

        html += `
          <tr onclick="window.verDetalleExpediente('${exp.id}')" class="cursor-pointer">
            <td class="font-mono font-bold text-blue-600 dark:text-blue-400">
              <i class="material-icons text-sm text-slate-400 mr-1 align-middle">folder</i> ${exp.id}
            </td>
            <td>
              <div class="font-semibold text-xs">${exp.socio}</div>
              <div class="text-[11px] text-[var(--text-muted)]">Legajo Nº ${exp.legajo} · ${exp.categoria}</div>
            </td>
            <td class="text-xs">${exp.subcomision}</td>
            <td class="max-w-xs truncate text-xs" title="${exp.motivo}">${exp.motivo}</td>
            <td>
              <span class="font-bold text-xs ${esSancion ? 'text-rose-600' : 'text-emerald-600'}">
                ${exp.puntos > 0 ? '+' : ''}${exp.puntos} pts
              </span>
            </td>
            <td>
              <span class="badge-mat ${estadoInfo.badgeClass}">
                <i class="material-icons text-xs">${estadoInfo.icon}</i> ${estadoInfo.nombre}
              </span>
            </td>
            <td>
              <div class="flex items-center gap-1.5" onclick="event.stopPropagation()">
                ${exp.estado === 'revision_resolucion' ? `
                  <button onclick="window.abrirModalVotacion('${exp.id}')" class="btn-mat btn-info text-xs py-1 px-2.5" title="Votar y Dictaminar">
                    <i class="material-icons text-xs mr-1">how_to_vote</i> Votar
                  </button>
                ` : ''}

                ${exp.estado === 'pendiente_firma' ? `
                  <button onclick="window.abrirModalFirma('${exp.id}')" class="btn-mat btn-rose text-xs py-1 px-2.5" title="Firmar Resolución">
                    <i class="material-icons text-xs mr-1">history_edu</i> Firmar
                  </button>
                ` : ''}

                <button onclick="window.verDetalleExpediente('${exp.id}')" class="btn-mat btn-white text-xs py-1 px-2" title="Ver Detalles de Causa">
                  <i class="material-icons text-xs">visibility</i>
                </button>
              </div>
            </td>
          </tr>
        `;
      });
    }

    html += `
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;

    return html;
  }

  function filtrarExpedientesData(filtro = '') {
    if (!filtro) return state.expedientes;
    const f = filtro.toLowerCase().trim();
    return state.expedientes.filter(e => 
      e.id.toLowerCase().includes(f) ||
      e.socio.toLowerCase().includes(f) ||
      e.legajo.toLowerCase().includes(f) ||
      e.motivo.toLowerCase().includes(f) ||
      e.subcomision.toLowerCase().includes(f)
    );
  }

  // =========================================================================
  // 6. SUBMÓDULO 3: REPORTES Y BALANCE CUATRIMESTRAL
  // =========================================================================

  function renderReportes(container) {
    // Métricas para el Balance Cuatrimestral
    const totalExpedientes = state.expedientes.length;
    const emitidos = state.expedientes.filter(e => e.estado === 'emitido').length;
    const enTramite = totalExpedientes - emitidos;
    const sancionesEmitidas = state.expedientes.filter(e => e.tipoPuntos === 'sancion').length;
    const premiosEmitidos = state.expedientes.filter(e => e.tipoPuntos === 'premio').length;

    // Desglose por subcomisión
    const subcomisionesStats = [
      { nombre: 'Cómputos', sanciones: 3, premios: 4, saldoTotal: 4.5 },
      { nombre: 'Relaciones Institucionales', sanciones: 2, premios: 1, saldoTotal: -2.0 },
      { nombre: 'Organización y Eventos', sanciones: 4, premios: 3, saldoTotal: -1.5 },
      { nombre: 'Prensa y Difusión', sanciones: 2, premios: 2, saldoTotal: 0.0 },
      { nombre: 'Mantenimiento', sanciones: 5, premios: 1, saldoTotal: -5.5 },
      { nombre: 'Recursos Humanos', sanciones: 1, premios: 2, saldoTotal: 1.5 },
      { nombre: 'Gestión Social y Ambiental', sanciones: 3, premios: 0, saldoTotal: -4.0 }
    ];

    let html = `
      <div class="space-y-6">
        <!-- 4 Stat Cards Material Dashboard PRO -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div class="card-mat card-stats">
            <div class="card-header-icon header-primary">
              <i class="material-icons">assignment</i>
            </div>
            <p class="card-category">Expedientes Tratados</p>
            <h3 class="card-title">${totalExpedientes}</h3>
            <div class="card-footer">
              <div class="stats text-emerald-600 font-medium flex items-center">
                <i class="material-icons text-sm mr-1">verified</i> ${emitidos} con resolución firme
              </div>
            </div>
          </div>

          <div class="card-mat card-stats">
            <div class="card-header-icon header-warning">
              <i class="material-icons">pending_actions</i>
            </div>
            <p class="card-category">Causas en Trámite</p>
            <h3 class="card-title text-amber-600">${enTramite}</h3>
            <div class="card-footer">
              <div class="stats flex items-center">
                <i class="material-icons text-sm mr-1">timer</i> Con plazos o deliberación activa
              </div>
            </div>
          </div>

          <div class="card-mat card-stats">
            <div class="card-header-icon header-success">
              <i class="material-icons">emoji_events</i>
            </div>
            <p class="card-category">Reconocimientos de Mérito</p>
            <h3 class="card-title text-emerald-600">${premiosEmitidos}</h3>
            <div class="card-footer">
              <div class="stats flex items-center">
                <i class="material-icons text-sm mr-1">stars</i> Puntos positivos aplicados
              </div>
            </div>
          </div>

          <div class="card-mat card-stats">
            <div class="card-header-icon header-danger">
              <i class="material-icons">gavel</i>
            </div>
            <p class="card-category">Medidas Disciplinarias</p>
            <h3 class="card-title text-rose-600">${sancionesEmitidas}</h3>
            <div class="card-footer">
              <div class="stats text-rose-600 flex items-center">
                <i class="material-icons text-sm mr-1">warning</i> Faltas e incumplimientos
              </div>
            </div>
          </div>
        </div>

        <!-- Tarjeta Principal de Balance Cuatrimestral -->
        <div class="card-mat mt-8">
          <div class="card-header-full header-primary flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
              <h4 class="card-title">Balance Cuatrimestral de Disciplina y Premiaciones</h4>
              <p class="card-category">Rendición Institucional de Cuentas · Primer Cuatrimestre · Ciclo 2026</p>
            </div>
            <div class="flex items-center gap-2">
              <button onclick="window.exportarReporteExcel()" class="btn-mat btn-success text-xs py-2 px-3">
                <i class="material-icons text-sm mr-1">table_view</i> Exportar a Excel
              </button>
              <button onclick="window.imprimirReportePDF()" class="btn-mat btn-info text-xs py-2 px-3">
                <i class="material-icons text-sm mr-1">picture_as_pdf</i> Imprimir / PDF
              </button>
            </div>
          </div>

          <div class="card-body p-6 pt-8 space-y-6">
            <!-- Tabla de Balance por Subcomisión -->
            <div>
              <h4 class="text-sm font-bold text-[var(--text-main)] mb-3 flex items-center gap-2">
                <i class="material-icons text-blue-500 text-base">domain</i> Desglose Comparativo por Subcomisión de Trabajo
              </h4>
              <div class="explorer-table-container">
                <table class="table-mat">
                  <thead>
                    <tr>
                      <th>Subcomisión / Área</th>
                      <th>Sanciones</th>
                      <th>Premios</th>
                      <th>Saldo Neto</th>
                      <th>Desempeño Institucional</th>
                    </tr>
                  </thead>
                  <tbody>
        `;

        subcomisionesStats.forEach(sub => {
          html += `
            <tr>
              <td class="font-bold text-xs">${sub.nombre}</td>
              <td class="text-rose-600 font-semibold text-xs">${sub.sanciones}</td>
              <td class="text-emerald-600 font-semibold text-xs">${sub.premios}</td>
              <td class="font-bold text-xs ${sub.saldoTotal >= 0 ? 'text-emerald-600' : 'text-rose-600'}">
                ${sub.saldoTotal > 0 ? '+' : ''}${sub.saldoTotal} pts
              </td>
              <td>
                <div class="w-full bg-slate-200 dark:bg-slate-700 h-2 rounded-full overflow-hidden max-w-xs">
                  <div class="h-full ${sub.saldoTotal >= 0 ? 'bg-emerald-500' : 'bg-rose-500'}" style="width: ${Math.min(100, Math.max(15, Math.abs(sub.saldoTotal) * 15))}%"></div>
                </div>
              </td>
            </tr>
          `;
        });

        html += `
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Segmentación de Socios Juniors vs Seniors -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-[var(--border-color)]">
              <div class="p-4 rounded-lg border border-[var(--border-color)] bg-blue-50/40 dark:bg-blue-950/20">
                <h5 class="text-xs font-bold uppercase tracking-wider text-blue-800 dark:text-blue-300 flex items-center gap-1">
                  <i class="material-icons text-sm">school</i> Segmento: Socios Juniors (1º y 2º Año)
                </h5>
                <p class="text-xs text-[var(--text-muted)] mt-1">Etapa formativa e integración asociativa</p>
                <div class="mt-3 grid grid-cols-2 gap-3 text-center">
                  <div class="bg-[var(--bg-card)] p-2.5 rounded border border-[var(--border-color)]">
                    <span class="text-xs text-[var(--text-muted)]">Asistencia Promedio</span>
                    <div class="text-lg font-bold text-emerald-600">88.4%</div>
                  </div>
                  <div class="bg-[var(--bg-card)] p-2.5 rounded border border-[var(--border-color)]">
                    <span class="text-xs text-[var(--text-muted)]">Descargos en Término</span>
                    <div class="text-lg font-bold text-blue-600">92.0%</div>
                  </div>
                </div>
              </div>

              <div class="p-4 rounded-lg border border-[var(--border-color)] bg-purple-50/40 dark:bg-purple-950/20">
                <h5 class="text-xs font-bold uppercase tracking-wider text-purple-800 dark:text-purple-300 flex items-center gap-1">
                  <i class="material-icons text-sm">military_tech</i> Segmento: Socios Seniors (3º a 6º Año)
                </h5>
                <p class="text-xs text-[var(--text-muted)] mt-1">Conducción operativa y preparación al Viaje Final</p>
                <div class="mt-3 grid grid-cols-2 gap-3 text-center">
                  <div class="bg-[var(--bg-card)] p-2.5 rounded border border-[var(--border-color)]">
                    <span class="text-xs text-[var(--text-muted)]">Asistencia Promedio</span>
                    <div class="text-lg font-bold text-emerald-600">94.1%</div>
                  </div>
                  <div class="bg-[var(--bg-card)] p-2.5 rounded border border-[var(--border-color)]">
                    <span class="text-xs text-[var(--text-muted)]">Reconocimientos al Mérito</span>
                    <div class="text-lg font-bold text-purple-600">75.0%</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    container.innerHTML = html;
  }

  // =========================================================================
  // 7. SUBMÓDULO 4: RANKING DE SOCIOS
  // =========================================================================

  let rankingSortOrder = 'desc'; // 'desc' (mayores premios) o 'asc' (más sancionados)
  let rankingFilterSubcomision = 'todas';
  let rankingFilterCategoria = 'todas';

  function renderRanking(container) {
    let sociosFiltrados = [...state.socios];

    if (rankingFilterSubcomision !== 'todas') {
      sociosFiltrados = sociosFiltrados.filter(s => s.subcomision === rankingFilterSubcomision);
    }
    if (rankingFilterCategoria !== 'todas') {
      sociosFiltrados = sociosFiltrados.filter(s => s.categoria.includes(rankingFilterCategoria));
    }

    sociosFiltrados.sort((a, b) => {
      if (rankingSortOrder === 'desc') {
        return b.saldo - a.saldo;
      } else {
        return a.saldo - b.saldo;
      }
    });

    let html = `
      <div class="space-y-6">
        <!-- Cabecera y Filtros del Ranking Material PRO -->
        <div class="card-mat">
          <div class="card-header-full header-info flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
              <h4 class="card-title">Padrón General y Ranking de Puntajes</h4>
              <p class="card-category">Control de saldos, límites preventivos y estado asociativo regular</p>
            </div>
            <!-- Ordenamiento Bidireccional Material PRO -->
            <div class="flex items-center gap-2 bg-white/20 p-1 rounded">
              <button onclick="window.setRankingSort('desc')" class="btn-mat ${rankingSortOrder === 'desc' ? 'btn-white' : 'btn-link text-white'} text-xs py-1.5 px-3">
                <i class="material-icons text-sm mr-1">trending_up</i> Mayor Puntaje
              </button>
              <button onclick="window.setRankingSort('asc')" class="btn-mat ${rankingSortOrder === 'asc' ? 'btn-white' : 'btn-link text-white'} text-xs py-1.5 px-3">
                <i class="material-icons text-sm mr-1">trending_down</i> Identificar Sancionados
              </button>
            </div>
          </div>

          <div class="card-body p-6 pt-8 space-y-4">
            <!-- Filtros de Categoría y Subcomisión -->
            <div class="flex flex-wrap items-center gap-3 text-xs">
              <span class="text-[var(--text-muted)] font-semibold">Filtrar por:</span>
              <select onchange="window.setRankingFilterSub(this.value)" class="px-3 py-1.5 rounded border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-main)] text-xs">
                <option value="todas">Todas las Subcomisiones</option>
                <option value="Cómputos">Cómputos</option>
                <option value="Relaciones Institucionales">Relaciones Institucionales</option>
                <option value="Organización y Eventos">Organización y Eventos</option>
                <option value="Prensa y Difusión">Prensa y Difusión</option>
                <option value="Mantenimiento">Mantenimiento</option>
                <option value="Recursos Humanos">Recursos Humanos</option>
                <option value="Gestión Social y Ambiental">Gestión Social y Ambiental</option>
              </select>

              <select onchange="window.setRankingFilterCat(this.value)" class="px-3 py-1.5 rounded border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-main)] text-xs">
                <option value="todas">Todas las Categorías</option>
                <option value="Junior">Socios Juniors (1º y 2º Año)</option>
                <option value="Senior">Socios Seniors (3º a 6º Año)</option>
              </select>

              <!-- Leyenda de Semáforos -->
              <div class="ml-auto flex items-center gap-3 text-[11px]">
                <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-emerald-500"></span> Regular</span>
                <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-amber-500"></span> Advertencia (-7 pts)</span>
                <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Límite Crítico (-10 pts)</span>
              </div>
            </div>

            <!-- Tabla de Ranking -->
            <div class="explorer-table-container">
              <table class="table-mat">
                <thead>
                  <tr>
                    <th>Posición</th>
                    <th>Socio / Legajo</th>
                    <th>Categoría</th>
                    <th>Subcomisión</th>
                    <th>Reconocimientos</th>
                    <th>Llamados de Atención</th>
                    <th>Saldo Neto</th>
                    <th>Semáforo</th>
                  </tr>
                </thead>
                <tbody>
      `;

      sociosFiltrados.forEach((socio, idx) => {
        const esAlertaAmarilla = socio.saldo <= -7.0 && socio.saldo > -10.0;
        const esAlertaRoja = socio.saldo <= -10.0;

        html += `
          <tr class="${esAlertaRoja ? 'bg-rose-50/70 dark:bg-rose-950/25' : (esAlertaAmarilla ? 'bg-amber-50/70 dark:bg-amber-950/25' : '')}">
            <td class="font-bold text-slate-400 text-xs">#${idx + 1}</td>
            <td>
              <div class="font-bold text-[var(--text-main)] text-xs">${socio.nombre}</div>
              <div class="text-[11px] text-[var(--text-muted)]">Legajo Nº ${socio.legajo}</div>
            </td>
            <td class="text-xs">${socio.categoria}</td>
            <td class="text-xs">${socio.subcomision}</td>
            <td class="text-emerald-600 font-semibold text-xs">${socio.felicitaciones}</td>
            <td class="text-rose-600 font-semibold text-xs">${socio.llamadosAtencion}</td>
            <td class="text-sm font-black ${getSaldoColorClass(socio.saldo)}">
              ${formatPuntos(socio.saldo)}
            </td>
            <td>
              ${esAlertaRoja ? `
                <span class="badge-mat badge-mat-danger">
                  <i class="material-icons text-xs">warning</i> Límite de Cese
                </span>
              ` : (esAlertaAmarilla ? `
                <span class="badge-mat badge-mat-warning">
                  <i class="material-icons text-xs">report_problem</i> Advertencia
                </span>
              ` : `
                <span class="badge-mat badge-mat-success">
                  <i class="material-icons text-xs">check_circle</i> Habilitado
                </span>
              `)}
            </td>
          </tr>
        `;
      });

      html += `
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    `;

    container.innerHTML = html;
  }

  // =========================================================================
  // 8. SUBMÓDULO 5: SOLICITAR PUNTOS (FORMULARIO T01 + HOJA ANEXO)
  // =========================================================================

  function renderSolicitarPuntos(container) {
    const currentActor = ACTORS[state.currentActorId];

    let html = `
      <div class="max-w-3xl mx-auto space-y-6">
        <div class="card-mat">
          <div class="card-header-full header-primary flex items-center justify-between">
            <div>
              <h4 class="card-title">Solicitud de Premiación o Sanción Disciplinaria</h4>
              <p class="card-category">Formulario Oficial T01 para autoridades habilitadas y líderes de subcomisión</p>
            </div>
            <span class="badge-mat badge-mat-info">Formulario T01</span>
          </div>

          <form onsubmit="window.enviarSolicitudPuntos(event)" class="card-body p-6 pt-8 space-y-5">
            <!-- Datos del Solicitante -->
            <div class="bg-slate-50 dark:bg-slate-800/40 p-3.5 rounded-lg border border-[var(--border-color)] text-xs text-[var(--text-muted)] flex items-center justify-between">
              <div>
                Solicitante: <strong>${currentActor.nombre}</strong> (${currentActor.rol}) · Subcomisión: <strong>${currentActor.subcomision}</strong>
              </div>
              <span class="text-emerald-600 font-semibold flex items-center gap-1">
                <i class="material-icons text-sm">verified</i> Competencia Autorizada
              </span>
            </div>

            <!-- Socio Destinatario y Tipo de Puntos -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-bold text-[var(--text-main)] mb-1.5">Socio Involucrado *</label>
                <select id="solicitud-socio" required class="w-full p-2.5 rounded border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-main)] text-xs">
                  <option value="">Seleccione un socio del padrón...</option>
                  ${state.socios.map(s => `<option value="${s.nombre}|${s.legajo}|${s.subcomision}|${s.categoria}">${s.nombre} (Legajo ${s.legajo} - ${s.subcomision})</option>`).join('')}
                </select>
              </div>

              <div>
                <label class="block text-xs font-bold text-[var(--text-main)] mb-1.5">Naturaleza de la Solicitud *</label>
                <select id="solicitud-tipo" onchange="window.actualizarEscalaPuntos(this.value)" required class="w-full p-2.5 rounded border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-main)] text-xs">
                  <option value="sancion">Sanción Disciplinaria (Puntos Negativos)</option>
                  <option value="premio">Reconocimiento al Mérito (Puntos Positivos)</option>
                </select>
              </div>
            </div>

            <!-- Escala de Puntos y Motivo -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-bold text-[var(--text-main)] mb-1.5">Cuantía de Puntos Solicitada *</label>
                <select id="solicitud-puntos" required class="w-full p-2.5 rounded border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-main)] text-xs">
                  <option value="-0.5">-0.5 puntos (Llegada tarde o retiro sin previo aviso)</option>
                  <option value="-1.0">-1.0 punto (Inasistencia a reunión obligatoria de subcomisión)</option>
                  <option value="-2.0" selected>-2.0 puntos (Falta a Asamblea o incumplimiento de tareas)</option>
                </select>
              </div>

              <div>
                <label class="block text-xs font-bold text-[var(--text-main)] mb-1.5">Carátula Sintética del Hecho *</label>
                <input type="text" id="solicitud-motivo" required placeholder="Ej: Omisión de turno general asignado" 
                  class="w-full p-2.5 rounded border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-main)] text-xs">
              </div>
            </div>

            <!-- Hoja de Anexo Circunstanciada Obligatoria -->
            <div class="p-4 rounded-lg border-2 border-dashed border-amber-300 dark:border-amber-700/60 bg-amber-50/40 dark:bg-amber-950/20 space-y-3">
              <div class="flex items-center justify-between">
                <h4 class="text-xs font-bold text-amber-900 dark:text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
                  <i class="material-icons text-sm text-amber-600">assignment_late</i> Hoja de Anexo Circunstanciada (Obligatoria)
                </h4>
                <span class="text-[11px] text-amber-700 dark:text-amber-400 font-medium">Requisito formal de admisibilidad</span>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label class="block text-[11px] font-semibold text-[var(--text-muted)] mb-1">Fecha y Hora de los Hechos *</label>
                  <input type="datetime-local" id="anexo-fecha" required class="w-full p-2 rounded border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-main)] text-xs">
                </div>
                <div>
                  <label class="block text-[11px] font-semibold text-[var(--text-muted)] mb-1">Testigos Presenciales / Autoridades *</label>
                  <input type="text" id="anexo-testigos" required placeholder="Nombres de socios presentes o autoridades" class="w-full p-2 rounded border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-main)] text-xs">
                </div>
              </div>

              <div>
                <label class="block text-[11px] font-semibold text-[var(--text-muted)] mb-1">Relato Detallado y Circunstanciado de los Hechos *</label>
                <textarea id="anexo-relato" rows="3" required placeholder="Describa pormenorizadamente los hechos, tareas omitidas o aportes extraordinarios verificados..." 
                  class="w-full p-2.5 rounded border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-main)] text-xs"></textarea>
              </div>
            </div>

            <!-- Acciones de Envío -->
            <div class="flex items-center justify-end gap-3 pt-3 border-t border-[var(--border-color)]">
              <button type="button" onclick="window.navigateTo('gestionar-expedientes')" class="btn-mat btn-white text-xs">
                Cancelar
              </button>
              <button type="submit" class="btn-mat btn-primary text-xs">
                <i class="material-icons text-sm mr-1">send</i> Presentar Solicitud de Causa
              </button>
            </div>
          </form>
        </div>
      </div>
    `;

    container.innerHTML = html;
  }

  // =========================================================================
  // 9. SUBMÓDULO 6: EVENTOS & ASISTENCIA DIGITAL
  // =========================================================================

  function renderEventos(container) {
    const eventos = state.eventos;

    let html = `
      <div class="space-y-6">
        <!-- Tarjetas de Eventos Activos Material PRO -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          ${eventos.map(evt => `
            <div class="card-mat overflow-hidden flex flex-col justify-between">
              <div>
                <div class="p-4 ${evt.estado === 'en_curso' ? 'bg-gradient-to-r from-[#151846] to-[#242a68] text-white shadow' : (evt.estado === 'cerrado' ? 'bg-slate-200 dark:bg-slate-800 text-[var(--text-main)]' : 'bg-amber-600 text-white shadow')}">
                  <div class="flex items-center justify-between text-xs mb-1">
                    <span class="font-mono opacity-80">${evt.id}</span>
                    <span class="px-2 py-0.5 rounded text-[10px] uppercase font-bold ${evt.estado === 'en_curso' ? 'bg-emerald-400 text-emerald-950 animate-pulse' : 'bg-black/20 text-white'}">
                      ${evt.estado === 'en_curso' ? 'En Curso (Asistencia Abierta)' : (evt.estado === 'cerrado' ? 'Cerrado' : 'Programado')}
                    </span>
                  </div>
                  <h4 class="text-base font-bold text-white">${evt.nombre}</h4>
                  <p class="text-xs opacity-90 mt-0.5 flex items-center gap-1"><i class="material-icons text-xs">label</i> ${evt.tipo}</p>
                </div>

                <div class="card-body p-5 space-y-3">
                  <div class="text-xs text-[var(--text-muted)] space-y-1">
                    <div class="flex items-center gap-1"><i class="material-icons text-xs text-blue-500">event</i> ${evt.fecha} (${evt.horario})</div>
                    <div class="flex items-center gap-1"><i class="material-icons text-xs text-rose-500">place</i> ${evt.lugar}</div>
                  </div>

                  <!-- Métricas de Asistencia en Tiempo Real -->
                  <div class="grid grid-cols-3 gap-2 text-center pt-2 border-t border-[var(--border-color)]">
                    <div class="bg-slate-50 dark:bg-slate-800 p-2 rounded">
                      <span class="text-[10px] text-[var(--text-muted)] uppercase">Convocados</span>
                      <div class="text-base font-bold text-[var(--text-main)]">${evt.totalConvocados}</div>
                    </div>
                    <div class="bg-emerald-50 dark:bg-emerald-950/40 p-2 rounded">
                      <span class="text-[10px] text-emerald-700 dark:text-emerald-400 uppercase">Presentes</span>
                      <div class="text-base font-bold text-emerald-600">${evt.presentes}</div>
                    </div>
                    <div class="bg-rose-50 dark:bg-rose-950/40 p-2 rounded">
                      <span class="text-[10px] text-rose-700 dark:text-rose-400 uppercase">Ausentes</span>
                      <div class="text-base font-bold text-rose-600">${evt.ausentes}</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Acciones de Evento -->
              <div class="p-4 bg-slate-50/50 dark:bg-slate-800/30 border-t border-[var(--border-color)] flex items-center justify-between gap-2">
                ${evt.estado === 'en_curso' ? `
                  <button onclick="window.activarTerminalAsistencia('${evt.id}')" class="btn-mat btn-info text-xs py-1.5 flex-1">
                    <i class="material-icons text-sm mr-1">fingerprint</i> Terminal "Pasar el Dedo"
                  </button>
                  <button onclick="window.confirmarCierreEvento('${evt.id}')" class="btn-mat btn-danger text-xs py-1.5" title="Cerrar Evento y Abrir Expedientes por Inasistencia">
                    <i class="material-icons text-sm mr-1">meeting_room</i> Cerrar
                  </button>
                ` : (evt.estado === 'cerrado' ? `
                  <span class="text-xs text-slate-500 flex items-center gap-1"><i class="material-icons text-xs">done_all</i> Evento concluido y causas emitidas</span>
                ` : `
                  <button onclick="window.iniciarEvento('${evt.id}')" class="btn-mat btn-success text-xs py-1.5 w-full">
                    <i class="material-icons text-sm mr-1">play_arrow</i> Iniciar Evento y Registro
                  </button>
                `)}
              </div>
            </div>
          `).join('')}
        </div>

        <!-- Terminal Interactiva de "Pasar el Dedo" (Simulador Biométrico Material PRO) -->
        <div id="terminal-asistencia-card" class="card-mat mt-8">
          <div class="card-header-full header-info flex items-center justify-between">
            <div>
              <h4 class="card-title">Terminal de Asistencia Digital ("Pasar el Dedo")</h4>
              <p class="card-category">Check-in digital en tiempo real para eventos obligatorios de la Asociación</p>
            </div>
            <span class="badge-mat badge-mat-success animate-pulse">
              <i class="material-icons text-xs">wifi_tethering</i> Dispositivo Conectado
            </span>
          </div>

          <div class="card-body p-6 pt-8">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
              <!-- Scanner Interactivo -->
              <div class="flex flex-col items-center justify-center p-6 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-[var(--border-color)] text-center">
                <div id="fingerprint-btn" onclick="window.simularPaseDeDedo()" class="fingerprint-scanner mb-4">
                  <i class="material-icons text-4xl text-[var(--color-accent)]">fingerprint</i>
                </div>
                <h4 class="text-sm font-bold text-[var(--text-main)]">Coloca la huella o haz clic para marcar</h4>
                <p class="text-xs text-[var(--text-muted)] mt-1 max-w-xs">
                  Simula la marcación biométrica del socio autenticado para registrar la entrada fehaciente al evento activo.
                </p>

                <div id="scan-feedback" class="mt-4 text-xs font-semibold text-emerald-600 hidden flex items-center gap-1">
                  <i class="material-icons text-sm">check_circle</i> ¡Asistencia registrada exitosamente!
                </div>
              </div>

              <!-- Lista de Últimas Marcaciones -->
              <div>
                <h4 class="text-xs font-bold text-[var(--text-main)] uppercase tracking-wider mb-3 flex items-center justify-between">
                  <span>Últimos ingresos registrados</span>
                  <span class="text-blue-500 font-normal">Actualización en vivo</span>
                </h4>
                <div class="space-y-2 max-h-56 overflow-y-auto pr-1">
                  <div class="p-2.5 rounded border border-[var(--border-color)] bg-[var(--bg-card)] flex items-center justify-between text-xs">
                    <div>
                      <span class="font-bold text-[var(--text-main)]">Nicolás Rosales</span>
                      <span class="text-slate-400 ml-1.5">(Tribunal)</span>
                    </div>
                    <span class="font-mono text-emerald-600 font-bold">18:04:12</span>
                  </div>
                  <div class="p-2.5 rounded border border-[var(--border-color)] bg-[var(--bg-card)] flex items-center justify-between text-xs">
                    <div>
                      <span class="font-bold text-[var(--text-main)]">Diego Sánchez</span>
                      <span class="text-slate-400 ml-1.5">(Comisión Directiva)</span>
                    </div>
                    <span class="font-mono text-emerald-600 font-bold">18:02:45</span>
                  </div>
                  <div class="p-2.5 rounded border border-[var(--border-color)] bg-[var(--bg-card)] flex items-center justify-between text-xs">
                    <div>
                      <span class="font-bold text-[var(--text-main)]">Lucas Gastiaburu</span>
                      <span class="text-slate-400 ml-1.5">(Cómputos)</span>
                    </div>
                    <span class="font-mono text-emerald-600 font-bold">17:58:30</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    container.innerHTML = html;
  }

  // =========================================================================
  // 10. MODALES INTERACTIVOS Y ACCIONES
  // =========================================================================

  // Modal de Justificación Unificada T02 / T03
  let justificacionSelectedOption = 'A'; // 'A' (con certificado) o 'B' (descargo libre)
  let currentJustificarExpId = null;

  window.abrirModalJustificacion = function (expId) {
    currentJustificarExpId = expId;
    const exp = state.expedientes.find(e => e.id === expId);
    if (!exp) return;

    justificacionSelectedOption = 'A';

    const modalBody = document.getElementById('justificacion-modal-body');
    modalBody.innerHTML = `
      <div class="space-y-4">
        <div class="p-3 bg-blue-50 dark:bg-blue-950/30 rounded border border-blue-200 dark:border-blue-900 text-xs">
          <div class="font-bold text-blue-900 dark:text-blue-300 font-mono">Expediente Nº ${exp.id}</div>
          <div class="text-[var(--text-muted)] mt-0.5">Motivo de sanción: <strong>${exp.motivo}</strong> (${exp.puntos} puntos)</div>
          <div class="text-amber-700 dark:text-amber-400 mt-1 font-mono flex items-center gap-1">
            <i class="material-icons text-xs">timer</i> Plazo restante: ${formatHorasRestantes(exp.horasPlazoRestantes)}
          </div>
        </div>

        <!-- Selector de Modo Unificado Material PRO: Opción A vs Opción B -->
        <div class="grid grid-cols-2 gap-3 p-1 rounded bg-slate-100 dark:bg-slate-800">
          <button type="button" onclick="window.selectJustificacionOption('A')" id="btn-opt-a" 
            class="py-2 px-3 text-xs font-bold rounded transition-all ${justificacionSelectedOption === 'A' ? 'bg-white dark:bg-slate-700 text-blue-900 dark:text-white shadow' : 'text-slate-500'}">
            <i class="material-icons text-xs mr-1 align-middle">description</i> Opción A: Causal con Certificado
          </button>
          <button type="button" onclick="window.selectJustificacionOption('B')" id="btn-opt-b" 
            class="py-2 px-3 text-xs font-bold rounded transition-all ${justificacionSelectedOption === 'B' ? 'bg-white dark:bg-slate-700 text-blue-900 dark:text-white shadow' : 'text-slate-500'}">
            <i class="material-icons text-xs mr-1 align-middle">chat</i> Opción B: Descargo Extraordinario
          </button>
        </div>

        <div id="justificacion-option-content" class="space-y-4 pt-1">
          ${renderJustificacionOptionContent()}
        </div>
      </div>
    `;

    openModal('modal-justificacion');
  };

  window.selectJustificacionOption = function (opt) {
    justificacionSelectedOption = opt;
    const btnA = document.getElementById('btn-opt-a');
    const btnB = document.getElementById('btn-opt-b');
    if (opt === 'A') {
      btnA.className = 'py-2 px-3 text-xs font-bold rounded transition-all bg-white dark:bg-slate-700 text-blue-900 dark:text-white shadow';
      btnB.className = 'py-2 px-3 text-xs font-bold rounded transition-all text-slate-500';
    } else {
      btnB.className = 'py-2 px-3 text-xs font-bold rounded transition-all bg-white dark:bg-slate-700 text-blue-900 dark:text-white shadow';
      btnA.className = 'py-2 px-3 text-xs font-bold rounded transition-all text-slate-500';
    }
    const container = document.getElementById('justificacion-option-content');
    if (container) {
      container.innerHTML = renderJustificacionOptionContent();
    }
  };

  function renderJustificacionOptionContent() {
    if (justificacionSelectedOption === 'A') {
      return `
        <div class="space-y-3">
          <div>
            <label class="block text-xs font-bold text-[var(--text-main)] mb-1">Causal Reglamentaria Tipificada *</label>
            <select id="justif-causal" class="w-full p-2.5 rounded border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-main)] text-xs">
              <option value="Enfermedad debidamente certificada">Enfermedad debidamente certificada (médico matriculado)</option>
              <option value="Obligaciones académicas en UTN FRC">Obligaciones académicas en UTN FRC (examen o cursado obligatorio)</option>
              <option value="Obligaciones laborales documentadas">Obligaciones laborales documentadas (recibo de sueldo / certificación)</option>
              <option value="Fuerza mayor o catástrofe">Causa de fuerza mayor justificada con constancias</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-bold text-[var(--text-main)] mb-1">Comprobante Digital Probatorio * (Obligatorio)</label>
            <div class="border-2 border-dashed border-blue-300 dark:border-blue-700/60 rounded p-4 text-center bg-blue-50/20 dark:bg-blue-950/20">
              <i class="material-icons text-3xl text-blue-500 mb-1">cloud_upload</i>
              <p class="text-xs font-semibold text-[var(--text-main)]">Selecciona o arrastra el certificado probatorio</p>
              <p class="text-[11px] text-[var(--text-muted)] mt-0.5">Formatos admitidos: PDF, JPG, PNG (máx. 5 MB)</p>
              <input type="file" id="justif-file" onchange="window.handleFileSelect(this)" class="hidden">
              <button type="button" onclick="document.getElementById('justif-file').click()" class="btn-mat btn-white text-xs mt-3 py-1.5 px-3">
                <i class="material-icons text-xs mr-1">attach_file</i> Adjuntar Certificado
              </button>
              <div id="file-name-preview" class="text-xs font-mono font-bold text-emerald-600 mt-2 hidden"></div>
            </div>
          </div>

          <div>
            <label class="block text-xs font-bold text-[var(--text-main)] mb-1">Observaciones aclaratorias (opcional)</label>
            <textarea id="justif-obs" rows="2" placeholder="Detalles de la constancia presentada o institución emisora..." class="w-full p-2 rounded border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-main)] text-xs"></textarea>
          </div>
        </div>
      `;
    } else {
      return `
        <div class="space-y-3">
          <div class="p-3 bg-amber-50 dark:bg-amber-950/30 rounded text-xs text-amber-800 dark:text-amber-300 flex items-center gap-1.5">
            <i class="material-icons text-sm">info</i> El descargo extraordinario será evaluado bajo criterio colegiado por el Tribunal de Disciplina.
          </div>

          <div>
            <label class="block text-xs font-bold text-[var(--text-main)] mb-1">Exposición Fáctica Libre de las Circunstancias *</label>
            <textarea id="justif-descargo-libre" rows="4" required placeholder="Exponga detalladamente los motivos excepcionales que impidieron el cumplimiento y fundamenten su petición..." 
              class="w-full p-2.5 rounded border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-main)] text-xs"></textarea>
          </div>

          <div>
            <label class="block text-xs font-bold text-[var(--text-main)] mb-1">Comprobante adicional o constancia de respaldo (opcional)</label>
            <input type="file" id="justif-file-opt" class="w-full text-xs text-[var(--text-muted)]">
          </div>
        </div>
      `;
    }
  }

  let selectedFileName = null;
  window.handleFileSelect = function (input) {
    if (input.files && input.files[0]) {
      selectedFileName = input.files[0].name;
      const preview = document.getElementById('file-name-preview');
      if (preview) {
        preview.textContent = `Archivo adjunto: ${selectedFileName}`;
        preview.classList.remove('hidden');
      }
    }
  };

  window.enviarJustificacion = function () {
    const exp = state.expedientes.find(e => e.id === currentJustificarExpId);
    if (!exp) return;

    if (justificacionSelectedOption === 'A') {
      const causal = document.getElementById('justif-causal').value;
      const obs = document.getElementById('justif-obs').value;
      if (!selectedFileName) {
        showToast('Para causales con certificado es obligatorio adjuntar el archivo probatorio.', 'danger');
        return;
      }
      exp.justificacion = {
        tipo: 'T02 (Causal con Certificado)',
        causal: causal,
        archivoNombre: selectedFileName,
        observaciones: obs || 'Sin observaciones adicionales.',
        fechaEnvio: new Date().toLocaleString()
      };
    } else {
      const texto = document.getElementById('justif-descargo-libre').value.trim();
      if (!texto) {
        showToast('Debes exponer los hechos de tu descargo extraordinario.', 'warning');
        return;
      }
      exp.justificacion = {
        tipo: 'T03 (Descargo Extraordinario)',
        causal: 'Circunstancia Extraordinaria',
        archivoNombre: 'descargo_texto.txt',
        observaciones: texto,
        fechaEnvio: new Date().toLocaleString()
      };
    }

    // Transición automática al estado unificado: En revisión y resolución
    exp.estado = 'revision_resolucion';
    exp.horasPlazoRestantes = 0;
    saveState();

    closeModal('modal-justificacion');
    renderCurrentSubmodule();
    showToast('Justificación ingresada con éxito. El expediente pasa a revisión y resolución.', 'success');
  };

  // Modal de Votación Colegiada de los 3 Jueces
  let currentVotacionExpId = null;
  window.abrirModalVotacion = function (expId) {
    currentVotacionExpId = expId;
    const exp = state.expedientes.find(e => e.id === expId);
    if (!exp) return;

    const modalBody = document.getElementById('votacion-modal-body');
    modalBody.innerHTML = `
      <div class="space-y-4">
        <div class="p-3 bg-cyan-50 dark:bg-cyan-950/30 rounded border border-cyan-200 dark:border-cyan-800 text-xs">
          <div class="font-bold text-cyan-900 dark:text-cyan-200">Causa: ${exp.id} · ${exp.socio}</div>
          <div class="text-[var(--text-muted)] mt-0.5">Motivo: <strong>${exp.motivo}</strong> (${exp.puntos} pts)</div>
        </div>

        ${exp.justificacion ? `
          <div class="p-3 bg-slate-50 dark:bg-slate-800 rounded text-xs border border-[var(--border-color)]">
            <span class="font-bold text-[var(--text-main)] flex items-center gap-1"><i class="material-icons text-xs">article</i> Descargo presentado:</span>
            <p class="text-[var(--text-muted)] mt-1 italic">"${exp.justificacion.observaciones}"</p>
            <div class="mt-2 text-[11px] text-blue-600 font-mono flex items-center gap-1">
              <i class="material-icons text-xs">attachment</i> Adjunto: ${exp.justificacion.archivoNombre}
            </div>
          </div>
        ` : '<div class="text-xs text-amber-600 italic">Causa sin descargo ingresado en término (preclusión).</div>'}

        <div class="border-t border-[var(--border-color)] pt-3">
          <h4 class="text-xs font-bold text-[var(--text-main)] uppercase tracking-wider mb-2">Votación Nominal de los 3 Jueces</h4>
          
          <div class="space-y-2.5">
            <!-- Juez 1 -->
            <div class="p-2.5 rounded border border-[var(--border-color)] flex items-center justify-between text-xs">
              <div>
                <span class="font-bold">Juez 1: Nicolás Rosales</span>
                <span class="text-slate-400 ml-1">(Titular - Senior)</span>
              </div>
              <select id="voto-juez1" onchange="window.actualizarMayorias()" class="p-1.5 rounded border border-[var(--border-color)] bg-[var(--bg-card)] text-xs font-semibold">
                <option value="aprobar" ${exp.votos.juez1 === 'aprobar' ? 'selected' : ''}>Aprobar Descargo (Eximir Sanción)</option>
                <option value="rechazar" ${exp.votos.juez1 === 'rechazar' ? 'selected' : ''}>Rechazar y Confirmar Sanción</option>
                <option value="graduar" ${exp.votos.juez1 === 'graduar' ? 'selected' : ''}>Graduar Puntos a la mitad</option>
              </select>
            </div>

            <!-- Juez 2 -->
            <div class="p-2.5 rounded border border-[var(--border-color)] flex items-center justify-between text-xs">
              <div>
                <span class="font-bold">Juez 2: Lucas Martín Guillén</span>
                <span class="text-slate-400 ml-1">(Titular - Senior)</span>
              </div>
              <select id="voto-juez2" onchange="window.actualizarMayorias()" class="p-1.5 rounded border border-[var(--border-color)] bg-[var(--bg-card)] text-xs font-semibold">
                <option value="aprobar" ${exp.votos.juez2 === 'aprobar' ? 'selected' : ''}>Aprobar Descargo (Eximir Sanción)</option>
                <option value="rechazar" ${exp.votos.juez2 === 'rechazar' ? 'selected' : ''}>Rechazar y Confirmar Sanción</option>
                <option value="graduar" ${exp.votos.juez2 === 'graduar' ? 'selected' : ''}>Graduar Puntos a la mitad</option>
              </select>
            </div>

            <!-- Juez 3 -->
            <div class="p-2.5 rounded border border-[var(--border-color)] flex items-center justify-between text-xs">
              <div>
                <span class="font-bold">Juez 3: Miembro del TD</span>
                <span class="text-slate-400 ml-1">(Titular / Suplente Senior)</span>
              </div>
              <select id="voto-juez3" onchange="window.actualizarMayorias()" class="p-1.5 rounded border border-[var(--border-color)] bg-[var(--bg-card)] text-xs font-semibold">
                <option value="aprobar" ${exp.votos.juez3 === 'aprobar' ? 'selected' : ''}>Aprobar Descargo (Eximir Sanción)</option>
                <option value="rechazar" ${exp.votos.juez3 === 'rechazar' ? 'selected' : ''}>Rechazar y Confirmar Sanción</option>
                <option value="graduar" ${exp.votos.juez3 === 'graduar' ? 'selected' : ''}>Graduar Puntos a la mitad</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Dictamen y Considerandos -->
        <div>
          <label class="block text-xs font-bold text-[var(--text-main)] mb-1">Vistos y Considerandos del Dictamen *</label>
          <textarea id="dictamen-considerandos" rows="3" placeholder="Fundamentación fáctica y antecedentes valorados por el Tribunal..." 
            class="w-full p-2.5 rounded border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-main)] text-xs">${exp.considerando || ''}</textarea>
        </div>

        <div id="mayoria-indicator" class="p-2.5 rounded text-xs font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 text-center flex items-center justify-center gap-1">
          <i class="material-icons text-sm">check_circle</i> Quórum y mayoría absoluta alcanzada (3/3 votos concordantes)
        </div>
      </div>
    `;

    openModal('modal-votacion');
  };

  window.actualizarMayorias = function () {
    const v1 = document.getElementById('voto-juez1').value;
    const v2 = document.getElementById('voto-juez2').value;
    const v3 = document.getElementById('voto-juez3').value;
    const indicator = document.getElementById('mayoria-indicator');
    if (!indicator) return;

    // Calcular mayoría
    const votos = [v1, v2, v3];
    const counts = {};
    votos.forEach(v => counts[v] = (counts[v] || 0) + 1);
    const mayoria = Object.values(counts).some(c => c >= 2);

    if (mayoria) {
      indicator.className = 'p-2.5 rounded text-xs font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 text-center flex items-center justify-center gap-1';
      indicator.innerHTML = '<i class="material-icons text-sm">check_circle</i> Mayoría absoluta reglamentaria verificada (mínimo 2 de 3 votos)';
    } else {
      indicator.className = 'p-2.5 rounded text-xs font-bold bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 text-center flex items-center justify-center gap-1';
      indicator.innerHTML = '<i class="material-icons text-sm">warning</i> Sin mayoría absoluta (votos disidentes sin quórum de fallo)';
    }
  };

  window.guardarVotacionYDictamen = function () {
    const exp = state.expedientes.find(e => e.id === currentVotacionExpId);
    if (!exp) return;

    const v1 = document.getElementById('voto-juez1').value;
    const v2 = document.getElementById('voto-juez2').value;
    const v3 = document.getElementById('voto-juez3').value;
    const considerandos = document.getElementById('dictamen-considerandos').value.trim();

    if (!considerandos) {
      showToast('Debes ingresar los Vistos y Considerandos del dictamen.', 'warning');
      return;
    }

    exp.votos = { juez1: v1, juez2: v2, juez3: v3 };
    exp.considerando = considerandos;
    
    // Transiciona al siguiente estado: Pendiente de firma y envío
    exp.estado = 'pendiente_firma';
    saveState();

    closeModal('modal-votacion');
    renderCurrentSubmodule();
    showToast('Votación y dictamen registrados. La resolución pasa a pendiente de firma.', 'success');
  };

  // Modal de Firma Digital Colegiada Material PRO
  let currentFirmaExpId = null;
  window.abrirModalFirma = function (expId) {
    currentFirmaExpId = expId;
    const exp = state.expedientes.find(e => e.id === expId);
    if (!exp) return;

    const modalBody = document.getElementById('firma-modal-body');
    const firmas = exp.firmas;
    const todasFirmadas = firmas.juez1 && firmas.juez2 && firmas.juez3;

    modalBody.innerHTML = `
      <div class="space-y-4">
        <div class="p-3 bg-purple-50 dark:bg-purple-950/30 rounded border border-purple-200 dark:border-purple-800 text-xs">
          <div class="font-bold text-purple-900 dark:text-purple-200 font-mono">Resolución Oficial: ${exp.id}</div>
          <div class="text-[var(--text-muted)] mt-0.5">Socio: <strong>${exp.socio}</strong> · Dictamen consensuado</div>
        </div>

        <div class="space-y-3">
          <!-- Firma Juez 1 -->
          <div class="p-3 rounded border border-[var(--border-color)] flex items-center justify-between text-xs">
            <div>
              <div class="font-bold">Juez 1: Nicolás Rosales</div>
              <div class="text-[11px] text-[var(--text-muted)]">Firma Digital Interna (Hash SHA-256)</div>
            </div>
            ${firmas.juez1 ? `
              <span class="badge-mat badge-mat-success"><i class="material-icons text-xs">check</i> Firmado Digitalmente</span>
            ` : `
              <button onclick="window.aplicarFirma('juez1')" class="btn-mat btn-primary text-xs py-1 px-3">
                <i class="material-icons text-xs mr-1">vpn_key</i> Firmar
              </button>
            `}
          </div>

          <!-- Firma Juez 2 -->
          <div class="p-3 rounded border border-[var(--border-color)] flex items-center justify-between text-xs">
            <div>
              <div class="font-bold">Juez 2: Lucas Martín Guillén</div>
              <div class="text-[11px] text-[var(--text-muted)]">Firma Digital Interna (Hash SHA-256)</div>
            </div>
            ${firmas.juez2 ? `
              <span class="badge-mat badge-mat-success"><i class="material-icons text-xs">check</i> Firmado Digitalmente</span>
            ` : `
              <button onclick="window.aplicarFirma('juez2')" class="btn-mat btn-primary text-xs py-1 px-3">
                <i class="material-icons text-xs mr-1">vpn_key</i> Firmar
              </button>
            `}
          </div>

          <!-- Firma Juez 3 -->
          <div class="p-3 rounded border border-[var(--border-color)] flex items-center justify-between text-xs">
            <div>
              <div class="font-bold">Juez 3: Juez Senior AVEIT</div>
              <div class="text-[11px] text-[var(--text-muted)]">Firma Digital Interna (Hash SHA-256)</div>
            </div>
            ${firmas.juez3 ? `
              <span class="badge-mat badge-mat-success"><i class="material-icons text-xs">check</i> Firmado Digitalmente</span>
            ` : `
              <button onclick="window.aplicarFirma('juez3')" class="btn-mat btn-primary text-xs py-1 px-3">
                <i class="material-icons text-xs mr-1">vpn_key</i> Firmar
              </button>
            `}
          </div>
        </div>

        <!-- Botón de Publicación Definitiva -->
        <div class="pt-3 border-t border-[var(--border-color)] text-right">
          ${todasFirmadas ? `
            <button onclick="window.publicarResolucionDefinitiva()" class="btn-mat btn-success text-xs py-2 px-4 w-full">
              <i class="material-icons text-sm mr-1">send</i> Emitir Resolución Oficial e Impactar Puntos
            </button>
          ` : `
            <div class="text-xs text-amber-600 text-center font-semibold flex items-center justify-center gap-1">
              <i class="material-icons text-sm">lock</i> Se requieren las 3 firmas colegiadas para emitir y publicar el fallo.
            </div>
          `}
        </div>
      </div>
    `;

    openModal('modal-firma');
  };

  window.aplicarFirma = function (juezKey) {
    const exp = state.expedientes.find(e => e.id === currentFirmaExpId);
    if (!exp) return;
    exp.firmas[juezKey] = true;
    saveState();
    window.abrirModalFirma(currentFirmaExpId);
    showToast(`Firma digital del ${juezKey} aplicada correctamente.`, 'info');
  };

  window.publicarResolucionDefinitiva = function () {
    const exp = state.expedientes.find(e => e.id === currentFirmaExpId);
    if (!exp) return;

    // Transicionar a expedientes emitidos
    exp.estado = 'emitido';

    // Impactar en el saldo del socio de forma auditada
    const socioTarget = state.socios.find(s => s.nombre.toLowerCase() === exp.socio.toLowerCase() || s.legajo === exp.legajo);
    if (socioTarget) {
      socioTarget.saldo += exp.puntos;
      if (exp.tipoPuntos === 'premio') {
        socioTarget.felicitaciones += 1;
      } else {
        socioTarget.llamadosAtencion += 1;
      }

      // Actualizar semáforos
      if (socioTarget.saldo <= -10.0) {
        socioTarget.estado = 'limite_rojo';
        showToast(`ALERTA ROJA CRÍTICA: El socio ${socioTarget.nombre} alcanzó el límite de cese estatutario (-10 pts).`, 'danger');
      } else if (socioTarget.saldo <= -7.0) {
        socioTarget.estado = 'alerta_amarilla';
        showToast(`Alerta Preventiva Amarilla: El socio ${socioTarget.nombre} acumuló -7 pts.`, 'warning');
      }
    }

    saveState();
    closeModal('modal-firma');
    renderCurrentSubmodule();
    showToast('Resolución emitida exitosamente con firmas colegiadas. Puntos impactados.', 'success');
  };

  // Modal de Detalle Completo de Expediente Material PRO
  window.verDetalleExpediente = function (expId) {
    const exp = state.expedientes.find(e => e.id === expId);
    if (!exp) return;

    const estadoInfo = ESTADOS[exp.estado] || ESTADOS.creado;
    const modalBody = document.getElementById('detalle-modal-body');
    modalBody.innerHTML = `
      <div class="space-y-4 text-xs">
        <div class="flex items-center justify-between pb-3 border-b border-[var(--border-color)]">
          <div>
            <span class="text-[10px] text-[var(--text-muted)] uppercase tracking-wider font-semibold">Identificador de Causa</span>
            <h3 class="text-base font-bold font-mono text-[var(--text-main)]">${exp.id}</h3>
          </div>
          <span class="badge-mat ${estadoInfo.badgeClass}">
            <i class="material-icons text-xs">${estadoInfo.icon}</i> ${estadoInfo.nombre}
          </span>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div>
            <span class="text-[var(--text-muted)] font-semibold">Socio Involucrado:</span>
            <div class="font-bold text-[var(--text-main)] text-sm">${exp.socio}</div>
            <div class="text-[11px] text-[var(--text-muted)]">Legajo Nº ${exp.legajo} · ${exp.categoria}</div>
          </div>
          <div>
            <span class="text-[var(--text-muted)] font-semibold">Subcomisión de Radicación:</span>
            <div class="font-bold text-[var(--text-main)]">${exp.subcomision}</div>
            <div class="text-[11px] text-[var(--text-muted)]">Apertura: ${exp.fechaApertura}</div>
          </div>
        </div>

        <div class="p-3 bg-slate-50 dark:bg-slate-800/60 rounded border border-[var(--border-color)]">
          <span class="text-[var(--text-muted)] font-semibold">Motivo e Imputación:</span>
          <div class="text-sm font-bold text-[var(--text-main)] mt-0.5">${exp.motivo}</div>
          <div class="mt-1 flex items-center justify-between text-[11px]">
            <span>Origen: <strong>${exp.origen}</strong></span>
            <span class="font-bold ${exp.tipoPuntos === 'premio' ? 'text-emerald-600' : 'text-rose-600'}">
              ${exp.puntos > 0 ? '+' : ''}${exp.puntos} puntos
            </span>
          </div>
        </div>

        <!-- Descargos o Justificaciones -->
        <div>
          <span class="font-bold text-[var(--text-main)] uppercase tracking-wider text-[11px]">Descargo o Justificación Registrada</span>
          ${exp.justificacion ? `
            <div class="mt-1.5 p-3 rounded border border-blue-200 dark:border-blue-900 bg-blue-50/40 dark:bg-blue-950/20">
              <div class="font-bold text-blue-900 dark:text-blue-200">${exp.justificacion.tipo}</div>
              <div class="text-[11px] text-[var(--text-muted)] mt-0.5">Causal: ${exp.justificacion.causal}</div>
              <p class="text-xs text-[var(--text-main)] mt-1.5 italic">"${exp.justificacion.observaciones}"</p>
              <div class="mt-2 text-[11px] text-blue-600 font-mono flex items-center gap-1.5">
                <i class="material-icons text-xs">picture_as_pdf</i> Adjunto: ${exp.justificacion.archivoNombre}
              </div>
            </div>
          ` : `
            <div class="mt-1 text-slate-400 italic">No se ha presentado justificación para este expediente.</div>
          `}
        </div>

        <!-- Vistos y Considerandos -->
        ${exp.considerando ? `
          <div class="pt-2 border-t border-[var(--border-color)]">
            <span class="font-bold text-[var(--text-main)] uppercase tracking-wider text-[11px]">Vistos y Considerandos de la Resolución</span>
            <p class="mt-1 p-3 bg-slate-50 dark:bg-slate-800 rounded text-xs leading-relaxed text-[var(--text-muted)]">
              ${exp.considerando}
            </p>
          </div>
        ` : ''}
      </div>
    `;

    openModal('modal-detalle');
  };

  // Simulación de Asistencia "Pasar el dedo"
  window.simularPaseDeDedo = function () {
    const scanner = document.getElementById('fingerprint-btn');
    const feedback = document.getElementById('scan-feedback');
    const currentActor = ACTORS[state.currentActorId];

    if (scanner) scanner.classList.add('scanning');

    // Reproducir tono sutil de confirmación
    playBeepSound();

    setTimeout(() => {
      if (scanner) scanner.classList.remove('scanning');
      if (feedback) {
        feedback.classList.remove('hidden');
        feedback.innerHTML = `<i class="fas fa-check-circle mr-1"></i> ¡Marcación exitosa: ${currentActor.nombre} (Legajo ${currentActor.legajo})!`;
      }

      // Actualizar contadores del evento activo
      const evt = state.eventos.find(e => e.id === 'EVT-101');
      if (evt && evt.estado === 'en_curso') {
        evt.presentes += 1;
        evt.ausentes = Math.max(0, evt.ausentes - 1);
        saveState();
      }

      showToast(`Check-in digital registrado: ${currentActor.nombre}`, 'success');
      setTimeout(() => {
        if (feedback) feedback.classList.add('hidden');
        renderEventos(document.getElementById('submodule-content'));
      }, 2000);
    }, 1200);
  };

  // Acción de Cierre de Evento (Apertura automática de expedientes a ausentes)
  window.confirmarCierreEvento = function (evtId) {
    const evt = state.eventos.find(e => e.id === evtId);
    if (!evt) return;

    if (!confirm(`¿Confirmas el cierre definitivo del evento "${evt.nombre}"? Se generarán automáticamente los expedientes disciplinarios por inasistencia para los ${evt.ausentes} socios ausentes.`)) {
      return;
    }

    evt.estado = 'cerrado';

    // Generar causas automáticas a los ausentes
    const nuevosExpedientes = evt.listaAusentes.map((ausente, idx) => {
      return {
        id: `EXP-2026-0${50 + idx}`,
        socio: ausente.nombre,
        legajo: ausente.legajo,
        subcomision: ausente.subcomision,
        categoria: 'Socio Activo',
        motivo: `Inasistencia injustificada a ${evt.nombre}`,
        tipoPuntos: 'sancion',
        puntos: -2.0,
        estado: 'creado',
        fechaApertura: new Date().toLocaleString(),
        horasPlazoRestantes: 120,
        origen: `Cierre Automático: ${evt.nombre}`,
        autoridadSolicitante: 'Sistema SGD-AVEIT (Automático)',
        justificacion: null,
        votos: { juez1: null, juez2: null, juez3: null },
        firmas: { juez1: false, juez2: false, juez3: false },
        considerando: ''
      };
    });

    state.expedientes.unshift(...nuevosExpedientes);
    saveState();

    renderCurrentSubmodule();
    showToast(`Evento cerrado. Se abrieron ${nuevosExpedientes.length} expedientes disciplinarios en estado Creado.`, 'info');
  };

  // Enviar formulario T01 de solicitud de puntos
  window.enviarSolicitudPuntos = function (e) {
    e.preventDefault();
    const socioVal = document.getElementById('solicitud-socio').value;
    if (!socioVal) {
      showToast('Selecciona el socio involucrado.', 'warning');
      return;
    }

    const [nombre, legajo, subcomision, categoria] = socioVal.split('|');
    const tipo = document.getElementById('solicitud-tipo').value;
    const puntos = parseFloat(document.getElementById('solicitud-puntos').value);
    const motivo = document.getElementById('solicitud-motivo').value.trim();
    const relato = document.getElementById('anexo-relato').value.trim();
    const currentActor = ACTORS[state.currentActorId];

    const nuevoExp = {
      id: `EXP-2026-0${state.expedientes.length + 10}`,
      socio: nombre,
      legajo: legajo,
      subcomision: subcomision,
      categoria: categoria,
      motivo: motivo,
      tipoPuntos: tipo,
      puntos: puntos,
      estado: 'creado',
      fechaApertura: new Date().toLocaleString(),
      horasPlazoRestantes: 120,
      origen: `Formulario T01 por ${currentActor.rol}`,
      autoridadSolicitante: currentActor.nombre,
      justificacion: null,
      votos: { juez1: null, juez2: null, juez3: null },
      firmas: { juez1: false, juez2: false, juez3: false },
      considerando: relato
    };

    state.expedientes.unshift(nuevoExp);
    saveState();

    showToast('Solicitud T01 con Hoja de Anexo ingresada. Causa en estado Expediente Creado.', 'success');
    window.navigateTo('gestionar-expedientes');
  };

  // Exportación a Excel y PDF
  window.exportarReporteExcel = function () {
    const csvContent = "data:text/csv;charset=utf-8," 
      + "Expediente,Socio,Legajo,Subcomision,Motivo,Puntos,Estado\n"
      + state.expedientes.map(e => `"${e.id}","${e.socio}","${e.legajo}","${e.subcomision}","${e.motivo}",${e.puntos},"${e.estado}"`).join("\n");
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `Balance_Disciplinario_AVEIT_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('Planilla de balance exportada en formato Excel/CSV.', 'success');
  };

  window.imprimirReportePDF = function () {
    window.print();
  };

  // =========================================================================
  // 11. HELPERS, MODALES GENÉRICOS Y SIMULADOR DE ACTORES
  // =========================================================================

  window.setExpedientesViewMode = function (mode) {
    state.expedientesViewMode = mode;
    saveState();
    const container = document.getElementById('expedientes-view-container');
    if (container) {
      container.innerHTML = mode === 'kanban' ? renderKanbanBoardHtml() : renderExplorerTableHtml();
    }
  };

  window.sortExplorer = function (field) {
    if (sortField === field) {
      sortAsc = !sortAsc;
    } else {
      sortField = field;
      sortAsc = true;
    }
    const container = document.getElementById('expedientes-view-container');
    if (container) {
      container.innerHTML = renderExplorerTableHtml(document.getElementById('expedientes-search-input')?.value);
    }
  };

  window.filtrarExpedientes = function (val) {
    const container = document.getElementById('expedientes-view-container');
    if (container) {
      container.innerHTML = state.expedientesViewMode === 'kanban' ? renderKanbanBoardHtml(val) : renderExplorerTableHtml(val);
    }
  };

  window.setRankingSort = function (order) {
    rankingSortOrder = order;
    renderRanking(document.getElementById('submodule-content'));
  };

  window.setRankingFilterSub = function (sub) {
    rankingFilterSubcomision = sub;
    renderRanking(document.getElementById('submodule-content'));
  };

  window.setRankingFilterCat = function (cat) {
    rankingFilterCategoria = cat;
    renderRanking(document.getElementById('submodule-content'));
  };

  window.cambiarActorSimulado = function (actorId) {
    if (!ACTORS[actorId]) return;
    state.currentActorId = actorId;
    saveState();

    // Actualizar avatar y nombre en topbar
    const nameEl = document.getElementById('user-profile-name');
    const roleEl = document.getElementById('user-profile-role');
    const avatarEl = document.getElementById('user-profile-avatar');
    if (nameEl) nameEl.textContent = ACTORS[actorId].nombre;
    if (roleEl) roleEl.textContent = ACTORS[actorId].categoria;
    if (avatarEl) avatarEl.textContent = ACTORS[actorId].avatar;

    showToast(`Actor simulado: ${ACTORS[actorId].nombre} (${ACTORS[actorId].rol})`, 'info');
    renderCurrentSubmodule();
  };

  window.actualizarEscalaPuntos = function (tipo) {
    const select = document.getElementById('solicitud-puntos');
    if (!select) return;
    if (tipo === 'premio') {
      select.innerHTML = `
        <option value="0.5">+0.5 puntos (Reconocimiento leve por proactividad)</option>
        <option value="1.0">+1.0 punto (Excelente cumplimiento de tareas del área)</option>
        <option value="2.0" selected>+2.0 puntos (Aporte sobresaliente en eventos)</option>
        <option value="3.0">+3.0 puntos (Liderazgo en proyectos de infraestructura)</option>
      `;
    } else {
      select.innerHTML = `
        <option value="-0.5">-0.5 puntos (Llegada tarde o retiro sin previo aviso)</option>
        <option value="-1.0">-1.0 punto (Inasistencia a reunión obligatoria de subcomisión)</option>
        <option value="-2.0" selected>-2.0 puntos (Falta a Asamblea o incumplimiento de tareas)</option>
      `;
    }
  };

  function getSocioSaldo(legajo) {
    const s = state.socios.find(soc => soc.legajo === legajo);
    return s ? s.saldo : 0;
  }

  function formatPuntos(pts) {
    if (pts > 0) return `+${pts.toFixed(1)} pts`;
    return `${pts.toFixed(1)} pts`;
  }

  function getSaldoColorClass(pts) {
    if (pts <= -10) return 'text-rose-700 dark:text-rose-400';
    if (pts <= -7) return 'text-amber-600 dark:text-amber-400';
    if (pts < 0) return 'text-orange-600 dark:text-orange-400';
    if (pts > 0) return 'text-emerald-600 dark:text-emerald-400';
    return 'text-slate-600 dark:text-slate-300';
  }

  function formatHorasRestantes(horas) {
    if (horas <= 0) return 'Plazo vencido (120 h)';
    const dias = Math.floor(horas / 24);
    const h = horas % 24;
    return `${dias}d ${h}h hábiles restantes`;
  }

  function openModal(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('active');
  }

  window.closeModal = function (id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('active');
  };

  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    const borderClasses = {
      success: 'border-l-4 border-emerald-500',
      warning: 'border-l-4 border-amber-500',
      danger: 'border-l-4 border-rose-500',
      info: 'border-l-4 border-cyan-500'
    };
    const icons = {
      success: '<i class="material-icons text-emerald-500 text-xl">check_circle</i>',
      warning: '<i class="material-icons text-amber-500 text-xl">warning</i>',
      danger: '<i class="material-icons text-rose-500 text-xl">error</i>',
      info: '<i class="material-icons text-cyan-500 text-xl">info</i>'
    };
    if (borderClasses[type]) {
      toast.className += ' ' + borderClasses[type];
    }
    toast.innerHTML = `
      ${icons[type] || icons.info}
      <div class="text-xs font-semibold leading-snug">${message}</div>
    `;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      toast.style.transition = 'all 0.25s ease';
      setTimeout(() => toast.remove(), 250);
    }, 3800);
  }

  function playBeepSound() {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      gain.gain.setValueAtTime(0.1, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.15);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.15);
    } catch (e) {}
  }

  // =========================================================================
  // 12. INICIALIZACIÓN DE LA APLICACIÓN
  // =========================================================================

  window.navigateTo = navigateTo;
  window.toggleTheme = toggleTheme;

  document.addEventListener('DOMContentLoaded', () => {
    initTheme();

    // Event listener para theme toggle
    const themeBtn = document.getElementById('theme-toggle-btn');
    if (themeBtn) themeBtn.addEventListener('click', toggleTheme);

    // Event listeners para sidebar
    document.querySelectorAll('.sidebar-nav-item').forEach(btn => {
      btn.addEventListener('click', () => {
        const sub = btn.dataset.submodule;
        if (sub) navigateTo(sub);
      });
    });

    // Selector de actor simulado en topbar
    const actorSelect = document.getElementById('actor-simulado-select');
    if (actorSelect) {
      actorSelect.value = state.currentActorId;
      actorSelect.addEventListener('change', (e) => {
        window.cambiarActorSimulado(e.target.value);
      });
    }

    // Cargar vista inicial
    navigateTo(state.activeSubmodule || 'gestionar-expedientes');
  });

})();
