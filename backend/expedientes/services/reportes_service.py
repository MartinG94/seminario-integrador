"""Servicio analítico de reportes y cómputo determinista de KPIs para SGD-AVEIT.

Implementa el motor de analítica institucional con los 7 KPIs del módulo:
- KPI-01: Tiempo de Vida Promedio del Expediente (días corridos, O2 Eficiencia).
- KPI-02: Pedidos por Autoridad Solicitante/Convocante (O1/O2 Actividad).
- KPI-03: Pedidos por Subcomisión (Intra vs. Inter) y Agrupación por Concepto TD.
- KPI-04: Backlog Activo y Envejecimiento por Urgencia y Estado (O2 Flujo TD).
- KPI-05: Tasa de Presentación y Aceptación de Descargos T02/T03 y Apelaciones (O1/O2 Garantías).
- KPI-06: Balance Neto de Puntos, Regla 3:1 y Socios en Riesgo Estatutario (O1 Eficacia).
- KPI-07: Índice de Asistencia y Validez Reglamentaria de Eventos (O1/O2 Cumplimiento).

Cumple estrictamente con la regla innegociable de CERO sentencias UPDATE/DELETE
manuales en MySQL para saldos de puntos.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from django.db.models import Q, Sum
from django.utils import timezone

from expedientes.models import (
    AdecuacionT01,
    ApelacionT01,
    AsistenciaEvento,
    AtencionFelicitacion,
    ConceptoExpedienteEnum,
    DecisionCausalDescargo,
    DecisionCausalEnum,
    DescargoExpediente,
    EstadoAsistenciaEventoEnum,
    EstadoEventoEnum,
    EstadoExpedienteEnum,
    EventoInstitucional,
    Expediente,
    SolicitudT01,
    TipoDescargoEnum,
    UrgenciaExpedienteEnum,
)
from ranking.models import PuntajeAplicado
from socios.models import SocialCategory, Socio, Subcomision


class ReportesMetricsService:
    """Motor analítico de cálculo puro para el tablero de control institucional."""

    @classmethod
    def resolve_date_range(
        cls,
        anio: int | str | None = None,
        cuatrimestre: str | None = None,
        fecha_desde: str | date | datetime | None = None,
        fecha_hasta: str | date | datetime | None = None,
    ) -> tuple[datetime | None, datetime | None]:
        """Resuelve el rango temporal (desde, hasta) consciente de timezone."""
        desde_dt: datetime | None = None
        hasta_dt: datetime | None = None

        if fecha_desde:
            if isinstance(fecha_desde, str):
                parsed = datetime.fromisoformat(fecha_desde)
            elif isinstance(fecha_desde, datetime):
                parsed = fecha_desde
            elif isinstance(fecha_desde, date):
                parsed = datetime.combine(fecha_desde, datetime.min.time())
            else:
                parsed = None

            if parsed:
                if timezone.is_naive(parsed):
                    desde_dt = timezone.make_aware(
                        datetime.combine(parsed.date(), datetime.min.time())
                    )
                else:
                    desde_dt = parsed

        if fecha_hasta:
            if isinstance(fecha_hasta, str):
                parsed = datetime.fromisoformat(fecha_hasta)
            elif isinstance(fecha_hasta, datetime):
                parsed = fecha_hasta
            elif isinstance(fecha_hasta, date):
                parsed = datetime.combine(fecha_hasta, datetime.max.time())
            else:
                parsed = None

            if parsed:
                if timezone.is_naive(parsed):
                    hasta_dt = timezone.make_aware(
                        datetime.combine(parsed.date(), datetime.max.time())
                    )
                else:
                    hasta_dt = parsed

        # Si no se definieron fechas explícitas pero sí año y/o cuatrimestre
        if not desde_dt and not hasta_dt:
            y = int(anio) if anio else None
            c = str(cuatrimestre).strip().lower() if cuatrimestre else None

            if c in ("1", "primer", "primero"):
                effective_year = y or timezone.now().year
                desde_dt = timezone.make_aware(datetime(effective_year, 3, 1, 0, 0, 0))
                hasta_dt = timezone.make_aware(datetime(effective_year, 6, 30, 23, 59, 59, 999999))
            elif c in ("2", "segundo"):
                effective_year = y or timezone.now().year
                desde_dt = timezone.make_aware(datetime(effective_year, 8, 1, 0, 0, 0))
                hasta_dt = timezone.make_aware(datetime(effective_year, 11, 30, 23, 59, 59, 999999))
            elif c == "anual" or y is not None:
                effective_year = y or timezone.now().year
                desde_dt = timezone.make_aware(datetime(effective_year, 1, 1, 0, 0, 0))
                hasta_dt = timezone.make_aware(datetime(effective_year, 12, 31, 23, 59, 59, 999999))

        return desde_dt, hasta_dt

    @classmethod
    def get_origin_subcomision(cls, expediente: Expediente) -> Subcomision | None:
        """Determina la subcomisión de origen de un expediente disciplinario."""
        # 1. Por SolicitudT01 vinculada
        if hasattr(expediente, "solicitud_t01") and expediente.solicitud_t01:
            solicitante = expediente.solicitud_t01.solicitante
            if solicitante and solicitante.subcomision:
                return solicitante.subcomision

        # 2. Por AsistenciaEvento de origen
        asistencia = (
            expediente.asistencias_origen.select_related(
                "evento__subcomision", "evento__convocante__subcomision"
            ).first()
            if hasattr(expediente, "asistencias_origen")
            else None
        )
        if asistencia and asistencia.evento:
            if asistencia.evento.subcomision:
                return asistencia.evento.subcomision
            if asistencia.evento.convocante and asistencia.evento.convocante.subcomision:
                return asistencia.evento.convocante.subcomision

        # 3. Fallback a la subcomisión del socio imputado
        if expediente.socio and expediente.socio.subcomision:
            return expediente.socio.subcomision

        return None

    @classmethod
    def calculate_resumen(
        cls,
        *,
        anio: int | str | None = None,
        cuatrimestre: str | None = None,
        fecha_desde: str | date | datetime | None = None,
        fecha_hasta: str | date | datetime | None = None,
        subcomision_id: int | str | None = None,
        concepto: str | None = None,
    ) -> dict[str, Any]:
        """Calcula el estado analítico completo del SGD-AVEIT conforme a los filtros provistos."""
        desde_dt, hasta_dt = cls.resolve_date_range(
            anio=anio,
            cuatrimestre=cuatrimestre,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

        sub_id_int: int | None = None
        if subcomision_id not in (None, "", "null"):
            try:
                sub_id_int = int(subcomision_id)
            except (ValueError, TypeError):
                sub_id_int = None

        # 1. Base QuerySet de Expedientes
        exp_qs = Expediente.objects.select_related(
            "socio__subcomision",
            "solicitud_t01__solicitante__subcomision",
        ).prefetch_related(
            "socios__subcomision",
            "cambios_estado",
            "asistencias_origen__evento__subcomision",
        )

        if desde_dt:
            exp_qs = exp_qs.filter(created_at__gte=desde_dt)
        if hasta_dt:
            exp_qs = exp_qs.filter(created_at__lte=hasta_dt)

        if concepto:
            concepto_clean = str(concepto).strip()
            if concepto_clean == "SIN_CLASIFICAR":
                exp_qs = exp_qs.filter(Q(concepto__isnull=True) | Q(concepto=""))
            else:
                exp_qs = exp_qs.filter(concepto=concepto_clean)

        if sub_id_int:
            exp_qs = exp_qs.filter(
                Q(solicitud_t01__solicitante__subcomision_id=sub_id_int)
                | Q(asistencias_origen__evento__subcomision_id=sub_id_int)
                | Q(socio__subcomision_id=sub_id_int)
                | Q(socios__subcomision_id=sub_id_int)
            ).distinct()

        expedientes_list = list(exp_qs)
        exp_ids = [e.id for e in expedientes_list]

        # 2. KPI-01: Tiempo de Vida Promedio (días corridos en expedientes emitidos)
        emitidos_evaluados = [
            e for e in expedientes_list if e.estado == EstadoExpedienteEnum.EMITIDO
        ]
        total_emitidos_evaluados = len(emitidos_evaluados)
        dias_acumulados = 0.0

        for exp in emitidos_evaluados:
            cambio_emitido = next(
                (
                    c
                    for c in exp.cambios_estado.all()
                    if c.estado_nuevo == EstadoExpedienteEnum.EMITIDO
                ),
                None,
            )
            fecha_emision = cambio_emitido.fecha_hora if cambio_emitido else exp.updated_at
            if fecha_emision and exp.created_at:
                delta_dias = max(0.0, (fecha_emision - exp.created_at).total_seconds() / 86400.0)
                dias_acumulados += delta_dias

        tiempo_vida_promedio_dias = (
            round(dias_acumulados / total_emitidos_evaluados, 1)
            if total_emitidos_evaluados > 0
            else 0.0
        )

        # Totales generales de expedientes
        total_expedientes = len(expedientes_list)
        emitidos_count = total_emitidos_evaluados
        en_tramite_count = total_expedientes - emitidos_count
        sanciones_count = sum(1 for e in expedientes_list if e.puntos < 0)
        meritos_count = sum(1 for e in expedientes_list if e.puntos > 0)
        sin_clasificar_count = sum(1 for e in expedientes_list if not e.concepto)

        # 3. KPI-04: Backlog Activo por Urgencia y Estado
        abiertos = [e for e in expedientes_list if e.estado != EstadoExpedienteEnum.EMITIDO]
        total_abiertos = len(abiertos)
        backlog_urgencia = {
            "total_abiertos": total_abiertos,
            "baja": sum(1 for e in abiertos if e.urgencia == UrgenciaExpedienteEnum.BAJA),
            "normal": sum(1 for e in abiertos if e.urgencia == UrgenciaExpedienteEnum.NORMAL),
            "urgente": sum(1 for e in abiertos if e.urgencia == UrgenciaExpedienteEnum.URGENTE),
            "por_estado": {
                EstadoExpedienteEnum.CREADO.value: sum(
                    1 for e in abiertos if e.estado == EstadoExpedienteEnum.CREADO
                ),
                EstadoExpedienteEnum.JUSTIFICANDO.value: sum(
                    1 for e in abiertos if e.estado == EstadoExpedienteEnum.JUSTIFICANDO
                ),
                EstadoExpedienteEnum.REVISION_RESOLUCION.value: sum(
                    1 for e in abiertos if e.estado == EstadoExpedienteEnum.REVISION_RESOLUCION
                ),
                EstadoExpedienteEnum.ESPERA_RESOLUCION.value: sum(
                    1 for e in abiertos if e.estado == EstadoExpedienteEnum.ESPERA_RESOLUCION
                ),
                EstadoExpedienteEnum.PENDIENTE_CORREOS.value: sum(
                    1 for e in abiertos if e.estado == EstadoExpedienteEnum.PENDIENTE_CORREOS
                ),
            },
        }

        # 4. KPI-05: Descargos y Apelaciones
        total_imputaciones = 0
        for exp in expedientes_list:
            soc_ids = {exp.socio_id}
            for s in exp.socios.all():
                soc_ids.add(s.id)
            total_imputaciones += len(soc_ids)

        descargos_qs = DescargoExpediente.objects.filter(expediente_id__in=exp_ids, es_vigente=True)
        descargos_t02 = descargos_qs.filter(tipo=TipoDescargoEnum.T02_CERTIFICADO).count()
        descargos_t03 = descargos_qs.filter(tipo=TipoDescargoEnum.T03_EXTRAORDINARIO).count()
        total_descargos = descargos_t02 + descargos_t03
        tasa_presentacion_pct = (
            round((total_descargos / total_imputaciones) * 100, 1)
            if total_imputaciones > 0
            else 0.0
        )

        decisiones_qs = DecisionCausalDescargo.objects.filter(expediente_id__in=exp_ids)
        decisiones_t02_aceptadas = decisiones_qs.filter(
            decision=DecisionCausalEnum.ACCEPTED
        ).count()
        decisiones_t02_rechazadas = decisiones_qs.filter(
            decision=DecisionCausalEnum.REJECTED
        ).count()
        decisiones_t02_total = decisiones_t02_aceptadas + decisiones_t02_rechazadas
        tasa_aceptacion_t02_pct = (
            round((decisiones_t02_aceptadas / decisiones_t02_total) * 100, 1)
            if decisiones_t02_total > 0
            else 0.0
        )

        apelaciones_t01 = ApelacionT01.objects.filter(expediente_id__in=exp_ids).count()
        adecuaciones_t01 = AdecuacionT01.objects.filter(expediente_id__in=exp_ids).count()

        descargos_resumen = {
            "total_imputaciones": total_imputaciones,
            "total_descargos": total_descargos,
            "descargos_t02": descargos_t02,
            "descargos_t03": descargos_t03,
            "tasa_presentacion_pct": tasa_presentacion_pct,
            "decisiones_t02_total": decisiones_t02_total,
            "decisiones_t02_aceptadas": decisiones_t02_aceptadas,
            "decisiones_t02_rechazadas": decisiones_t02_rechazadas,
            "tasa_aceptacion_t02_pct": tasa_aceptacion_t02_pct,
            "apelaciones_t01": apelaciones_t01,
            "adecuaciones_t01": adecuaciones_t01,
        }

        # 5. KPI-06: Balance de Puntos, Regla 3:1 y Socios en Riesgo
        saldos_por_socio: dict[int, Decimal] = {}
        try:
            for row in (
                PuntajeAplicado.objects.values("socio_id")
                .annotate(total=Sum("puntajeAplicado"))
                .iterator()
            ):
                saldos_por_socio[row["socio_id"]] = Decimal(str(row["total"] or 0))
        except Exception:
            pass

        socios_base_qs = Socio.objects.filter(is_enabled=True).select_related("subcomision")
        if sub_id_int:
            socios_base_qs = socios_base_qs.filter(subcomision_id=sub_id_int)

        socios_alerta_preventiva = 0
        socios_riesgo_estatutario = 0

        puntos_pos_sum = Decimal("0.00")
        puntos_neg_sum = Decimal("0.00")

        # Balance de puntos filtrado por subcomisión si aplica
        try:
            pa_filter_qs = PuntajeAplicado.objects.all()
            if sub_id_int:
                pa_filter_qs = pa_filter_qs.filter(socio_id__in=socios_base_qs.values("id"))
            p_pos = pa_filter_qs.filter(puntajeAplicado__gt=0).aggregate(s=Sum("puntajeAplicado"))[
                "s"
            ] or Decimal("0.00")
            p_neg = pa_filter_qs.filter(puntajeAplicado__lt=0).aggregate(s=Sum("puntajeAplicado"))[
                "s"
            ] or Decimal("0.00")
            puntos_pos_sum = Decimal(str(p_pos))
            puntos_neg_sum = Decimal(str(p_neg))
        except Exception:
            pass

        saldo_neto_total = puntos_pos_sum + puntos_neg_sum

        for s in socios_base_qs:
            s_saldo = saldos_por_socio.get(s.id, Decimal("0.00"))
            if s_saldo <= Decimal("-10.0"):
                socios_riesgo_estatutario += 1
            elif s_saldo <= Decimal("-7.0"):
                socios_alerta_preventiva += 1

        at_qs = AtencionFelicitacion.objects.all()
        if sub_id_int:
            at_qs = at_qs.filter(socio__subcomision_id=sub_id_int)
        llamados_atencion_total = at_qs.aggregate(s=Sum("llamadosAtencion"))["s"] or 0
        felicitaciones_total = at_qs.aggregate(s=Sum("felicitaciones"))["s"] or 0

        puntos_y_riesgo = {
            "puntos_positivos": float(puntos_pos_sum),
            "puntos_negativos": float(puntos_neg_sum),
            "saldo_neto": float(saldo_neto_total),
            "llamados_atencion_total": llamados_atencion_total,
            "felicitaciones_total": felicitaciones_total,
            "socios_alerta_preventiva": socios_alerta_preventiva,
            "socios_riesgo_estatutario": socios_riesgo_estatutario,
        }

        # 6. KPI-07: Asistencia y Validez de Eventos
        evt_qs = EventoInstitucional.objects.all()
        if desde_dt:
            evt_qs = evt_qs.filter(fecha_programada__gte=desde_dt)
        if hasta_dt:
            evt_qs = evt_qs.filter(fecha_programada__lte=hasta_dt)
        if sub_id_int:
            evt_qs = evt_qs.filter(
                Q(subcomision_id=sub_id_int) | Q(convocante__subcomision_id=sub_id_int)
            )

        total_eventos = evt_qs.count()
        eventos_finalizados = evt_qs.filter(estado=EstadoEventoEnum.FINALIZADO).count()
        eventos_no_sancionables = evt_qs.filter(es_sancionable=False).count()
        pct_no_sancionables = (
            round((eventos_no_sancionables / total_eventos) * 100, 1) if total_eventos > 0 else 0.0
        )

        asist_qs = AsistenciaEvento.objects.filter(evento__in=evt_qs)
        total_convocatorias = asist_qs.count()
        total_presentes = asist_qs.filter(
            estado_asistencia__in=[
                EstadoAsistenciaEventoEnum.PRESENTE,
                EstadoAsistenciaEventoEnum.TARDE_LEVE,
                EstadoAsistenciaEventoEnum.TARDE_GRAVE,
                EstadoAsistenciaEventoEnum.RETIRO_ANTICIPADO_LEVE,
                EstadoAsistenciaEventoEnum.RETIRO_ANTICIPADO_GRAVE,
            ]
        ).count()
        tasa_asistencia_pct = (
            round((total_presentes / total_convocatorias) * 100, 1)
            if total_convocatorias > 0
            else 0.0
        )

        eventos_resumen = {
            "total_eventos": total_eventos,
            "eventos_finalizados": eventos_finalizados,
            "total_convocatorias": total_convocatorias,
            "total_presentes": total_presentes,
            "tasa_asistencia_pct": tasa_asistencia_pct,
            "eventos_no_sancionables": eventos_no_sancionables,
            "pct_no_sancionables": pct_no_sancionables,
        }

        # 7. KPI-03: Subcomisiones Intra vs. Inter y Desglose por Concepto
        subcomisiones_qs = Subcomision.objects.all().order_by("name")
        pedidos_por_subcomision = []

        for sub in subcomisiones_qs:
            # Expedientes originados por esta subcomisión
            expedientes_sub = [e for e in expedientes_list if cls.get_origin_subcomision(e) == sub]
            total_exp_sub = len(expedientes_sub)

            expedientes_intra = 0
            expedientes_inter = 0
            imputaciones_intra = 0
            imputaciones_inter = 0
            desglose_concepto: dict[str, int] = {}

            for exp in expedientes_sub:
                soc_implicados = {exp.socio}
                for s in exp.socios.all():
                    soc_implicados.add(s)

                tiene_intra = False
                tiene_inter = False

                for s in soc_implicados:
                    if s.subcomision_id == sub.id:
                        tiene_intra = True
                        imputaciones_intra += 1
                    else:
                        tiene_inter = True
                        imputaciones_inter += 1

                if tiene_intra:
                    expedientes_intra += 1
                if tiene_inter:
                    expedientes_inter += 1

                c_code = exp.concepto or "SIN_CLASIFICAR"
                desglose_concepto[c_code] = desglose_concepto.get(c_code, 0) + 1

            pedidos_por_subcomision.append(
                {
                    "subcomision_id": sub.id,
                    "subcomision_nombre": sub.name,
                    "total_expedientes": total_exp_sub,
                    "expedientes_intra": expedientes_intra,
                    "expedientes_inter": expedientes_inter,
                    "imputaciones_intra": imputaciones_intra,
                    "imputaciones_inter": imputaciones_inter,
                    "desglose_por_concepto": desglose_concepto,
                }
            )

        # Agrupación completa por Concepto del TD
        agrupacion_por_concepto = []
        for choice_val, choice_label in ConceptoExpedienteEnum.choices:
            c_exp = [e for e in expedientes_list if e.concepto == choice_val]
            agrupacion_por_concepto.append(
                {
                    "concepto": choice_val,
                    "nombre": choice_label,
                    "total": len(c_exp),
                    "sanciones": sum(1 for e in c_exp if e.puntos < 0),
                    "meritos": sum(1 for e in c_exp if e.puntos > 0),
                    "en_tramite": sum(1 for e in c_exp if e.estado != EstadoExpedienteEnum.EMITIDO),
                    "emitidos": sum(1 for e in c_exp if e.estado == EstadoExpedienteEnum.EMITIDO),
                }
            )

        # Fila para casos pendientes de clasificar
        c_sin_clasificar = [e for e in expedientes_list if not e.concepto]
        agrupacion_por_concepto.append(
            {
                "concepto": "SIN_CLASIFICAR",
                "nombre": "Sin clasificar por el TD",
                "total": len(c_sin_clasificar),
                "sanciones": sum(1 for e in c_sin_clasificar if e.puntos < 0),
                "meritos": sum(1 for e in c_sin_clasificar if e.puntos > 0),
                "en_tramite": sum(
                    1 for e in c_sin_clasificar if e.estado != EstadoExpedienteEnum.EMITIDO
                ),
                "emitidos": sum(
                    1 for e in c_sin_clasificar if e.estado == EstadoExpedienteEnum.EMITIDO
                ),
            }
        )

        # 8. KPI-02: Pedidos por Autoridad
        authorities_map: dict[int, dict[str, Any]] = {}

        # Solicitudes T01
        sol_qs = SolicitudT01.objects.select_related("solicitante__subcomision", "expediente")
        if desde_dt:
            sol_qs = sol_qs.filter(created_at__gte=desde_dt)
        if hasta_dt:
            sol_qs = sol_qs.filter(created_at__lte=hasta_dt)
        if sub_id_int:
            sol_qs = sol_qs.filter(solicitante__subcomision_id=sub_id_int)

        for sol in sol_qs:
            aut_soc = sol.solicitante
            if not aut_soc:
                continue
            if aut_soc.id not in authorities_map:
                authorities_map[aut_soc.id] = {
                    "socio_id": aut_soc.id,
                    "nombre_completo": f"{aut_soc.last_name}, {aut_soc.first_name}",
                    "legajo": aut_soc.legajo,
                    "subcomision": aut_soc.subcomision.name
                    if aut_soc.subcomision
                    else "Sin Subcomisión",
                    "rol_display": aut_soc.get_role_display(),
                    "total_pedidos": 0,
                    "sanciones": 0,
                    "meritos": 0,
                    "en_tramite": 0,
                    "emitidos": 0,
                }
            auth = authorities_map[aut_soc.id]
            auth["total_pedidos"] += 1
            if sol.tipo_accion == SolicitudT01.TipoAccion.SANCTION:
                auth["sanciones"] += 1
            elif sol.tipo_accion == SolicitudT01.TipoAccion.MERIT:
                auth["meritos"] += 1

            if sol.expediente and sol.expediente.estado == EstadoExpedienteEnum.EMITIDO:
                auth["emitidos"] += 1
            else:
                auth["en_tramite"] += 1

        # Eventos convocados
        for evt in evt_qs.select_related("convocante__subcomision"):
            aut_soc = evt.convocante
            if not aut_soc:
                continue
            if aut_soc.id not in authorities_map:
                authorities_map[aut_soc.id] = {
                    "socio_id": aut_soc.id,
                    "nombre_completo": f"{aut_soc.last_name}, {aut_soc.first_name}",
                    "legajo": aut_soc.legajo,
                    "subcomision": aut_soc.subcomision.name
                    if aut_soc.subcomision
                    else "Sin Subcomisión",
                    "rol_display": aut_soc.get_role_display(),
                    "total_pedidos": 0,
                    "sanciones": 0,
                    "meritos": 0,
                    "en_tramite": 0,
                    "emitidos": 0,
                }
            auth = authorities_map[aut_soc.id]
            auth["total_pedidos"] += 1
            auth["sanciones"] += 1  # Convocatorias obligatorias
            if evt.estado == EstadoEventoEnum.FINALIZADO:
                auth["emitidos"] += 1
            else:
                auth["en_tramite"] += 1

        pedidos_por_autoridad = list(authorities_map.values())
        for auth in pedidos_por_autoridad:
            tot = auth["total_pedidos"]
            auth["tasa_emision_pct"] = round((auth["emitidos"] / tot) * 100, 1) if tot > 0 else 0.0

        pedidos_por_autoridad.sort(key=lambda a: a["total_pedidos"], reverse=True)

        # 9. Balance por Subcomisión y Categoría Social (Pasivo vs Activo)
        balance_subcomisiones_y_categorias = []
        for sub in subcomisiones_qs:
            socios_sub = Socio.objects.filter(subcomision=sub, is_enabled=True)
            total_socios_sub = socios_sub.count()

            p_pos_sub = Decimal("0.00")
            p_neg_sub = Decimal("0.00")
            try:
                p_pos_sub = Decimal(
                    str(
                        PuntajeAplicado.objects.filter(
                            socio_id__in=socios_sub.values("id"), puntajeAplicado__gt=0
                        ).aggregate(s=Sum("puntajeAplicado"))["s"]
                        or 0
                    )
                )
                p_neg_sub = Decimal(
                    str(
                        PuntajeAplicado.objects.filter(
                            socio_id__in=socios_sub.values("id"), puntajeAplicado__lt=0
                        ).aggregate(s=Sum("puntajeAplicado"))["s"]
                        or 0
                    )
                )
            except Exception:
                pass

            saldo_neto_sub = p_pos_sub + p_neg_sub

            alerta_sub = 0
            riesgo_sub = 0

            # Desglose de categorías Pasivo vs Activo
            pasivos_count = 0
            pasivos_alerta = 0
            pasivos_riesgo = 0
            pasivos_saldo = Decimal("0.00")

            activos_count = 0
            activos_alerta = 0
            activos_riesgo = 0
            activos_saldo = Decimal("0.00")

            for s in socios_sub:
                s_saldo = saldos_por_socio.get(s.id, Decimal("0.00"))
                is_alerta = s_saldo <= Decimal("-7.0") and s_saldo > Decimal("-10.0")
                is_riesgo = s_saldo <= Decimal("-10.0")

                if is_alerta:
                    alerta_sub += 1
                if is_riesgo:
                    riesgo_sub += 1

                if s.category == SocialCategory.PASSIVE or s.social_year < 4:
                    pasivos_count += 1
                    pasivos_saldo += s_saldo
                    if is_alerta:
                        pasivos_alerta += 1
                    if is_riesgo:
                        pasivos_riesgo += 1
                else:
                    activos_count += 1
                    activos_saldo += s_saldo
                    if is_alerta:
                        activos_alerta += 1
                    if is_riesgo:
                        activos_riesgo += 1

            balance_subcomisiones_y_categorias.append(
                {
                    "subcomision_id": sub.id,
                    "subcomision_nombre": sub.name,
                    "total_socios": total_socios_sub,
                    "puntos_positivos": float(p_pos_sub),
                    "puntos_negativos": float(p_neg_sub),
                    "saldo_neto": float(saldo_neto_sub),
                    "socios_alerta_preventiva": alerta_sub,
                    "socios_riesgo_estatutario": riesgo_sub,
                    "desglose_categorias": {
                        "pasivo": {
                            "total_socios": pasivos_count,
                            "saldo_neto": float(pasivos_saldo),
                            "alerta_preventiva": pasivos_alerta,
                            "riesgo_estatutario": pasivos_riesgo,
                        },
                        "activo": {
                            "total_socios": activos_count,
                            "saldo_neto": float(activos_saldo),
                            "alerta_preventiva": activos_alerta,
                            "riesgo_estatutario": activos_riesgo,
                        },
                    },
                }
            )

        # 10. Catálogos auxiliares
        catalogo_conceptos = [
            {"codigo": c[0], "nombre": c[1]} for c in ConceptoExpedienteEnum.choices
        ]
        catalogo_subcomisiones = [{"id": sub.id, "nombre": sub.name} for sub in subcomisiones_qs]

        return {
            "filtros_aplicados": {
                "anio": int(anio) if anio else None,
                "cuatrimestre": str(cuatrimestre) if cuatrimestre else None,
                "fecha_desde": desde_dt.date().isoformat() if desde_dt else None,
                "fecha_hasta": hasta_dt.date().isoformat() if hasta_dt else None,
                "subcomision_id": sub_id_int,
                "concepto": str(concepto).strip() if concepto else None,
            },
            "kpis_resumen": {
                "tiempo_vida_promedio_dias": tiempo_vida_promedio_dias,
                "total_emitidos_evaluados": total_emitidos_evaluados,
                "total_expedientes": total_expedientes,
                "en_tramite": en_tramite_count,
                "emitidos": emitidos_count,
                "sanciones": sanciones_count,
                "meritos": meritos_count,
                "sin_clasificar_concepto": sin_clasificar_count,
                "backlog_urgencia": backlog_urgencia,
                "descargos_resumen": descargos_resumen,
                "puntos_y_riesgo": puntos_y_riesgo,
                "eventos_resumen": eventos_resumen,
            },
            "pedidos_por_subcomision": pedidos_por_subcomision,
            "agrupacion_por_concepto": agrupacion_por_concepto,
            "pedidos_por_autoridad": pedidos_por_autoridad,
            "balance_subcomisiones_y_categorias": balance_subcomisiones_y_categorias,
            "catalogo_conceptos": catalogo_conceptos,
            "catalogo_subcomisiones": catalogo_subcomisiones,
        }
