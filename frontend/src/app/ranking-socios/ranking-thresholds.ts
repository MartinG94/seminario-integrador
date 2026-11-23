/** Umbrales de saldo vigentes (parámetros del sistema, Spec 012). */
export interface UmbralesVigentes {
  critico: number;
  preventivo: number;
  preventivoActivo: boolean;
}

/** Valores iniciales del catálogo; rigen hasta recibir los configurados. */
export const UMBRALES_INICIALES: Readonly<UmbralesVigentes> = Object.freeze({
  critico: -10,
  preventivo: -7,
  preventivoActivo: false
});

export type NivelSaldo = 'critico' | 'preventivo' | 'regular';

/** Clasifica un saldo según los umbrales; el preventivo sólo rige si está activo. */
export function nivelSaldo(saldo: number, umbrales: UmbralesVigentes): NivelSaldo {
  if (saldo <= umbrales.critico) return 'critico';
  if (umbrales.preventivoActivo && saldo <= umbrales.preventivo) return 'preventivo';
  return 'regular';
}

/** Saldo desde el cual un socio figura "en alerta". */
export function umbralAlerta(umbrales: UmbralesVigentes): number {
  return umbrales.preventivoActivo ? umbrales.preventivo : umbrales.critico;
}

/** Número con coma decimal rioplatense y sin ceros sobrantes (p. ej. -7 o -8,5). */
export function formatearPuntos(valor: number): string {
  return String(valor).replace('.', ',');
}
