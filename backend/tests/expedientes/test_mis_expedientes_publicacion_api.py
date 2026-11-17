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
    vocal = make_socio(legajo="78010", role=Role.TD, social_year=5)
    a = make_socio(legajo="78001")
    b = make_socio(legajo="78002", role=Role.CD, social_year=5)
    ajeno = make_socio(legajo="78003")
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
        assert fila["resolucion_estado"] == "DRAFT"
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
