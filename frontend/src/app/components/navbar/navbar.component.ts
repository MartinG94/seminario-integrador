import { Component, OnInit, ElementRef } from '@angular/core';
import { ROUTES } from '../sidebar/sidebar.component';
import { Location } from '@angular/common';
import { Router } from '@angular/router';
import { TribunalDataService, RolUsuario } from '../../services/tribunal-data.service';
import { AuthService, PerfilSocio } from '../../services/auth.service';

@Component({
  selector: 'app-navbar',
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.css']
})
export class NavbarComponent implements OnInit {
    private listTitles: any[];
    location: Location;
    mobile_menu_visible: any = 0;
    private toggleButton: any;
    private sidebarVisible: boolean;

    currentRole: RolUsuario = 'tribunal';
    isDarkMode = false;

    perfil: PerfilSocio | null = null;

    constructor(
      location: Location,
      private element: ElementRef,
      private router: Router,
      public dataService: TribunalDataService,
      private auth: AuthService
    ) {
      this.location = location;
      this.sidebarVisible = false;
    }

    cerrarSesion(): void {
      this.auth.logout();
      this.router.navigate(['/login']);
    }

    ngOnInit(){
      this.auth.perfil$.subscribe(perfil => this.perfil = perfil);
      this.listTitles = ROUTES.filter(listTitle => listTitle);
      const navbar: HTMLElement = this.element.nativeElement;
      this.toggleButton = navbar.getElementsByClassName('navbar-toggler')[0];
      this.router.events.subscribe((event) => {
        this.sidebarClose();
        var $layer: any = document.getElementsByClassName('close-layer')[0];
        if ($layer) {
          $layer.remove();
          this.mobile_menu_visible = 0;
        }
      });

      this.dataService.currentRole$.subscribe(r => this.currentRole = r);
      this.dataService.darkMode$.subscribe(d => this.isDarkMode = d);
    }

    setRole(role: RolUsuario): void {
      this.dataService.setRole(role);
    }

    toggleTheme(): void {
      this.dataService.toggleDarkMode();
    }

    sidebarOpen() {
        const toggleButton = this.toggleButton;
        const body = document.getElementsByTagName('body')[0];
        setTimeout(function(){
            toggleButton.classList.add('toggled');
        }, 500);

        body.classList.add('nav-open');
        this.sidebarVisible = true;
    };

    sidebarClose() {
        const body = document.getElementsByTagName('body')[0];
        if (this.toggleButton) {
          this.toggleButton.classList.remove('toggled');
        }
        this.sidebarVisible = false;
        body.classList.remove('nav-open');
    };

    sidebarToggle() {
        var $toggle = document.getElementsByClassName('navbar-toggler')[0];

        if (this.sidebarVisible === false) {
            this.sidebarOpen();
        } else {
            this.sidebarClose();
        }
        const body = document.getElementsByTagName('body')[0];

        if (this.mobile_menu_visible == 1) {
            body.classList.remove('nav-open');
            var $layer: any = document.getElementsByClassName('close-layer')[0];
            if ($layer) {
                $layer.remove();
            }
            setTimeout(function() {
                $toggle.classList.remove('toggled');
            }, 400);

            this.mobile_menu_visible = 0;
        } else {
            setTimeout(function() {
                $toggle.classList.add('toggled');
            }, 430);

            const layerElement = document.createElement('div');
            layerElement.setAttribute('class', 'close-layer');

            if (body.querySelectorAll('.main-panel')) {
                document.getElementsByClassName('main-panel')[0].appendChild(layerElement);
            } else if (body.classList.contains('off-canvas-sidebar')) {
                document.getElementsByClassName('wrapper-full-page')[0].appendChild(layerElement);
            }

            setTimeout(function() {
                layerElement.classList.add('visible');
            }, 100);

            layerElement.onclick = function() {
              body.classList.remove('nav-open');
              this.mobile_menu_visible = 0;
              layerElement.classList.remove('visible');
              setTimeout(function() {
                  layerElement.remove();
                  $toggle.classList.remove('toggled');
              }, 400);
            }.bind(this);

            body.classList.add('nav-open');
            this.mobile_menu_visible = 1;
        }
    };

    getTitle(){
      var titlee = this.location.prepareExternalUrl(this.location.path());
      if(titlee.charAt(0) === '#'){
          titlee = titlee.slice( 1 );
      }

      for(var item = 0; item < this.listTitles.length; item++){
          if(this.listTitles[item].path === titlee){
              return this.listTitles[item].title;
          }
      }
      return 'Mis Expedientes';
    }
}
