"""Saldo del socio, aislamiento en Mis Expedientes y publicación protegida (Spec 011, T5/T6/T8)."""

from decimal import Decimal

import pytest

from expedientes.models import (
    AuditoriaConsultaExpediente,
    DescargoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    Resolucion,
    TipoDescargoEnum,
)
from expedientes.services.ledger_service import LedgerService
from expedientes.services.resolution_service import emitir_resolucion
from socios.models import Role
from tests.expedientes.test_ledger_service import ProveedorCerrado

pytestmark = pytest.mark.django_db

MIS = "/api/v1/expedientes/mis-expedientes/"
SALDO = "/api/v1/expedientes/mis-expedientes/saldo/"


def _publicada(expediente_id: int) -> str:
    return f"/api/v1/expedientes/{expediente_id}/resolucion/publicada/"


@pytest.fixture
def escenario(make_socio):
    """Causa compartida por A y B, con descargo médico de B y resolución emitida."""
    vocal = make_socio(legajo="78010", role=Role.TD, social_year=5, numero_socio=78010)
    a = make_socio(legajo="78001", numero_socio=78001)
    b = make_socio(legajo="78002", role=Role.CD, social_year=5, numero_socio=78002)
    ajeno = make_socio(legajo="78003", numero_socio=78003)
    expediente = Expediente.objects.create(
        numero="EXP-0950/2026",
        titulo="Inasistencia a plenario",
        socio=a,
        motivo="Faltaron a la reunión",
        puntos=Decimal("-2.00"),
        estado=EstadoExpedienteEnum.REVISION_RESOLUCION,
    )
    expediente.socios.add(a, b)
    DescargoExpediente.objects.create(
        expediente=expediente,
        socio=b,
        tipo=TipoDescargoEnum.T02_CERTIFICADO,
        causal="Certificado médico",
        texto="Estuve internado por una cirugía.",
    )
    resolucion = Resolucion.objects.create(
        expediente=expediente,
        numero_expediente_snapshot=expediente.numero,
        vistos="El expediente de referencia.",
        considerandos="Faltaron sin aviso. El socio B presentó certificado médico por cirugía.",
        articulos_resolutivos="Art. 1: Aplicar -2 puntos a los socios involucrados.",
        reglamentos_respaldantes=["Art. 83 R.I."],
        firmantes=[
            {
                "user_id": vocal.user_id,
                "numero_socio": 78010,
                "legajo": "78010",
                "full_name": "Nombre Apellido78010",
                "grupo": "G59",
                "social_year": 5,
                "etiqueta": "78010 - Nombre Apellido78010 - G59",
            }
        ],
        created_by=vocal.user,
    )
    return {"vocal": vocal, "a": a, "b": b, "ajeno": ajeno, "exp": expediente, "res": resolucion}


def _emitir(escenario):
    emitir_resolucion(escenario["res"], escenario["vocal"].user, ProveedorCerrado())


class TestMisExpedientesAislamiento:
    def test_socio_ajeno_no_ve_la_causa(self, escenario, authenticate):
        client = authenticate(escenario["ajeno"])
        assert client.get(MIS).data == []
        detalle = client.get(f"/api/v1/expedientes/{escenario['exp'].id}/")
        assert detalle.status_code == 403

    def test_autoridad_imputada_solo_ve_lo_propio(self, escenario, authenticate):
        """B integra CD, pero en Mis Expedientes no ve el descargo de A ni viceversa."""
        client = authenticate(escenario["a"])
        (fila,) = client.get(MIS).data
        assert fila["descargos"] == []
        assert fila["evidencias"] == []

        client = authenticate(escenario["b"])
        (fila,) = client.get(MIS).data
        assert [d["socio_id"] for d in fila["descargos"]] == [escenario["b"].id]
        assert "decisiones_causal" not in fila["descargos"][0]

    def test_resolucion_no_emitida_no_se_expone(self, escenario, authenticate):
        (fila,) = authenticate(escenario["a"]).get(MIS).data
        # Ni siquiera el estado del borrador se revela al imputado.
        assert fila["resolucion_estado"] is None
        assert fila["considerandos"] == ""
        assert fila["firmantes_td"] == []
        assert fila["contenido_hash"] == ""
        assert fila["puntos_aplicados"] is None

    def test_resolucion_emitida_censurada_y_puntos_aplicados(self, escenario, authenticate):
        _emitir(escenario)
        (fila,) = authenticate(escenario["a"]).get(MIS).data
        assert "médico" not in fila["considerandos"]
        assert "[Dato de salud reservado]" in fila["considerandos"]
        assert "user_id" not in fila["firmantes_td"][0]
        assert fila["puntos_aplicados"] == "-2.00"
        assert fila["medida_aplicada"] is None


