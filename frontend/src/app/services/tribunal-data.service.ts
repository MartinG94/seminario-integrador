import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export type EstadoExpediente = 
  | 'creado' 
  | 'justificando' 
  | 'revision_resolucion' 
  | 'pendiente_firma' 
  | 'emitido';

export type RolUsuario = 'socio' | 'tribunal' | 'presidente_cd';

export interface Expediente {
  id: string;
  numero: string;
  socio: string;
  legajo: string;
  subcomision: string;
  motivo: string;
  fechaCreacion: string;
  estado: EstadoExpediente;
  horasRestantes: number;
  tipo: 'falta' | 'merito';
  puntos: number;
  descargo?: {
    tipo: 'T02_CERTIFICADO' | 'T03_EXTRAORDINARIO';
    causal?: string;
    archivo?: string;
    texto: string;
    fecha: string;
  };
  votacion?: {
    votos: { [juez: string]: 'FAVORABLE' | 'DESFAVORABLE' | 'ABSTENCION' };
    considerandos?: string;
    aprobado?: boolean;
  };
  firmas?: {
    juecesFirmantes: string[];
    hashCriptografico?: string;
    timestamp?: string;
  };
}

export interface Socio {
  id: string;
  nombre: string;
  legajo: string;
  email: string;
  subcomision: string;
  saldo: number;
  estado: 'HABILITADO' | 'ADVERTENCIA' | 'CESE_ESTATUTARIO';
  felicitaciones: number;
  sanciones: number;
}

export interface EventoAsistencia {
  id: string;
  titulo: string;
  fecha: string;
  tipo: string;
  convocados: number;
  presentes: number;
  ausentes: number;
  estado: 'EN_CURSO' | 'CERRADO';
  logAsistencia: { socio: string; hora: string }[];
}

export interface SubcomisionReporte {
  nombre: string;
  totalExpedientes: number;
  sanciones: number;
  reconocimientos: number;
  saldoNeto: number;
  cumplimiento: number;
}

@Injectable({
  providedIn: 'root'
})
export class TribunalDataService {
  private currentRoleSubject = new BehaviorSubject<RolUsuario>('tribunal');
  public currentRole$ = this.currentRoleSubject.asObservable();

  private darkModeSubject = new BehaviorSubject<boolean>(false);
  public darkMode$ = this.darkModeSubject.asObservable();

  private expedientesSubject = new BehaviorSubject<Expediente[]>([
    {
      id: 'EXP-2026-001',
      numero: 'EXP-001/2026',
      socio: 'Lucas Gastiaburu',
      legajo: '74907',
      subcomision: 'Cómputos',
      motivo: 'Inasistencia no informada a asamblea general ordinaria',
      fechaCreacion: '2026-03-01',
      estado: 'justificando',
      horasRestantes: 74,
      tipo: 'falta',
      puntos: -1.0
    },
    {
      id: 'EXP-2026-002',
      numero: 'EXP-002/2026',
      socio: 'Lucas Martín Guillén',
      legajo: '85194',
      subcomision: 'Cómputos',
      motivo: 'Falta reiterada de entrega de informes operativos cuatrimestrales',
      fechaCreacion: '2026-03-02',
      estado: 'revision_resolucion',
      horasRestantes: 0,
      tipo: 'falta',
      puntos: -1.5,
      descargo: {
        tipo: 'T02_CERTIFICADO',
        causal: 'Examen Académico Universitario en UTN FRC',
        archivo: 'certificado_examen_utn.pdf',
        texto: 'Presento constancia de examen final rendido el mismo día en sede central.',
        fecha: '2026-03-03'
      },
      votacion: {
        votos: { 'Juez 1': 'FAVORABLE', 'Juez 2': 'FAVORABLE' },
        considerandos: 'El justificativo académico cumple las formalidades estatutarias requeridas.',
        aprobado: true
      }
    },
    {
      id: 'EXP-2026-003',
      numero: 'EXP-003/2026',
      socio: 'Nicolás Rosales',
      legajo: '408917',
      subcomision: 'Cómputos',
      motivo: 'Coordinación ejemplar en jornadas tecnológicas solidarias',
      fechaCreacion: '2026-02-28',
      estado: 'pendiente_firma',
      horasRestantes: 0,
      tipo: 'merito',
      puntos: 2.0,

      votacion: {
        votos: { 'Juez 1': 'FAVORABLE', 'Juez 2': 'FAVORABLE', 'Juez 3': 'FAVORABLE' },
        considerandos: 'Desempeño sobresaliente con impacto directo en la comunidad.',
        aprobado: true
      },
      firmas: {
        juecesFirmantes: ['Dr. Argañaraz (Presidente TD)', 'Dra. Bustos (Vocal)'],
        hashCriptografico: '',
        timestamp: ''
      }
    },
    {
      id: 'EXP-2026-004',
      numero: 'EXP-004/2026',
      socio: 'Valentina Rossi',
      legajo: 'LEG-6541',
      subcomision: 'Prensa y Difusión',
      motivo: 'Incumplimiento de tareas asignadas en cobertura institucional',
      fechaCreacion: '2026-02-15',
      estado: 'emitido',
      horasRestantes: 0,
      tipo: 'falta',
      puntos: -0.5,
      firmas: {
        juecesFirmantes: ['Presidente TD', 'Vocal 1', 'Vocal 2'],
        hashCriptografico: 'sha256-8f4b23c90e1a4d5e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0',
        timestamp: '2026-02-22 18:30:12'
      }
    },
    {
      id: 'EXP-2026-005',
      numero: 'EXP-005/2026',
      socio: 'Martín Gómez',
      legajo: 'LEG-5412',
      subcomision: 'Deportes',
      motivo: 'Ausencia en convocatoria de reacondicionamiento edilicio',
      fechaCreacion: '2026-03-04',
      estado: 'creado',
      horasRestantes: 120,
      tipo: 'falta',
      puntos: -1.0
    }
  ]);
  public expedientes$ = this.expedientesSubject.asObservable();

