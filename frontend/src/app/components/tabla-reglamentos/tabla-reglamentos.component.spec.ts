import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TablaReglamentosComponent } from './tabla-reglamentos.component';
import { ReglamentoCiteView } from '../../utils/reglamento-format.util';

describe('TablaReglamentosComponent', () => {
  let component: TablaReglamentosComponent;
  let fixture: ComponentFixture<TablaReglamentosComponent>;

  const mockArticulos: ReglamentoCiteView[] = [
    {
      raw: 'Estatuto - Art. 1: Denominacion',
      documento: 'Estatuto',
      articulo: '1',
      inciso: '-',
      cuerpo: 'Con la denominacion de AVEIT...',
      citaCorta: 'Estatuto · Art. 1'
    },
    {
      raw: 'Reglamento Interno - Art. 14 Inc. b: Faltas leves',
      documento: 'Reglamento Interno',
      articulo: '14',
      inciso: 'b',
      cuerpo: 'Toda inconducta en comisiones...',
      citaCorta: 'Reglamento Interno · Art. 14 Inc. b'
    }
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [TablaReglamentosComponent]
    }).compileComponents();

    fixture = TestBed.createComponent(TablaReglamentosComponent);
    component = fixture.componentInstance;
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('debe mostrar el estado vacio cuando no hay articulos', () => {
    component.articulos = [];
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.empty-reglamentos-state')).toBeTruthy();
    expect(compiled.querySelector('.table-reglamentos-normativa')).toBeFalsy();
  });

  it('debe renderizar los encabezados Documento, Art., Inc., Cuerpo', () => {
    component.articulos = mockArticulos;
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const headers = Array.from(compiled.querySelectorAll('thead th')).map(th => th.textContent?.trim());
    expect(headers).toContain('Documento');
    expect(headers).toContain('Art.');
    expect(headers).toContain('Inc.');
    expect(headers).toContain('Cuerpo');
    expect(headers).not.toContain('Quitar');
  });

  it('debe renderizar filas con datos de los articulos', () => {
    component.articulos = mockArticulos;
    fixture.detectChanges();
    const compiled = fixture.nativeElement as HTMLElement;
    const rows = compiled.querySelectorAll('tbody tr');
    expect(rows.length).toBe(2);

    expect(rows[0].querySelector('.td-documento')?.textContent).toContain('Estatuto');
    expect(rows[0].querySelector('.td-articulo')?.textContent?.trim()).toBe('1');
    expect(rows[0].querySelector('.td-inciso')?.textContent?.trim()).toBe('-');
    expect(rows[0].querySelector('.td-cuerpo')?.textContent).toContain('Con la denominacion de AVEIT...');

    expect(rows[1].querySelector('.td-documento')?.textContent).toContain('Reglamento Interno');
    expect(rows[1].querySelector('.td-articulo')?.textContent?.trim()).toBe('14');
    expect(rows[1].querySelector('.td-inciso')?.textContent?.trim()).toBe('b');
  });

  it('debe incluir columna y boton de Quitar cuando editable es true', () => {
    component.articulos = mockArticulos;
    component.editable = true;
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    const headers = Array.from(compiled.querySelectorAll('thead th')).map(th => th.textContent?.trim());
    expect(headers).toContain('Quitar');

    const removeBtns = compiled.querySelectorAll('.btn-quitar-art');
    expect(removeBtns.length).toBe(2);

    spyOn(component.remover, 'emit');
    (removeBtns[0] as HTMLButtonElement).click();
    expect(component.remover.emit).toHaveBeenCalledWith('Estatuto - Art. 1: Denominacion');
  });
});
