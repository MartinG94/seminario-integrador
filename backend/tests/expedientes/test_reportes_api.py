"""Suite Integral de Pruebas Automatizadas para el Motor Analítico y Endpoints (SCRUM-63).

Verifica:
1. RBAC estricto: 401 unauthenticated, 403 para SOCIO, 200 para TD, CD, FISCALIZADORA, ADMIN.
2. Exactitud matemática de los 7 KPIs (KPI-01 a KPI-07):
   - KPI-01: Tiempo de vida promedio en días corridos sobre expedientes emitidos.
   - KPI-02: Pedidos por autoridad solicitante y convocante con tasa de emisión.
   - KPI-03: Subcomisiones intra vs. inter y desglose por concepto TD.
   - KPI-04: Backlog activo por nivel de urgencia y estado.
   - KPI-05: Tasa de presentación y aceptación de descargos T02/T03 y apelaciones.
   - KPI-06: Balance de puntos desde PuntajeAplicado, regla 3:1 y socios en alerta y riesgo.
   - KPI-07: Asistencia a eventos institucionales y porcentaje de eventos no sancionables.
3. Filtros temporales (año, cuatrimestre, fecha) y dimensionales (subcomisión, concepto).
4. Exportación en CSV: cabeceras, UTF-8 BOM, Content-Disposition y cabecera X-Report-SHA256.
"""

