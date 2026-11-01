import { CommonModule } from '@angular/common';
import { SimpleChange } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';

import { AntecedenteT03DTO, ValoracionT03DTO } from '../../services/expediente-api.service';
import { NotificationService } from '../../services/notification.service';
import { ValoracionT03PanelComponent } from './valoracion-t03-panel.component';

describe('ValoracionT03PanelComponent', () => {
  let component: ValoracionT03PanelComponent;
  let fixture: ComponentFixture<ValoracionT03PanelComponent>;
  let notifications: jasmine.SpyObj<NotificationService>;

  const fundamento = 'El Tribunal considera acreditada la causa extraordinaria.';

  const antecedente: AntecedenteT03DTO = {
    id: 7,
    numero: 'EXP-0007/2026',
    fecha_emision: '2026-09-15T12:00:00Z',
    motivo: 'Inasistencia a la reunión plenaria',
    reglamento_invocado: 'Art. 86 del Reglamento Interno'
  };

  const version = (overrides: Partial<ValoracionT03DTO> = {}): ValoracionT03DTO => ({
    id: 1,
    descargo: 6,
    version: 1,
    resultado: 'ACCEPTED',
    resultado_display: 'Aprobada',
    fundamento,
    antecedentes: [{ expediente_id: 7, numero: 'EXP-0007/2026' }],
    autor: 'miembro.td',
    autor_legajo: '408917',
    autor_rol: 'TD',
    autor_condicion: 'TITULAR',
    autor_condicion_display: 'Miembro Titular',
    created_at: '2026-10-20T15:30:00Z',
    ...overrides
  });

  const texto = () => (fixture.nativeElement as HTMLElement).textContent || '';
  const consultar = <T extends HTMLElement>(selector: string) =>
    (fixture.nativeElement as HTMLElement).querySelector<T>(selector);

  beforeEach(async () => {
    notifications = jasmine.createSpyObj('NotificationService', ['error', 'success']);
    await TestBed.configureTestingModule({
      imports: [CommonModule, FormsModule],
      declarations: [ValoracionT03PanelComponent],
      providers: [{ provide: NotificationService, useValue: notifications }]
    }).compileComponents();

    fixture = TestBed.createComponent(ValoracionT03PanelComponent);
    component = fixture.componentInstance;
    component.descargoId = 6;
    component.puedeValorar = true;
    fixture.detectChanges();
  });

  describe('resultado y fundamento (TS4-03.18)', () => {
    let emitido: jasmine.Spy;

    beforeEach(() => {
      emitido = spyOn(component.registrar, 'emit');
    });

    it('emite el registro con el resultado, el fundamento sin espacios y los antecedentes', () => {
      component.antecedentes = [antecedente];
      component.elegirResultado('ACCEPTED');
      component.fundamento = `  ${fundamento}  `;

      component.enviar();

      expect(emitido).toHaveBeenCalledOnceWith({
        resultado: 'ACCEPTED',
        fundamento,
        antecedente_ids: [7]
      });
      expect(notifications.error).not.toHaveBeenCalled();
    });

    it('permite registrar sin antecedentes', () => {
      component.elegirResultado('REJECTED');
      component.fundamento = fundamento;

      component.enviar();

      expect(emitido).toHaveBeenCalledOnceWith({
        resultado: 'REJECTED',
        fundamento,
        antecedente_ids: []
      });
    });

    it('no registra sin elegir el resultado', () => {
      component.fundamento = fundamento;

      component.enviar();

      expect(emitido).not.toHaveBeenCalled();
      expect(notifications.error).toHaveBeenCalledOnceWith('Elegí si aprobás o desaprobás el T03.');
    });

    it('exige el fundamento también al aprobar', () => {
      component.elegirResultado('ACCEPTED');
      component.fundamento = '   ';

      component.enviar();

      expect(emitido).not.toHaveBeenCalled();
      expect(notifications.error).toHaveBeenCalledOnceWith('Escribí un fundamento de al menos 20 caracteres.');
    });

    it('rechaza el fundamento que sólo alcanza el mínimo contando espacios', () => {
      component.elegirResultado('REJECTED');
      component.fundamento = `Muy corto${' '.repeat(30)}`;

      component.enviar();

      expect(emitido).not.toHaveBeenCalled();
    });

    it('rechaza el fundamento que supera el máximo', () => {
      component.elegirResultado('ACCEPTED');
      component.fundamento = 'a'.repeat(5001);

      component.enviar();

      expect(emitido).not.toHaveBeenCalled();
      expect(notifications.error).toHaveBeenCalledOnceWith('El fundamento no puede superar los 5000 caracteres.');
    });

    it('muestra el contador de caracteres del fundamento', () => {
      component.fundamento = 'abc';
      fixture.detectChanges();

      expect(consultar('.contador-fundamento-t03')?.textContent).toContain('3 / 5000 caracteres');
    });

    it('no reenvía mientras hay un registro en curso', () => {
      component.registrando = true;
      fixture.detectChanges();
      component.elegirResultado('ACCEPTED');
      component.fundamento = fundamento;

      component.enviar();

      expect(emitido).not.toHaveBeenCalled();
      expect(consultar<HTMLButtonElement>('.btn-registrar-valoracion')?.disabled).toBeTrue();
    });

    it('oculta el formulario a quien sólo puede consultar', () => {
      component.puedeValorar = false;
      fixture.detectChanges();

      expect(consultar('.btn-registrar-valoracion')).toBeNull();
      expect(consultar('.campo-antecedente')).toBeNull();
    });

    it('limpia el borrador cuando llega una versión nueva al historial', () => {
      component.elegirResultado('ACCEPTED');
      component.fundamento = fundamento;

      component.historial = [version()];
      component.ngOnChanges({ historial: new SimpleChange([], component.historial, false) });

      expect(component.resultado).toBe('');
      expect(component.fundamento).toBe('');
    });
  });

  describe('antecedentes y aviso orientativo (TS4-03.19)', () => {
    const conAntecedente = () => {
      component.antecedentes = [antecedente];
      fixture.detectChanges();
    };

    it('pide buscar el antecedente con el número escrito', () => {
      const emitido = spyOn(component.buscarAntecedente, 'emit');
      component.numeroAntecedente = ' 7/2026 ';

      component.agregarAntecedente();

      expect(emitido).toHaveBeenCalledOnceWith('7/2026');
    });

    it('no busca sin un número escrito', () => {
      const emitido = spyOn(component.buscarAntecedente, 'emit');
      component.numeroAntecedente = '   ';

      component.agregarAntecedente();

      expect(emitido).not.toHaveBeenCalled();
      expect(notifications.error).toHaveBeenCalledOnceWith('Escribí el número del expediente antecedente.');
    });

    it('muestra sólo el número, la fecha, el motivo y el reglamento del antecedente', () => {
      conAntecedente();

      const ficha = consultar('.ficha-antecedente')?.textContent || '';
      expect(ficha).toContain('7/2026');
      expect(ficha).toContain('15/09/2026');
      expect(ficha).toContain('Inasistencia a la reunión plenaria');
      expect(ficha).toContain('Art. 86 del Reglamento Interno');
    });

    it('permite quitar un antecedente de la valoración', () => {
      const emitido = spyOn(component.quitarAntecedente, 'emit');
      conAntecedente();

      consultar<HTMLButtonElement>('.btn-quitar-antecedente')?.click();

      expect(emitido).toHaveBeenCalledOnceWith(7);
    });

    it('limpia el campo cuando el antecedente queda agregado', () => {
      component.numeroAntecedente = '7/2026';

      component.antecedentes = [antecedente];
      component.ngOnChanges({ antecedentes: new SimpleChange([], component.antecedentes, false) });

      expect(component.numeroAntecedente).toBe('');
    });

    it('muestra el aviso orientativo fijo cuando hay un antecedente', () => {
      conAntecedente();

      const aviso = consultar('.aviso-orientativo');
      expect(aviso?.getAttribute('role')).toBe('note');
      expect(aviso?.textContent).toContain('sana crítica');
      expect(aviso?.textContent).toContain('debe quedar fundamentado');
    });

    it('no muestra el aviso sin antecedentes', () => {
      expect(consultar('.aviso-orientativo')).toBeNull();
    });

    it('el aviso no bloquea el registro ni altera el resultado elegido', () => {
      const emitido = spyOn(component.registrar, 'emit');
      conAntecedente();
      component.elegirResultado('REJECTED');
      component.fundamento = fundamento;

      component.enviar();

      expect(emitido).toHaveBeenCalledOnceWith(jasmine.objectContaining({ resultado: 'REJECTED' }));
    });
  });

  describe('historial de versiones (TS4-03.20)', () => {
    it('avisa cuando todavía no hay valoraciones', () => {
      expect(texto()).toContain('Todavía no hay valoraciones registradas.');
    });

    it('muestra versión, resultado, fundamento, antecedentes, autor con su condición y fecha', () => {
      component.historial = [version()];
      fixture.detectChanges();

      const item = consultar('.historial-t03')?.textContent || '';
      expect(item).toContain('v1');
      expect(item).toContain('Aprobada');
      expect(item).toContain(fundamento);
      expect(item).toContain('7/2026');
      expect(item).toContain('408917');
      expect(item).toContain('Miembro Titular');
      expect(item).toContain('20/10/2026');
    });

    it('conserva el orden recibido, de la más nueva a la más vieja', () => {
      component.historial = [
        version({ id: 2, version: 2, resultado: 'REJECTED', resultado_display: 'Desaprobada' }),
        version()
      ];
      fixture.detectChanges();

      const items = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('.historial-t03'));
      expect(items.map(item => item.textContent?.trim().slice(0, 2))).toEqual(['v2', 'v1']);
    });

    it('informa cuando la versión no tiene la condición del autor', () => {
      component.historial = [version({
        autor_condicion: 'NO_INFORMADA',
        autor_condicion_display: 'No informada en el padrón'
      })];
      fixture.detectChanges();

      const item = consultar('.historial-t03')?.textContent || '';
      expect(item).toContain('Condición no informada');
      expect(item).not.toContain('No informada en el padrón');
    });

    it('sigue mostrando el historial a quien sólo puede consultar', () => {
      component.puedeValorar = false;
      component.historial = [version()];
      fixture.detectChanges();

      expect(consultar('.historial-t03')).not.toBeNull();
    });
  });
});
