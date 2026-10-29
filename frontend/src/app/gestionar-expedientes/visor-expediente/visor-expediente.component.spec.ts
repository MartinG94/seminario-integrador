import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { of, throwError } from 'rxjs';

import { AuthService } from '../../services/auth.service';
import { ExpedienteApiService, ExpedienteVisorData } from '../../services/expediente-api.service';
import { NotificationService } from '../../services/notification.service';
import { VisorExpedienteComponent } from './visor-expediente.component';

describe('VisorExpedienteComponent (US S4-01 / SCRUM-51)', () => {
  let component: VisorExpedienteComponent;
  let fixture: ComponentFixture<VisorExpedienteComponent>;
  let expedienteApiSpy: jasmine.SpyObj<ExpedienteApiService>;
  let notificationServiceSpy: jasmine.SpyObj<NotificationService>;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let routerSpy: jasmine.SpyObj<Router>;

  const mockVisorData: ExpedienteVisorData = {
    id: 123,
    numero: 'EXP-0888/2026',
    anio: 2026,
    titulo: 'Inasistencia y desorden en laboratorio',
    motivo: 'Relato de hechos acaecidos en la sede.',
    razon: 'Apertura formal de causa disciplinaria.',
    causal: 'Art. 21 y 24 Reglamento Procesal',
    reglamento_asociado: 'Reglamento Procesal 2026',
    reglamentos_respaldantes: ['Art. 21', 'Art. 24'],
    puntos: '-1.00',
    concepto: null,
    concepto_display: null,
    estado: 'revision_resolucion',
    estado_display: 'Justificaciones en revisión',
    urgencia: 'urgente',
    urgencia_display: 'Urgente',
    fecha_solicitud: '2026-10-20T10:00:00Z',
    created_at: '2026-10-20T10:00:00Z',
    solicitante: {
      legajo: '75001',
      nombre: 'Martín Guillén',
      grupo: 'G58',
      display: 'Martín Guillén (75001)',
    },
    anexo: {
      anexo_fecha: '2026-10-19',
      anexo_lugar: 'Sede Central AVEIT, Lab de Cómputos',
      anexo_relato: 'Se constató la ausencia injustificada y alteración de equipos.',
      anexo_testigos: 'Juan Pérez (11200) - Testigo presencial',
    },
    plazo_inicio_at: '2026-10-20T10:00:00Z',
    plazo_limite_at: '2026-10-27T18:00:00Z',
    esta_en_plazo: false,
    horas_restantes: 0,
    responsables_td: [
      {
        titulo: 'Responsable 1',
        legajo: '11239',
        nombre: 'Giuliano Toselli',
        grupo: 'G57',
        es_suplente: false,
        display: '11239 - Giuliano Toselli - G57',
      },
      {
        titulo: 'Responsable 2',
        legajo: '11737',
        nombre: 'Catalina Cerda Gallego',
        grupo: 'G58',
        es_suplente: false,
        display: '11737 - Catalina Cerda Gallego - G58',
      },
      {
        titulo: 'Responsable 3',
        legajo: '11735',
        nombre: 'Candela Moreno Migliore',
        grupo: 'G59',
        es_suplente: false,
        display: '11735 - Candela Moreno Migliore - G59',
      },
    ],
    involucrados: [
      {
        id: 1,
        legajo: '77001',
        nombre: 'Esteban Quito',
        grupo: 'G58',
        estado: 'Activo',
        tiene_descargo: true,
        estado_descargo: 'PRESENTADO',
        estado_descargo_display: 'Descargo presentado',
        descargo: {
          id: 10,
          socio_id: 1,
          socio_legajo: '77001',
          socio_nombre: 'Esteban Quito',
          tipo: 'T02_CERTIFICADO',
          tipo_display: 'Formulario T02 - Causal con Certificado',
          causal: 'Enfermedad certificada de salud',
          texto: 'Diagnóstico médico de reposo por 48 hs.',
          archivo: 'certificado.pdf',
          presentado_at: '2026-10-22T14:30:00Z',
          contiene_datos_medicos: true,
          datos_medicos_restringidos: false,
          evidencias: [
            {
              id: 'ev-1',
              nombre_original: 'certificado_medico.pdf',
              extension: '.pdf',
              mime_type: 'application/pdf',
              tamanio_bytes: 204800,
              sha256_hash: 'aabbcc112233',
              sha256_valido: true,
              archivo_danado: false,
              es_vigente: true,
              created_at: '2026-10-22T14:30:00Z',
            },
            {
              id: 'ev-2',
              nombre_original: 'receta_adulterada.pdf',
              extension: '.pdf',
              mime_type: 'application/pdf',
              tamanio_bytes: 102400,
              sha256_hash: '112233445566',
              sha256_valido: false,
              archivo_danado: true,
              es_vigente: true,
              created_at: '2026-10-22T14:35:00Z',
            },
          ],
          regla_sugerida: 'ACCEPTED',
          decisiones_causal: [],
        },
      },
      {
        id: 2,
        legajo: '77002',
        nombre: 'Lucas Blanco',
        grupo: 'G59',
        estado: 'Pasivo',
        tiene_descargo: false,
        estado_descargo: 'PLAZO_VENCIDO_SIN_DESCARGO',
        estado_descargo_display: 'Plazo vencido sin descargo',
        descargo: null,
      },
    ],
    timeline: [
      {
        id: 'creacion-123',
        fecha_hora: '2026-10-20T10:00:00Z',
        tipo: 'CREACION',
        tipo_display: 'Apertura formal de causa',
        titulo: 'Apertura formal: EXP-0888/2026',
        descripcion: 'Causa formalizada con motivo.',
        actor: 'Martín Guillén (75001)',
        icono: 'folder_open',
        color: '#1e3a8a',
      },
      {
        id: 'plazo-123',
        fecha_hora: '2026-10-20T10:05:00Z',
        tipo: 'NOTIFICACION_PLAZO',
        tipo_display: 'Notificación procesal de apertura',
        titulo: 'Inicio de plazo de justificaciones (5 días hábiles)',
        descripcion: 'Plazo perentorio congelado.',
        actor: 'Tribunal de Disciplina',
        icono: 'schedule',
        color: '#d97706',
      },
    ],
    puede_resolver_causal: true,
    puede_dictar_resolucion: true,
  };

  beforeEach(async () => {
    expedienteApiSpy = jasmine.createSpyObj('ExpedienteApiService', [
      'obtenerVisorExpediente',
      'descargarEvidencia',
      'registrarDecisionCausal',
      'actualizarConceptoExpediente',
    ]);
    notificationServiceSpy = jasmine.createSpyObj('NotificationService', [
      'success',
      'error',
      'warning',
      'info',
      'showSuccess',
      'showError',
    ]);
    authServiceSpy = jasmine.createSpyObj('AuthService', ['tieneRol']);
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    authServiceSpy.tieneRol.and.returnValue(true);
    expedienteApiSpy.obtenerVisorExpediente.and.returnValue(of(mockVisorData));

    await TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, FormsModule],
      declarations: [VisorExpedienteComponent],
      providers: [
        { provide: ExpedienteApiService, useValue: expedienteApiSpy },
        { provide: NotificationService, useValue: notificationServiceSpy },
        { provide: AuthService, useValue: authServiceSpy },
        { provide: Router, useValue: routerSpy },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: {
                get: (key: string) => (key === 'id' ? '123' : null),
              },
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(VisorExpedienteComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse e inicializar cargando los datos del visor para el ID de ruta', () => {
    expect(component).toBeTruthy();
    expect(expedienteApiSpy.obtenerVisorExpediente).toHaveBeenCalledWith(123);
    expect(component.visorData?.numero).toBe('EXP-0888/2026');
  });

  it('debe renderizar la cabecera canónica del TD con número, urgencia y los 3 jueces con grupo Gxx (CA1)', () => {
    const el = fixture.nativeElement as HTMLElement;

    // Cabecera
    expect(el.textContent).toContain('EXP-0888/2026');
    expect(el.textContent).toContain('Urgencia: Urgente');
    expect(el.textContent).toContain('Justificaciones en revisión');

    // 3 Responsables del TD
    expect(el.textContent).toContain('11239');
    expect(el.textContent).toContain('Giuliano Toselli');
    expect(el.textContent).toContain('G57');

    expect(el.textContent).toContain('Catalina Cerda Gallego');
    expect(el.textContent).toContain('G58');

    expect(el.textContent).toContain('Candela Moreno Migliore');
    expect(el.textContent).toContain('G59');
  });

  it('debe desplegar los hitos cronológicos en el timeline vertical (CA1)', () => {
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Línea de Tiempo Procesal');
    expect(el.textContent).toContain('Apertura formal: EXP-0888/2026');
    expect(el.textContent).toContain('Inicio de plazo de justificaciones');
  });

  it('debe rotular visiblemente "Plazo vencido sin descargo" para imputados sin justificación (CA4)', () => {
    const el = fixture.nativeElement as HTMLElement;
    const badgeVencido = el.querySelector('.badge-plazo-vencido');
    expect(badgeVencido).toBeTruthy();
    expect(badgeVencido?.textContent).toContain('Plazo vencido sin descargo');
  });

  it('debe alertar visualmente ante archivos dañados o con discrepancia SHA-256 (CA4)', () => {
    const el = fixture.nativeElement as HTMLElement;
    const badgeDanado = el.querySelector('.badge-sha-danado');
    expect(badgeDanado).toBeTruthy();
    expect(badgeDanado?.textContent).toContain('Archivo dañado / Discordancia');

    const badgeValido = el.querySelector('.badge-sha-valido');
    expect(badgeValido).toBeTruthy();
    expect(badgeValido?.textContent).toContain('SHA-256 verificado');
  });

  it('debe permitir descargar piezas probatorias custodiadas (CA3)', () => {
    expedienteApiSpy.descargarEvidencia.and.returnValue(
      of(new Blob(['%PDF-1.4 Mock content'], { type: 'application/pdf' }))
    );

    const evidencia = mockVisorData.involucrados[0].descargo!.evidencias[0];
    component.descargarEvidencia(evidencia);

    expect(expedienteApiSpy.descargarEvidencia).toHaveBeenCalledWith(123, 'ev-1', 'descarga');
    expect(notificationServiceSpy.info).toHaveBeenCalledWith(
      jasmine.stringMatching(/Descargando comprobante/)
    );
  });

  it('debe notificar error centralizado de 10s ante acceso 403 Forbidden', () => {
    expedienteApiSpy.obtenerVisorExpediente.and.returnValue(
      throwError(() => ({ status: 403 }))
    );

    component.cargarDatosVisor();

    expect(component.errorCarga).toContain('Acceso denegado');
    expect(notificationServiceSpy.error).toHaveBeenCalledWith(
      'No tenés permisos para sustanciar o consultar este expediente.'
    );
  });

  it('debe navegar de vuelta al tablero al hacer clic en volver', () => {
    component.volverAlTablero();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/gestionar-expedientes']);
  });

  describe('Clasificación de concepto institucional TD (SCRUM-63)', () => {
    it('debe mostrar la advertencia "Sin clasificar · Obligatorio antes de emitir" si concepto es null o vacío', () => {
      component.visorData!.concepto = null;
      component.visorData!.concepto_display = null;
      fixture.detectChanges();

      const el = fixture.nativeElement as HTMLElement;
      expect(el.textContent).toContain('Sin clasificar · Obligatorio antes de emitir');
      const badgeWarning = el.querySelector('.badge-warning');
      expect(badgeWarning).toBeTruthy();
    });

    it('debe mostrar el badge con el concepto clasificado cuando existe', () => {
      component.visorData!.concepto = 'GSA';
      component.visorData!.concepto_display = 'GSA — Gestión Social y Ambiental';
      fixture.detectChanges();

      const el = fixture.nativeElement as HTMLElement;
      expect(el.textContent).not.toContain('Sin clasificar · Obligatorio antes de emitir');
      expect(el.textContent).toContain('GSA — Gestión Social y Ambiental');
      const badgeInfo = el.querySelector('.badge-info');
      expect(badgeInfo).toBeTruthy();
    });

    it('debe renderizar el selector de conceptos para usuarios con rol TD, CD o ADMIN', () => {
      authServiceSpy.tieneRol.and.returnValue(true);
      fixture.detectChanges();

      const select = fixture.nativeElement.querySelector('#selector-concepto-expediente') as HTMLSelectElement;
      expect(select).toBeTruthy();
      expect(component.isTribunalOrAdmin).toBeTrue();
      expect(component.catalogoConceptos.length).toBe(13);
    });

    it('no debe renderizar el selector de conceptos para roles sin privilegios (SOCIO, FISCALIZADORA)', () => {
      authServiceSpy.tieneRol.and.returnValue(false);
      fixture.detectChanges();

      const select = fixture.nativeElement.querySelector('#selector-concepto-expediente');
      expect(select).toBeFalsy();
      expect(component.isTribunalOrAdmin).toBeFalse();
    });

    it('debe despachar actualizarConceptoExpediente al cambiar concepto y notificar éxito con NotificationService', () => {
      expedienteApiSpy.actualizarConceptoExpediente.and.returnValue(
        of({ concepto: 'GSA', concepto_display: 'GSA — Gestión Social y Ambiental' })
      );

      component.actualizarConcepto('GSA');

      expect(expedienteApiSpy.actualizarConceptoExpediente).toHaveBeenCalledWith(123, 'GSA');
      expect(component.visorData?.concepto).toBe('GSA');
      expect(component.visorData?.concepto_display).toBe('GSA — Gestión Social y Ambiental');
      expect(notificationServiceSpy.showSuccess).toHaveBeenCalledWith(
        'Concepto institucional actualizado correctamente.',
        'Tribunal de Disciplina'
      );
    });

    it('debe notificar error centralizado con NotificationService si la API rechaza la actualización', () => {
      expedienteApiSpy.actualizarConceptoExpediente.and.returnValue(
        throwError(() => ({
          error: { detail: 'No posee facultades para clasificar la causa.' },
        }))
      );

      component.actualizarConcepto('OTROS');

      expect(expedienteApiSpy.actualizarConceptoExpediente).toHaveBeenCalledWith(123, 'OTROS');
      expect(notificationServiceSpy.showError).toHaveBeenCalledWith(
        'No posee facultades para clasificar la causa.'
      );
    });
  });
});
