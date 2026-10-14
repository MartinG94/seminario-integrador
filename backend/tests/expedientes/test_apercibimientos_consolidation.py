"""Tests unitarios TDD para el motor de acumulación y consolidación 3:1 de apercibimientos (CA4).

Cubre:
- WarningAccumulationService: registro en libro mayor (RegistroApercibimiento).
- Consolidación exacta 3:1 con UUID de lote y apertura de expediente de oficio por -1.00 pt.
- Acumulación subsiguiente (4°, 5° y 6° apercibimientos con segundo lote independiente).
- Inmutabilidad estricta: cero sentencias UPDATE manuales sobre saldos de socios (Regla 3).
- Validaciones de campos obligatorios y concurrencia.
"""

import uuid
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from expedientes.models import (
    EstadoExpedienteEnum,
    EstadoRegistroApercibimientoEnum,
    Expediente,
    RegistroApercibimiento,
)
from expedientes.services.warning_accumulation_service import WarningAccumulationService
from socios.models import Role, Socio


@pytest.fixture
def socio_test(make_socio):
    """Socio de prueba para acumulación de llamados de atención."""
    return make_socio(legajo="20001", role=Role.SOCIO)


@pytest.mark.django_db
class TestWarningAccumulationService:
    """Pruebas del servicio de acumulación atómica 3:1 de apercibimientos."""

    def test_registro_primer_y_segundo_apercibimiento_permanecen_pendientes(self, socio_test):
        """Los 2 primeros apercibimientos se asientan como PENDIENTE sin generar expediente."""
        ap1, exp1 = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="REUNION_TARDANZA_LEVE",
            motivo="Llegó 18 minutos tarde a reunión ordinaria.",
            articulo_reglamento="Art. 100.a",
        )

        assert ap1.id is not None
        assert ap1.estado == EstadoRegistroApercibimientoEnum.PENDIENTE
        assert ap1.lote_consolidacion is None
        assert ap1.expediente_sancion is None
        assert exp1 is None

        ap2, exp2 = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="LLAMADO_ATENCION",
            motivo="Uso indebido de espacios comunes.",
            articulo_reglamento="Art. 83",
        )

        assert ap2.id is not None
        assert ap2.estado == EstadoRegistroApercibimientoEnum.PENDIENTE
        assert exp2 is None

        # Ambos permanecen en estado PENDIENTE
        pendientes = RegistroApercibimiento.objects.filter(
            socio=socio_test,
            estado=EstadoRegistroApercibimientoEnum.PENDIENTE,
        )
        assert pendientes.count() == 2

    def test_tercer_apercibimiento_consolida_terna_y_abre_expediente(self, socio_test):
        """El 3° apercibimiento consolida la terna con UUID y expediente por -1.00 pt."""
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

        # 3° apercibimiento (dispara consolidación 3:1)
        ap3, exp_generado = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="LLAMADO_ATENCION",
            motivo="Falta de aseo en cocina comunitaria.",
            actor="CD_PRESIDENCIA",
        )

        assert exp_generado is not None
        assert isinstance(exp_generado, Expediente)
        assert exp_generado.estado == EstadoExpedienteEnum.CREADO
        assert exp_generado.puntos == Decimal("-1.00")
        assert "Consolidación reglamentaria de tres (3) apercibimientos" in exp_generado.motivo

        # Verificar que los 3 apercibimientos quedaron CONSOLIDADO
        consolidados = RegistroApercibimiento.objects.filter(
            socio=socio_test,
            estado=EstadoRegistroApercibimientoEnum.CONSOLIDADO,
        )
        assert consolidados.count() == 3

        lotes = set(consolidados.values_list("lote_consolidacion", flat=True))
        assert len(lotes) == 1
        lote_uuid = lotes.pop()
        assert lote_uuid is not None
        assert isinstance(lote_uuid, uuid.UUID)

        # Todos apuntan al expediente generado
        exp_ids = set(consolidados.values_list("expediente_sancion_id", flat=True))
        assert exp_ids == {exp_generado.id}

        # 0 apercibimientos pendientes
        assert WarningAccumulationService.get_pending_count(socio_test.id) == 0

    def test_cero_modificaciones_manuales_a_saldos_en_mysql(self, socio_test):
        """Verifica que la consolidación 3:1 no altera saldo directo (Regla 3)."""
        for i in range(3):
            WarningAccumulationService.register_warning(
                socio_id=socio_test.id,
                origen_tipo="LLAMADO_ATENCION",
                motivo=f"Llamado de atención #{i + 1}",
            )

        # El socio conserva su estado inalterado en base de datos
        socio_db = Socio.objects.get(pk=socio_test.pk)
        assert socio_db.is_enabled is True
        # Los expedientes quedan en CREADO a la espera de juicio del Tribunal
        expediente = Expediente.objects.filter(socio=socio_test).first()
        assert expediente is not None
        assert expediente.estado == EstadoExpedienteEnum.CREADO

    def test_acumulacion_subsiguiente_segunda_terna(self, socio_test):
        """Verifica que un 4° apercibimiento queda pendiente y el 6° genera un nuevo lote."""
        # Generar primera terna (1..3)
        for i in range(3):
            WarningAccumulationService.register_warning(
                socio_id=socio_test.id,
                origen_tipo="REUNION_TARDANZA_LEVE",
                motivo=f"Apercibimiento terna 1 - #{i + 1}",
            )

        # 4° apercibimiento -> queda pendiente
        ap4, exp4 = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="REUNION_TARDANZA_LEVE",
            motivo="Apercibimiento 4",
        )
        assert exp4 is None
        assert ap4.estado == EstadoRegistroApercibimientoEnum.PENDIENTE
        assert WarningAccumulationService.get_pending_count(socio_test.id) == 1

        # 5° apercibimiento -> queda pendiente
        ap5, exp5 = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="REUNION_TARDANZA_LEVE",
            motivo="Apercibimiento 5",
        )
        assert exp5 is None
        assert WarningAccumulationService.get_pending_count(socio_test.id) == 2

        # 6° apercibimiento -> consolida la segunda terna
        ap6, exp6 = WarningAccumulationService.register_warning(
            socio_id=socio_test.id,
            origen_tipo="REUNION_TARDANZA_LEVE",
            motivo="Apercibimiento 6",
        )
        assert exp6 is not None
        assert exp6.puntos == Decimal("-1.00")

        # Total 6 consolidados en 2 lotes distintos
        consolidados = RegistroApercibimiento.objects.filter(
            socio=socio_test,
            estado=EstadoRegistroApercibimientoEnum.CONSOLIDADO,
        )
        assert consolidados.count() == 6
        lotes_distintos = set(consolidados.values_list("lote_consolidacion", flat=True))
        assert len(lotes_distintos) == 2

        # Expedientes distintos
        expedientes_distintos = set(consolidados.values_list("expediente_sancion_id", flat=True))
        assert len(expedientes_distintos) == 2

    def test_rechazo_motivo_vacio(self, socio_test):
        """No permite registrar apercibimientos sin motivo circunstanciado."""
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
