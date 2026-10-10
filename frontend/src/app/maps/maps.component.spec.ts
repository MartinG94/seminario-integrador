import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MapsComponent } from './maps.component';

describe('MapsComponent', () => {
  let component: MapsComponent;
  let fixture: ComponentFixture<MapsComponent>;
  let originalGoogle: unknown;
  let mapConstructor: jasmine.Spy;
  let setMap: jasmine.Spy;
  const mapInstance = {};
  const browserWindow = window as Window & { google?: unknown };

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MapsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    originalGoogle = browserWindow.google;
    mapConstructor = jasmine.createSpy('Map').and.returnValue(mapInstance);
    setMap = jasmine.createSpy('setMap');
    browserWindow.google = {
      maps: {
        LatLng: jasmine.createSpy('LatLng').and.returnValue({}),
        Map: mapConstructor,
        Marker: jasmine.createSpy('Marker').and.returnValue({ setMap })
      }
    };
    fixture = TestBed.createComponent(MapsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  afterEach(() => {
    if (originalGoogle === undefined) { delete browserWindow.google; }
    else { browserWindow.google = originalGoogle; }
  });

  it('should create', () => {
    expect(component).toBeTruthy();
    expect(mapConstructor).toHaveBeenCalledWith(
      fixture.nativeElement.querySelector('#map'),
      jasmine.objectContaining({ zoom: 13, scrollwheel: false })
    );
    expect(setMap).toHaveBeenCalledWith(mapInstance);
  });
});
