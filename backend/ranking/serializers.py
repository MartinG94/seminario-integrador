"""Serializadores para el Ranking de Socios Reconciliado (SGD-AVEIT)."""

from decimal import Decimal

from rest_framework import serializers

from ranking.models import PuntajeGeneral, Socio, Subcomision
from ranking.services import calculate_reconciliation


class RankingSocioSerializer(serializers.ModelSerializer):
    """
    Serializador que implementa el contrato RankingSocio esperado por Angular:
    - id (string / int)
    - legajo (string)
    - nombre (string)
    - apellido (string)
    - categoria ('ACTIVO' | 'PASIVO')
    - subcomision (string)
    - saldo (number)
    - saldoHistorico (number)
    - saldoPuntajeGeneral (number)
    - diferencia (number)
    - reconciliado (boolean)
    """

    id = serializers.SerializerMethodField()
    legajo = serializers.SerializerMethodField()
    nombre = serializers.CharField()
    apellido = serializers.CharField()
    categoria = serializers.SerializerMethodField()
    subcomision = serializers.SerializerMethodField()
    saldo = serializers.SerializerMethodField()
    saldoHistorico = serializers.SerializerMethodField()
    saldoPuntajeGeneral = serializers.SerializerMethodField()
    diferencia = serializers.SerializerMethodField()
    reconciliado = serializers.SerializerMethodField()

    class Meta:
        model = Socio
        fields = (
            "id",
            "legajo",
            "nombre",
            "apellido",
            "categoria",
            "subcomision",
            "saldo",
            "saldoHistorico",
            "saldoPuntajeGeneral",
            "diferencia",
            "reconciliado",
        )

    def get_id(self, obj: Socio) -> str:
        return str(obj.nroSocio)

    def get_legajo(self, obj: Socio) -> str:
        legajo_val = getattr(obj, "legajo_calc", None)
        if legajo_val is not None and str(legajo_val).strip():
            return str(legajo_val)
        # Si la instancia viene de get_reconciled_ranking_queryset (tiene legajo_calc),
        # sabemos que no tiene estudio sin disparar queries adicionales (evita N+1).
        if hasattr(obj, "legajo_calc"):
            return str(obj.nroSocio)
        # Fallback defensivo cuando la instancia no fue anotada por la función de servicio
        try:
            estudio = obj.estudios.first() if hasattr(obj, "estudios") else None
            return str(estudio.nroLegajo) if estudio else str(obj.nroSocio)
        except Exception:
            return str(obj.nroSocio)

    def get_categoria(self, obj: Socio) -> str:
        return obj.categoria

    def get_subcomision(self, obj: Socio) -> str:
        sub_calc = getattr(obj, "subcomision_nombre_calc", None)
        if sub_calc is not None and str(sub_calc).strip():
            return str(sub_calc)
        try:
            return obj.subcomision.nombre if obj.subcomision else "Sin Subcomisión"
        except (Subcomision.DoesNotExist, AttributeError):
            return "Sin Subcomisión"

    def _get_reconciliation(self, obj: Socio) -> tuple[Decimal, Decimal, Decimal, bool]:
        """Calcula o recupera del caché de instancia las cifras de reconciliación."""
        if hasattr(obj, "_cached_reconciliation"):
            return obj._cached_reconciliation

        saldo_hist = getattr(obj, "saldo_historico_calc", None)
        saldo_cache = getattr(obj, "saldo_cache_calc", None)

        if saldo_hist is None:
            saldo_hist = sum(p.puntajeAplicado for p in obj.puntajes_aplicados.all())
        if saldo_cache is None:
            try:
                saldo_cache = (
                    obj.puntaje_general.puntos
                    if hasattr(obj, "puntaje_general") and obj.puntaje_general
                    else Decimal("0.00")
                )
            except (PuntajeGeneral.DoesNotExist, AttributeError):
                saldo_cache = Decimal("0.00")

        obj._cached_reconciliation = calculate_reconciliation(saldo_hist, saldo_cache)
        return obj._cached_reconciliation

    def get_saldo(self, obj: Socio) -> Decimal:
        sh, _, _, _ = self._get_reconciliation(obj)
        return sh

    def get_saldoHistorico(self, obj: Socio) -> Decimal:
        sh, _, _, _ = self._get_reconciliation(obj)
        return sh

    def get_saldoPuntajeGeneral(self, obj: Socio) -> Decimal:
        _, sc, _, _ = self._get_reconciliation(obj)
        return sc

    def get_diferencia(self, obj: Socio) -> Decimal:
        _, _, diff, _ = self._get_reconciliation(obj)
        return diff

    def get_reconciliado(self, obj: Socio) -> bool:
        _, _, _, rec = self._get_reconciliation(obj)
        return rec
