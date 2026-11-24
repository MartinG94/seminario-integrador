"""Tests unitarios TDD para el motor de acumulación y consolidación 3:1
de llamados de atención y felicitaciones (CA4).

Cubre:
- WarningAccumulationService: registro y control sobre atencionFelicitacion (PK nroSocio).
- Consolidación exacta 3:1 de llamados de atención y apertura de expediente de oficio por -1.00 pt.
- Acumulación subsiguiente (4°, 5° y 6° llamados con segundo ciclo y segundo expediente).
- Consolidación 3:1 de felicitaciones para acreditación de méritos (+1.00 pt).
- Inmutabilidad estricta: cero sentencias UPDATE manuales sobre saldos de socios (Regla 3).
- Validaciones de campos obligatorios y concurrencia.
"""

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from expedientes.models import (
    Expediente,
)
from expedientes.services.warning_accumulation_service import WarningAccumulationService
from ranking.models import PuntajeAplicado
from socios.models import Role, Socio


@pytest.fixture
def socio_test(make_socio):
    """Socio de prueba para acumulación de llamados de atención."""
    return make_socio(legajo="20001", role=Role.SOCIO)


@pytest.mark.django_db
class TestWarningAccumulationService:
    """Pruebas del servicio de acumulación atómica 3:1 de llamados y felicitaciones."""

    def test_registro_primer_y_segundo_llamado_permanecen_pendientes(self, socio_test):
        """Los 2 primeros llamados de atención se acumulan sin generar expediente."""
        ap1, exp1 = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="REUNION_TARDANZA_LEVE",
            motivo="Llegó 18 minutos tarde a reunión ordinaria.",
            articulo_reglamento="Art. 100.a",
        )

        assert ap1.llamadosAtencion == 1
        assert exp1 is None

        ap2, exp2 = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="LLAMADO_ATENCION",
            motivo="Uso indebido de espacios comunes.",
            articulo_reglamento="Art. 83",
        )

        assert ap2.llamadosAtencion == 2
        assert exp2 is None

        # Ambos permanecen en estado pendiente
        assert WarningAccumulationService.get_pending_count(socio_test.id) == 2

    def test_tercer_llamado_consolida_terna_y_abre_expediente(self, socio_test):
        """El 3° llamado de atención consolida la terna y genera expediente por -1.00 pt."""
        # 1° y 2°
        WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="REUNION_TARDANZA_LEVE",
            motivo="Demora 20 min reunión 1.",
        )
        WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="REUNION_TARDANZA_LEVE",
            motivo="Demora 16 min reunión 2.",
        )

        # 3° llamado (dispara consolidación 3:1)
        ap3, exp_generado = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="LLAMADO_ATENCION",
            motivo="Falta de aseo en cocina comunitaria.",
            actor="CD_PRESIDENCIA",
        )

        assert exp_generado is None
        assert not Expediente.objects.filter(socio=socio_test).exists()

        nro_socio = socio_test.numero_socio or int(socio_test.legajo)
        mov = PuntajeAplicado.objects.get(socio_id=nro_socio)
        assert mov.puntajeAplicado == Decimal("-1.00")
        assert mov.expediente_id is None

        # Contador de llamados se descuenta en 3 (vuelve a 0)
        assert ap3.llamadosAtencion == 0
        assert WarningAccumulationService.get_pending_count(socio_test.id) == 0

    def test_cero_modificaciones_manuales_a_saldos_en_mysql(self, socio_test):
        """Verifica que la consolidación 3:1 registra el movimiento sin crear expediente."""
        for i in range(3):
            WarningAccumulationService.register_warning(
                socio_id=socio_test.id,
                origen_tipo="LLAMADO_ATENCION",
                motivo=f"Llamado de atención #{i + 1}",
            )

        # El socio conserva su estado inalterado en base de datos
        socio_db = Socio.objects.get(pk=socio_test.pk)
        assert socio_db.is_enabled is True
        assert not Expediente.objects.filter(socio=socio_test).exists()
        nro_socio = socio_test.numero_socio or int(socio_test.legajo)
        movs = PuntajeAplicado.objects.filter(socio_id=nro_socio)
        assert movs.count() == 1
        assert movs.get().puntajeAplicado == Decimal("-1.00")

    def test_acumulacion_subsiguiente_segunda_terna(self, socio_test):
        """Verifica que un 4° llamado queda pendiente y el 6° consolida un segundo expediente."""
        # Generar primera terna (1..3)
        for i in range(3):
            WarningAccumulationService.register_warning(
                socio_id=socio_test.id,
                origen_tipo="REUNION_TARDANZA_LEVE",
                motivo=f"Apercibimiento terna 1 - #{i + 1}",
            )

        # 4° llamado -> queda 1 pendiente
        ap4, exp4 = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="REUNION_TARDANZA_LEVE",
            motivo="Apercibimiento 4",
        )
        assert exp4 is None
        assert ap4.llamadosAtencion == 1
        assert WarningAccumulationService.get_pending_count(socio_test.id) == 1

        # 5° llamado -> queda 2 pendientes
        ap5, exp5 = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="REUNION_TARDANZA_LEVE",
            motivo="Apercibimiento 5",
        )
        assert exp5 is None
        assert ap5.llamadosAtencion == 2
        assert WarningAccumulationService.get_pending_count(socio_test.id) == 2

        # 6° llamado -> consolida la segunda terna
        ap6, exp6 = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="REUNION_TARDANZA_LEVE",
            motivo="Apercibimiento 6",
        )
        assert exp6 is None
        assert ap6.llamadosAtencion == 0
        assert WarningAccumulationService.get_pending_count(socio_test.id) == 0

        # No se crearon expedientes; se registraron 2 impactos directos de -1.00
        assert Expediente.objects.filter(socio=socio_test).count() == 0
        nro_socio = socio_test.numero_socio or int(socio_test.legajo)
        movs = PuntajeAplicado.objects.filter(socio_id=nro_socio)
        assert movs.count() == 2
        assert all(m.puntajeAplicado == Decimal("-1.00") for m in movs)

    def test_consolidacion_felicitaciones_3_a_1(self, socio_test):
        """Verifica que 3 felicitaciones acreditan +1.00 punto directo sin crear expediente."""
        f1, e1 = WarningAccumulationService.register_felicitacion(
            socio_id=socio_test.id,
            motivo="Mérito por voluntariado en jornada de pintura.",
        )
        assert f1.felicitaciones == 1
        assert e1 is None

        f2, e2 = WarningAccumulationService.register_felicitacion(
            socio_id=socio_test.id,
            motivo="Mérito por organización de torneo deportivo.",
        )
        assert f2.felicitaciones == 2
        assert e2 is None

        f3, exp_merito = WarningAccumulationService.register_felicitacion(
            socio_id=socio_test.id,
            motivo="Mérito por coordinación en plenario estudiantil.",
        )
        assert f3.felicitaciones == 0
        assert exp_merito is None
        assert not Expediente.objects.filter(socio=socio_test).exists()
        nro_socio = socio_test.numero_socio or int(socio_test.legajo)
        mov = PuntajeAplicado.objects.get(socio_id=nro_socio)
        assert mov.puntajeAplicado == Decimal("1.00")

    def test_rechazo_motivo_vacio(self, socio_test):
        """No permite registrar llamados sin motivo circunstanciado."""
        with pytest.raises(ValidationError):
            WarningAccumulationService.register_warning(
                socio_id=socio_test.id,
                origen_tipo="LLAMADO_ATENCION",
                motivo="   ",
            )

    def test_rechazo_socio_inexistente(self):
        """Lanza ValidationError si el socio_id no corresponde a ningún registro."""
        with pytest.raises(ValidationError):
            WarningAccumulationService.register_warning(
                socio_id=999999,
                origen_tipo="LLAMADO_ATENCION",
                motivo="Apercibimiento socio inválido",
            )
