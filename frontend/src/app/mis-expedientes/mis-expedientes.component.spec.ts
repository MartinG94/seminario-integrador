import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { environment } from '../../environments/environment';
import { MisExpedientesComponent } from './mis-expedientes.component';
import { NotificationService } from '../services/notification.service';
import { TribunalDataService, Expediente } from '../services/tribunal-data.service';

describe('MisExpedientesComponent', () => {
  let component: MisExpedientesComponent;
  let fixture: ComponentFixture<MisExpedientesComponent>;
  let notifications: jasmine.SpyObj<NotificationService>;
  let http: HttpTestingController;
  const apiUrl = `${environment.apiUrl}/expedientes`;

  beforeEach(async(() => {
    notifications = jasmine.createSpyObj('NotificationService', ['error', 'success', 'info']);
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, FormsModule],
      declarations: [MisExpedientesComponent],
      providers: [TribunalDataService, { provide: NotificationService, useValue: notifications }]
    }).compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MisExpedientesComponent);
    component = fixture.componentInstance;
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('notifica validaciones de justificativo sin enviar un descargo inválido', () => {
    const submit = spyOn(TestBed.inject(TribunalDataService), 'enviarDescargo');
    component.expedienteSeleccionado = { id: 'test' } as Expediente;
    component.tipoDescargo = 'T02_CERTIFICADO';
    component.nombreArchivo = '';
    component.archivosSeleccionados = [];
    component.enviarDescargo();
    expect(notifications.error).toHaveBeenCalledWith('Debe adjuntar al menos un documento.');
    component.tipoDescargo = 'T03_EXTRAORDINARIO';
    component.relatoTexto = '';
    component.enviarDescargo();
    expect(notifications.error).toHaveBeenCalledWith('Por favor ingrese el motivo de la justificación.');
    
    // Validar límite superior de 5000 caracteres (decisión del PO, igual al T01)
    component.relatoTexto = 'X'.repeat(5001);
    component.enviarDescargo();
    expect(notifications.error).toHaveBeenCalledWith('El motivo o justificación no puede superar los 5000 caracteres.');
    expect(submit).not.toHaveBeenCalled();
  });

  it('expone el límite de 5000 caracteres y acepta un texto de exactamente ese largo', () => {
    expect(component.MAX_CARACTERES_JUSTIFICACION).toBe(5000);
    const submit = spyOn(TestBed.inject(TribunalDataService), 'enviarDescargo');
    component.expedienteSeleccionado = { id: 'test' } as Expediente;
    component.tipoDescargo = 'T03_EXTRAORDINARIO';
    component.causalSeleccionada = 'Otro';
    component.relatoTexto = 'X'.repeat(5000);
    component.enviarDescargo();
    expect(notifications.error).not.toHaveBeenCalledWith(
      'El motivo o justificación no puede superar los 5000 caracteres.'
    );
    const req = http.expectOne({ method: 'POST', url: `${apiUrl}/test/descargo/` });
    expect(req.request.body.texto.length).toBe(5000);
    req.flush({ detail: 'ok' }, { status: 201, statusText: 'Created' });
    expect(submit).toHaveBeenCalled();
  });

  it('permite alternar causal a Otro y modela descargo como extraordinario', () => {
    component.causalSeleccionada = 'Otro';
    component.onCausalChange();
    expect(component.tipoDescargo).toBe('T03_EXTRAORDINARIO');
    expect(component.limiteActual).toBe(5);

    component.causalSeleccionada = 'Compromiso Laboral Comprobable';
    component.onCausalChange();
    expect(component.tipoDescargo).toBe('T02_CERTIFICADO');
    expect(component.limiteActual).toBe(3);
  });

  it('permite enviar motivo o justificación opcional en justificaciones con certificado (T02)', () => {
    const submit = spyOn(TestBed.inject(TribunalDataService), 'enviarDescargo');
    component.expedienteSeleccionado = { id: 'test-t02' } as Expediente;
    component.tipoDescargo = 'T02_CERTIFICADO';
    component.causalSeleccionada = 'Examen Académico Universitario en UTN FRC';
    component.nombreArchivo = 'certificado.pdf';
    component.relatoTexto = 'Rendí examen de Sistemas Operativos en el turno mañana.';
    component.enviarDescargo();

    const req = http.expectOne({ method: 'POST', url: `${apiUrl}/test-t02/descargo/` });
    expect(req.request.body.tipo).toBe('T02_CERTIFICADO');
    expect(req.request.body.causal).toBe('Examen Académico Universitario en UTN FRC');
    expect(req.request.body.texto).toBe('Rendí examen de Sistemas Operativos en el turno mañana.');
    req.flush({ detail: 'ok' }, { status: 201, statusText: 'Created' });
    expect(submit).toHaveBeenCalled();
  });

  describe('Custodia de Evidencias Protegidas (US S3-04)', () => {
    it('valida límite de hasta 3 comprobantes para causal tipificada considerando evidencias existentes y nuevas', () => {
      component.tipoDescargo = 'T02_CERTIFICADO';
      component.evidenciasExistentes = [{ id: 10, nombre_original: 'previo.pdf', tamano_bytes: 1024 }];
      const file1 = new File(['1'], 'doc1.pdf', { type: 'application/pdf' });
      const file2 = new File(['2'], 'doc2.pdf', { type: 'application/pdf' });
      const file3 = new File(['3'], 'doc3.pdf', { type: 'application/pdf' });

      // 1 existente + 3 nuevos = 4 > 3
      component.onFileSelected({ target: { files: [file1, file2, file3] } });
      expect(notifications.error).toHaveBeenCalledWith('Solo se admite un máximo de 3 documentos en total.');
      expect(component.archivosSeleccionados.length).toBe(0);
    });

    it('valida límite de 5 MB por archivo', () => {
      component.tipoDescargo = 'T02_CERTIFICADO';
      const bigFile = new File([''], 'grande.pdf', { type: 'application/pdf' });
      Object.defineProperty(bigFile, 'size', { value: 6 * 1024 * 1024 });

      component.onFileSelected({ target: { files: [bigFile] } });
      expect(notifications.error).toHaveBeenCalledWith('El archivo "grande.pdf" supera el límite de 5 MB.');
      expect(component.archivosSeleccionados.length).toBe(0);
    });

    it('valida formatos permitidos (PDF, JPG, PNG)', () => {
      component.tipoDescargo = 'T02_CERTIFICADO';
      const exeFile = new File(['test'], 'malicioso.exe', { type: 'application/octet-stream' });

      component.onFileSelected({ target: { files: [exeFile] } });
      expect(notifications.error).toHaveBeenCalledWith('El archivo "malicioso.exe" no tiene un formato válido (PDF, JPG, PNG).');
      expect(component.archivosSeleccionados.length).toBe(0);
    });

    it('rechaza archivos que ya están en custodia (evidenciasExistentes)', () => {
      component.tipoDescargo = 'T02_CERTIFICADO';
      component.evidenciasExistentes = [{ id: 1, nombre_original: 'comprobante_duplicado.pdf' }];
      const dupFile = new File(['test'], 'comprobante_duplicado.pdf', { type: 'application/pdf' });

      component.onFileSelected({ target: { files: [dupFile] } });
      expect(notifications.error).toHaveBeenCalledWith('El documento "comprobante_duplicado.pdf" ya se encuentra adjunto.');
      expect(component.archivosSeleccionados.length).toBe(0);
    });

    it('rechaza archivos que ya fueron seleccionados en la tanda actual', () => {
      component.tipoDescargo = 'T02_CERTIFICADO';
      const file = new File(['test'], 'repetido.pdf', { type: 'application/pdf' });
      component.archivosSeleccionados = [file];

      const dupFile = new File(['test'], 'repetido.pdf', { type: 'application/pdf' });
      component.onFileSelected({ target: { files: [dupFile] } });
      expect(notifications.error).toHaveBeenCalledWith('El archivo "repetido.pdf" ya está seleccionado.');
      expect(component.archivosSeleccionados.length).toBe(1);
    });

    it('abre modal propio de confirmación al querer remover un archivo seleccionado y lo elimina si confirma', () => {
      const file1 = new File(['1'], 'doc1.pdf', { type: 'application/pdf' });
      const file2 = new File(['2'], 'doc2.pdf', { type: 'application/pdf' });
      component.tipoDescargo = 'T02_CERTIFICADO';
      component.archivosSeleccionados = [file1, file2];

      component.removerArchivo(0);
      expect(component.modalConfirmacionAbierto).toBeTrue();
      expect(component.modalConfirmacionTitulo).toBe('Quitar archivo');

      component.confirmarAccion();
      expect(component.modalConfirmacionAbierto).toBeFalse();
      expect(component.archivosSeleccionados.length).toBe(1);
      expect(component.archivosSeleccionados[0].name).toBe('doc2.pdf');
    });

    it('no remueve un archivo si el usuario cancela en el modal propio', () => {
      const file1 = new File(['1'], 'doc1.pdf', { type: 'application/pdf' });
      component.archivosSeleccionados = [file1];

      component.removerArchivo(0);
      expect(component.modalConfirmacionAbierto).toBeTrue();

      component.cerrarConfirmacion();
      expect(component.modalConfirmacionAbierto).toBeFalse();
      expect(component.archivosSeleccionados.length).toBe(1);
    });

    it('abre modal propio y remueve evidencia existente tras confirmación', () => {
      component.evidenciasExistentes = [{ id: 10, nombre_original: 'doc_custodia.pdf' }];

      component.removerEvidenciaExistente(0);
      expect(component.modalConfirmacionAbierto).toBeTrue();
      expect(component.modalConfirmacionTitulo).toBe('Eliminar documento');

      component.confirmarAccion();
      expect(component.modalConfirmacionAbierto).toBeFalse();
      expect(component.evidenciasExistentes.length).toBe(0);
      expect(notifications.info).toHaveBeenCalledWith('Documento "doc_custodia.pdf" eliminado del justificativo.');
    });

    it('controla puedeSubirMas ocultando subida al alcanzar límite (3 para T02, 5 para T03)', () => {
      component.tipoDescargo = 'T02_CERTIFICADO';
      component.evidenciasExistentes = [
        { id: 1, nombre_original: 'a.pdf' },
        { id: 2, nombre_original: 'b.pdf' }
      ];
      component.archivosSeleccionados = [new File([''], 'c.pdf')];
      expect(component.totalComprobantes).toBe(3);
      expect(component.puedeSubirMas).toBeFalse();

      component.removerArchivo(0);
      expect(component.modalConfirmacionAbierto).toBeTrue();
      component.confirmarAccion();
      expect(component.totalComprobantes).toBe(2);
      expect(component.puedeSubirMas).toBeTrue();
    });

    it('abre modal propio de confirmación al retirar el descargo y lo procesa al confirmar el servidor', () => {
      const expMock: Expediente = {
        id: 'EXP-1',
        numero: 'EXP-001/2026',
        descargo: { tipo: 'T02_CERTIFICADO', texto: 'test', fecha: '2026-10-10' }
      } as Expediente;

      const eliminarSpy = spyOn(TestBed.inject(TribunalDataService), 'eliminarDescargo');

      component.eliminarDescargo(expMock);
      expect(component.modalConfirmacionAbierto).toBeTrue();
      expect(component.modalConfirmacionTitulo).toBe('Retirar descargo');
      expect(eliminarSpy).not.toHaveBeenCalled();

      component.confirmarAccion();
      expect(component.modalConfirmacionAbierto).toBeFalse();
      expect(eliminarSpy).not.toHaveBeenCalled();

      http.expectOne({ method: 'DELETE', url: `${apiUrl}/EXP-1/descargo/` }).flush({ detail: 'ok' });
      expect(eliminarSpy).toHaveBeenCalledWith('EXP-1', jasmine.any(Object));
      expect(notifications.info).toHaveBeenCalledWith(
        'Descargo del expediente 1/2026 retirado. Queda registrado en el historial.'
      );
    });

    it('formatea adecuadamente el tamaño de archivo en bytes', () => {
      expect(component.formatFileSize(500)).toBe('500 B');
      expect(component.formatFileSize(2048)).toBe('2.0 KB');
      expect(component.formatFileSize(1048576 * 2.5)).toBe('2.50 MB');
    });
  });

  describe('Coloreado de Puntos Totales', () => {
    it('retorna clase verde para puntos >= 0', () => {
      expect(component.getColorClasePuntos(10)).toBe('puntos-verde');
      expect(component.getColorClasePuntos(0)).toBe('puntos-verde');
      expect(component.getHeaderClassPuntos(0)).toBe('card-header-success');
    });

    it('retorna clase gris para puntos < 0 y >= -7', () => {
      expect(component.getColorClasePuntos(-1)).toBe('puntos-gris');
      expect(component.getColorClasePuntos(-7)).toBe('puntos-gris');
      expect(component.getHeaderClassPuntos(-5)).toBe('card-header-secondary');
    });

    it('retorna clase amarillo para puntos < -7 y >= -9', () => {
      expect(component.getColorClasePuntos(-7.5)).toBe('puntos-amarillo');
      expect(component.getColorClasePuntos(-8)).toBe('puntos-amarillo');
      expect(component.getColorClasePuntos(-9)).toBe('puntos-amarillo');
      expect(component.getHeaderClassPuntos(-8)).toBe('card-header-warning');
    });

    it('retorna clase rojo para puntos < -9', () => {
      expect(component.getColorClasePuntos(-9.5)).toBe('puntos-rojo');
      expect(component.getColorClasePuntos(-15)).toBe('puntos-rojo');
      expect(component.getHeaderClassPuntos(-10)).toBe('card-header-danger');
    });
  });

  describe('Ordenamiento de tabla', () => {
    const mockExpedientes: Expediente[] = [
      {
        id: '1',
        numero: 'EXP-2026-002',
        tipo: 'falta',
        socio: 'Juan Perez',
        legajo: '12345',
        motivo: 'Falta a reunión',
        subcomision: 'Deportes',
        puntos: -2,
        estado: 'creado',
        fechaCreacion: '2026-03-01',
        horasRestantes: 72
      },
      {
        id: '2',
        numero: 'EXP-2026-001',
        tipo: 'merito',
        socio: 'Juan Perez',
        legajo: '12345',
        motivo: 'Reconocimiento',
        subcomision: 'Cultura',
        puntos: 5,
        estado: 'emitido',
        fechaCreacion: '2026-02-15',
        horasRestantes: 0
      }
    ];

    beforeEach(() => {
      component.misExpedientes = [...mockExpedientes];
    });

    it('ordena ascendentemente por defecto', () => {
      component.columnaOrden = 'numero';
      component.ordenAscendente = true;
      const ordenados = component.expedientesOrdenados;
      expect(ordenados[0].numero).toBe('EXP-2026-001');
      expect(ordenados[1].numero).toBe('EXP-2026-002');
    });

    it('invierte orden al hacer click en la misma columna', () => {
      component.columnaOrden = 'numero';
      component.ordenAscendente = true;
      component.cambiarOrden('numero');
      expect(component.ordenAscendente).toBeFalse();
      const ordenados = component.expedientesOrdenados;
      expect(ordenados[0].numero).toBe('EXP-2026-002');
      expect(ordenados[1].numero).toBe('EXP-2026-001');
    });

    it('cambia columna y reinicia orden a ascendente', () => {
      component.columnaOrden = 'numero';
      component.ordenAscendente = false;
      component.cambiarOrden('motivo');
      expect(component.columnaOrden).toBe('motivo');
      expect(component.ordenAscendente).toBeTrue();
    });
  });

  describe('Temporizador Dinámico y Plazo Preclusivo (S3-02 / CA3)', () => {
    const expEnPlazo: Expediente = {
      id: 'EXP-01',
      numero: 'EXP-001/2026',
      tipo: 'falta',
      socio: 'Lucas Gastiaburu',
      legajo: '74907',
      motivo: 'Inasistencia',
      subcomision: 'Cómputos',
      puntos: -1,
      estado: 'justificando',
      fechaCreacion: '2026-10-08',
      horasRestantes: 48,
      plazoInicioAt: '2026-10-08T18:00:00-03:00',
      plazoLimiteAt: '2026-10-15T18:00:00-03:00',
      descargoPresentado: false
    };

    it('formatea la fecha y hora exacta del vencimiento (getDeadlineLabel)', () => {
      const label = component.getDeadlineLabel(expEnPlazo);
      expect(label).toContain('Vence:');
      expect(label).toContain('15/10/2026');
      expect(label).toContain('18:00 hs');
    });

    it('calcula el countdown dinámico restante cuando está en plazo (getCountdownLabel)', () => {
      // Fijamos ahoraMs a 2 días y 4 horas antes del vencimiento
      const vencimientoMs = new Date('2026-10-15T18:00:00-03:00').getTime();
      component.ahoraMs = vencimientoMs - (2 * 86400 + 4 * 3600 + 15 * 60) * 1000;

      const countdown = component.getCountdownLabel(expEnPlazo);
      expect(countdown).toBe('2d 04h 15m restantes');
      expect(component.esPlazoVencido(expEnPlazo)).toBeFalse();
    });

    it('detecta plazo vencido y muestra "Plazo expirado" al superar el límite', () => {
      const vencimientoMs = new Date('2026-10-15T18:00:00-03:00').getTime();
      component.ahoraMs = vencimientoMs + 1000; // 1 segundo después

      expect(component.esPlazoVencido(expEnPlazo)).toBeTrue();
      expect(component.getCountdownLabel(expEnPlazo)).toBe('Plazo expirado');
    });

    it('formatea countdown compacto para el badge (getCompactCountdownLabel)', () => {
      const vencimientoMs = new Date('2026-10-15T18:00:00-03:00').getTime();
      component.ahoraMs = vencimientoMs - (2 * 86400 + 4 * 3600 + 15 * 60) * 1000;

      const compact = component.getCompactCountdownLabel(expEnPlazo);
      expect(compact).toBe('2d 04h');
      expect(component.getEstadoLabel('justificando', expEnPlazo)).toBe('Justificando 2d 04h');
    });

    it('abre y cierra el modal de detalle del expediente', () => {
      expect(component.modalDetalleAbierto).toBeFalse();
      expect(component.expedienteDetalle).toBeNull();

      component.abrirModalDetalle(expEnPlazo);
      expect(component.modalDetalleAbierto).toBeTrue();
      expect(component.expedienteDetalle).toBe(expEnPlazo);

      component.cerrarModalDetalle();
      expect(component.modalDetalleAbierto).toBeFalse();
      expect(component.expedienteDetalle).toBeNull();
    });

    it('limpia el timer subscription en ngOnDestroy para evitar memory leaks', () => {
      component.ngOnDestroy();
      expect((component as any).tickerSub).toBeNull();
    });
  });

  describe('Gestión de Justificativos y Auditoría en Modal Detalle', () => {
    const expConDescargo: Expediente = {
      id: 'EXP-99',
      numero: 'EXP-099/2026',
      tipo: 'falta',
      socio: 'Lucas Gastiaburu',
      legajo: '74907',
      motivo: 'Inasistencia',
      subcomision: 'Cómputos',
      puntos: -1,
      estado: 'revision_resolucion',
      fechaCreacion: '2026-10-01',
      horasRestantes: 0,
      descargoPresentado: true,
      descargo: {
        tipo: 'T02_CERTIFICADO',
        causal: 'Examen Académico Universitario en UTN FRC',
        archivo: 'comprobante.pdf',
        texto: 'Certificado de examen rendido',
        fecha: '2026-10-01'
      },
      logsDescargo: [
        {
          operacion: 'CREACION',
          accionLabel: 'Añadir Justificativo',
          usuario: 'Lucas Gastiaburu (Legajo 74907)',
          timestamp: '01/10/2026 10:00 hs',
          detalle: 'Modalidad T02 (Certificado)'
        }
      ]
    };

    it('abre el modal de añadir justificativo en modo creación', () => {
      const expSinDescargo: Expediente = { ...expConDescargo, descargo: undefined, logsDescargo: [] };
      component.abrirModalDescargo(expSinDescargo);
      expect(component.modalAbierto).toBeTrue();
      expect(component.esEdicion).toBeFalse();
      expect(component.expedienteSeleccionado).toBe(expSinDescargo);
      expect(component.nombreArchivo).toBe('');
    });

    it('abre el modal de editar justificativo precargando los datos existentes', () => {
      component.abrirModalEditarDescargo(expConDescargo);
      expect(component.modalAbierto).toBeTrue();
      expect(component.esEdicion).toBeTrue();
      expect(component.tipoDescargo).toBe('T02_CERTIFICADO');
      expect(component.causalSeleccionada).toBe('Examen Académico Universitario en UTN FRC');
      expect(component.nombreArchivo).toBe('comprobante.pdf');
      expect(component.relatoTexto).toBe('Certificado de examen rendido');
    });

    it('abre el modal de editar justificativo extraordinario precargando causal como Otro', () => {
      const expExtraordinario: Expediente = {
        ...expConDescargo,
        descargo: {
          tipo: 'T03_EXTRAORDINARIO',
          texto: 'Motivos imprevistos',
          fecha: '2026-10-02'
        }
      };
      component.abrirModalEditarDescargo(expExtraordinario);
      expect(component.modalAbierto).toBeTrue();
      expect(component.tipoDescargo).toBe('T03_EXTRAORDINARIO');
      expect(component.causalSeleccionada).toBe('Otro');
      expect(component.relatoTexto).toBe('Motivos imprevistos');
    });

    it('retira el descargo al confirmar en el diálogo propio y tras la respuesta del servidor', () => {
      const dataSpy = spyOn(component.dataService, 'eliminarDescargo').and.callThrough();

      component.eliminarDescargo(expConDescargo);
      expect(component.modalConfirmacionAbierto).toBeTrue();
      expect(dataSpy).not.toHaveBeenCalled();

      component.confirmarAccion();
      expect(component.modalConfirmacionAbierto).toBeFalse();
      http.expectOne({ method: 'DELETE', url: `${apiUrl}/EXP-99/descargo/` }).flush({ detail: 'ok' });
      expect(dataSpy).toHaveBeenCalledWith('EXP-99', jasmine.objectContaining({ nombre: jasmine.any(String) }));
    });

    it('no elimina el justificativo si el usuario cancela en el diálogo propio', () => {
      const dataSpy = spyOn(component.dataService, 'eliminarDescargo').and.callThrough();

      component.eliminarDescargo(expConDescargo);
      expect(component.modalConfirmacionAbierto).toBeTrue();

      component.cerrarConfirmacion();
      expect(component.modalConfirmacionAbierto).toBeFalse();
      expect(dataSpy).not.toHaveBeenCalled();
    });

    it('asigna clases badge adecuadas a cada tipo de operación', () => {
      expect(component.getBadgeClaseOperacion('CREACION')).toBe('badge-success');
      expect(component.getBadgeClaseOperacion('EDICION')).toBe('badge-info');
      expect(component.getBadgeClaseOperacion('ELIMINACION')).toBe('badge-danger');
    });
  });

  describe('Descargo versionado contra el backend (SCRUM-49)', () => {
    const expDetalle: Expediente = {
      id: 'EXP-77',
      numero: 'EXP-077/2026',
      tipo: 'falta',
      socio: 'Lucas Gastiaburu',
      legajo: '74907',
      motivo: 'Inasistencia',
      subcomision: 'Cómputos',
      puntos: -1,
      estado: 'justificando',
      fechaCreacion: '2026-10-01',
      horasRestantes: 48
    } as Expediente;

    const versionesApi = [
      {
        id: 1, numero: 1, operacion: 'PRESENTADO', operacion_display: 'Descargo presentado',
        tipo: 'T03_EXTRAORDINARIO', causal: 'Otro', texto: 'v1', archivo: '', evidencias: [{ id: 'a' }],
        actor: 'SOCIO_74907', socio_id: 1, socio_legajo: '74907', socio_nombre: 'Lucas Gastiaburu',
        created_at: '2026-10-16T15:30:00-03:00'
      },
      {
        id: 2, numero: 2, operacion: 'CORREGIDO', operacion_display: 'Descargo corregido dentro del plazo',
        tipo: 'T02_CERTIFICADO', causal: 'Examen', texto: '', archivo: 'c.pdf', evidencias: [],
        actor: 'SOCIO_74907', socio_id: 1, socio_legajo: '74907', socio_nombre: 'Lucas Gastiaburu',
        created_at: '2026-10-16T16:05:00-03:00'
      },
      {
        id: 3, numero: 3, operacion: 'RETIRADO', operacion_display: 'Descargo retirado dentro del plazo',
        tipo: 'T02_CERTIFICADO', causal: 'Examen', texto: '', archivo: 'c.pdf', evidencias: [],
        actor: 'SOCIO_74907', socio_id: 1, socio_legajo: '74907', socio_nombre: 'Lucas Gastiaburu',
        created_at: '2026-10-16T17:00:00-03:00'
      }
    ];

    it('carga el historial real del backend al abrir el detalle y lo mapea a la tabla de auditoría', () => {
      component.abrirModalDetalle(expDetalle);
      http.expectOne({ method: 'GET', url: `${apiUrl}/EXP-77/descargo/versiones/` }).flush(versionesApi);

      expect(component.historialDescargo.length).toBe(3);
      const [primera, segunda, tercera] = component.historialDescargo;
      expect(primera.operacion).toBe('CREACION');
      expect(primera.accionLabel).toBe('Descargo presentado');
      expect(primera.usuario).toBe('Lucas Gastiaburu (Legajo 74907)');
      expect(primera.timestamp).toBe('16/10/2026 15:30 hs');
      expect(primera.detalle).toBe('v1 · T03 (Extraordinario) · Otro · 1 comprobante');
      expect(segunda.operacion).toBe('EDICION');
      expect(segunda.detalle).toBe('v2 · T02 (Certificado) · Examen · 0 comprobantes');
      expect(tercera.operacion).toBe('ELIMINACION');
    });

    it('limpia el historial al cerrar el detalle y no depende del estado local del navegador', () => {
      component.abrirModalDetalle({ ...expDetalle, logsDescargo: [{ operacion: 'CREACION', accionLabel: 'Local', usuario: 'x', timestamp: 'y', detalle: 'z' }] });
      http.expectOne(`${apiUrl}/EXP-77/descargo/versiones/`).flush(versionesApi);
      expect(component.historialDescargo.map(h => h.accionLabel)).not.toContain('Local');

      component.cerrarModalDetalle();
      expect(component.historialDescargo).toEqual([]);
    });

    it('informa el error si no puede cargar el historial y deja la tabla vacía', () => {
      component.abrirModalDetalle(expDetalle);
      http.expectOne(`${apiUrl}/EXP-77/descargo/versiones/`).flush({ detail: 'Error' }, { status: 500, statusText: 'Server Error' });

      expect(component.historialDescargo).toEqual([]);
      expect(notifications.error).toHaveBeenCalledWith('No se pudo cargar el historial del descargo.');
    });

    it('refresca el historial cuando el retiro se confirma con el detalle abierto', () => {
      component.abrirModalDetalle({ ...expDetalle, descargo: { tipo: 'T03_EXTRAORDINARIO', texto: 'x', fecha: '2026-10-16' } });
      http.expectOne(`${apiUrl}/EXP-77/descargo/versiones/`).flush([]);

      component.eliminarDescargo(component.expedienteDetalle as Expediente);
      component.confirmarAccion();
      http.expectOne({ method: 'DELETE', url: `${apiUrl}/EXP-77/descargo/` }).flush({ detail: 'ok' });

      http.expectOne({ method: 'GET', url: `${apiUrl}/EXP-77/descargo/versiones/` }).flush(versionesApi);
      expect(component.historialDescargo.length).toBe(3);
    });

    it('no registra el retiro ni avisa éxito si el servidor lo rechaza fuera de plazo', () => {
      const localSpy = spyOn(component.dataService, 'eliminarDescargo');
      component.eliminarDescargo({ ...expDetalle, descargo: { tipo: 'T03_EXTRAORDINARIO', texto: 'x', fecha: '2026-10-16' } });
      component.confirmarAccion();

      http.expectOne({ method: 'DELETE', url: `${apiUrl}/EXP-77/descargo/` }).flush(
        { detail: 'El plazo perentorio de 5 días hábiles ha expirado.' },
        { status: 409, statusText: 'Conflict' }
      );

      expect(localSpy).not.toHaveBeenCalled();
      expect(notifications.info).not.toHaveBeenCalled();
      expect(notifications.error).toHaveBeenCalledWith('El plazo perentorio de 5 días hábiles ha expirado.');
    });

    it('no confirma la presentación y conserva el modal si el servidor rechaza el descargo', () => {
      const localSpy = spyOn(component.dataService, 'enviarDescargo');
      component.expedienteSeleccionado = expDetalle;
      component.modalAbierto = true;
      component.tipoDescargo = 'T03_EXTRAORDINARIO';
      component.causalSeleccionada = 'Otro';
      component.relatoTexto = 'Exposición de los hechos.';

      component.enviarDescargo();
      http.expectOne({ method: 'POST', url: `${apiUrl}/EXP-77/descargo/` }).flush(
        { detail: 'El plazo perentorio de 5 días hábiles ha expirado.' },
        { status: 409, statusText: 'Conflict' }
      );

      expect(localSpy).not.toHaveBeenCalled();
      expect(notifications.success).not.toHaveBeenCalled();
      expect(notifications.error).toHaveBeenCalledWith('El plazo perentorio de 5 días hábiles ha expirado.');
      expect(component.modalAbierto).toBeTrue();
    });

    it('muestra el primer error de validación del campo cuando el servidor responde 400', () => {
      component.expedienteSeleccionado = expDetalle;
      component.modalAbierto = true;
      component.tipoDescargo = 'T03_EXTRAORDINARIO';
      component.causalSeleccionada = 'Otro';
      component.relatoTexto = 'Texto';

      component.enviarDescargo();
      http.expectOne({ method: 'POST', url: `${apiUrl}/EXP-77/descargo/` }).flush(
        { texto: ['El motivo o justificación no puede superar los 5000 caracteres.'] },
        { status: 400, statusText: 'Bad Request' }
      );

      expect(notifications.error).toHaveBeenCalledWith('El motivo o justificación no puede superar los 5000 caracteres.');
    });

    it('registra la presentación y refresca el historial cuando el servidor la acepta', () => {
      const localSpy = spyOn(component.dataService, 'enviarDescargo');
      component.expedienteSeleccionado = expDetalle;
      component.modalAbierto = true;
      component.tipoDescargo = 'T03_EXTRAORDINARIO';
      component.causalSeleccionada = 'Otro';
      component.relatoTexto = 'Exposición de los hechos.';

      component.enviarDescargo();
      http.expectOne({ method: 'POST', url: `${apiUrl}/EXP-77/descargo/` }).flush({ detail: 'ok' }, { status: 201, statusText: 'Created' });

      expect(localSpy).toHaveBeenCalled();
      expect(notifications.success).toHaveBeenCalledWith('Justificación y documentos registrados correctamente.');
      expect(component.modalAbierto).toBeFalse();
    });

    describe('Panel de detalle sincronizado con la lista del backend', () => {
      const listaUrl = `${apiUrl}/mis-expedientes/`;
      const rawExpediente = (extra: object = {}) => ({
        id: 'EXP-77', numero: 'EXP-077/2026', socio_nombre: 'Lucas Gastiaburu', socio_legajo: '74907',
        motivo: 'Inasistencia', estado: 'justificando', puntos: -1, ...extra
      });

      /** Recarga la lista y responde solo la última petición, ignorando las del arranque del componente. */
      const recargarLista = (respuesta: any[]) => {
        component.cargarMisExpedientes();
        const pendientes = http.match(listaUrl);
        pendientes[pendientes.length - 1].flush(respuesta);
      };

      beforeEach(() => {
        http.match(listaUrl).forEach(req => req.flush([]));
      });

      it('muestra el descargo recién presentado sin cerrar el detalle ni depender del almacén local', () => {
        component.abrirModalDetalle(expDetalle);
        http.expectOne(`${apiUrl}/EXP-77/descargo/versiones/`).flush([]);
        expect(component.expedienteDetalle?.descargo).toBeUndefined();

        recargarLista([rawExpediente({
          descargo_presentado: true, descargo_tipo: 'T03_EXTRAORDINARIO',
          descargo_causal: 'Otro', descargo_texto: 'Exposición de los hechos.'
        })]);

        expect(component.expedienteDetalle?.id).toBe('EXP-77');
        expect(component.expedienteDetalle?.descargo?.tipo).toBe('T03_EXTRAORDINARIO');
        expect(component.expedienteDetalle?.descargoPresentado).toBeTrue();
      });

      it('quita el descargo del detalle abierto cuando la lista del backend ya no lo tiene vigente', () => {
        component.abrirModalDetalle({ ...expDetalle, descargoPresentado: true, descargo: { tipo: 'T03_EXTRAORDINARIO', texto: 'x', fecha: '2026-10-16' } });
        http.expectOne(`${apiUrl}/EXP-77/descargo/versiones/`).flush([]);

        recargarLista([rawExpediente({ descargo_presentado: false })]);

        expect(component.expedienteDetalle?.descargo).toBeUndefined();
        expect(component.expedienteDetalle?.descargoPresentado).toBeFalse();
      });

      it('conserva el detalle abierto si el expediente no figura en la lista recargada', () => {
        component.abrirModalDetalle(expDetalle);
        http.expectOne(`${apiUrl}/EXP-77/descargo/versiones/`).flush([]);

        recargarLista([rawExpediente({ id: 'OTRO-1', numero: 'EXP-001/2026' })]);

        expect(component.expedienteDetalle).toBe(expDetalle);
      });

      it('no abre ningún detalle al recargar la lista con el panel cerrado', () => {
        recargarLista([rawExpediente()]);

        expect(component.expedienteDetalle).toBeNull();
        expect(component.modalDetalleAbierto).toBeFalse();
      });
    });
  });

  describe('Bloqueo de scroll al abrir modales', () => {
    const mockExpediente: Expediente = {
      id: 'EXP-101',
      numero: 'EXP-2026-101',
      tipo: 'falta',
      socio: 'Lucas Gastiaburu',
      legajo: '74907',
      motivo: 'Inasistencia',
      subcomision: 'Cómputos',
      puntos: -1,
      estado: 'justificando',
      fechaCreacion: '2026-10-01',
      horasRestantes: 72
    };

    afterEach(() => {
      document.body.classList.remove('modal-open');
      document.body.style.removeProperty('overflow');
      document.documentElement.style.removeProperty('overflow');
    });

    it('bloquea el scroll del fondo al abrir el modal de detalle y lo restaura al cerrar', () => {
      component.abrirModalDetalle(mockExpediente);
      expect(component.modalDetalleAbierto).toBeTrue();
      expect(document.body.classList.contains('modal-open')).toBeTrue();
      expect(document.body.style.overflow).toBe('hidden');
      expect(document.documentElement.style.overflow).toBe('hidden');

      component.cerrarModalDetalle();
      expect(component.modalDetalleAbierto).toBeFalse();
      expect(document.body.classList.contains('modal-open')).toBeFalse();
      expect(document.body.style.overflow).toBe('');
      expect(document.documentElement.style.overflow).toBe('');
    });

    it('bloquea el scroll al abrir el modal de justificación T02/T03 y lo restaura al cerrar', () => {
      component.abrirModalDescargo(mockExpediente);
      expect(component.modalAbierto).toBeTrue();
      expect(document.body.classList.contains('modal-open')).toBeTrue();
      expect(document.body.style.overflow).toBe('hidden');

      component.cerrarModal();
      expect(component.modalAbierto).toBeFalse();
      expect(document.body.classList.contains('modal-open')).toBeFalse();
      expect(document.body.style.overflow).toBe('');
    });

    it('mantiene el bloqueo de scroll activo si el modal de detalle sigue abierto al cerrar el de justificación', () => {
      component.abrirModalDetalle(mockExpediente);
      component.abrirModalDescargo(mockExpediente);
      expect(component.modalDetalleAbierto).toBeTrue();
      expect(component.modalAbierto).toBeTrue();
      expect(document.body.style.overflow).toBe('hidden');

      // Cerrar solo el de justificación
      component.cerrarModal();
      expect(component.modalAbierto).toBeFalse();
      expect(component.modalDetalleAbierto).toBeTrue();
      expect(document.body.style.overflow).toBe('hidden');
      expect(document.body.classList.contains('modal-open')).toBeTrue();

      // Cerrar finalmente el de detalle
      component.cerrarModalDetalle();
      expect(document.body.style.overflow).toBe('');
      expect(document.body.classList.contains('modal-open')).toBeFalse();
    });

    it('limpia las clases y estilos de scroll al destruir el componente', () => {
      component.abrirModalDetalle(mockExpediente);
      expect(document.body.classList.contains('modal-open')).toBeTrue();
      expect(document.body.style.overflow).toBe('hidden');

      component.ngOnDestroy();
      expect(document.body.classList.contains('modal-open')).toBeFalse();
      expect(document.body.style.overflow).toBe('');
    });
  });

  describe('Interacción Drag and Drop y Carga API', () => {
    it('maneja eventos dragover y dragleave alternando isDragging', () => {
      const eventMock = {
        preventDefault: jasmine.createSpy('preventDefault'),
        stopPropagation: jasmine.createSpy('stopPropagation')
      } as any;

      component.onDragOver(eventMock);
      expect(component.isDragging).toBeTrue();
      expect(eventMock.preventDefault).toHaveBeenCalled();

      component.onDragLeave(eventMock);
      expect(component.isDragging).toBeFalse();
    });

    it('procesa archivos arrojados en onFileDropped', () => {
      const dropSpy = spyOn(component, 'procesarArchivos');
      const testFile = new File(['content'], 'prueba.pdf', { type: 'application/pdf' });
      const eventMock = {
        preventDefault: jasmine.createSpy('preventDefault'),
        stopPropagation: jasmine.createSpy('stopPropagation'),
        dataTransfer: {
          files: [testFile]
        }
      } as any;

      component.onFileDropped(eventMock);
      expect(component.isDragging).toBeFalse();
      expect(dropSpy).toHaveBeenCalledWith([testFile]);
    });
  });

  describe('Cálculo Estricto de Saldo Neto desde Expedientes Emitidos', () => {
    it('computa saldo 0 cuando el socio no tiene expedientes registrados', () => {
      component.misExpedientes = [];
      component.actualizarSaldoNeto();
      expect(component.saldoNeto).toBe(0);
    });

    it('computa saldo 0 cuando el socio tiene expedientes pero ninguno está emitido/cerrado', () => {
      component.misExpedientes = [
        {
          id: 'EXP-1',
          numero: 'EXP-001/2026',
          tipo: 'falta',
          socio: 'Diego Gabriel Sánchez',
          legajo: '87414',
          motivo: 'Inasistencia',
          subcomision: 'Cómputos',
          puntos: -1,
          estado: 'justificando',
          fechaCreacion: '2026-10-08',
          horasRestantes: 48
        },
        {
          id: 'EXP-2',
          numero: 'EXP-002/2026',
          tipo: 'falta',
          socio: 'Diego Gabriel Sánchez',
          legajo: '87414',
          motivo: 'Falta informe',
          subcomision: 'Cómputos',
          puntos: -2,
          estado: 'revision_resolucion',
          fechaCreacion: '2026-10-09',
          horasRestantes: 0
        }
      ];

      component.actualizarSaldoNeto();
      expect(component.saldoNeto).toBe(0);
    });

    it('computa estrictamente la sumatoria de puntos de expedientes en estado emitido', () => {
      component.misExpedientes = [
        {
          id: 'EXP-1',
          numero: 'EXP-001/2026',
          tipo: 'merito',
          socio: 'Diego Gabriel Sánchez',
          legajo: '87414',
          motivo: 'Colaboración destacada',
          subcomision: 'CD',
          puntos: 3,
          estado: 'emitido',
          fechaCreacion: '2026-10-01',
          horasRestantes: 0
        },
        {
          id: 'EXP-2',
          numero: 'EXP-002/2026',
          tipo: 'falta',
          socio: 'Diego Gabriel Sánchez',
          legajo: '87414',
          motivo: 'Inasistencia',
          subcomision: 'CD',
          puntos: -1,
          estado: 'justificando',
          fechaCreacion: '2026-10-05',
          horasRestantes: 24
        },
        {
          id: 'EXP-3',
          numero: 'EXP-003/2026',
          tipo: 'merito',
          socio: 'Diego Gabriel Sánchez',
          legajo: '87414',
          motivo: 'Organización aniversario',
          subcomision: 'CD',
          puntos: 2,
          estado: 'emitido',
          fechaCreacion: '2026-10-06',
          horasRestantes: 0
        }
      ];

      component.actualizarSaldoNeto();
      // Solo suman los emitidos: 3 + 2 = 5 (el de -1 en justificando no se computa)
      expect(component.saldoNeto).toBe(5);
    });

    it('no sobreescribe el saldo con mocks estáticos al emitir socios$', () => {
      component.misExpedientes = [];
      component.actualizarSaldoNeto();
      expect(component.saldoNeto).toBe(0);

      // Simular emisión de socios
      (component.dataService as any).sociosSubject?.next?.([
        { id: '1', nombre: 'Diego Gabriel Sánchez', legajo: '87414', saldo: 10.0 }
      ]);

      // Debe mantenerse en 0 porque no tiene expedientes emitidos
      expect(component.saldoNeto).toBe(0);
    });
  });

  describe('Unificación transversal de expedientes (<n>/<YYYY>) y estados sin guiones', () => {
    it('formatea el identificador de expediente como <n>/<YYYY> sin ceros a la izquierda', () => {
      expect(component.formatCaseNumber('EXP-0007/2026')).toBe('7/2026');
      expect(component.formatCaseNumber('EXP-2026-0007')).toBe('7/2026');
      expect(component.formatCaseNumber('007/2026')).toBe('7/2026');
      expect(component.formatCaseNumber('7/2026')).toBe('7/2026');
      expect(component.formatCaseNumber('EXP-0419/2025')).toBe('419/2025');
      expect(component.formatCaseNumber('')).toBe('');
      expect(component.formatCaseNumber(null)).toBe('');
    });

    it('formatea el solicitante correctamente', () => {
      expect(component.formatSolicitante(null)).toBe('Comisión Directiva');
      expect(component.formatSolicitante({ solicitante: 'Giuliano Toselli (11239)' } as any)).toBe('11239 - Giuliano Toselli');
      expect(component.formatSolicitante({ creador: 'Toselli, Giuliano (11239)' } as any)).toBe('11239 - Toselli, Giuliano');
      expect(component.formatSolicitante({} as any)).toBe('Comisión Directiva');
    });

    it('homologa estados y evita guiones o snake_case', () => {
      expect(component.getEstadoLabel('espera_resolucion')).toBe('En Revisión');
      expect(component.getEstadoLabel('ESPERA_RESOLUCION')).toBe('En Revisión');
      expect(component.getEstadoLabel('revision_resolucion')).toBe('En Revisión');
      expect(component.getEstadoLabel('creado')).toBe('Creado');
      expect(component.getEstadoLabel('pendiente_firma')).toBe('Pendiente de Firma');
      expect(component.getEstadoLabel('pendiente_correos')).toBe('Pendiente de Envío');
      expect(component.getEstadoLabel('emitido')).toBe('Emitido');
      // Fallback
      expect(component.getEstadoLabel('otro_estado_proceso')).toBe('Otro Estado Proceso');
    });

    it('solo crea descargoObj si hay contenido real de descargo en la API', () => {
      const rawVacio = {
        id: 1,
        numero: 'EXP-0001/2026',
        descargo_presentado: true,
        descargo_texto: null,
        descargo_causal: null,
        descargo_archivo: null,
        evidencias: []
      };
      const mapeadoVacio = (component as any).mapearExpedienteApi(rawVacio);
      expect(mapeadoVacio.descargo).toBeUndefined();

      const rawValido = {
        id: 3,
        numero: 'EXP-0003/2026',
        descargo_presentado: true,
        descargo_texto: 'Presento constancia de examen',
        descargo_causal: 'Examen Académico',
        descargo_archivo: 'certificado.pdf',
        evidencias: []
      };
      const mapeadoValido = (component as any).mapearExpedienteApi(rawValido);
      expect(mapeadoValido.descargo).toBeDefined();
      expect(mapeadoValido.descargo.texto).toBe('Presento constancia de examen');
    });
  });
  describe('Apelación del T01 (PB-02)', () => {
    const texto = 'No estuve presente en el laboratorio ese día; hay testigos.';
    const futuro = new Date(Date.now() + 3 * 24 * 3600 * 1000).toISOString();
    const pasado = new Date(Date.now() - 3600 * 1000).toISOString();

    const expT01 = {
      id: '7',
      numero: 'EXP-0701/2026',
      socio: 'Ana Pérez',
      legajo: '78002',
      subcomision: 'Cómputos',
      motivo: 'Uso indebido del laboratorio',
      fechaCreacion: '2026-10-20',
      estado: 'justificando',
      horasRestantes: 72,
      tipo: 'falta',
      puntos: -2,
      plazoLimiteAt: futuro,
      esT01: true
    } as Expediente;

    const historial = (limite = futuro, apelaciones: any[] = []) => ({
      es_t01: true,
      estado: 'justificando',
      plazo_dias_vigente: 5,
      puntos_vigentes: '-2.00',
      involucrados: [],
      original: null,
      periodos: [{ socio_id: 3, socio: 'Ana Pérez', origen: 'APERTURA', dias_habiles: 5, inicio_at: pasado, limite_at: limite, abierto: limite === futuro }],
      apelaciones,
      adecuaciones: [{
        version: 1, puntos_anteriores: '-2.00', puntos_nuevos: '-1.50', socios_anteriores: [], socios_nuevos: [],
        motivos: 'El debate atenuó la gravedad de la falta.', reabre_plazo: false, socios_con_nuevo_plazo: [],
        autor_legajo: '78100', created_at: pasado
      }]
    });

    function abrir(h = historial()): void {
      component.abrirModalDetalle(expT01);
      http.expectOne(`${apiUrl}/7/t01/historial/`).flush(h);
      http.match(`${apiUrl}/7/`).forEach(r => r.flush({ id: 7, numero: 'EXP-0701/2026', estado: 'justificando', es_t01: true, plazo_limite_at: futuro }));
      fixture.detectChanges();
    }

    it('mapea el origen T01 desde la API', () => {
      expect((component as any).mapearExpedienteApi({ id: 1, es_t01: true }).esT01).toBeTrue();
      expect((component as any).mapearExpedienteApi({ id: 2 }).esT01).toBeFalse();
    });

    it('muestra la apelación en lugar del justificativo T02/T03 y no consulta versiones de descargo', () => {
      abrir();
      http.expectNone(`${apiUrl}/7/descargo/versiones/`);
      const compiled = fixture.nativeElement as HTMLElement;
      expect(compiled.querySelector('.seccion-apelacion')).toBeTruthy();
      expect(compiled.textContent).not.toContain('Añadir Justificativo');
      expect(compiled.querySelector('.btn-apelar')?.textContent).toContain('Apelar');
      expect(compiled.querySelector('.adecuacion-t01')?.textContent).toContain('-2.00 → -1.50');
    });

    it('exige un texto mínimo antes de enviar', () => {
      abrir();
      component.abrirApelacion();
      component.textoApelacion = 'No fui yo';
      component.enviarApelacion();
      http.expectNone(`${apiUrl}/7/apelacion/`);
      expect(notifications.error).toHaveBeenCalledWith('Escribí tu apelación con al menos 20 caracteres.');
    });

    it('envía la apelación y muestra la versión registrada', () => {
      abrir();
      component.abrirApelacion();
      component.textoApelacion = `  ${texto}  `;
      component.enviarApelacion();

      const req = http.expectOne(`${apiUrl}/7/apelacion/`);
      expect(req.request.body).toEqual({ texto });
      req.flush(historial(futuro, [{ socio_id: 3, socio: 'Ana Pérez', numero: 1, texto, created_at: pasado }]));
      fixture.detectChanges();

      expect(component.apelacionAbierta).toBeFalse();
      expect(component.ultimaApelacion?.numero).toBe(1);
      expect(notifications.success).toHaveBeenCalledWith('Apelación registrada. Te enviamos la constancia por mail.');
      expect(fixture.nativeElement.querySelector('.btn-apelar').textContent).toContain('Editar apelación');
    });

    it('con el plazo vencido no permite apelar', () => {
      abrir(historial(pasado));
      expect(component.puedeApelar).toBeFalse();
      expect(fixture.nativeElement.querySelector('.btn-apelar')).toBeNull();
    });

    it('informa el rechazo del servidor', () => {
      abrir();
      component.abrirApelacion();
      component.textoApelacion = texto;
      component.enviarApelacion();
      http.expectOne(`${apiUrl}/7/apelacion/`).flush({ detail: 'Tu plazo de apelación venció.' }, { status: 409, statusText: 'Conflict' });
      expect(notifications.error).toHaveBeenCalled();
      expect(component.enviandoApelacion).toBeFalse();
    });
  });
});