  private sociosSubject = new BehaviorSubject<Socio[]>([
    { id: '1', nombre: 'Lucas Gastiaburu', legajo: '74907', email: '74907@aveit.test', subcomision: 'Cómputos', saldo: 4.5, estado: 'HABILITADO', felicitaciones: 3, sanciones: 0 },
    { id: '2', nombre: 'Lucas Martín Guillén', legajo: '85194', email: '85194@aveit.test', subcomision: 'Cómputos', saldo: 2.0, estado: 'HABILITADO', felicitaciones: 2, sanciones: 1 },
    { id: '3', nombre: 'Diego Gabriel Sánchez', legajo: '87414', email: '87414@aveit.test', subcomision: 'Cómputos', saldo: -2.5, estado: 'HABILITADO', felicitaciones: 1, sanciones: 2 },
    { id: '4', nombre: 'Nicolás Rosales', legajo: '408917', email: '408917@aveit.test', subcomision: 'Cómputos', saldo: 6.0, estado: 'HABILITADO', felicitaciones: 4, sanciones: 0 },
    { id: '5', nombre: 'Axel René Villegas', legajo: '403655', email: '403655@aveit.test', subcomision: 'Cómputos', saldo: -7.5, estado: 'ADVERTENCIA', felicitaciones: 0, sanciones: 4 }
  ]);
  public socios$ = this.sociosSubject.asObservable();

  private eventosSubject = new BehaviorSubject<EventoAsistencia[]>([
    {
      id: 'EVT-01',
      titulo: 'Asamblea Ordinaria Primer Cuatrimestre',
      fecha: '2026-03-05',
      tipo: 'Asamblea Obligatoria',
      convocados: 48,
      presentes: 41,
      ausentes: 7,
      estado: 'EN_CURSO',
      logAsistencia: [
        { socio: 'Ignacio Morales', hora: '19:04:12' },
        { socio: 'Florencia Herrera', hora: '19:06:45' },
        { socio: 'Lucas Benítez', hora: '19:10:02' }
      ]
    },
    {
      id: 'EVT-02',
      titulo: 'Jornada Integral de Voluntariado Comunitario',
      fecha: '2026-02-20',
      tipo: 'Actividad Institucional',
      convocados: 35,
      presentes: 33,
      ausentes: 2,
      estado: 'CERRADO',
      logAsistencia: []
    }
  ]);
  public eventos$ = this.eventosSubject.asObservable();

  constructor() {
    const savedDark = localStorage.getItem('aveit_dark_mode') === 'true';
    if (savedDark) {
      this.setDarkMode(true);
    }
  }

  setRole(role: RolUsuario): void {
    this.currentRoleSubject.next(role);
  }

  getRole(): RolUsuario {
    return this.currentRoleSubject.value;
  }

  setDarkMode(isDark: boolean): void {
    this.darkModeSubject.next(isDark);
    localStorage.setItem('aveit_dark_mode', String(isDark));
    if (isDark) {
      document.body.classList.add('dark-edition');
      document.documentElement.classList.add('dark');
    } else {
      document.body.classList.remove('dark-edition');
      document.documentElement.classList.remove('dark');
    }
  }