class TestSaldoDelSocio:
    def test_requiere_autenticacion(self, api_client):
        assert api_client.get(SALDO).status_code == 401

    def test_saldo_y_movimientos_propios(self, escenario, authenticate):
        _emitir(escenario)
        data = authenticate(escenario["a"]).get(SALDO).data
        assert data["saldo"] == "-2.00"
        assert data["llamados_pendientes"] == 0
        assert data["felicitaciones_pendientes"] == 0
        (movimiento,) = data["movimientos"]
        assert movimiento["expediente_numero"] == "EXP-0950/2026"
        assert movimiento["tipo"] == "PUNTOS_DIRECTOS"
        assert movimiento["puntos"] == "-2.00"

    def test_socio_ajeno_no_hereda_movimientos(self, escenario, authenticate):
        _emitir(escenario)
        data = authenticate(escenario["ajeno"]).get(SALDO).data
        assert data["saldo"] == "0.00"
        assert data["movimientos"] == []

    def test_llamados_pendientes(self, escenario, authenticate):
        escenario["exp"].puntos = Decimal("-0.25")
        escenario["exp"].save()
        LedgerService.registrar_resolucion(escenario["res"], escenario["vocal"].user)
        data = authenticate(escenario["a"]).get(SALDO).data
        assert data["llamados_pendientes"] == 1
        assert data["saldo"] == "0.00"


class TestPublicacion:
    def test_no_publicada_antes_de_emitir(self, escenario, authenticate):
        response = authenticate(escenario["a"]).get(_publicada(escenario["exp"].id))
        assert response.status_code == 404

    def test_tercero_no_accede(self, escenario, authenticate):
        _emitir(escenario)
        response = authenticate(escenario["ajeno"]).get(_publicada(escenario["exp"].id))
        assert response.status_code == 403

    def test_imputado_ve_publicacion_censurada_y_solo_su_impacto(self, escenario, authenticate):
        _emitir(escenario)
        response = authenticate(escenario["a"]).get(_publicada(escenario["exp"].id))
        assert response.status_code == 200
        data = response.data
        assert data["identificador"] == "RESOLUCIÓN 0950/2026"
        assert data["considerandos"] == "Faltaron sin aviso. [Dato de salud reservado]"
        assert data["contiene_datos_reservados"] is True
        assert data["integridad_verificada"] is True
        assert [i["numero_socio"] for i in data["impactos"]] == ["78001"]
        assert data["impactos"][0]["puntos"] == "-2.00"
        assert data["firmantes"][0]["etiqueta"] == "78010 - Nombre Apellido78010 - G59"
        cuerpo = str(data)
        for prohibido in ("user_id", "causal", "evidencias", "internado", "texto"):
            assert prohibido not in cuerpo
        assert AuditoriaConsultaExpediente.objects.filter(expediente=escenario["exp"]).exists()

    def test_autoridad_ve_todos_los_impactos(self, escenario, authenticate):
        _emitir(escenario)
        data = authenticate(escenario["vocal"]).get(_publicada(escenario["exp"].id)).data
        assert sorted(i["numero_socio"] for i in data["impactos"]) == ["78001", "78002"]
        assert "[Dato de salud reservado]" in data["considerandos"]

    def test_pdf_censurado(self, escenario, authenticate):
        _emitir(escenario)
        response = authenticate(escenario["a"]).get(_publicada(escenario["exp"].id) + "pdf/")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert b"cirug" not in response.content
        assert b"BORRADOR" not in response.content


