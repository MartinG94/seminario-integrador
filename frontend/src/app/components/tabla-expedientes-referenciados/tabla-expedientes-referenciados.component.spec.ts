import { ComponentFixture, TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { TablaExpedientesReferenciadosComponent } from './tabla-expedientes-referenciados.component';
import { AntecedenteT03DTO } from '../../services/expediente-api.service';

describe('TablaExpedientesReferenciadosComponent', () => {
  let component: TablaExpedientesReferenciadosComponent;
  let fixture: ComponentFixture<TablaExpedientesReferenciadosComponent>;

  const mockExpedientes: AntecedenteT03DTO[] = [
    {
      id: 10,
      numero: 'EXP-0007/2026',
      fecha_emision: '2026-03-01T10:00:00Z',
      motivo: 'Inasistencia reiterada a comisiones',
      reglamento_invocado: 'Estatuto Art. 12 Inc. A',
      titulo: 'Sanción disciplinaria 7',
      puntos: -1.5,
      tipo_accion: 'SANCTION'
    },
    {
      id: 20,
      numero: 'EXP-0012/2026',
      fecha_emision: '2026-03-05T14:30:00Z',
      motivo: 'Reconocimiento por jornada solidaria',
      reglamento_invocado: 'Reglamento Interno Art. 5',
      titulo: 'Mérito institucional 12',
      puntos: 2.0,
      tipo_accion: 'MERIT'
    }
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [TablaExpedientesReferenciadosComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(TablaExpedientesReferenciadosComponent);
    component = fixture.componentInstance;
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('debe mostrar estado vacío cuando no hay expedientes', () => {
    component.expedientes = [];
    component.emptyMessage = 'Sin antecedentes cargados';
    fixture.detectChanges();

    const emptyText = fixture.debugElement.query(By.css('.empty-text'));
    expect(emptyText).toBeTruthy();
    expect(emptyText.nativeElement.textContent).toContain('Sin antecedentes cargados');
  });

  it('debe renderizar filas para cada expediente', () => {
    component.expedientes = mockExpedientes;
    fixture.detectChanges();

    const filas = fixture.debugElement.queryAll(By.css('tbody tr.fila-expediente'));
    expect(filas.length).toBe(2);

    const textoFila1 = filas[0].nativeElement.textContent;
    expect(textoFila1).toContain('7/2026');
    expect(textoFila1).toContain('Sanción');
    expect(textoFila1).toContain('Sanción disciplinaria 7');

    const textoFila2 = filas[1].nativeElement.textContent;
    expect(textoFila2).toContain('12/2026');
    expect(textoFila2).toContain('Mérito');
    expect(textoFila2).toContain('Mérito institucional 12');
  });

  it('debe emitir remover al hacer clic en el botón de quitar cuando editable es true', () => {
    component.expedientes = mockExpedientes;
    component.editable = true;
    fixture.detectChanges();

    spyOn(component.remover, 'emit');

    const botonesQuitar = fixture.debugElement.queryAll(By.css('.btn-quitar-art'));
    expect(botonesQuitar.length).toBe(2);

    botonesQuitar[0].nativeElement.click();
    expect(component.remover.emit).toHaveBeenCalledWith(10);
  });

  it('no debe mostrar botón de quitar cuando editable es false', () => {
    component.expedientes = mockExpedientes;
    component.editable = false;
    fixture.detectChanges();

    const botonesQuitar = fixture.debugElement.queryAll(By.css('.btn-quitar-art'));
    expect(botonesQuitar.length).toBe(0);
  });
});