  toggleDarkMode(): void {
    this.setDarkMode(!this.darkModeSubject.value);
  }

  // --- Operaciones de Dominio de Expedientes ---

  enviarDescargo(
    expedienteId: string, 
    tipo: 'T02_CERTIFICADO' | 'T03_EXTRAORDINARIO', 
    datos: { causal?: string; archivo?: string; texto: string }
  ): boolean {
    const current = this.expedientesSubject.value;
    const index = current.findIndex(e => e.id === expedienteId);
    if (index === -1) return false;

    const updated = { ...current[index] };
    updated.estado = 'revision_resolucion';
    updated.descargo = {
      tipo,
      causal: datos.causal,
      archivo: datos.archivo,
      texto: datos.texto,
      fecha: new Date().toISOString().split('T')[0]
    };

    const newArr = [...current];
    newArr[index] = updated;
    this.expedientesSubject.next(newArr);
    return true;
  }

  votarDictamen(
    expedienteId: string, 
    votos: { [juez: string]: 'FAVORABLE' | 'DESFAVORABLE' | 'ABSTENCION' }, 
    considerandos: string
  ): boolean {
    const current = this.expedientesSubject.value;
    const index = current.findIndex(e => e.id === expedienteId);
    if (index === -1) return false;

    const exp = { ...current[index] };
    const favorables = Object.values(votos).filter(v => v === 'FAVORABLE').length;
    const quorumn = Object.keys(votos).length;
    const aprobado = quorumn >= 2 && favorables >= 2;

    exp.votacion = {
      votos,
      considerandos,
      aprobado
    };

    if (aprobado) {
      exp.estado = 'pendiente_firma';
      exp.firmas = {
        juecesFirmantes: [],
        hashCriptografico: '',
        timestamp: ''
      };
    }

    const newArr = [...current];
    newArr[index] = exp;
    this.expedientesSubject.next(newArr);
    return true;
  }

  firmarResolucion(expedienteId: string, juezFirmante: string): { completo: boolean; exp?: Expediente } {
    const current = this.expedientesSubject.value;
    const index = current.findIndex(e => e.id === expedienteId);
    if (index === -1) return { completo: false };

    const exp = { ...current[index] };
    if (!exp.firmas) {
      exp.firmas = { juecesFirmantes: [], hashCriptografico: '', timestamp: '' };
    }

    if (!exp.firmas.juecesFirmantes.includes(juezFirmante)) {
      exp.firmas.juecesFirmantes.push(juezFirmante);
    }

    let completo = false;
    if (exp.firmas.juecesFirmantes.length >= 3) {
      completo = true;
      exp.estado = 'emitido';
      exp.firmas.hashCriptografico = 'sha256-' + Math.random().toString(36).substring(2) + Date.now().toString(36);
      exp.firmas.timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);

      // Impactar en el saldo del socio
      this.actualizarSaldoSocio(exp.socio, exp.puntos);
    }