# --- Revisión PR #79: aislamiento multi-socio, autoridad imputada y publicación ---

DETALLE = "/api/v1/expedientes/{}/"
VERSIONES = "/api/v1/expedientes/{}/descargo/versiones/"
EVIDENCIA = "/api/v1/expedientes/{}/evidencia/{}/"


@pytest.fixture
def con_descargos(escenario, make_evidencia):
    """A y B con descargo y comprobante propios; la causal de B fue aceptada por el TD."""
    from expedientes.models import DecisionCausalDescargo

    exp = escenario["exp"]
    descargo_a = DescargoExpediente.objects.create(
        expediente=exp,
        socio=escenario["a"],
        tipo=TipoDescargoEnum.T02_CERTIFICADO,
        causal="Examen académico",
        texto="Rendí un parcial.",
    )
    descargo_b = DescargoExpediente.objects.get(expediente=exp, socio=escenario["b"])
    ev_a = make_evidencia(exp, escenario["a"], descargo=descargo_a, nombre="parcial.pdf")
    ev_b = make_evidencia(exp, escenario["b"], descargo=descargo_b, nombre="cirugia.pdf")
    DecisionCausalDescargo.objects.create(
        expediente=exp,
        descargo=descargo_b,
        version=1,
        decision="ACCEPTED",
        regla_sugerida="ACCEPTED",
        descargo_snapshot={"puntaje_final": "0.0"},
        autor=escenario["vocal"].user,
        autor_legajo=escenario["vocal"].legajo,
        autor_rol=escenario["vocal"].role,
    )
    DescargoExpediente.objects.filter(pk=descargo_b.pk).update(puntaje_ratificado="0.0")
    return {**escenario, "ev_a": ev_a, "ev_b": ev_b, "descargo_a": descargo_a}


class TestAislamientoMultiSocio:
    def test_justificacion_aceptada_del_coimputado_no_se_filtra(self, con_descargos, authenticate):
        _emitir(con_descargos)
        (fila_a,) = authenticate(con_descargos["a"]).get(MIS).data
        assert fila_a["justificacion_aprobada"] is False
        (fila_b,) = authenticate(con_descargos["b"]).get(MIS).data
        assert fila_b["justificacion_aprobada"] is True

    def test_valoracion_reservada_antes_de_emitir(self, con_descargos, authenticate):
        (fila_b,) = authenticate(con_descargos["b"]).get(MIS).data
        (descargo,) = fila_b["descargos"]
        assert descargo["leido"] is False
        assert descargo["puntaje_ratificado"] is None
        assert fila_b["justificacion_aprobada"] is False

    def test_autoridad_imputada_sin_parametro_origen_solo_ve_lo_propio(
        self, con_descargos, authenticate
    ):
        """B integra CD: sin ?origen= no accede a lo de A ni a lo reservado."""
        client = authenticate(con_descargos["b"])
        data = client.get(DETALLE.format(con_descargos["exp"].id)).data
        assert [d["socio_id"] for d in data["descargos"]] == [con_descargos["b"].id]
        assert "decisiones_causal" not in data["descargos"][0]
        assert {e["nombre_original"] for e in data["evidencias"]} == {"cirugia.pdf"}
        assert data["considerandos"] == ""  # borrador DRAFT no visible

    def test_autoridad_imputada_no_lista_versiones_ajenas(self, con_descargos, authenticate):
        response = authenticate(con_descargos["b"]).get(VERSIONES.format(con_descargos["exp"].id))
        assert response.status_code == 200
        assert all(v.get("socio_id") != con_descargos["a"].id for v in response.data)

    def test_autoridad_imputada_no_descarga_comprobantes_ajenos(self, con_descargos, authenticate):
        client = authenticate(con_descargos["b"])
        exp_id = con_descargos["exp"].id
        assert client.get(EVIDENCIA.format(exp_id, con_descargos["ev_a"].id)).status_code == 403
        assert client.get(EVIDENCIA.format(exp_id, con_descargos["ev_b"].id)).status_code == 200

    def test_socio_no_descarga_comprobante_del_coimputado(self, con_descargos, authenticate):
        client = authenticate(con_descargos["a"])
        exp_id = con_descargos["exp"].id
        assert client.get(EVIDENCIA.format(exp_id, con_descargos["ev_b"].id)).status_code == 403

    def test_autoridad_no_imputada_conserva_la_vista_completa(self, con_descargos, authenticate):
        client = authenticate(con_descargos["vocal"])
        data = client.get(DETALLE.format(con_descargos["exp"].id)).data
        assert {d["socio_id"] for d in data["descargos"]} == {
            con_descargos["a"].id,
            con_descargos["b"].id,
        }
        assert all("decisiones_causal" in d for d in data["descargos"])


