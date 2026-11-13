import { PaginatedResponse } from './paginated-response.model';

interface MockItem {
  id: number;
  nombre: string;
}

describe('PaginatedResponse Model', () => {
  it('debe estructurar correctamente una respuesta paginada con los 7 campos canónicos', () => {
    const mockResponse: PaginatedResponse<MockItem> = {
      count: 50,
      total_pages: 3,
      current_page: 1,
      page_size: 20,
      next: 'http://localhost:8000/api/v1/items/?page=2',
      previous: null,
      results: [
        { id: 1, nombre: 'Item 1' },
        { id: 2, nombre: 'Item 2' }
      ]
    };

    expect(mockResponse.count).toBe(50);
    expect(mockResponse.total_pages).toBe(3);
    expect(mockResponse.current_page).toBe(1);
    expect(mockResponse.page_size).toBe(20);
    expect(mockResponse.next).toContain('page=2');
    expect(mockResponse.previous).toBeNull();
    expect(mockResponse.results.length).toBe(2);
    expect(mockResponse.results[0].nombre).toBe('Item 1');
  });

  it('debe admitir arrays vacíos y enlaces nulos en páginas iniciales o finales', () => {
    const emptyResponse: PaginatedResponse<string> = {
      count: 0,
      total_pages: 0,
      current_page: 1,
      page_size: 20,
      next: null,
      previous: null,
      results: []
    };

    expect(emptyResponse.count).toBe(0);
    expect(emptyResponse.total_pages).toBe(0);
    expect(emptyResponse.results).toEqual([]);
    expect(emptyResponse.next).toBeNull();
    expect(emptyResponse.previous).toBeNull();
  });
});
