"""Carga expedientes disciplinarios de demostración para el tablero Kanban y pruebas de UI.

Uso:
    python manage.py seed_expedientes [--clean]

Sólo corre con DEBUG=True: puebla expedientes en los seis estados canónicos del
Art. 12 del Reglamento Procesal 2026 para testing de interfaz y flujos.
"""

from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from expedientes.domain.calendar import compute_business_deadline
from expedientes.domain.holiday_provider import Argentina2026HolidayProvider
from expedientes.models import (
    CambioEstadoExpediente,
    EstadoExpedienteEnum,
    Expediente,
    ExpedienteNumberSequence,
    SolicitudT01,
    TipoDescargoEnum,
)
from socios.models import Socio


class Command(BaseCommand):
    help = "Carga expedientes de demostración en los seis estados del Art. 12."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Elimina expedientes de prueba anteriores antes de sembrar.",
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.DEBUG:
            raise CommandError("seed_expedientes sólo puede ejecutarse con DEBUG=True.")

        if options.get("clean"):
            self.stdout.write("Limpiando expedientes y solicitudes previas...")
            SolicitudT01.objects.all().delete()
            CambioEstadoExpediente.objects.all().delete()
            Expediente.objects.all().delete()
            ExpedienteNumberSequence.objects.filter(year=2026).update(last_value=0)

        if Expediente.objects.exists():
            self.stdout.write(
                self.style.WARNING("Ya existen expedientes en la BD. Use --clean para resembrar.")
            )
            return

        socios_map = {s.legajo: s for s in Socio.objects.all()}
        required_legajos = ["74907", "85194", "87414", "408917", "403655"]
        for leg in required_legajos:
            if leg not in socios_map:
                raise CommandError(
                    f"Falta el socio legajo {leg}. Ejecute antes 'python manage.py seed_demo'."
                )

        ahora = timezone.now()
        holiday_provider = Argentina2026HolidayProvider()

        # Asegurar contador de secuencia
        seq, _ = ExpedienteNumberSequence.objects.get_or_create(
            year=2026, defaults={"last_value": 0}
        )

        def _crear_exp(
            numero_num: int,
            socio: Socio,
            motivo: str,
            puntos: float,
            estado_final: EstadoExpedienteEnum,
            socios_implicados: list[Socio],
            descargo_data: dict[str, Any] | None = None,
        ) -> Expediente:
            numero = f"EXP-{numero_num:04d}/2026"
            plazo_inicio = ahora - timedelta(days=2)
            plazo_limite = compute_business_deadline(
                start_at=plazo_inicio,
                business_days=5,
                holiday_provider=holiday_provider,
            )

            inicio_at = plazo_inicio if estado_final != EstadoExpedienteEnum.CREADO else None
            limite_at = plazo_limite if estado_final != EstadoExpedienteEnum.CREADO else None

            exp = Expediente.objects.create(
                numero=numero,
                socio=socio,
                motivo=motivo,
                puntos=puntos,
                estado=estado_final,
                plazo_inicio_at=inicio_at,
                plazo_limite_at=limite_at,
                descargo_presentado=bool(descargo_data),
                descargo_tipo=descargo_data.get("tipo") if descargo_data else None,
                descargo_causal=descargo_data.get("causal") if descargo_data else None,
                descargo_archivo=descargo_data.get("archivo") if descargo_data else None,
                descargo_texto=descargo_data.get("texto") if descargo_data else None,
                descargo_presentado_at=descargo_data.get("fecha") if descargo_data else None,
            )
            exp.socios.set(socios_implicados)

            # Historial de auditoría de transiciones
            secuencia_estados = [
                EstadoExpedienteEnum.CREADO,
                EstadoExpedienteEnum.JUSTIFICANDO,
                EstadoExpedienteEnum.REVISION_RESOLUCION,
                EstadoExpedienteEnum.ESPERA_RESOLUCION,
                EstadoExpedienteEnum.PENDIENTE_CORREOS,
                EstadoExpedienteEnum.EMITIDO,
            ]
            idx_final = secuencia_estados.index(estado_final)

            CambioEstadoExpediente.objects.create(
                expediente=exp,
                estado_anterior=EstadoExpedienteEnum.CREADO,
                estado_nuevo=EstadoExpedienteEnum.CREADO,
                actor="408917",
                motivo="Apertura formal de causa sumarial",
            )
            for i in range(idx_final):
                est_prev = secuencia_estados[i]
                est_next = secuencia_estados[i + 1]
                CambioEstadoExpediente.objects.create(
                    expediente=exp,
                    estado_anterior=est_prev,
                    estado_nuevo=est_next,
                    actor="408917",
                    motivo=f"Pase procesal canónico a {est_next.label}",
                )

            return exp

        # 1. CREADO
        e1 = _crear_exp(
            1,
            socios_map["74907"],
            "Inasistencia no informada a asamblea general ordinaria",
            -1.0,
            EstadoExpedienteEnum.CREADO,
            [socios_map["74907"]],
        )

        # 2. JUSTIFICANDO (plazo activo de 5 días hábiles)
        _crear_exp(
            2,
            socios_map["85194"],
            "Falta reiterada de entrega de informes operativos cuatrimestrales",
            -1.5,
            EstadoExpedienteEnum.JUSTIFICANDO,
            [socios_map["85194"]],
        )

        # 3. REVISION_RESOLUCION (con descargo T02 presentado)
        _crear_exp(
            3,
            socios_map["87414"],
            "Ausencia injustificada en guardia asignada de laboratorio informático",
            -1.0,
            EstadoExpedienteEnum.REVISION_RESOLUCION,
            [socios_map["87414"], socios_map["74907"]],
            descargo_data={
                "tipo": TipoDescargoEnum.T02_CERTIFICADO,
                "causal": "Examen Académico Universitario en UTN FRC",
                "archivo": "certificado_examen_utn.pdf",
                "texto": "Constancia de examen final de Sistemas Operativos rendido el mismo día.",
                "fecha": ahora - timedelta(hours=12),
            },
        )

        # 4. ESPERA_RESOLUCION
        _crear_exp(
            4,
            socios_map["408917"],
            "Coordinación destacada en jornadas tecnológicas solidarias comunitarias",
            2.0,
            EstadoExpedienteEnum.ESPERA_RESOLUCION,
            [socios_map["408917"]],
        )

        # 5. PENDIENTE_CORREOS
        _crear_exp(
            5,
            socios_map["403655"],
            "Retraso injustificado en entrega de documentación administrativa y balances",
            -2.0,
            EstadoExpedienteEnum.PENDIENTE_CORREOS,
            [socios_map["403655"]],
        )

        # 6. EMITIDO
        _crear_exp(
            6,
            socios_map["74907"],
            "Incumplimiento de tareas asignadas en cobertura institucional de evento",
            -0.5,
            EstadoExpedienteEnum.EMITIDO,
            [socios_map["74907"]],
        )

        seq.last_value = 6
        seq.save(update_fields=["last_value"])

        # Crear solicitudes T01 de demostración vinculadas
        SolicitudT01.objects.create(
            solicitante=socios_map["408917"],
            expediente=e1,
            titulo="Inasistencia a Asamblea General Ordinaria",
            motivo="El socio no concurrió a la asamblea sin previo aviso estatutario.",
            puntos=-1.0,
            tipo_accion=SolicitudT01.TipoAccion.SANCTION,
            estado=SolicitudT01.Estado.ISSUED,
            destinatario_socio_id=socios_map["74907"].id,
            destinatarios_socios_ids=[socios_map["74907"].id],
            issued_at=ahora,
        )

        SolicitudT01.objects.create(
            solicitante=socios_map["408917"],
            expediente=None,
            titulo="Borrador de reconocimiento por mérito académico",
            motivo="Participación en congreso representando a la institución.",
            puntos=1.0,
            tipo_accion=SolicitudT01.TipoAccion.MERIT,
            estado=SolicitudT01.Estado.DRAFT,
            destinatario_socio_id=socios_map["85194"].id,
            destinatarios_socios_ids=[socios_map["85194"].id],
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Sembrados exitosamente 6 expedientes (EXP-0001 a EXP-0006) en los 6 estados."
            )
        )
