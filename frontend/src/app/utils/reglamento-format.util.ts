import { ArticuloReglamentoDTO } from '../services/expediente-api.service';

export interface ReglamentoCiteView {
  raw: string;
  documento: 'Estatuto' | 'Reglamento Interno' | 'Normativa';
  articulo: string;
  inciso: string;
  cuerpo: string;
  citaCorta: string;
}

/**
 * Normaliza una cadena de reglamento respaldante para extraer:
 * - documento ('Estatuto' | 'Reglamento Interno' | 'Normativa')
 * - articulo (ej. "1", "2", "14")
 * - inciso (ej. "a", "b", "-" si no aplica)
 * - cuerpo (texto íntegro del artículo)
 * - citaCorta (ej. "Estatuto · Art. 14 Inc. a")
 */
export function parseReglamentoCite(
  rawInput: string,
  catalogo?: ArticuloReglamentoDTO[]
): ReglamentoCiteView {
  const raw = (rawInput || '').trim();
  if (!raw) {
    return {
      raw: '',
      documento: 'Normativa',
      articulo: '-',
      inciso: '-',
      citaCorta: 'Sin especificar',
      cuerpo: ''
    };
  }

  // 1. Buscar coincidencia exacta o por prefijo en el catálogo de artículos si está disponible
  if (catalogo && catalogo.length > 0) {
    const match = catalogo.find(
      art =>
        art.cita_completa === raw ||
        art.cita_corta === raw ||
        (art.cita_corta && raw.startsWith(`${art.cita_corta}:`))
    );
    if (match) {
      const doc = detectarDocumento(match.titulo || raw);
      const artNum = match.articulo !== undefined && match.articulo !== null ? String(match.articulo) : '-';
      const incVal = match.inciso && match.inciso.trim() !== '-' ? match.inciso.trim() : '-';
      const artLabel = incVal !== '-' ? `Art. ${artNum} Inc. ${incVal}` : `Art. ${artNum}`;
      const citaCorta = `${match.titulo} · ${artLabel}`;
      const cuerpo = (match.cuerpo || match.descripcion || '').trim() || raw;
      return {
        raw,
        documento: doc,
        articulo: artNum,
        inciso: incVal,
        citaCorta,
        cuerpo
      };
    }
  }

  // 2. Parsear patrón estándar "<Documento> - Art. <N>[ Inc. <X>]: <Cuerpo>"
  const colonIdx = raw.indexOf(':');
  const head = colonIdx >= 0 ? raw.slice(0, colonIdx).trim() : raw;
  const tail = colonIdx >= 0 ? raw.slice(colonIdx + 1).trim() : '';

  const dashMatch = /^(.+?)\s*-\s*(Art\.\s*[^\(:]+?)(?:\s*(\(.+\)))?$/i.exec(head);
  if (dashMatch) {
    const docTitle = dashMatch[1].trim();
    const artPart = dashMatch[2].trim();
    const extraNote = dashMatch[3] ? ` ${dashMatch[3].trim()}` : '';
    const documento = detectarDocumento(docTitle);
    const citaCorta = `${docTitle} · ${artPart}`;
    const cuerpo = tail || (extraNote ? `${citaCorta}${extraNote}` : raw);

    const artRegex = /Art\.\s*([^\sInc\(\):]+)(?:\s*Inc\.\s*([^\s\(\):]+))?/i.exec(artPart);
    const articulo = artRegex && artRegex[1] ? artRegex[1].trim() : '-';
    const inciso = artRegex && artRegex[2] ? artRegex[2].trim() : '-';

    return {
      raw,
      documento,
      articulo,
      inciso,
      citaCorta,
      cuerpo
    };
  }

  // 3. Fallback para nombres de reglamentos o formatos libres
  const documento = detectarDocumento(raw);
  const citaCorta = head.replace(/\s+-\s+/g, ' · ');
  const cuerpo = tail || raw;

  const fallbackArt = /Art(?:[íi]culo|\.)?\s*([0-9a-zA-Z]+)/i.exec(head);
  const fallbackInc = /Inc(?:iso|\.)?\s*([0-9a-zA-Z]+)/i.exec(head);
  const articulo = fallbackArt && fallbackArt[1] ? fallbackArt[1].trim() : '-';
  const inciso = fallbackInc && fallbackInc[1] ? fallbackInc[1].trim() : '-';

  return {
    raw,
    documento,
    articulo,
    inciso,
    citaCorta,
    cuerpo
  };
}

export function parseReglamentosList(
  rawList: string[] | undefined | null,
  fallbackSingle?: string | null,
  catalogo?: ArticuloReglamentoDTO[]
): ReglamentoCiteView[] {
  const source =
    Array.isArray(rawList) && rawList.length > 0
      ? rawList.filter(Boolean)
      : fallbackSingle && fallbackSingle.trim()
      ? [fallbackSingle.trim()]
      : [];

  return source.map(item => parseReglamentoCite(item, catalogo));
}

function detectarDocumento(texto: string): 'Estatuto' | 'Reglamento Interno' | 'Normativa' {
  const lower = (texto || '').toLowerCase();
  if (lower.includes('estatuto')) {
    return 'Estatuto';
  }
  if (lower.includes('reglamento interno')) {
    return 'Reglamento Interno';
  }
  return 'Normativa';
}
