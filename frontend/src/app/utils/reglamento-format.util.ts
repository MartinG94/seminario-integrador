import { ArticuloReglamentoDTO } from '../services/expediente-api.service';

export interface ReglamentoCiteView {
  raw: string;
  documento: 'Estatuto' | 'Reglamento Interno' | 'Normativa';
  citaCorta: string;
  cuerpo: string;
}

/**
 * Normaliza una cadena de reglamento respaldante para extraer:
 * - documento ('Estatuto' | 'Reglamento Interno' | 'Normativa')
 * - citaCorta (ej. "Estatuto · Art. 14 Inc. a")
 * - cuerpo (texto íntegro del artículo para tooltip y panel desplegable)
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
      const artLabel =
        match.inciso && match.inciso !== '-'
          ? `Art. ${match.articulo} Inc. ${match.inciso}`
          : `Art. ${match.articulo}`;
      const citaCorta = `${match.titulo} · ${artLabel}`;
      const cuerpo = (match.cuerpo || match.descripcion || '').trim() || raw;
      return {
        raw,
        documento: doc,
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
    return {
      raw,
      documento,
      citaCorta,
      cuerpo
    };
  }

  // 3. Fallback para nombres de reglamentos o formatos libres (ej. "Reglamento de Faltas Internas Art. 4")
  const documento = detectarDocumento(raw);
  const citaCorta = head.replace(/\s+-\s+/g, ' · ');
  const cuerpo = tail || raw;

  return {
    raw,
    documento,
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
