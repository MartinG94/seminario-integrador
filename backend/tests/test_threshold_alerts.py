"""
Pruebas automatizadas para S5-06: Alertar umbral crítico -10 y política preventiva configurable.

Criterios de Aceptación verificados:
- CA1: Saldo negativo de 10 o más genera alerta crítica única por cruce descendente.
- CA2: Destinatario y acción siguen acto aprobado (documentando bloqueo si falta el acto).
- CA3: Umbral preventivo (-7) diferenciado, configurable y desactivable hasta Circular 001/2026.
- CA4: Reversiones reevalúan sin borrar historial previo (inmutabilidad).
- CA5: Cero información médica o sensible en alertas y metadatos.
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings

from ranking.domain.threshold_alerts import (
    ActoAprobado,
    ActoAprobadoResolver,
    AlertaSanitizer,
    EstadoDespachoAlerta,
    FaltaActoAprobadoError,
    InternalAlertRepository,
    PrivacyViolationError,
    RegistroAlerta,
    ThresholdAlertEngine,
    ThresholdAlertNotificationService,
    TipoAlerta,
    TipoCruce,
    UmbralConfig,
    get_default_from_email,
    resolver_destinatarios_alerta_critica,
)


@pytest.fixture
def config_defecto() -> UmbralConfig:
    """Configuración predeterminada: crítico -10.0, preventivo -7.0 desactivado."""
    return UmbralConfig()


@pytest.fixture
def config_preventivo_activo() -> UmbralConfig:
    """Configuración con política preventiva activada en -7.0."""
    cfg = UmbralConfig()
    cfg.activar_preventivo()
    return cfg


@pytest.fixture
def acto_aprobado_oficial() -> ActoAprobado:
    """Acto aprobado formal emitido por CD para revocación de condición de socio."""
    return ActoAprobado(
        codigo="RES-CD-2026-004",
        destinatarios=[
            "cd@aveit.test",
            "fiscalizadora@aveit.test",
            "tribunal@aveit.test",
        ],
        accion_autorizada="REVOCACION_ALTA_ASOCIATIVA_ART_93",
        fecha_aprobacion=datetime(2026, 10, 1, 10, 0),
        descripcion="Protocolo de revocación formal y notificación fehaciente bajo Art. 93 R.I.",
    )


# ==============================================================================
# CA1: Saldo negativo de 10 o más genera alerta crítica única por cruce
# ==============================================================================


class TestCruceCriticoCA1:
    """Verifica detección de cruce descendente hacia -10.0 o inferior y no duplicación."""

    def test_cruce_descendente_exacto_menos_10_genera_alerta_critica(
        self, config_defecto: UmbralConfig
    ) -> None:
        """Un saldo que pasa de -9.0 a -10.0 cruza el umbral crítico y genera alerta única."""
        res = ThresholdAlertEngine.evaluar_cruce(
            socio_id=101,
            saldo_anterior=Decimal("-9.0"),
            saldo_nuevo=Decimal("-10.0"),
            config=config_defecto,
        )

        assert res.cruce == TipoCruce.CRITICO_DESCENDENTE
        assert res.alerta_generada is not None
        assert res.alerta_generada.tipo == TipoAlerta.CRITICA
        assert res.alerta_generada.saldo_anterior == Decimal("-9.0")
        assert res.alerta_generada.saldo_nuevo == Decimal("-10.0")
        assert res.alerta_generada.umbral_evaluado == Decimal("-10.0")
        assert res.esta_en_zona_critica is True

    def test_cruce_descendente_superior_a_inferior_menos_10_genera_alerta(
        self, config_defecto: UmbralConfig
    ) -> None:
        """Un saldo que pasa de 0 a -10.5 cruza el umbral y genera alerta crítica."""
        res = ThresholdAlertEngine.evaluar_cruce(
            socio_id=102,
            saldo_anterior=Decimal("0.0"),
            saldo_nuevo=Decimal("-10.5"),
            config=config_defecto,
        )

        assert res.cruce == TipoCruce.CRITICO_DESCENDENTE
        assert res.alerta_generada is not None
        assert res.alerta_generada.tipo == TipoAlerta.CRITICA
        assert res.esta_en_zona_critica is True

    def test_permanecer_en_zona_critica_no_genera_alertas_duplicadas(
        self, config_defecto: UmbralConfig
    ) -> None:
        """Un saldo que ya estaba en -10.0 y desciende a -11.0 o -12.5 NO duplica alerta."""
        res = ThresholdAlertEngine.evaluar_cruce(
            socio_id=103,
            saldo_anterior=Decimal("-10.0"),
            saldo_nuevo=Decimal("-11.5"),
            config=config_defecto,
        )

        assert res.cruce == TipoCruce.SIN_CRUCE
        assert res.alerta_generada is None
        assert res.esta_en_zona_critica is True
        assert "no se duplica alerta" in res.motivo

    def test_permanecer_en_zona_critica_con_ajuste_positivo_leve_no_duplica(
        self, config_defecto: UmbralConfig
    ) -> None:
        """Un saldo que pasa de -12.0 a -10.5 permanece en zona crítica y no genera alerta."""
        res = ThresholdAlertEngine.evaluar_cruce(
            socio_id=103,
            saldo_anterior=Decimal("-12.0"),
            saldo_nuevo=Decimal("-10.5"),
            config=config_defecto,
        )

        assert res.cruce == TipoCruce.SIN_CRUCE
        assert res.alerta_generada is None
        assert res.esta_en_zona_critica is True

    def test_salir_de_zona_critica_y_volver_a_cruzar_permite_nueva_alerta(
        self, config_defecto: UmbralConfig
    ) -> None:
        """Salir de la zona crítica y luego descender nuevamente debe generar una nueva alerta."""
        # 1. Primer cruce hacia zona crítica
        res1 = ThresholdAlertEngine.evaluar_cruce(
            socio_id=104,
            saldo_anterior=Decimal("-8.0"),
            saldo_nuevo=Decimal("-10.0"),
            config=config_defecto,
        )
        assert res1.cruce == TipoCruce.CRITICO_DESCENDENTE
        assert res1.alerta_generada is not None
        historial = [res1.alerta_generada]

        # 2. Salida de zona crítica por acreditación o reversión a -7.5
        res2 = ThresholdAlertEngine.evaluar_cruce(
            socio_id=104,
            saldo_anterior=Decimal("-10.0"),
            saldo_nuevo=Decimal("-7.5"),
            config=config_defecto,
            historial_alertas=historial,
        )
        assert res2.cruce == TipoCruce.SALIDA_ZONA_CRITICA
        assert res2.alerta_generada is None
        assert res2.esta_en_zona_critica is False

        # 3. Nuevo cruce descendente hacia -10.5
        res3 = ThresholdAlertEngine.evaluar_cruce(
            socio_id=104,
            saldo_anterior=Decimal("-7.5"),
            saldo_nuevo=Decimal("-10.5"),
            config=config_defecto,
            historial_alertas=historial,
        )
        assert res3.cruce == TipoCruce.CRITICO_DESCENDENTE
        assert res3.alerta_generada is not None
        assert res3.alerta_generada.tipo == TipoAlerta.CRITICA
        assert res3.alerta_generada.saldo_nuevo == Decimal("-10.5")


# ==============================================================================
# CA2: Destinatario y acción siguen acto aprobado (y bloqueo documentado)
# ==============================================================================


class TestActoAprobadoCA2:
    """Verifica resolución de destinatarios oficiales y acción reglamentaria (CA2)."""

    def test_con_acto_aprobado_despacha_con_destinatarios_y_accion_oficiales(
        self, config_defecto: UmbralConfig, acto_aprobado_oficial: ActoAprobado
    ) -> None:
        """Si existe acto aprobado, la alerta toma sus destinatarios y acción autorizada."""
        resolver = ActoAprobadoResolver(acto_aprobado_oficial)

        res = ThresholdAlertEngine.evaluar_cruce(
            socio_id=201,
            saldo_anterior=Decimal("-9.5"),
            saldo_nuevo=Decimal("-10.0"),
            config=config_defecto,
            resolver_acto=resolver,
            socio_email="imputado201@aveit.test",
        )

        alerta = res.alerta_generada
        assert alerta is not None
        assert alerta.estado_despacho == EstadoDespachoAlerta.DESPACHADA
        assert "imputado201@aveit.test" in alerta.destinatarios
        for d in acto_aprobado_oficial.destinatarios:
            assert d in alerta.destinatarios
        assert alerta.accion_asociada == acto_aprobado_oficial.accion_autorizada

    def test_sin_acto_aprobado_no_bloquea_y_resuelve_destinatarios_oficiales(
        self, config_defecto: UmbralConfig
    ) -> None:
        """Sin acto aprobado, no bloquea: resuelve Socio, CD y Tribunal, con espera de acto CD."""
        resolver_vacio = ActoAprobadoResolver(None)

        res = ThresholdAlertEngine.evaluar_cruce(
            socio_id=202,
            saldo_anterior=Decimal("-5.0"),
            saldo_nuevo=Decimal("-10.0"),
            config=config_defecto,
            socio_email="socio202@aveit.test",
            resolver_acto=resolver_vacio,
        )

        alerta = res.alerta_generada
        assert alerta is not None
        assert alerta.estado_despacho == EstadoDespachoAlerta.DESPACHADA
        assert alerta.destinatarios == [
            "socio202@aveit.test",
            getattr(settings, "CD_EMAIL", "cd@example.org"),
            getattr(settings, "TRIBUNAL_EMAIL", "tribunal@example.org"),
        ]
        assert alerta.accion_asociada == "ESPERA_ACTO_RESOLUTIVO_CD"
        assert alerta.baja_automatica_aplicada is False
        assert alerta.metadata.get("canal") == "EMAIL_OUTBOX"
        assert alerta.metadata.get("notificacion_in_app") is False

    def test_resolver_destinatarios_sin_acto_aprobado_resuelve_directamente(self) -> None:
        """Resolución sin acto aprobado retorna los 3 destinatarios y ESPERA_ACTO_RESOLUTIVO_CD."""
        resolver_vacio = ActoAprobadoResolver(None)
        dests, accion = resolver_vacio.resolver_destinatario_y_accion(
            socio_email="socio@aveit.test"
        )

        assert dests == [
            "socio@aveit.test",
            getattr(settings, "CD_EMAIL", "cd@example.org"),
            getattr(settings, "TRIBUNAL_EMAIL", "tribunal@example.org"),
        ]
        assert accion == "ESPERA_ACTO_RESOLUTIVO_CD"

    def test_resolver_con_forzar_acto_permite_validar_bloqueo_si_se_solicita(self) -> None:
        """Si explícitamente se fuerza la exigencia de un acto, lanza FaltaActoAprobadoError."""
        resolver_vacio = ActoAprobadoResolver(None)
        with pytest.raises(FaltaActoAprobadoError) as exc_info:
            resolver_vacio.resolver_destinatario_y_accion(forzar_acto=True)

        assert "No existe un acto aprobado registrado" in str(exc_info.value)


# ==============================================================================
# CA3: Umbral -7 configurable y desactivable hasta validar Circular 001/2026
# ==============================================================================


class TestUmbralPreventivoConfigurableCA3:
    """Verifica que el umbral preventivo se configure y desactive sin tocar el umbral crítico."""

    def test_umbral_preventivo_desactivado_por_defecto_no_emite_alerta(
        self, config_defecto: UmbralConfig
    ) -> None:
        """Estando desactivado, cruzar -7.0 no emite alerta preventiva ni altera nada."""
        assert config_defecto.preventivo_activo is False

        res = ThresholdAlertEngine.evaluar_cruce(
            socio_id=301,
            saldo_anterior=Decimal("-6.0"),
            saldo_nuevo=Decimal("-7.0"),
            config=config_defecto,
        )

        assert res.cruce == TipoCruce.SIN_CRUCE
        assert res.alerta_generada is None
        assert res.esta_en_zona_preventiva is False

    def test_umbral_preventivo_activo_genera_alerta_preventiva(
        self, config_preventivo_activo: UmbralConfig
    ) -> None:
        """Al activarse, cruzar de -6.5 a -7.0 genera Alerta Preventiva sin tocar el crítico."""
        res = ThresholdAlertEngine.evaluar_cruce(
            socio_id=302,
            saldo_anterior=Decimal("-6.5"),
            saldo_nuevo=Decimal("-7.0"),
            config=config_preventivo_activo,
        )

        assert res.cruce == TipoCruce.PREVENTIVO_DESCENDENTE
        assert res.alerta_generada is not None
        assert res.alerta_generada.tipo == TipoAlerta.PREVENTIVA
        assert res.alerta_generada.umbral_evaluado == Decimal("-7.0")
        assert res.esta_en_zona_preventiva is True
        assert res.esta_en_zona_critica is False

    def test_umbral_preventivo_configurable_a_otro_valor(
        self, config_defecto: UmbralConfig
    ) -> None:
        """Se puede reconfigurar el umbral preventivo a -8.0 de forma personalizada."""
        config_defecto.configurar_preventivo(valor=Decimal("-8.0"), activo=True)
        assert config_defecto.umbral_preventivo == Decimal("-8.0")
        assert config_defecto.preventivo_activo is True

        # -7.0 no cruza el umbral preventivo de -8.0
        res1 = ThresholdAlertEngine.evaluar_cruce(
            socio_id=303,
            saldo_anterior=Decimal("-6.0"),
            saldo_nuevo=Decimal("-7.0"),
            config=config_defecto,
        )
        assert res1.alerta_generada is None

        # -8.0 sí cruza el umbral preventivo configurado
        res2 = ThresholdAlertEngine.evaluar_cruce(
            socio_id=303,
            saldo_anterior=Decimal("-7.0"),
            saldo_nuevo=Decimal("-8.0"),
            config=config_defecto,
        )
        assert res2.cruce == TipoCruce.PREVENTIVO_DESCENDENTE
        assert res2.alerta_generada is not None
        assert res2.alerta_generada.umbral_evaluado == Decimal("-8.0")

    def test_desactivar_preventivo_no_altera_umbral_critico(
        self, config_preventivo_activo: UmbralConfig
    ) -> None:
        """Desactivar la política preventiva mantiene 100% operativo el umbral crítico -10.0."""
        config_preventivo_activo.desactivar_preventivo()
        assert config_preventivo_activo.preventivo_activo is False

        # El umbral crítico de -10.0 debe seguir disparando de forma ineludible
        res = ThresholdAlertEngine.evaluar_cruce(
            socio_id=304,
            saldo_anterior=Decimal("-9.5"),
            saldo_nuevo=Decimal("-10.0"),
            config=config_preventivo_activo,
        )
        assert res.cruce == TipoCruce.CRITICO_DESCENDENTE
        assert res.alerta_generada is not None
        assert res.alerta_generada.tipo == TipoAlerta.CRITICA

    def test_umbral_critico_es_estricto_e_inmutable(self) -> None:
        """Intentar instanciar UmbralConfig con umbral crítico distinto de -10.0 falla."""
        with pytest.raises(ValueError, match="umbral crítico es inmutable y estatutario"):
            UmbralConfig(umbral_critico=Decimal("-12.0"))


# ==============================================================================
# CA4: Reversiones reevalúan sin borrar historial
# ==============================================================================


class TestReversionesEHistorialCA4:
    """Verifica que las reversiones reevalúen condiciones conservando el historial intacto."""

    def test_reversion_conserva_historial_anterior_integro(
        self, config_defecto: UmbralConfig
    ) -> None:
        """Una reversión que alivia el saldo de -10.5 a -8.0 no borra la alerta previa."""
        # 1. Alerta crítica inicial
        res1 = ThresholdAlertEngine.evaluar_cruce(
            socio_id=401,
            saldo_anterior=Decimal("-9.0"),
            saldo_nuevo=Decimal("-10.5"),
            config=config_defecto,
        )
        assert res1.alerta_generada is not None
        historial_inicial = [res1.alerta_generada]
        alerta_id_original = res1.alerta_generada.id

        # 2. Reversión de sanción: saldo pasa de -10.5 a -8.0
        resultado_rev, historial_actualizado = ThresholdAlertEngine.reevaluar_por_reversion(
            socio_id=401,
            saldo_anterior=Decimal("-10.5"),
            saldo_resultante=Decimal("-8.0"),
            historial_alertas=historial_inicial,
            config=config_defecto,
            motivo_reversion="Anulación de sanción indebida por Tribunal de Disciplina",
        )

        # Inmutabilidad: el historial contiene el registro original intacto
        assert len(historial_actualizado) == 1
        assert historial_actualizado[0].id == alerta_id_original
        assert historial_actualizado[0].tipo == TipoAlerta.CRITICA
        assert resultado_rev.cruce == TipoCruce.SALIDA_ZONA_CRITICA
        assert resultado_rev.esta_en_zona_critica is False

    def test_reversion_que_provoca_cruce_descendente_emite_alerta_y_agrega_al_historial(
        self, config_defecto: UmbralConfig
    ) -> None:
        """Reversión de méritos que hace caer el saldo a -11.0 genera alerta y la agrega."""
        historial_previo: list[RegistroAlerta] = []

        resultado_rev, historial_actualizado = ThresholdAlertEngine.reevaluar_por_reversion(
            socio_id=402,
            saldo_anterior=Decimal("-8.0"),
            saldo_resultante=Decimal("-11.0"),
            historial_alertas=historial_previo,
            config=config_defecto,
            motivo_reversion="Reversión de felicitación acreditada por error material",
        )

        assert resultado_rev.cruce == TipoCruce.CRITICO_DESCENDENTE
        assert resultado_rev.alerta_generada is not None
        assert resultado_rev.alerta_generada.es_reversion is True
        assert len(historial_actualizado) == 1
        assert historial_actualizado[0].saldo_nuevo == Decimal("-11.0")

    def test_reversion_y_posterior_caida_acumula_dos_alertas_en_historial(
        self, config_defecto: UmbralConfig
    ) -> None:
        """Secuencia: cruce -> reversión -> nuevo cruce = 2 alertas en historial sin pérdidas."""
        # Paso 1: Saldo cae a -10.0 -> Alerta 1
        res1 = ThresholdAlertEngine.evaluar_cruce(
            socio_id=403,
            saldo_anterior=Decimal("-9.0"),
            saldo_nuevo=Decimal("-10.0"),
            config=config_defecto,
        )
        assert res1.alerta_generada is not None
        historial = [res1.alerta_generada]

        # Paso 2: Reversión lleva saldo a -7.0 -> Sale de zona crítica
        res_rev, historial = ThresholdAlertEngine.reevaluar_por_reversion(
            socio_id=403,
            saldo_anterior=Decimal("-10.0"),
            saldo_resultante=Decimal("-7.0"),
            historial_alertas=historial,
            config=config_defecto,
            motivo_reversion="Contramovimiento formal por reconsideración T03",
        )
        assert len(historial) == 1
        assert res_rev.esta_en_zona_critica is False

        # Paso 3: Nueva sanción lleva saldo a -10.5 -> Alerta 2
        res3 = ThresholdAlertEngine.evaluar_cruce(
            socio_id=403,
            saldo_anterior=Decimal("-7.0"),
            saldo_nuevo=Decimal("-10.5"),
            config=config_defecto,
            historial_alertas=historial,
        )
        assert res3.alerta_generada is not None
        historial.append(res3.alerta_generada)

        # Historial preservó ambas alertas
        assert len(historial) == 2
        assert historial[0].saldo_nuevo == Decimal("-10.0")
        assert historial[1].saldo_nuevo == Decimal("-10.5")


# ==============================================================================
# CA5: Cero información médica en alertas y metadatos
# ==============================================================================


class TestPrivacidadMedicaCA5:
    """Verifica que ninguna alerta ni metadato contenga referencias o información médica."""

    @pytest.mark.parametrize(
        "termino_prohibido",
        [
            "diagnóstico de gastroenteritis",
            "reposo médico certificado",
            "enfermedad infecciosa",
            "licencia médica de 48 hs",
            "consulta con médico clínico",
            "síntomas febriles",
            "tratamiento psiquiátrico",
            "atención psicológica",
            "caso sospechoso de covid-19",
            "receta de fármaco",
            "internación hospitalaria",
        ],
    )
    def test_metadatos_con_datos_medicos_son_rechazados(
        self, config_defecto: UmbralConfig, termino_prohibido: str
    ) -> None:
        """Cualquier metadato o texto con información médica es rechazado."""
        with pytest.raises(PrivacyViolationError, match="Infracción a CA5"):
            ThresholdAlertEngine.evaluar_cruce(
                socio_id=501,
                saldo_anterior=Decimal("-9.0"),
                saldo_nuevo=Decimal("-10.0"),
                config=config_defecto,
                metadata_adicional={"observacion": f"Detalle: {termino_prohibido}"},
            )

    def test_motivo_reversion_con_datos_medicos_es_rechazado(
        self, config_defecto: UmbralConfig
    ) -> None:
        """El motivo de una reversión no puede incluir información médica."""
        with pytest.raises(PrivacyViolationError, match="Infracción a CA5"):
            ThresholdAlertEngine.reevaluar_por_reversion(
                socio_id=502,
                saldo_anterior=Decimal("-11.0"),
                saldo_resultante=Decimal("-8.0"),
                historial_alertas=[],
                config=config_defecto,
                motivo_reversion="Justificado por certificado médico de patología respiratoria",
            )

    def test_sanitizer_permite_metadatos_institucionales_limpios(self) -> None:
        """Metadatos estrictamente administrativos y no médicos son procesados normalmente."""
        metadatos_validos = {
            "expediente_numero": "EXP-0012/2026",
            "causal": "Inasistencia reiterada a reunión ordinaria",
            "resolucion": "RES-2026-04",
            "sistema": "SGD-AVEIT",
            "actor": "Tribunal de Disciplina",
        }
        # No debe lanzar excepción
        AlertaSanitizer.sanitize_dict(metadatos_validos)


# ==============================================================================
# Integración con ranking.services
# ==============================================================================


class TestRankingServicesIntegration:
    """Verifica que las funciones expuestas en ranking.services funcionen idénticamente."""

    def test_evaluate_socio_threshold_crossing_helper(self, config_defecto: UmbralConfig) -> None:
        from ranking.services import evaluate_socio_threshold_crossing

        res = evaluate_socio_threshold_crossing(
            socio_id=601,
            saldo_anterior=Decimal("-9.0"),
            saldo_nuevo=Decimal("-10.0"),
            config=config_defecto,
        )
        assert res.cruce == TipoCruce.CRITICO_DESCENDENTE
        assert res.alerta_generada is not None

    def test_reevaluate_socio_reversal_helper(self, config_defecto: UmbralConfig) -> None:
        from ranking.services import reevaluate_socio_reversal

        res_inicial = ThresholdAlertEngine.evaluar_cruce(
            socio_id=602,
            saldo_anterior=Decimal("-9.0"),
            saldo_nuevo=Decimal("-11.0"),
            config=config_defecto,
        )
        historial = [res_inicial.alerta_generada]

        res_rev, hist_rev = reevaluate_socio_reversal(
            socio_id=602,
            saldo_anterior=Decimal("-11.0"),
            saldo_resultante=Decimal("-8.0"),
            historial_alertas=historial,
            config=config_defecto,
            motivo_reversion="Ajuste de puntos por enmienda",
        )
        assert res_rev.cruce == TipoCruce.SALIDA_ZONA_CRITICA
        assert len(hist_rev) == 1


# ==============================================================================
# Criterio 4: Rectificaciones y preservación de historial
# ==============================================================================


class TestRectificacionesCA4:
    """Verifica que las rectificaciones de saldo reevalúen alertas sin alterar el historial."""

    def test_rectificacion_reevalua_y_preserva_historial(
        self, config_defecto: UmbralConfig
    ) -> None:
        """Una rectificación administrativa preserva alertas anteriores intactas."""
        res1 = ThresholdAlertEngine.evaluar_cruce(
            socio_id=701,
            saldo_anterior=Decimal("-9.0"),
            saldo_nuevo=Decimal("-10.0"),
            config=config_defecto,
        )
        assert res1.alerta_generada is not None
        historial = [res1.alerta_generada]

        res_rect, hist_rect = ThresholdAlertEngine.reevaluar_por_rectificacion(
            socio_id=701,
            saldo_anterior=Decimal("-10.0"),
            saldo_resultante=Decimal("-8.5"),
            historial_alertas=historial,
            config=config_defecto,
            motivo_rectificacion="Rectificación de cómputo por error aritmético en acta",
        )

        assert len(hist_rect) == 1
        assert res_rect.cruce == TipoCruce.SALIDA_ZONA_CRITICA
        assert res_rect.esta_en_zona_critica is False

    def test_rectificacion_que_cruza_hacia_zona_critica_agrega_alerta(
        self, config_defecto: UmbralConfig
    ) -> None:
        """Una rectificación desfavorable que hace descender a -10.5 genera alerta interna."""
        historial_previo: list[RegistroAlerta] = []

        res_rect, hist_rect = ThresholdAlertEngine.reevaluar_por_rectificacion(
            socio_id=702,
            saldo_anterior=Decimal("-9.5"),
            saldo_resultante=Decimal("-10.5"),
            historial_alertas=historial_previo,
            config=config_defecto,
            motivo_rectificacion="Rectificación formal de saldo por duplicidad de mérito",
        )

        assert res_rect.cruce == TipoCruce.CRITICO_DESCENDENTE
        assert res_rect.alerta_generada is not None
        assert res_rect.alerta_generada.es_rectificacion is True
        assert res_rect.alerta_generada.es_registro_interno is True
        assert len(hist_rect) == 1

    def test_motivo_rectificacion_con_datos_medicos_es_rechazado(
        self, config_defecto: UmbralConfig
    ) -> None:
        """El motivo de rectificación rechaza terminología médica (CA5 y Principio 6)."""
        with pytest.raises(PrivacyViolationError, match="Infracción a CA5"):
            ThresholdAlertEngine.reevaluar_por_rectificacion(
                socio_id=703,
                saldo_anterior=Decimal("-10.5"),
                saldo_resultante=Decimal("-8.0"),
                historial_alertas=[],
                config=config_defecto,
                motivo_rectificacion="Rectificado por certificado médico de internación",
            )


# ==============================================================================
# Criterio 7: Sin envíos externos ni bajas automáticas de socio
# ==============================================================================


class TestCriterio7SinEnviosExternosNiBajas:
    """Verifica que el alcance se restrinja a registro interno sin efectos externos colaterales."""

    def test_alerta_critica_es_registro_interno_sin_envio_externo_ni_baja(
        self, config_defecto: UmbralConfig
    ) -> None:
        """El registro crítico garantiza es_registro_interno=True, sin envíos ni baja de socio."""
        res = ThresholdAlertEngine.evaluar_cruce(
            socio_id=801,
            saldo_anterior=Decimal("-9.5"),
            saldo_nuevo=Decimal("-10.0"),
            config=config_defecto,
        )

        alerta = res.alerta_generada
        assert alerta is not None
        assert alerta.es_registro_interno is True
        assert alerta.envio_externo_realizado is False
        assert alerta.baja_automatica_aplicada is False

    def test_repositorio_interno_almacena_alertas_sin_despacho_externo(self) -> None:
        """InternalAlertRepository almacena y permite consultar el historial interno."""

        repo = InternalAlertRepository()
        assert repo.total() == 0

        res = ThresholdAlertEngine.evaluar_cruce(
            socio_id=802,
            saldo_anterior=Decimal("-9.0"),
            saldo_nuevo=Decimal("-10.5"),
            config=UmbralConfig(),
        )
        assert res.alerta_generada is not None

        repo.registrar(res.alerta_generada)
        assert repo.total() == 1
        alertas_socio = repo.obtener_por_socio(802)
        assert len(alertas_socio) == 1
        assert alertas_socio[0].saldo_nuevo == Decimal("-10.5")
        assert alertas_socio[0].envio_externo_realizado is False
        assert alertas_socio[0].baja_automatica_aplicada is False

    def test_reevaluate_socio_rectification_service_helper(
        self, config_defecto: UmbralConfig
    ) -> None:
        """Verifica la función helper expuesta en ranking.services para rectificaciones."""
        from ranking.services import reevaluate_socio_rectification

        res, hist = reevaluate_socio_rectification(
            socio_id=803,
            saldo_anterior=Decimal("-10.0"),
            saldo_resultante=Decimal("-7.0"),
            historial_alertas=[],
            config=config_defecto,
            motivo_rectificacion="Ajuste por enmienda de resolución colegiada",
        )
        assert res.cruce == TipoCruce.SALIDA_ZONA_CRITICA
        assert len(hist) == 0


# ==============================================================================
# S5-06 Revision PR #72: Configuración de correos, Outbox y Reglas PO
# ==============================================================================


class TestConfiguracionCorreos:
    """Verifica configuración de correos electrónicos en settings y helpers de resolución."""

    def test_settings_email_defaults(self) -> None:
        """Verifica los valores por defecto en settings.py según requerimiento del PO."""
        assert getattr(settings, "DEFAULT_FROM_EMAIL") == "sistema@example.org"
        assert getattr(settings, "CD_EMAIL") == "cd@example.org"
        assert getattr(settings, "TRIBUNAL_EMAIL") == "tribunal@example.org"

    def test_get_default_from_email(self) -> None:
        """Verifica que get_default_from_email retorne el remitente configurado."""
        expected_from = getattr(settings, "DEFAULT_FROM_EMAIL", "sistema@example.org")
        assert get_default_from_email() == expected_from

    def test_resolver_destinatarios_alerta_critica(self) -> None:
        """Verifica la resolución de los tres destinatarios oficiales."""
        dests = resolver_destinatarios_alerta_critica("imputado@aveit.test")
        assert dests == [
            "imputado@aveit.test",
            getattr(settings, "CD_EMAIL", "cd@example.org"),
            getattr(settings, "TRIBUNAL_EMAIL", "tribunal@example.org"),
        ]

    def test_resolver_destinatarios_alerta_critica_sin_email_socio(self) -> None:
        """Si el socio no tiene email registrado, resuelve CD y Tribunal."""
        dests = resolver_destinatarios_alerta_critica(None)
        assert dests == [
            getattr(settings, "CD_EMAIL", "cd@example.org"),
            getattr(settings, "TRIBUNAL_EMAIL", "tribunal@example.org"),
        ]


class TestOutboxYDespachoNotificacion:
    """Verifica que la notificación formal se realice por Outbox sin notificaciones in-app."""

    def test_construir_payload_outbox_formato_y_metadatos(
        self, config_defecto: UmbralConfig
    ) -> None:
        """Verifica que el payload de Outbox cumpla con metadatos, canal y privacidad."""
        res = ThresholdAlertEngine.evaluar_cruce(
            socio_id=901,
            saldo_anterior=Decimal("-9.0"),
            saldo_nuevo=Decimal("-10.0"),
            config=config_defecto,
            socio_email="socio901@aveit.test",
        )
        assert res.alerta_generada is not None
        alerta = res.alerta_generada

        payload = ThresholdAlertNotificationService.construir_payload_outbox(
            alerta, socio_nombre="Juan Pérez"
        )

        assert payload["to"] == alerta.destinatarios
        assert "Juan Pérez" in payload["body_text"]
        assert "Art. 93" in payload["body_text"]
        assert payload["metadata"]["canal"] == "EMAIL_OUTBOX"
        assert payload["metadata"]["notificacion_in_app"] is False
        expected_from = getattr(settings, "DEFAULT_FROM_EMAIL", "sistema@example.org")
        assert payload["metadata"]["remitente"] == expected_from
        assert payload["metadata"]["baja_automatica_aplicada"] is False
        assert payload["idempotency_key"] == f"threshold-alert-critica-901-{alerta.id}"

    @patch("notifications.services.EmailDispatcherService.dispatch")
    @patch("notifications.services.EmailDispatcherService.create_or_get_outbox")
    def test_despacho_outbox_con_mocks(
        self,
        mock_create: MagicMock,
        mock_dispatch: MagicMock,
        config_defecto: UmbralConfig,
    ) -> None:
        """Verifica que evaluar_cruce con despachar_outbox=True invoque el encolador y despacho."""
        mock_outbox = MagicMock()
        mock_create.return_value = (mock_outbox, True)
        mock_dispatch.return_value = True

        res = ThresholdAlertEngine.evaluar_cruce(
            socio_id=902,
            saldo_anterior=Decimal("-9.0"),
            saldo_nuevo=Decimal("-10.5"),
            config=config_defecto,
            socio_email="socio902@aveit.test",
            despachar_outbox=True,
            socio_nombre="Lucía Gómez",
        )

        assert res.alerta_generada is not None
        assert res.alerta_generada.envio_externo_realizado is True
        mock_create.assert_called_once()
        mock_dispatch.assert_called_once_with(mock_outbox)

    def test_baja_automatica_aplicada_es_falso_y_sin_mutacion_padron(
        self, config_defecto: UmbralConfig
    ) -> None:
        """Verifica que la alerta crítica garantice baja_automatica_aplicada=False."""
        res = ThresholdAlertEngine.evaluar_cruce(
            socio_id=903,
            saldo_anterior=Decimal("-8.0"),
            saldo_nuevo=Decimal("-12.0"),
            config=config_defecto,
            socio_email="socio903@aveit.test",
        )
        assert res.alerta_generada is not None
        assert res.alerta_generada.baja_automatica_aplicada is False
        assert res.alerta_generada.accion_asociada == "ESPERA_ACTO_RESOLUTIVO_CD"
