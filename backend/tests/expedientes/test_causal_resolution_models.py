"""Pruebas del registro inmutable y versionado de decisiones por causal (S4-02, CA3)."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from expedientes.models import DecisionCausalDescargo, DecisionCausalEnum


def _create(descargo, autor, version: int = 1) -> DecisionCausalDescargo:
    return DecisionCausalDescargo.objects.create(
        expediente=descargo.expediente,
        descargo=descargo,
        version=version,
        decision=DecisionCausalEnum.ACCEPTED,
        regla_sugerida=DecisionCausalEnum.ACCEPTED,
        descargo_snapshot={"causal": descargo.causal},
        autor=autor,
        autor_legajo="76002",
        autor_rol="TD",
    )


@pytest.mark.django_db
class TestDecisionCausalModel:
    def test_persists_author_date_and_version(self, causal_descargo, causal_vocal) -> None:
        decision = _create(causal_descargo, causal_vocal.user)

        assert decision.version == 1
        assert decision.autor == causal_vocal.user
        assert decision.created_at is not None

    def test_registered_decision_cannot_be_modified(self, causal_descargo, causal_vocal) -> None:
        decision = _create(causal_descargo, causal_vocal.user)
        decision.decision = DecisionCausalEnum.REJECTED

        with pytest.raises(ValidationError):
            decision.save()

        decision.refresh_from_db()
        assert decision.decision == DecisionCausalEnum.ACCEPTED

    def test_registered_decision_cannot_be_deleted(self, causal_descargo, causal_vocal) -> None:
        decision = _create(causal_descargo, causal_vocal.user)

        with pytest.raises(ValidationError):
            decision.delete()

        assert DecisionCausalDescargo.objects.filter(pk=decision.pk).exists()

    def test_version_is_unique_per_descargo(self, causal_descargo, causal_vocal) -> None:
        _create(causal_descargo, causal_vocal.user, version=1)

        with pytest.raises(IntegrityError), transaction.atomic():
            _create(causal_descargo, causal_vocal.user, version=1)

    def test_descargo_with_decisions_is_protected(self, causal_descargo, causal_vocal) -> None:
        from django.db.models import ProtectedError

        _create(causal_descargo, causal_vocal.user)

        with pytest.raises(ProtectedError):
            causal_descargo.delete()
