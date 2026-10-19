import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MapsComponent } from './maps.component';

describe('MapsComponent', () => {
  let component: MapsComponent;
  let fixture: ComponentFixture<MapsComponent>;
  let originalGoogle: unknown;
  let mapConstructor: jasmine.Spy;
  let attachMarker: jasmine.Spy;
  const sdkHost = window as unknown as { google?: unknown };

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MapsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    originalGoogle = sdkHost.google;
    mapConstructor = jasmine.createSpy('Map').and.returnValue({});
    attachMarker = jasmine.createSpy('setMap');
    sdkHost.google = {
      maps: {
        LatLng: jasmine.createSpy('LatLng').and.returnValue({}),
        Map: mapConstructor,
        Marker: jasmine.createSpy('Marker').and.returnValue({ setMap: attachMarker })
      }
    };
    fixture = TestBed.createComponent(MapsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    if (originalGoogle === undefined) delete sdkHost.google;
    else sdkHost.google = originalGoogle;
  });

  it('inicializa el mapa y asocia el marcador usando el SDK externo', () => {
    expect(component).toBeTruthy();
    expect(mapConstructor).toHaveBeenCalledWith(
      fixture.nativeElement.querySelector('#map'),
      jasmine.objectContaining({ zoom: 13, scrollwheel: false })
    );
    expect(attachMarker).toHaveBeenCalledWith(mapConstructor.calls.mostRecent().returnValue);
  });
});
