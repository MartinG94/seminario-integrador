import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Component } from '@angular/core';
import { RouterTestingModule } from '@angular/router/testing';

import { AdminLayoutComponent } from './admin-layout.component';

@Component({ selector: 'app-sidebar', template: '<div class="sidebar-wrapper"></div>' })
class SidebarStubComponent {}
@Component({ selector: 'app-navbar', template: '' })
class NavbarStubComponent {}
@Component({ selector: 'app-footer', template: '' })
class FooterStubComponent {}

describe('AdminLayoutComponent', () => {
  let component: AdminLayoutComponent;
  let fixture: ComponentFixture<AdminLayoutComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      declarations: [AdminLayoutComponent, SidebarStubComponent, NavbarStubComponent, FooterStubComponent]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AdminLayoutComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
