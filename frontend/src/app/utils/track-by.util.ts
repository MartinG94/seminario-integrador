/**
 * Utilitario universal de funciones puras trackBy para directivas *ngFor en Angular.
 * Optimiza la reconciliación del Virtual DOM y evita Layout Thrashing e invalidaciones
 * innecesarias de nodos DOM (requisito EARS-U04, SCRUM-87 / SCRUM-119).
 */
export class TrackByUtils {
  /**
   * Comparador puro por identificador unívoco `id`.
   * Si no existe o el elemento es nulo, recurre al índice posicional.
   */
  static byId(index: number, item: any): any {
    if (item == null) {
      return index;
    }
    return item.id ?? index;
  }

  /**
   * Comparador puro para entidades de Socios.
   * Evalúa secuencialmente `nroSocio` (o `nro_socio`), `id` y `legajo`.
   * Si ninguno está definido, recurre al índice posicional.
   */
  static bySocio(index: number, item: any): any {
    if (item == null) {
      return index;
    }
    return item.nroSocio ?? item.nro_socio ?? item.id ?? item.legajo ?? index;
  }

  /**
   * Comparador puro para entidades de Expedientes disciplinarios.
   * Evalúa secuencialmente `numero`, `id`, `expediente_id` (o `numero_expediente` / `numeroExpediente`).
   * Si ninguno está definido, recurre al índice posicional.
   */
  static byExpediente(index: number, item: any): any {
    if (item == null) {
      return index;
    }
    return item.numero ?? item.id ?? item.expediente_id ?? item.numero_expediente ?? item.numeroExpediente ?? index;
  }

  /**
   * Comparador puro por valor primitivo o referencia de elemento.
   * Utilizado en iteraciones sobre arrays de tipos primitivos (strings, números, enums).
   * Si el elemento es null o undefined, recurre al índice posicional.
   */
  static byValue(index: number, item: any): any {
    if (typeof item === 'object' && item !== null && 'value' in item) {
      return item.value ?? index;
    }
    return item ?? index;
  }

  // Métodos de instancia delegados para compatibilidad si se instancia en componentes
  byId(index: number, item: any): any {
    return TrackByUtils.byId(index, item);
  }

  bySocio(index: number, item: any): any {
    return TrackByUtils.bySocio(index, item);
  }

  byExpediente(index: number, item: any): any {
    return TrackByUtils.byExpediente(index, item);
  }

  byValue(index: number, item: any): any {
    return TrackByUtils.byValue(index, item);
  }
}

// Exportación de funciones puras standalone para uso directo
export const trackById = TrackByUtils.byId;
export const trackBySocio = TrackByUtils.bySocio;
export const trackByExpediente = TrackByUtils.byExpediente;
export const trackByValue = TrackByUtils.byValue;
