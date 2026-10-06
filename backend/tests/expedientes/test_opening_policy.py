"""Pruebas unitarias para OpeningPolicy, NotificationSanitizer y Template.

Valida:
- CA2: Resguardo de privacidad y prohibición estricta de términos médicos o sensibles.
- Principio 6: Fallo cerrado ante ambigüedades médicas o abreviaturas.
- Principio 7: No filtración de contenido sensible en mensajes de excepción.
- CA3: Idempotencia determinista de la notificación.
"""

from datetime import datetime, timezone

import pytest

from expedientes.domain.opening_policy import (
    NotificationPayload,
    NotificationSanitizer,
    OpeningNotificationTemplate,
)


class TestNotificationSanitizer:
    """Verifica la política de exclusión y fallo cerrado ante datos médicos o sensibles."""

    @pytest.mark.parametrize(
        "sensitive_text",
        [
            "Inasistencia justificada con diagnóstico de gripe",
            "Presentó licencia médica por 72 horas",
            "El socio aduce una enfermedad respiratoria",
            "Causa por patología crónica declarada",
            "Certificado de atención médica en guardia",
            "Tratamiento médico en curso",
            "Síntoma febril durante la jornada",
            "Reposo médico prescrito",
            "Historia clínica confidencial",
            "Aislamiento por contagio de covid",
        ],
    )
    def test_sanitizer_rejects_obvious_medical_terms(self, sensitive_text: str) -> None:
        with pytest.raises(ValueError, match="Infracción a CA2"):
            NotificationSanitizer.assert_no_sensitive_data(sensitive_text)

    @pytest.mark.parametrize(
        "ambiguous_text",
        [
            "Ausencia acompañada de lic. médica",
            "Adjunta constancia de lic. med.",
            "Informe con diag. reservado",
            "Certificado emitido por centro de salud",
            "Tratamiento psiquiátrico en curso",
            "Derivación a atención psicológica",
            "Reposo por intervención quirúrgica",
            "Constancia de internación clínica",
            "Receta médica adjuntada",
            "Causal vinculada al estado de salud del socio",
        ],
    )
    def test_sanitizer_rejects_ambiguous_and_abbreviated_terms_fail_closed(
        self, ambiguous_text: str
    ) -> None:
        """Principio 6: Fallo cerrado ante ambigüedades o abreviaturas clínicas."""
        with pytest.raises(ValueError, match="Infracción a CA2"):
            NotificationSanitizer.assert_no_sensitive_data(ambiguous_text)

    @pytest.mark.parametrize(
        "clean_text",
        [
            "Inasistencia injustificada a la Asamblea General Ordinaria",
            "Daño a mobiliario en las instalaciones de la sede social",
            "Incumplimiento reiterado de guardias asignadas en cómputos",
            "Comportamiento antirreglamentario durante el plenario",
            "Retención indebida de equipamiento institucional",
            "Falta de entrega de balance contable en fecha reglamentaria",
        ],
    )
    def test_sanitizer_accepts_clean_institutional_motives(self, clean_text: str) -> None:
        # No debe lanzar excepción
        NotificationSanitizer.assert_no_sensitive_data(clean_text)

    def test_sanitizer_error_message_does_not_leak_entire_text(self) -> None:
        """Principio 7: El error no debe volcar el texto completo confidencial en el mensaje."""
        private_text = "El socio Juan Pérez padece de patología cardíaca severa y adjuntó estudios."
        with pytest.raises(ValueError) as exc_info:
            NotificationSanitizer.assert_no_sensitive_data(private_text)

        msg = str(exc_info.value)
        assert "Infracción a CA2" in msg
        assert "Juan Pérez" not in msg  # No filtra los nombres ni el contexto privado completo

    def test_sanitizer_handles_empty_or_none_text(self) -> None:
        """Verifica que textos vacíos no generen falsos positivos."""
        NotificationSanitizer.assert_no_sensitive_data("")


class TestOpeningNotificationTemplate:
    """Verifica la composición institucional formal de la cédula de notificación."""

    @pytest.fixture
    def sample_data(self) -> dict:
        return {
            "expediente_numero": "EXP-2026-0001",
            "socio_nombre": "Carlos Gómez",
            "motivo_caratula": "Inasistencia injustificada a jornada institucional",
            "plazo_inicio_at": datetime(2026, 10, 5, 10, 0, 0, tzinfo=timezone.utc),
            "plazo_limite_at": datetime(2026, 10, 12, 10, 0, 0, tzinfo=timezone.utc),
            "frontend_url": "https://tribunal.aveit.utn.edu.ar/",
            "expediente_id": 42,
            "socio_id": 105,
        }

    def test_template_renders_payload_with_all_required_elements(self, sample_data: dict) -> None:
        payload = OpeningNotificationTemplate.render(**sample_data)

        assert isinstance(payload, NotificationPayload)

        # Asunto formal
        assert (
            payload.subject == "[SGD-AVEIT] Notificación de Apertura de Causa — Autos EXP-2026-0001"
        )

        # Cuerpo en texto plano
        assert "Carlos Gómez" in payload.body_text
        assert "EXP-2026-0001" in payload.body_text
        assert "Actuación disciplinaria en trámite" in payload.body_text
        # CRIT-001: El motivo en texto libre no se interpola en el correo para evitar filtraciones
        assert sample_data["motivo_caratula"] not in payload.body_text
        assert "05/10/2026 10:00" in payload.body_text
        assert "12/10/2026 10:00" in payload.body_text
        assert "cinco (5) días hábiles" in payload.body_text
        assert "Art. 12 Inc. 2" in payload.body_text
        assert "https://tribunal.aveit.utn.edu.ar/mis-expedientes/42" in payload.body_text
        assert "Tribunal de Disciplina — A.V.E.I.T. (UTN FRC)" in payload.body_text

        # Versión HTML
        assert "EXP-2026-0001" in payload.body_html
        assert "Carlos Gómez" in payload.body_html
        assert sample_data["motivo_caratula"] not in payload.body_html
        assert "https://tribunal.aveit.utn.edu.ar/mis-expedientes/42" in payload.body_html
        assert "#0b3c5d" in payload.body_html  # Color institucional AVEIT de DESIGN.md

        # Idempotencia y metadatos (BAJO-002)
        assert payload.idempotency_key == "opening-expediente-42-socio-105"
        assert payload.metadata == {
            "expediente_id": 42,
            "socio_id": 105,
            "tipo_notificacion": "APERTURA_EXPEDIENTE",
            "expediente_numero": "EXP-2026-0001",
        }

    def test_template_sanitizes_motivo_before_rendering(self, sample_data: dict) -> None:
        sample_data["motivo_caratula"] = "Inasistencia acompañada de licencia médica"
        with pytest.raises(ValueError, match="Infracción a CA2"):
            OpeningNotificationTemplate.render(**sample_data)

    def test_idempotency_key_deterministic_and_unique(self, sample_data: dict) -> None:
        payload1 = OpeningNotificationTemplate.render(**sample_data)
        payload2 = OpeningNotificationTemplate.render(**sample_data)
        assert payload1.idempotency_key == payload2.idempotency_key

        sample_data_other_socio = dict(sample_data, socio_id=106)
        payload_other = OpeningNotificationTemplate.render(**sample_data_other_socio)
        assert payload1.idempotency_key != payload_other.idempotency_key

        sample_data_other_exp = dict(sample_data, expediente_id=43)
        payload_other_exp = OpeningNotificationTemplate.render(**sample_data_other_exp)
        assert payload1.idempotency_key != payload_other_exp.idempotency_key
