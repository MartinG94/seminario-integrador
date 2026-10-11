import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { NotificationsComponent } from './notifications.component';
import { NotificationService, NotificationType } from '../services/notification.service';

describe('NotificationsComponent', () => {
  let component: NotificationsComponent;
  let fixture: ComponentFixture<NotificationsComponent>;
  let notifications: jasmine.SpyObj<NotificationService>;

  beforeEach(async(() => {
    notifications = jasmine.createSpyObj('NotificationService', ['show']);
    TestBed.configureTestingModule({
      declarations: [ NotificationsComponent ],
      providers: [{ provide: NotificationService, useValue: notifications }]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(NotificationsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('usa el servicio central para todas las variantes sin alertas dentro de la vista', () => {
    const buttons = fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>;
    expect(buttons.length).toBe(4);
    buttons.forEach(button => button.click());
    expect(notifications.show.calls.allArgs().map(args => args[0] as NotificationType))
      .toEqual(['success', 'error', 'warning', 'info']);
    expect(fixture.nativeElement.querySelector('.alert')).toBeNull();
  });
});
