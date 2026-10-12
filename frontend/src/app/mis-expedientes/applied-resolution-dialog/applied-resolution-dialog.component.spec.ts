import { CommonModule } from '@angular/common';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { AppliedPointsEntryDTO } from '../../services/socio-api.service';
import { AppliedResolutionDialogComponent } from './applied-resolution-dialog.component';

describe('AppliedResolutionDialogComponent', () => {
  let fixture: ComponentFixture<AppliedResolutionDialogComponent>;
  let close: jasmine.Spy;
  const entry: AppliedPointsEntryDTO = {
    movement_id: 17, applied_points: 2,
    historical_case: { id: 101, number: 'HIST-101', recorded_at: null, state: 'emitido' },
    resolution: { id: 201, text: 'VISTO\n<img src="x">\nCONSIDERANDO\nSE RESUELVE', regulations: ['Art. <93>'] },
    managed_case: null
  };

  beforeEach(async () => {
    close = jasmine.createSpy('close');
    await TestBed.configureTestingModule({
      imports: [CommonModule], declarations: [AppliedResolutionDialogComponent],
      providers: [
        { provide: MAT_DIALOG_DATA, useValue: entry },
        { provide: MatDialogRef, useValue: { close } }
      ]
    }).compileComponents();
    fixture = TestBed.createComponent(AppliedResolutionDialogComponent);
    fixture.detectChanges();
  });

  it('conserva texto formal y reglamentos como texto plano, con importe individual e identidad histórica', () => {
    const body: HTMLElement = fixture.nativeElement;
    expect(body.textContent).toContain(entry.resolution.text);
    expect(body.textContent).toContain('Art. <93>');
    expect(body.querySelector('img')).toBeNull();
    expect(body.textContent).toContain('HIST-101');
    expect(body.textContent).toContain('+2 pts');
    expect(body.textContent).not.toContain('EXP-');
  });

  it('cierra mediante un botón con nombre accesible', () => {
    const button: HTMLButtonElement = fixture.nativeElement.querySelector('.resolution-close');
    expect(button.getAttribute('aria-label')).toBe('Cerrar resolución');
    button.click();
    expect(close).toHaveBeenCalledOnceWith();
  });

  it('limpia el detalle cuando finaliza la sesión que lo autorizó', () => {
    fixture.componentInstance.clear();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).not.toContain('HIST-101');
    expect(fixture.nativeElement.textContent).not.toContain('CONSIDERANDO');
  });
});