import hashlib
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import (
    AdecuacionT01,
    ApelacionT01,
    AsistenciaEvento,
    AtencionFelicitacion,
    CambioEstadoExpediente,
    CategoriaEventoEnum,
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
from padron.models import Socio as PadronSocio
from padron.models import Subcomision as PadronSubcomision
from ranking.models import PuntajeAplicado
from socios.models import Role, Socio, Subcomision
from tests.legacy_schema import create_legacy_record

User = get_user_model()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def sub_computos(db) -> Subcomision:
    sub, _ = Subcomision.objects.get_or_create(name="Cómputos")
    return sub


@pytest.fixture
def sub_gsa(db) -> Subcomision:
    sub, _ = Subcomision.objects.get_or_create(name="GSA")
    return sub


@pytest.fixture
def users_by_role(db, sub_computos):
    roles = {
        "socio": Role.SOCIO,
        "td": Role.TD,
        "cd": Role.CD,
        "fiscalizadora": Role.FISCALIZADORA,
        "admin": Role.ADMIN,
    }
    created = {}
    for role_key, role_val in roles.items():
        user = User.objects.create_user(
            username=f"user_{role_key}",
            email=f"{role_key}@aveit.test",
            password="TestPassword123!",
        )
        socio = Socio.objects.create(
            user=user,
            legajo=f"LEG_{role_key.upper()}",
            first_name="Test",
            last_name=role_key.capitalize(),
            email=user.email,
            subcomision=sub_computos,
            social_year=5,
            role=role_val,
            is_enabled=True,
        )
        created[role_key] = {"user": user, "socio": socio}
    return created


@pytest.mark.django_db
class TestReportesRBAC:
    """Verifica el cumplimiento de RBAC en servidor para los endpoints de reportes."""

    URL_RESUMEN = "/api/v1/expedientes/reportes/resumen/"
    URL_CSV = "/api/v1/expedientes/reportes/exportar-csv/"

    def test_unauthenticated_request_returns_401(self, api_client):
        res_resumen = api_client.get(self.URL_RESUMEN)
        assert res_resumen.status_code == status.HTTP_401_UNAUTHORIZED

        res_csv = api_client.get(self.URL_CSV)
        assert res_csv.status_code == status.HTTP_401_UNAUTHORIZED

    def test_socio_role_returns_403(self, api_client, users_by_role):
        api_client.force_authenticate(user=users_by_role["socio"]["user"])

        res_resumen = api_client.get(self.URL_RESUMEN)
        assert res_resumen.status_code == status.HTTP_403_FORBIDDEN

        res_csv = api_client.get(self.URL_CSV)
        assert res_csv.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.parametrize("role_key", ["td", "cd", "fiscalizadora", "admin"])
    def test_authorized_roles_return_200(self, api_client, users_by_role, role_key):
        api_client.force_authenticate(user=users_by_role[role_key]["user"])

        res_resumen = api_client.get(self.URL_RESUMEN)
        assert res_resumen.status_code == status.HTTP_200_OK

        res_csv = api_client.get(self.URL_CSV)
        assert res_csv.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestReportesCalculosKPI:
    """Verifica la exactitud del cálculo de los 7 KPIs del módulo analítico."""

    URL_RESUMEN = "/api/v1/expedientes/reportes/resumen/"
    URL_CSV = "/api/v1/expedientes/reportes/exportar-csv/"

    def test_kpi01_tiempo_de_vida_promedio(self, api_client, users_by_role, sub_computos):
        api_client.force_authenticate(user=users_by_role["td"]["user"])
        socio_td = users_by_role["td"]["socio"]

        now = timezone.now()
        # Expediente 1: Creado hace 10 días, emitido hace 6 días (vida: 4.0 días)
        exp1 = Expediente.objects.create(
            numero="EXP-0001/2026",
            socio=socio_td,
            motivo="Prueba KPI-01 - 1",
            puntos=Decimal("-1.0"),
            estado=EstadoExpedienteEnum.EMITIDO,
            concepto=ConceptoExpedienteEnum.COMP,
        )
        Expediente.objects.filter(pk=exp1.pk).update(created_at=now - timedelta(days=10))
        c1 = CambioEstadoExpediente.objects.create(
            expediente=exp1,
            estado_anterior=EstadoExpedienteEnum.ESPERA_RESOLUCION,
            estado_nuevo=EstadoExpedienteEnum.EMITIDO,
            actor="TD",
        )
        CambioEstadoExpediente.objects.filter(pk=c1.pk).update(fecha_hora=now - timedelta(days=6))

        # Expediente 2: Creado hace 8 días, emitido hace 2 días (vida: 6.0 días)
        exp2 = Expediente.objects.create(
            numero="EXP-0002/2026",
            socio=socio_td,
            motivo="Prueba KPI-01 - 2",
            puntos=Decimal("-1.0"),
            estado=EstadoExpedienteEnum.EMITIDO,
            concepto=ConceptoExpedienteEnum.GSA,
        )
        Expediente.objects.filter(pk=exp2.pk).update(created_at=now - timedelta(days=8))
        c2 = CambioEstadoExpediente.objects.create(
            expediente=exp2,
            estado_anterior=EstadoExpedienteEnum.ESPERA_RESOLUCION,
            estado_nuevo=EstadoExpedienteEnum.EMITIDO,
            actor="TD",
        )
        CambioEstadoExpediente.objects.filter(pk=c2.pk).update(fecha_hora=now - timedelta(days=2))

        # Expediente 3: No emitido (no debe entrar en el promedio de tiempo de vida)
        Expediente.objects.create(
            numero="EXP-0003/2026",
            socio=socio_td,
            motivo="Prueba KPI-01 - En trámite",
            puntos=Decimal("-1.0"),
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            concepto=ConceptoExpedienteEnum.CD,
        )

        res = api_client.get(self.URL_RESUMEN)
        assert res.status_code == status.HTTP_200_OK
        kpis = res.data["kpis_resumen"]

        # Promedio: (4.0 + 6.0) / 2 = 5.0 días
        assert kpis["total_emitidos_evaluados"] == 2
        assert kpis["tiempo_vida_promedio_dias"] == 5.0
        assert kpis["total_expedientes"] == 3
        assert kpis["en_tramite"] == 1
        assert kpis["emitidos"] == 2

    def test_kpi02_pedidos_por_autoridad(self, api_client, users_by_role, sub_computos):
        api_client.force_authenticate(user=users_by_role["cd"]["user"])
        cd_socio = users_by_role["cd"]["socio"]
        socio_dest = users_by_role["socio"]["socio"]

        # Crear expediente emitido vinculado a SolicitudT01 sancionatoria
        exp = Expediente.objects.create(
            numero="EXP-0010/2026",
            socio=socio_dest,
            motivo="Sanción CD",
            puntos=Decimal("-2.0"),
            estado=EstadoExpedienteEnum.EMITIDO,
            concepto=ConceptoExpedienteEnum.CD,
        )
        SolicitudT01.objects.create(
            estado=SolicitudT01.Estado.ISSUED,
            solicitante=cd_socio,
            destinatario_socio_id=socio_dest.id,
            tipo_accion=SolicitudT01.TipoAccion.SANCTION,
            puntos=Decimal("-2.0"),
            expediente=exp,
        )

        # Crear solicitud en trámite de mérito
        SolicitudT01.objects.create(
            estado=SolicitudT01.Estado.ISSUED,
            solicitante=cd_socio,
            destinatario_socio_id=socio_dest.id,
            tipo_accion=SolicitudT01.TipoAccion.MERIT,
            puntos=Decimal("1.0"),
        )

        res = api_client.get(self.URL_RESUMEN)
        assert res.status_code == status.HTTP_200_OK
        aut_list = res.data["pedidos_por_autoridad"]
        cd_entry = next((a for a in aut_list if a["socio_id"] == cd_socio.id), None)
        assert cd_entry is not None
        assert cd_entry["total_pedidos"] == 2
        assert cd_entry["sanciones"] == 1
        assert cd_entry["meritos"] == 1
        assert cd_entry["emitidos"] == 1
        assert cd_entry["en_tramite"] == 1
        assert cd_entry["tasa_emision_pct"] == 50.0

    def test_kpi03_subcomisiones_intra_vs_inter_y_conceptos(
        self, api_client, users_by_role, sub_computos, sub_gsa
    ):
        api_client.force_authenticate(user=users_by_role["td"]["user"])

        soc_computos_1 = users_by_role["socio"]["socio"]
        soc_gsa_u = User.objects.create_user(
            username="soc_gsa", email="gsa_soc@aveit.test", password="Pass123!"
        )
        soc_gsa = Socio.objects.create(
            user=soc_gsa_u,
            legajo="LEG_GSA_1",
            first_name="GSA",
            last_name="Socio",
            email="gsa_soc@aveit.test",
            subcomision=sub_gsa,
            social_year=2,
            role=Role.SOCIO,
        )

        # Expediente 1: Origen Cómputos, imputado Cómputos -> INTRA
        exp_intra = Expediente.objects.create(
            numero="EXP-INTRA/2026",
            socio=soc_computos_1,
            motivo="Causa Intra",
            puntos=Decimal("-1.0"),
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            concepto=ConceptoExpedienteEnum.COMP,
        )
        SolicitudT01.objects.create(
            estado=SolicitudT01.Estado.ISSUED,
            solicitante=users_by_role["cd"]["socio"],  # Pertenece a sub_computos
            destinatario_socio_id=soc_computos_1.id,
            tipo_accion=SolicitudT01.TipoAccion.SANCTION,
            puntos=Decimal("-1.0"),
            expediente=exp_intra,
        )

        # Expediente 2: Origen Cómputos, imputado GSA -> INTER
        exp_inter = Expediente.objects.create(
            numero="EXP-INTER/2026",
            socio=soc_gsa,
            motivo="Causa Inter",
            puntos=Decimal("-1.0"),
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
            concepto=ConceptoExpedienteEnum.GSA,
        )
        SolicitudT01.objects.create(
            estado=SolicitudT01.Estado.ISSUED,
            solicitante=users_by_role["cd"]["socio"],  # Pertenece a sub_computos
            destinatario_socio_id=soc_gsa.id,
            tipo_accion=SolicitudT01.TipoAccion.SANCTION,
            puntos=Decimal("-1.0"),
            expediente=exp_inter,
        )

        # Expediente 3: Sin clasificar por el TD
        Expediente.objects.create(
            numero="EXP-UNCLASSIFIED/2026",
            socio=soc_computos_1,
            motivo="Sin clasificar",
            puntos=Decimal("-1.0"),
            estado=EstadoExpedienteEnum.CREADO,
            concepto=None,
        )

        res = api_client.get(self.URL_RESUMEN)
        assert res.status_code == status.HTTP_200_OK

        # Verificar desglose de subcomisión Cómputos
        sub_data = res.data["pedidos_por_subcomision"]
        comp_entry = next((s for s in sub_data if s["subcomision_id"] == sub_computos.id), None)
        assert comp_entry is not None
        assert comp_entry["expedientes_intra"] >= 1
        assert comp_entry["expedientes_inter"] >= 1
        assert comp_entry["imputaciones_intra"] >= 1
        assert comp_entry["imputaciones_inter"] >= 1

        # Verificar catálogo completo de conceptos presentes en la respuesta
        conceptos_data = res.data["agrupacion_por_concepto"]
        concept_keys = [c["concepto"] for c in conceptos_data]
        for choice_val, _ in ConceptoExpedienteEnum.choices:
            assert choice_val in concept_keys
        assert "SIN_CLASIFICAR" in concept_keys

        # El concepto COMP tiene al menos 1
        comp_concept = next(c for c in conceptos_data if c["concepto"] == "COMP")
        assert comp_concept["total"] >= 1

        # Sin clasificar tiene al menos 1
        unclassified_concept = next(c for c in conceptos_data if c["concepto"] == "SIN_CLASIFICAR")
        assert unclassified_concept["total"] >= 1

    def test_kpi04_backlog_por_urgencia_y_estado(self, api_client, users_by_role, sub_computos):
        api_client.force_authenticate(user=users_by_role["td"]["user"])
        soc = users_by_role["socio"]["socio"]

        Expediente.objects.create(
            numero="EXP-URG-1/2026",
            socio=soc,
            motivo="Causa urgente",
            urgencia=UrgenciaExpedienteEnum.URGENTE,
            estado=EstadoExpedienteEnum.CREADO,
        )
        Expediente.objects.create(
            numero="EXP-NORM-1/2026",
            socio=soc,
            motivo="Causa normal",
            urgencia=UrgenciaExpedienteEnum.NORMAL,
            estado=EstadoExpedienteEnum.JUSTIFICANDO,
        )
        Expediente.objects.create(
            numero="EXP-BAJA-1/2026",
            socio=soc,
            motivo="Causa baja",
            urgencia=UrgenciaExpedienteEnum.BAJA,
            estado=EstadoExpedienteEnum.ESPERA_RESOLUCION,
        )
        # Emitido: no debe computar en backlog abierto
        Expediente.objects.create(
            numero="EXP-EMIT-1/2026",
            socio=soc,
            motivo="Causa emitida",
            urgencia=UrgenciaExpedienteEnum.URGENTE,
            estado=EstadoExpedienteEnum.EMITIDO,
            concepto=ConceptoExpedienteEnum.CD,
        )

        res = api_client.get(self.URL_RESUMEN)
        assert res.status_code == status.HTTP_200_OK
        backlog = res.data["kpis_resumen"]["backlog_urgencia"]
        assert backlog["total_abiertos"] == 3
        assert backlog["urgente"] == 1
        assert backlog["normal"] == 1
        assert backlog["baja"] == 1
        assert backlog["por_estado"]["creado"] == 1
        assert backlog["por_estado"]["justificando"] == 1
        assert backlog["por_estado"]["espera_resolucion"] == 1

    def test_kpi05_descargos_decisiones_y_apelaciones(self, api_client, users_by_role):
        api_client.force_authenticate(user=users_by_role["td"]["user"])
        td_user = users_by_role["td"]["user"]
        soc = users_by_role["socio"]["socio"]

        exp = Expediente.objects.create(
            numero="EXP-DESCARGOS/2026",
            socio=soc,
            motivo="Causa para descargos",
            estado=EstadoExpedienteEnum.REVISION_RESOLUCION,
        )

        descargo_t02 = DescargoExpediente.objects.create(
            expediente=exp,
            socio=soc,
            tipo=TipoDescargoEnum.T02_CERTIFICADO,
            causal="Enfermedad",
            texto="Certificado médico adjunto",
        )

        DecisionCausalDescargo.objects.create(
            expediente=exp,
            descargo=descargo_t02,
            version=1,
            decision=DecisionCausalEnum.ACCEPTED,
            regla_sugerida=DecisionCausalEnum.ACCEPTED,
            autor=td_user,
            autor_legajo="LEG_TD",
            autor_rol="TD",
        )

        ApelacionT01.objects.create(
            expediente=exp,
            socio=soc,
            numero=1,
            texto="Apelo fundamentando desacuerdo",
        )
        AdecuacionT01.objects.create(
            expediente=exp,
            version=1,
            puntos_anteriores=Decimal("-2.0"),
            puntos_nuevos=Decimal("-1.0"),
            motivos="Adecuación por atenuantes",
            autor=td_user,
            autor_legajo="LEG_TD",
        )

        res = api_client.get(self.URL_RESUMEN)
        assert res.status_code == status.HTTP_200_OK
        desc_res = res.data["kpis_resumen"]["descargos_resumen"]
        assert desc_res["total_descargos"] == 1
        assert desc_res["descargos_t02"] == 1
        assert desc_res["decisiones_t02_total"] == 1
        assert desc_res["decisiones_t02_aceptadas"] == 1
        assert desc_res["tasa_aceptacion_t02_pct"] == 100.0
        assert desc_res["apelaciones_t01"] == 1
        assert desc_res["adecuaciones_t01"] == 1

    def test_kpi06_puntos_regla31_y_socios_en_riesgo(self, api_client, users_by_role, sub_computos):
        api_client.force_authenticate(user=users_by_role["td"]["user"])

        # Crear socio pasivo en alerta (saldo = -7.5)
        u_alerta = User.objects.create_user(
            username="u_alerta", email="alerta@aveit.test", password="P1!"
        )
        soc_alerta = Socio.objects.create(
            user=u_alerta,
            legajo="LEG_ALERTA",
            first_name="Alerta",
            last_name="Preventiva",
            email="alerta@aveit.test",
            subcomision=sub_computos,
            social_year=2,  # PASIVO
            role=Role.SOCIO,
        )

        # Crear socio activo en riesgo estatutario (saldo = -10.5)
        u_riesgo = User.objects.create_user(
            username="u_riesgo", email="riesgo@aveit.test", password="P1!"
        )
        soc_riesgo = Socio.objects.create(
            user=u_riesgo,
            legajo="LEG_RIESGO",
            first_name="Riesgo",
            last_name="Estatutario",
            email="riesgo@aveit.test",
            subcomision=sub_computos,
            social_year=5,  # ACTIVO
            role=Role.SOCIO,
        )

        # Legacy Padron records
        sub_legacy = create_legacy_record(PadronSubcomision, codSubcomision=88, nombre="Sub Legacy")
        s_leg_alerta = create_legacy_record(
            PadronSocio,
            nroSocio=soc_alerta.id,
            nombre="Alerta",
            apellido="Prev",
            subcomision=sub_legacy,
        )
        s_leg_riesgo = create_legacy_record(
            PadronSocio,
            nroSocio=soc_riesgo.id,
            nombre="Riesgo",
            apellido="Estat",
            subcomision=sub_legacy,
        )

        create_legacy_record(
            PuntajeAplicado,
            idPuntajeAplicado=8001,
            socio=s_leg_alerta,
            puntajeAplicado=Decimal("-7.50"),
        )
        create_legacy_record(
            PuntajeAplicado,
            idPuntajeAplicado=8002,
            socio=s_leg_riesgo,
            puntajeAplicado=Decimal("-10.50"),
        )

        # Contador 3:1 de atencion y felicitacion
        AtencionFelicitacion.objects.create(
            socio=soc_alerta,
            llamadosAtencion=2,
            felicitaciones=1,
        )

        res = api_client.get(self.URL_RESUMEN)
        assert res.status_code == status.HTTP_200_OK
        puntos_res = res.data["kpis_resumen"]["puntos_y_riesgo"]
        assert puntos_res["socios_alerta_preventiva"] >= 1
        assert puntos_res["socios_riesgo_estatutario"] >= 1
        assert puntos_res["llamados_atencion_total"] >= 2
        assert puntos_res["felicitaciones_total"] >= 1

        balance_subs = res.data["balance_subcomisiones_y_categorias"]
        comp_bal = next((b for b in balance_subs if b["subcomision_id"] == sub_computos.id), None)
        assert comp_bal is not None
        assert comp_bal["desglose_categorias"]["pasivo"]["alerta_preventiva"] >= 1
        assert comp_bal["desglose_categorias"]["activo"]["riesgo_estatutario"] >= 1

    def test_kpi07_asistencia_y_eventos_no_sancionables(
        self, api_client, users_by_role, sub_computos
    ):
        api_client.force_authenticate(user=users_by_role["cd"]["user"])
        cd_socio = users_by_role["cd"]["socio"]
        soc1 = users_by_role["socio"]["socio"]

        # Evento 1: Finalizado, sancionable, con 2 asistencias (1 presente, 1 ausente)
        evt_sancionable = EventoInstitucional.objects.create(
            titulo="Reunión Ordinaria",
            categoria=CategoriaEventoEnum.REUNION,
            fecha_publicacion=timezone.now() - timedelta(days=5),
            fecha_programada=timezone.now() - timedelta(days=2),
            estado=EstadoEventoEnum.FINALIZADO,
            convocante=cd_socio,
            subcomision=sub_computos,
            es_sancionable=True,
        )
        AsistenciaEvento.objects.create(
            evento=evt_sancionable,
            socio=cd_socio,
            estado_asistencia=EstadoAsistenciaEventoEnum.PRESENTE,
        )
        AsistenciaEvento.objects.create(
            evento=evt_sancionable,
            socio=soc1,
            estado_asistencia=EstadoAsistenciaEventoEnum.AUSENTE,
        )

        # Evento 2: No sancionable (es_sancionable=False)
        EventoInstitucional.objects.create(
            titulo="Reunión Fuera de Plazo",
            categoria=CategoriaEventoEnum.REUNION,
            fecha_publicacion=timezone.now() - timedelta(days=1),
            fecha_programada=timezone.now() - timedelta(hours=5),
            estado=EstadoEventoEnum.FINALIZADO,
            convocante=cd_socio,
            subcomision=sub_computos,
            es_sancionable=False,
        )

        res = api_client.get(self.URL_RESUMEN)
        assert res.status_code == status.HTTP_200_OK
        evt_res = res.data["kpis_resumen"]["eventos_resumen"]
        assert evt_res["total_eventos"] >= 2
        assert evt_res["eventos_finalizados"] >= 2
        assert evt_res["total_convocatorias"] >= 2
        assert evt_res["total_presentes"] >= 1
        assert evt_res["eventos_no_sancionables"] >= 1
        assert evt_res["pct_no_sancionables"] > 0

    def test_filtros_temporales_y_dimensionales(
        self, api_client, users_by_role, sub_computos, sub_gsa
    ):
        api_client.force_authenticate(user=users_by_role["td"]["user"])
        soc_comp = users_by_role["socio"]["socio"]

        # Crear expediente con concepto GSA
        Expediente.objects.create(
            numero="EXP-FILTER-GSA/2026",
            socio=soc_comp,
            motivo="Filtro GSA",
            concepto=ConceptoExpedienteEnum.GSA,
        )
        # Crear expediente con concepto COMP
        Expediente.objects.create(
            numero="EXP-FILTER-COMP/2026",
            socio=soc_comp,
            motivo="Filtro COMP",
            concepto=ConceptoExpedienteEnum.COMP,
        )

        # Filtrar por concepto=GSA
        res_gsa = api_client.get(self.URL_RESUMEN, {"concepto": "GSA"})
        assert res_gsa.status_code == status.HTTP_200_OK
        assert res_gsa.data["filtros_aplicados"]["concepto"] == "GSA"
        assert res_gsa.data["kpis_resumen"]["total_expedientes"] == 1

        # Filtrar por cuatrimestre 1 de 2026
        res_c1 = api_client.get(self.URL_RESUMEN, {"anio": 2026, "cuatrimestre": "1"})
        assert res_c1.status_code == status.HTTP_200_OK
        assert res_c1.data["filtros_aplicados"]["cuatrimestre"] == "1"

    def test_exportar_csv_secciones_y_headers(self, api_client, users_by_role):
        api_client.force_authenticate(user=users_by_role["admin"]["user"])

        secciones = ["subcomisiones", "autoridades", "conceptos", "balance"]
        for sec in secciones:
            res = api_client.get(self.URL_CSV, {"seccion": sec})
            assert res.status_code == status.HTTP_200_OK
            assert "text/csv; charset=utf-8" in res["Content-Type"]
            assert f'attachment; filename="reporte_{sec}_' in res["Content-Disposition"]

            # Verificación obligatoria de firma SHA-256
            sha_header = res.get("X-Report-SHA256")
            assert sha_header is not None
            expected_sha = hashlib.sha256(res.content).hexdigest()
            assert sha_header == expected_sha

            # Verificación obligatoria de UTF-8 BOM (\xef\xbb\xbf)
            assert res.content.startswith(b"\xef\xbb\xbf")
