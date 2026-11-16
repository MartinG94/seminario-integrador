import { Component, OnInit, OnDestroy, AfterViewInit } from '@angular/core';
import { Location, PopStateEvent } from '@angular/common';
import { Router, NavigationEnd, NavigationStart } from '@angular/router';
import PerfectScrollbar from 'perfect-scrollbar';
import * as $ from "jquery";
import { Subject } from 'rxjs';
import { filter, takeUntil } from 'rxjs/operators';

@Component({
  selector: 'app-admin-layout',
  templateUrl: './admin-layout.component.html',
  styleUrls: ['./admin-layout.component.scss']
})
export class AdminLayoutComponent implements OnInit, AfterViewInit, OnDestroy {
  private readonly destroy$ = new Subject<void>();
  private locationSub: { unsubscribe: () => void } | null = null;
  private psMainPanel: PerfectScrollbar | null = null;
  private psSidebar: PerfectScrollbar | null = null;
  private lastPoppedUrl: string;
  private yScrollStack: number[] = [];

  constructor( public location: Location, private router: Router) {}

  ngOnInit() {
      const isWindows = navigator.platform.indexOf('Win') > -1 ? true : false;

      if (isWindows && !document.getElementsByTagName('body')[0].classList.contains('sidebar-mini')) {
          // if we are on windows OS we activate the perfectScrollbar function

          document.getElementsByTagName('body')[0].classList.add('perfect-scrollbar-on');
      } else {
          document.getElementsByTagName('body')[0].classList.remove('perfect-scrollbar-off');
      }
      const elemMainPanel = <HTMLElement>document.querySelector('.main-panel');
      const elemSidebar = <HTMLElement>document.querySelector('.sidebar .sidebar-wrapper');

      this.locationSub = this.location.subscribe((ev:PopStateEvent) => {
          this.lastPoppedUrl = ev.url;
      }) as { unsubscribe: () => void };
      this.router.events.pipe(takeUntil(this.destroy$)).subscribe((event:any) => {
          if (event instanceof NavigationStart) {
             if (event.url != this.lastPoppedUrl)
                 this.yScrollStack.push(window.scrollY);
         } else if (event instanceof NavigationEnd) {
             if (event.url == this.lastPoppedUrl) {
                 this.lastPoppedUrl = undefined;
                 window.scrollTo(0, this.yScrollStack.pop());
             } else
                 window.scrollTo(0, 0);
         }
      });
      this.router.events.pipe(
        filter(event => event instanceof NavigationEnd),
        takeUntil(this.destroy$)
      ).subscribe(() => {
           if (elemMainPanel) elemMainPanel.scrollTop = 0;
           if (elemSidebar) elemSidebar.scrollTop = 0;
      });
      if (window.matchMedia(`(min-width: 960px)`).matches && !this.isMac()) {
          if (elemMainPanel) {
            this.psMainPanel = new PerfectScrollbar(elemMainPanel);
          }
          if (elemSidebar) {
            this.psSidebar = new PerfectScrollbar(elemSidebar);
          }
      }

      const window_width = $(window).width();
      let $sidebar = $('.sidebar');
      let $sidebar_responsive = $('body > .navbar-collapse');
      let $sidebar_img_container = $sidebar.find('.sidebar-background');


      if(window_width > 767){
          if($('.fixed-plugin .dropdown').hasClass('show-dropdown')){
              $('.fixed-plugin .dropdown').addClass('open');
          }

      }

      $('.fixed-plugin a').on('click.adminLayout', function(event){
        // Alex if we click on switch, stop propagation of the event, so the dropdown will not be hide, otherwise we set the  section active
          if($(this).hasClass('switch-trigger')){
              if(event.stopPropagation){
                  event.stopPropagation();
              }
              else if(window.event){
                 window.event.cancelBubble = true;
              }
          }
      });

      $('.fixed-plugin .badge').on('click.adminLayout', function(){
          let $full_page_background = $('.full-page-background');


          $(this).siblings().removeClass('active');
          $(this).addClass('active');

          var new_color = $(this).data('color');

          if($sidebar.length !== 0){
              $sidebar.attr('data-color', new_color);
          }

          if($sidebar_responsive.length != 0){
              $sidebar_responsive.attr('data-color',new_color);
          }
      });

      $('.fixed-plugin .img-holder').on('click.adminLayout', function(){
          let $full_page_background = $('.full-page-background');

          $(this).parent('li').siblings().removeClass('active');
          $(this).parent('li').addClass('active');


          var new_image = $(this).find("img").attr('src');

          if($sidebar_img_container.length !=0 ){
              $sidebar_img_container.fadeOut('fast', function(){
                 $sidebar_img_container.css('background-image','url("' + new_image + '")');
                 $sidebar_img_container.fadeIn('fast');
              });
          }

          if($full_page_background.length != 0){

              $full_page_background.fadeOut('fast', function(){
                 $full_page_background.css('background-image','url("' + new_image + '")');
                 $full_page_background.fadeIn('fast');
              });
          }

          if($sidebar_responsive.length != 0){
              $sidebar_responsive.css('background-image','url("' + new_image + '")');
          }
      });
  }
  ngAfterViewInit() {
      this.runOnRouteChange();
  }
  isMaps(path){
      var titlee = this.location.prepareExternalUrl(this.location.path());
      titlee = titlee.slice( 1 );
      if(path == titlee){
          return false;
      }
      else {
          return true;
      }
  }
  runOnRouteChange(): void {
    if (window.matchMedia(`(min-width: 960px)`).matches && !this.isMac()) {
      const elemMainPanel = <HTMLElement>document.querySelector('.main-panel');
      if (elemMainPanel) {
        if (!this.psMainPanel) {
          this.psMainPanel = new PerfectScrollbar(elemMainPanel);
        } else {
          this.psMainPanel.update();
        }
      }
    }
  }
  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.locationSub?.unsubscribe();
    this.locationSub = null;
    this.psMainPanel?.destroy();
    this.psMainPanel = null;
    this.psSidebar?.destroy();
    this.psSidebar = null;
    $('.fixed-plugin a, .fixed-plugin .badge, .fixed-plugin .img-holder').off('.adminLayout');
  }
  isMac(): boolean {
      let bool = false;
      if (navigator.platform.toUpperCase().indexOf('MAC') >= 0 || navigator.platform.toUpperCase().indexOf('IPAD') >= 0) {
          bool = true;
      }
      return bool;
  }

}
