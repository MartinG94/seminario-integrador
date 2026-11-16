import { Injectable } from '@angular/core';
import { MatPaginatorIntl } from '@angular/material/paginator';

/**
 * Etiquetas institucionales en español rioplatense para MatPaginator.
 */
@Injectable()
export class SpanishPaginatorIntl extends MatPaginatorIntl {
  itemsPerPageLabel = 'Ítems por página:';
  nextPageLabel = 'Página siguiente';
  previousPageLabel = 'Página anterior';
  firstPageLabel = 'Primera página';
  lastPageLabel = 'Última página';

  getRangeLabel = (page: number, pageSize: number, length: number): string => {
    if (length === 0 || pageSize === 0) {
      return `0 de ${length}`;
    }
    const safeLength = Math.max(length, 0);
    const startIndex = page * pageSize;
    const endIndex =
      startIndex < safeLength
        ? Math.min(startIndex + pageSize, safeLength)
        : startIndex + pageSize;
    return `${startIndex + 1} – ${endIndex} de ${safeLength}`;
  };
}
