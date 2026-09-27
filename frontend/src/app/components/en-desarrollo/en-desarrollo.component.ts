import { Component, Input, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

@Component({
  selector: 'app-en-desarrollo',
  templateUrl: './en-desarrollo.component.html',
  styleUrls: ['./en-desarrollo.component.scss']
})
export class EnDesarrolloComponent implements OnInit {
  @Input() titulo = 'En desarrollo';
  @Input() descripcion = 'Esta sección se implementa en un sprint posterior del proyecto.';
  @Input() icono = 'construction';

  constructor(private route: ActivatedRoute) {}

  ngOnInit(): void {
    const data = this.route.snapshot.data;
    if (data) {
      if (data['titulo']) {
        this.titulo = data['titulo'];
      }
      if (data['descripcion']) {
        this.descripcion = data['descripcion'];
      }
      if (data['icono']) {
        this.icono = data['icono'];
      }
    }
  }
}