class TestPublicacionProtegida:
    def test_impactos_sin_identificadores_internos(self, escenario, authenticate):
        _emitir(escenario)
        data = authenticate(escenario["vocal"]).get(_publicada(escenario["exp"].id)).data
        assert all("socio_id" not in impacto for impacto in data["impactos"])
        assert data["firmantes"][0]["numero_socio"] == "78010"

    def test_titulo_censurado_cuenta_como_dato_reservado(self, escenario, authenticate):
        Expediente.objects.filter(pk=escenario["exp"].id).update(
            titulo="Inasistencia por cirugía programada"
        )
        Resolucion.objects.filter(pk=escenario["res"].pk).update(considerandos="Sin datos.")
        _emitir(escenario)
        data = authenticate(escenario["a"]).get(_publicada(escenario["exp"].id)).data
        assert "cirug" not in data["titulo"]
        assert data["contiene_datos_reservados"] is True
        (fila,) = authenticate(escenario["a"]).get(MIS).data
        assert "cirug" not in fila["titulo"]

    def test_pdf_con_encabezados_seguros_y_contenido_oficial(self, escenario, authenticate):
        numero = 'EXP-0950/2026";x'
        Expediente.objects.filter(pk=escenario["exp"].id).update(numero=numero)
        Resolucion.objects.filter(pk=escenario["res"].pk).update(numero_expediente_snapshot=numero)
        _emitir(escenario)
        response = authenticate(escenario["a"]).get(_publicada(escenario["exp"].id) + "pdf/")
        assert response.status_code == 200
        assert response["X-Content-Type-Options"] == "nosniff"
        disposicion = response["Content-Disposition"]
        assert disposicion == 'attachment; filename="resolucion-EXP-0950-2026-x.pdf"'
        contenido = response.content
        assert b"IMPACTO POR SOCIO" in contenido
        assert b"REGLAMENTOS RESPALDANTES" in contenido
        assert b"Integridad del contenido" in contenido
        assert b"78001" in contenido
        assert AuditoriaConsultaExpediente.objects.filter(
            expediente=escenario["exp"], tipo_acceso="DESCARGA_PDF"
        ).exists()

    def test_auditoria_es_de_solo_insercion_y_valida_la_ip(self, escenario, authenticate):
        from django.core.exceptions import ValidationError

        _emitir(escenario)
        authenticate(escenario["a"]).get(
            _publicada(escenario["exp"].id), HTTP_X_FORWARDED_FOR="no-es-una-ip, 10.0.0.1"
        )
        registro = AuditoriaConsultaExpediente.objects.get(expediente=escenario["exp"])
        assert registro.tipo_acceso == "CONSULTA"
        assert registro.ip_address == "127.0.0.1"
        with pytest.raises(ValidationError):
            AuditoriaConsultaExpediente.objects.filter(pk=registro.pk).update(rol="ADMIN")
        with pytest.raises(ValidationError):
            AuditoriaConsultaExpediente.objects.all().delete()