    const newArr = [...current];
    newArr[index] = exp;
    this.expedientesSubject.next(newArr);
    return { completo, exp };
  }

  private actualizarSaldoSocio(nombreSocio: string, deltaPuntos: number): void {
    const socios = this.sociosSubject.value;
    const idx = socios.findIndex(s => s.nombre.toLowerCase() === nombreSocio.toLowerCase());
    if (idx !== -1) {
      const socio = { ...socios[idx] };
      socio.saldo = Math.round((socio.saldo + deltaPuntos) * 10) / 10;
      if (deltaPuntos > 0) socio.felicitaciones++;
      if (deltaPuntos < 0) socio.sanciones++;

      if (socio.saldo <= -10.0) {
        socio.estado = 'CESE_ESTATUTARIO';
      } else if (socio.saldo <= -7.0) {
        socio.estado = 'ADVERTENCIA';
      } else {
        socio.estado = 'HABILITADO';
      }

      const newSocios = [...socios];
      newSocios[idx] = socio;
      this.sociosSubject.next(newSocios);
    }
  }

  solicitarPuntos(solicitud: {
    socio: string;
    subcomision: string;
    tipo: 'falta' | 'merito';
    puntos: number;
    motivo: string;
    anexoRelato: string;
    anexoFecha: string;
    anexoTestigos: string;
  }): Expediente {
    const current = this.expedientesSubject.value;
    const num = (current.length + 1).toString().padStart(3, '0');
    const newExp: Expediente = {
      id: `EXP-2026-${num}`,
      numero: `EXP-${num}/2026`,
      socio: solicitud.socio,
      legajo: 'LEG-' + Math.floor(1000 + Math.random() * 9000),
      subcomision: solicitud.subcomision,
      motivo: `${solicitud.motivo} (Anexo: ${solicitud.anexoRelato.substring(0, 50)}...)`,
      fechaCreacion: new Date().toISOString().split('T')[0],
      estado: 'creado',
      horasRestantes: 120,
      tipo: solicitud.tipo,
      puntos: solicitud.puntos
    };

    this.expedientesSubject.next([newExp, ...current]);
    return newExp;
  }

  // --- Operaciones de Asistencia y Biometría ---

  registrarAsistenciaBiometrica(eventoId: string, nombreSocio: string): boolean {
    const eventos = this.eventosSubject.value;
    const idx = eventos.findIndex(e => e.id === eventoId);
    if (idx === -1) return false;

    const evento = { ...eventos[idx] };
    if (evento.estado === 'CERRADO') return false;

    evento.presentes++;
    if (evento.ausentes > 0) evento.ausentes--;

    const hora = new Date().toTimeString().split(' ')[0];
    evento.logAsistencia = [{ socio: nombreSocio, hora }, ...evento.logAsistencia];

    this.reproducirBeepBiometrico();

    const newEventos = [...eventos];
    newEventos[idx] = evento;
    this.eventosSubject.next(newEventos);
    return true;
  }

  reproducirBeepBiometrico(): void {
    try {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioContextClass) return;
      const ctx = new AudioContextClass();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(1320, ctx.currentTime + 0.12);

      gain.gain.setValueAtTime(0.15, ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0.01, ctx.currentTime + 0.12);

      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.12);
    } catch (e) {
      console.warn('AudioContext feedback not supported', e);
    }
  }

  cerrarEvento(eventoId: string): { expedientesGenerados: number } {
    const eventos = this.eventosSubject.value;
    const idx = eventos.findIndex(e => e.id === eventoId);
    if (idx === -1) return { expedientesGenerados: 0 };

    const evt = { ...eventos[idx] };
    evt.estado = 'CERRADO';
    const newEventos = [...eventos];
    newEventos[idx] = evt;
    this.eventosSubject.next(newEventos);

    // Generar expedientes por ausencia injustificada
    const ausentes = evt.ausentes;
    for (let i = 1; i <= ausentes; i++) {
      this.solicitarPuntos({
        socio: `Miembro Ausente #${i}`,
        subcomision: 'Comunicaciones',
        tipo: 'falta',
        puntos: -1.0,
        motivo: `Inasistencia no justificada a evento institucional: ${evt.titulo}`,
        anexoRelato: `Ausente registrado en el cierre formal de la asistencia digital sin descargo previo.`,
        anexoFecha: evt.fecha,
        anexoTestigos: 'Autoridades de Mesa de Entrada y Registro Digital'
      });
    }

    return { expedientesGenerados: ausentes };
  }

  // --- Reportes & Balances Cuatrimestrales ---

  obtenerBalancePorSubcomision(): SubcomisionReporte[] {
    const exps = this.expedientesSubject.value;
    const subcomisiones = [
      'Comunicaciones', 'Deportes', 'Extensión Universitaria', 
      'Finanzas', 'Prensa y Difusión', 'Relaciones Públicas', 'Tesorería'
    ];

    return subcomisiones.map(sub => {
      const subExps = exps.filter(e => e.subcomision.toLowerCase().includes(sub.toLowerCase()));
      const sanciones = subExps.filter(e => e.tipo === 'falta').length;
      const reconocimientos = subExps.filter(e => e.tipo === 'merito').length;
      const saldoNeto = subExps.reduce((acc, curr) => acc + curr.puntos, 0);
      const cumplimiento = subExps.length > 0 ? Math.round((reconocimientos / subExps.length) * 100) : 100;

      return {
        nombre: sub,
        totalExpedientes: subExps.length,
        sanciones,
        reconocimientos,
        saldoNeto: Math.round(saldoNeto * 10) / 10,
        cumplimiento
      };
    });
  }

  exportarCSV(nombreArchivo: string, datos: any[]): void {
    if (!datos || !datos.length) return;
    const headers = Object.keys(datos[0]).join(',');
    const rows = datos.map(obj => Object.values(obj).map(val => `"${val}"`).join(','));
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers, ...rows].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${nombreArchivo}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}
