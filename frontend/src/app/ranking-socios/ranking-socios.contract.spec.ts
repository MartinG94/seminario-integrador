import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';

import { RankingService } from '../services/ranking.service';
import { NotificationService } from '../services/notification.service';
import { RankingSocio } from './ranking-socio.model';
import { RankingSociosComponent } from './ranking-socios.component';

describe('RankingSociosComponent — contrato TS77.35', () => {
  let component: RankingSociosComponent;
  let dialog: jasmine.SpyObj<MatDialog>;
  const categories: RankingSocio['categoria'][] = ['JUNIOR', 'SENIOR', 'EX_TRAVELER', 'UNKNOWN'];
  const members: RankingSocio[] = categories.map((category, index) => ({
    id: `${41 + index}`, legajo: `${75000 + index}`, nombre: `Nombre${index}`,
    apellido: `Apellido${index}`, categoria: category, subcomision: 'Cómputos', saldo: index
  }));

  beforeEach(() => {
    dialog = jasmine.createSpyObj<MatDialog>('MatDialog', ['open']);
    const service = jasmine.createSpyObj<RankingService>('RankingService', ['obtenerRanking']);
    const notifications = jasmine.createSpyObj<NotificationService>('NotificationService', ['error']);
    service.obtenerRanking.and.returnValue(of(members));
    component = new RankingSociosComponent(service, dialog, notifications);
    component.ngOnInit();
  });

  categories.forEach(category => {
    it(`filtra ${category} por su código vigente sin incluir otra condición`, () => {
      component.filtroCategoria = category;
      expect(component.sociosOrdenados.map(member => member.categoria)).toEqual([category]);
    });
  });

  it('el filtro vacío conserva las cuatro categorías y la paginación', () => {
    component.tamanoPagina = 2;
    expect(component.totalPaginas).toBe(2);
    expect(component.sociosOrdenados.length).toBe(4);
    component.cambiarPagina(2);
    expect(component.sociosPaginados.map(member => member.id)).toEqual(['42', '41']);
  });

  it('abre el legajo con ID institucional sin sustituirlo por legajo o PK local', () => {
    component.abrirLegajoSocio(members[2]);
    expect(dialog.open).toHaveBeenCalledWith(jasmine.any(Function), jasmine.objectContaining({
      data: jasmine.objectContaining({
        socioId: '43', nombreSocio: 'Nombre2 Apellido2', saldo: 2,
        identitySource: 'institutional'
      })
    }));
  });
});
