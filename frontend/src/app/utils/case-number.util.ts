/**
 * Utilidades para la representación unificada de expedientes y estados en SGD-AVEIT.
 * Estandariza el identificador al formato canónico <n>/<YYYY> sin ceros a la izquierda
 * y humaniza los estados procesales eliminando guiones o nomenclaturas técnicas de backend.
 */

export function formatCaseNumber(caseNumber: string | null | undefined): string {
  if (!caseNumber) return '';
  const trimmed = caseNumber.trim();

  // Formato: (EXP-)?<num>/<year> (ej: EXP-0007/2026 -> 7/2026, 007/2026 -> 7/2026, 7/2026 -> 7/2026)
  let match = /^(?:EXP-)?0*(\d+)\/(\d{4})$/i.exec(trimmed);
  if (match) {
    const num = parseInt(match[1], 10);
    const year = match[2];
    return `${num}/${year}`;
  }

  // Formato: (EXP-)?<year>-<num> (ej: EXP-2026-0007 -> 7/2026, 2026-7 -> 7/2026)
  match = /^(?:EXP-)?(\d{4})-0*(\d+)$/i.exec(trimmed);
  if (match) {
    const year = match[1];
    const num = parseInt(match[2], 10);
    return `${num}/${year}`;
  }

  return trimmed;
}

export function humanizeEstado(estado: string | null | undefined): string {
  if (!estado) return '';
  const normalizado = estado.toLowerCase().trim();

  switch (normalizado) {
    case 'creado':
      return 'Creado';
    case 'justificando':
      return 'Justificando';
    case 'revision_resolucion':
    case 'espera_resolucion':
      return 'En Revisión';
    case 'pendiente_firma':
      return 'Pendiente de Firma';
    case 'pendiente_correos':
      return 'Pendiente de Envío';
    case 'emitido':
      return 'Emitido';
    default:
      // Fallback seguro: reemplaza guiones bajos o medios por espacios y pasa a Title Case
      return estado
        .replace(/[_-]+/g, ' ')
        .trim()
        .toLowerCase()
        .replace(/\b\w/g, l => l.toUpperCase());
  }
}
