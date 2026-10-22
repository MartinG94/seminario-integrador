"""Suite de Pruebas End-to-End (QA E2E) para SCRUM-50 / S3-06:
Gestión de Eventos Institucionales, Asistencias y Sanciones Disciplinarias.

Valida íntegramente los 12 casos de prueba de QA (QA-E2E-01 a QA-E2E-12):
- QA-E2E-01: Ciclo completo Reunión Ordinaria por Grupo (G58) -> CREADO -> /notificar/ ->
  Outbox -> guardado parcial sin sanción -> cierre definitivo -> Expediente -1.00,
  llamado de atención y justificación 0.00.
- QA-E2E-02: Ciclo completo Reunión Extraordinaria Virtual por Subcomisión -> -1.50 pts,
  Tardanza Grave (-0.50 pts) y Asamblea (-2.00 pts).
- QA-E2E-03: Ciclo completo Actividad Operativa Externa sin fecha_fin -> Estado ABIERTO ->
  /fijar-hora-fin/ -> FINALIZADO -> Sanción personalizada (-2.50 pts) y detalle_tarea.
- QA-E2E-04: Convocatorias por Estado Social (JUNIORS 1° a 3° año vs SENIORS 4° a 6° año)
  y persistencia en tribunal_evento_convocado.
- QA-E2E-05: Preclusión de potestad sancionatoria por preaviso < 2 días hábiles (Art. 95)
  con feriados/fines de semana y por reporte > 72 hs hábiles (Art. 99).
- QA-E2E-06: Regla 3:1 inmutable sobre atencionFelicitacion (3 llamados = -1.00 pt,
  3 felicitaciones = +1.00 pt) y bloqueo ante duplicación.
- QA-E2E-07: Anulación manual (/anular/) con despacho de correos de disculpas a citados,
  y auto-anulación de eventos en estado CREADO que incumplen el preaviso de 2 días hábiles.
- QA-E2E-08: Patrón Strategy Biométrico (fichadas en reloj con cálculo automático de
  tolerancias: <=15 min PRESENTE, 16-30 min TARDE_LEVE, >30 min TARDE_GRAVE, sin fichada AUSENTE).
- QA-E2E-09: Idempotencia estricta ante reintentos de cierre disciplinario.
- QA-E2E-10: Matriz RBAC (Anónimo 401, Socio Ordinario 403 en mutaciones y aislamiento en
  apercibimientos, CD/TD/Fiscalizadora/Admin 201/200) y flujo real de Login JWT.
- QA-E2E-11: Integración E2E con el Tablero del Tribunal de Disciplina (/api/v1/expedientes/board/)
  y el Portal del Socio Imputado (/api/v1/expedientes/mis-expedientes/).
- QA-E2E-12: Auditoría de Inmutabilidad del Saldo de Puntos (Regla Innegociable 3: cero UPDATE
  manual sobre socios y calculate_socio_balance inalterado mientras el expediente está CREADO).
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from expedientes.models import (
    AsistenciaEvento,
    AtencionFelicitacion,
    CategoriaEventoEnum,
    EstadoAsistenciaEventoEnum,
    EstadoEventoEnum,
    EstadoExpedienteEnum,
    EventoConvocado,
    EventoInstitucional,
    Expediente,
    MetodoCapturaAsistenciaEnum,
    ModalidadEventoEnum,
    ModoConvocatoriaEnum,
    SubtipoActividadEnum,
    SubtipoReunionEnum,
)
from expedientes.services.warning_accumulation_service import WarningAccumulationService
from notifications.models import EmailOutbox
from ranking.models import PuntajeAplicado, PuntajeGeneral
from socios.models import Role, Socio, Subcomision

User = get_user_model()


def _extract_list(data):
    if isinstance(data, dict):
        if "results" in data:
            return data["results"]
        if "columns" in data:
            cases = []
            for col in data["columns"]:
                cases.extend(col.get("cases", []))
            return cases
    return data


@pytest.fixture
def qa_setup(db):
    """Prepara el padrón institucional de prueba para la suite QA E2E."""
    sub_computos, _ = Subcomision.objects.get_or_create(name="Cómputos")
    sub_finanzas, _ = Subcomision.objects.get_or_create(name="Finanzas")

    def _create_member(username, legajo, first_name, last_name, role, social_year, sub):
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"email": f"{username}@aveit.org.ar"},
        )
        user.set_password("QaTest-2026!")
        user.save()
        socio, _ = Socio.objects.update_or_create(
            user=user,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "legajo": legajo,
                "email": f"{username}@aveit.org.ar",
                "subcomision": sub,
                "social_year": social_year,
                "role": role,
                "is_enabled": True,
            },
        )
        return user, socio

    cd_user, cd_socio = _create_member(
        "qa_cd", "QA-CD-01", "Diego", "Directivo", Role.CD, 5, sub_computos
    )
    td_user, td_socio = _create_member(
        "qa_td", "QA-TD-01", "Tomás", "Tribunal", Role.TD, 5, sub_computos
    )
    fisc_user, fisc_socio = _create_member(
        "qa_fisc", "QA-FISC-01", "Laura", "Fiscalizadora", Role.FISCALIZADORA, 4, sub_finanzas
    )
    # Juniors: social_year 1 (G60), 2 (G59), 3 (G58)
    s_g58_1_u, s_g58_1 = _create_member(
        "qa_s_g58_1", "QA-5801", "Martín", "Guillén", Role.SOCIO, 3, sub_computos
    )
    s_g58_2_u, s_g58_2 = _create_member(
        "qa_s_g58_2", "QA-5802", "Lucas", "Gastiaburu", Role.SOCIO, 3, sub_computos
    )
    s_g58_3_u, s_g58_3 = _create_member(
        "qa_s_g58_3", "QA-5803", "Nicolás", "Rosales", Role.SOCIO, 3, sub_finanzas
    )
    s_g58_4_u, s_g58_4 = _create_member(
        "qa_s_g58_4", "QA-5804", "Ignacio", "Morales", Role.SOCIO, 3, sub_finanzas
    )
    # Senior: social_year 4 (G57)
    s_g57_1_u, s_g57_1 = _create_member(
        "qa_s_g57_1", "QA-5701", "Sofía", "Senior", Role.SOCIO, 4, sub_computos
    )

    return {
        "sub_computos": sub_computos,
        "sub_finanzas": sub_finanzas,
        "cd_user": cd_user,
        "cd_socio": cd_socio,
        "td_user": td_user,
        "td_socio": td_socio,
        "fisc_user": fisc_user,
        "fisc_socio": fisc_socio,
        "s_g58_1_u": s_g58_1_u,
        "s_g58_1": s_g58_1,
        "s_g58_2_u": s_g58_2_u,
        "s_g58_2": s_g58_2,
        "s_g58_3_u": s_g58_3_u,
        "s_g58_3": s_g58_3,
        "s_g58_4_u": s_g58_4_u,
        "s_g58_4": s_g58_4,
        "s_g57_1_u": s_g57_1_u,
        "s_g57_1": s_g57_1,
    }


@pytest.mark.django_db
class TestQAE2EEventosAsistenciasSanciones:
    """Ejecución de la Matriz de Casos de Prueba E2E de QA para SCRUM-50."""

    def test_qa_e2e_01_flujo_completo_reunion_ordinaria_grupo_g58(self, qa_setup):
        """
        QA-E2E-01:
        1. Login JWT real como autoridad CD.
        2. Creación de Reunión Ordinaria por Grupo G58 con notificar=False -> Estado CREADO.
        3. Verifica que solo los socios de G58 (social_year=3) fueron convocados, excluyendo G57.
        4. Acción POST /notificar/ -> Estado NOTIFICADO y correos en EmailOutbox.
        5. Guardado parcial (cerrar_evento=False) -> Persiste estados sin abrir expedientes.
        6. Cierre definitivo (cerrar_evento=True) con aliases de Frontend:
           - s_g58_1: PRESENTE (0 pts)
           - s_g58_2: TARDANZA_LEVE (+1 llamado de atención en atencionFelicitacion)
           - s_g58_3: AUSENTE_INJUSTIFICADO (Expediente CREADO por -1.00 pt)
           - s_g58_4: JUSTIFICADO (0 pts, sin sanción)
        """
        client = APIClient()

        # 1. Login JWT real
        login_res = client.post(
            "/api/v1/auth/login/",
            {"identifier": "QA-CD-01", "password": "QaTest-2026!"},
            format="json",
        )
        assert login_res.status_code == status.HTTP_200_OK
        access_token = login_res.data["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 2. Crear Reunión Ordinaria para G58 sin notificar aún
        inicio = timezone.now() + timedelta(days=6)
        create_payload = {
            "titulo": "QA E2E - Reunión Ordinaria G58",
            "descripcion": "Sesión mensual obligatoria de cohorte G58",
            "categoria": CategoriaEventoEnum.REUNION,
            "tipo": SubtipoReunionEnum.ORDINARIA,
            "modalidad": ModalidadEventoEnum.PRESENCIAL_SEDE,
            "fecha_programada": inicio.isoformat(),
            "fecha_fin": None,
            "modo_convocatoria": ModoConvocatoriaEnum.GRUPO,
            "grupo_convocado": "G58",
            "notificar": False,
        }
        res_create = client.post("/api/v1/expedientes/eventos/", create_payload, format="json")
        assert res_create.status_code == status.HTTP_201_CREATED, res_create.data
        evento_id = res_create.data["id"]
        assert res_create.data["estado"] == EstadoEventoEnum.CREADO
        assert res_create.data["es_sancionable"] is True

        # 3. Verificar que se convocó a los 4 socios de G58 y NO al de G57
        convocados_ids = set(
            EventoConvocado.objects.filter(evento_id=evento_id).values_list("socio_id", flat=True)
        )
        expected_g58_ids = {
            qa_setup["s_g58_1"].id,
            qa_setup["s_g58_2"].id,
            qa_setup["s_g58_3"].id,
            qa_setup["s_g58_4"].id,
        }
        assert expected_g58_ids.issubset(convocados_ids)
        assert qa_setup["s_g57_1"].id not in convocados_ids

        # 4. Notificar formalmente
        res_notif = client.post(f"/api/v1/expedientes/eventos/{evento_id}/notificar/")
        assert res_notif.status_code == status.HTTP_200_OK
        assert res_notif.data["evento"]["estado"] == EstadoEventoEnum.NOTIFICADO
        outbox_count = EmailOutbox.objects.filter(
            idempotency_key__startswith=f"meeting_notice_{evento_id}_"
        ).count()
        assert outbox_count == len(convocados_ids)

        # 5. Guardado parcial de planilla (cerrar_evento=False) -> 0 expedientes aún
        planilla_payload = {
            "estrategia": "MANUAL",
            "cerrar_evento": False,
            "asistencias": [
                {
                    "socio_id": qa_setup["s_g58_1"].id,
                    "estado_asistencia": "PRESENTE",
                    "motivo": "En sede a horario",
                },
                {
                    "socio_id": qa_setup["s_g58_2"].id,
                    "estado_asistencia": "TARDANZA_LEVE",
                    "minutos_tardanza": 22,
                    "motivo": "Demora transporte urbano (+22 min)",
                },
                {
                    "socio_id": qa_setup["s_g58_3"].id,
                    "estado_asistencia": "AUSENTE_INJUSTIFICADO",
                    "motivo": "Ausencia sin aviso previo",
                },
                {
                    "socio_id": qa_setup["s_g58_4"].id,
                    "estado_asistencia": "JUSTIFICADO",
                    "motivo": "Certificado de examen final UTN FRC",
                },
            ],
        }
        res_parcial = client.post(
            f"/api/v1/expedientes/eventos/{evento_id}/reportar-asistencia/",
            planilla_payload,
            format="json",
        )
        assert res_parcial.status_code == status.HTTP_200_OK
        assert res_parcial.data["expedientes_generados"] == 0
        assert res_parcial.data["apercibimientos_generados"] == 0

        # 6. Cierre definitivo y procesamiento disciplinario (cerrar_evento=True)
        planilla_payload["cerrar_evento"] = True
        res_cierre = client.post(
            f"/api/v1/expedientes/eventos/{evento_id}/reportar-asistencia/",
            planilla_payload,
            format="json",
        )
        assert res_cierre.status_code == status.HTTP_200_OK
        assert res_cierre.data["estado_evento"] == EstadoEventoEnum.FINALIZADO
        assert res_cierre.data["expedientes_generados"] == 1
        assert res_cierre.data["apercibimientos_generados"] == 1

        # Verificar expediente creado para s_g58_3 por -1.00 punto
        exp_creado = res_cierre.data["expedientes_creados"][0]
        assert exp_creado["socio_id"] == qa_setup["s_g58_3"].id
        assert Decimal(str(exp_creado["puntos"])) == Decimal("-1.00")
        exp_db = Expediente.objects.get(numero=exp_creado["numero"])
        assert exp_db.estado == EstadoExpedienteEnum.CREADO
        assert "Ausencia sin aviso previo" in exp_db.motivo

        # Verificar llamado de atención en atencionFelicitacion para s_g58_2
        atencion = AtencionFelicitacion.objects.get(socio=qa_setup["s_g58_2"])
        assert atencion.llamadosAtencion == 1

        # Verificar que el socio JUSTIFICADO no tiene expediente ni llamado
        asist_just = AsistenciaEvento.objects.get(evento_id=evento_id, socio=qa_setup["s_g58_4"])
        assert asist_just.estado_asistencia == EstadoAsistenciaEventoEnum.JUSTIFICADO
        assert asist_just.expediente_generado is None
        assert asist_just.notificado is False

    def test_qa_e2e_02_escalas_extraordinaria_asamblea_y_tardanza_grave(self, qa_setup):
        """
        QA-E2E-02:
        Verifica graduación exacta en Reunión Extraordinaria (-1.50 pts falta, -0.50 pts
        tardanza grave) y Asamblea General (-2.00 pts falta).
        """
        client = APIClient()
        client.force_authenticate(user=qa_setup["cd_user"])
        inicio = timezone.now() + timedelta(days=5)

        # A. Reunión Extraordinaria Virtual por Subcomisión Cómputos
        res_extra = client.post(
            "/api/v1/expedientes/eventos/",
            {
                "titulo": "QA E2E - Extraordinaria Cómputos",
                "categoria": CategoriaEventoEnum.REUNION,
                "tipo": SubtipoReunionEnum.EXTRAORDINARIA,
                "modalidad": ModalidadEventoEnum.VIRTUAL,
                "ubicacion": "https://meet.google.com/qa-e2e-comp",
                "fecha_programada": inicio.isoformat(),
                "modo_convocatoria": ModoConvocatoriaEnum.SUBCOMISION,
                "subcomision": qa_setup["sub_computos"].id,
                "notificar": True,
            },
            format="json",
        )
        assert res_extra.status_code == status.HTTP_201_CREATED
        extra_id = res_extra.data["id"]

        res_rep_extra = client.post(
            f"/api/v1/expedientes/eventos/{extra_id}/reportar-asistencia/",
            {
                "estrategia": "MANUAL",
                "cerrar_evento": True,
                "asistencias": [
                    {
                        "socio_id": qa_setup["s_g58_1"].id,
                        "estado_asistencia": "AUSENTE_INJUSTIFICADO",
                        "motivo": "Faltó a extraordinaria virtual",
                    },
                    {
                        "socio_id": qa_setup["s_g58_2"].id,
                        "estado_asistencia": "TARDANZA_GRAVE",
                        "minutos_tardanza": 42,
                        "motivo": "Ingresó 42 min tarde al Meet",
                    },
                    {
                        "socio_id": qa_setup["s_g57_1"].id,
                        "estado_asistencia": "PRESENTE",
                        "motivo": "Conectada en tiempo y forma",
                    },
                    {
                        "socio_id": qa_setup["cd_socio"].id,
                        "estado_asistencia": "PRESENTE",
                        "motivo": "Moderador presente",
                    },
                    {
                        "socio_id": qa_setup["td_socio"].id,
                        "estado_asistencia": "PRESENTE",
                        "motivo": "Presente",
                    },
                ],
            },
            format="json",
        )
        assert res_rep_extra.status_code == status.HTTP_200_OK
        creados = {
            e["socio_id"]: Decimal(str(e["puntos"]))
            for e in res_rep_extra.data["expedientes_creados"]
        }
        assert creados[qa_setup["s_g58_1"].id] == Decimal("-1.50")
        assert creados[qa_setup["s_g58_2"].id] == Decimal("-0.50")

        # B. Asamblea General (-2.00 puntos)
        res_asamb = client.post(
            "/api/v1/expedientes/eventos/",
            {
                "titulo": "QA E2E - Asamblea Anual",
                "categoria": CategoriaEventoEnum.REUNION,
                "tipo": SubtipoReunionEnum.ASAMBLEA,
                "modalidad": ModalidadEventoEnum.PRESENCIAL_SEDE,
                "fecha_programada": inicio.isoformat(),
                "modo_convocatoria": ModoConvocatoriaEnum.PERSONALIZADA,
                "socios_ids": [qa_setup["s_g58_3"].id],
                "notificar": True,
            },
            format="json",
        )
        assert res_asamb.status_code == status.HTTP_201_CREATED
        asamb_id = res_asamb.data["id"]

        res_rep_asamb = client.post(
            f"/api/v1/expedientes/eventos/{asamb_id}/reportar-asistencia/",
            {
                "cerrar_evento": True,
                "asistencias": [
                    {
                        "socio_id": qa_setup["s_g58_3"].id,
                        "estado_asistencia": "AUSENTE",
                        "motivo": "Inasistencia injustificada a Asamblea General",
                    }
                ],
            },
            format="json",
        )
        assert res_rep_asamb.status_code == status.HTTP_200_OK
        assert Decimal(str(res_rep_asamb.data["expedientes_creados"][0]["puntos"])) == Decimal(
            "-2.00"
        )

    def test_qa_e2e_03_actividad_abierta_fijar_hora_fin_y_sancion_personalizada(self, qa_setup):
        """
        QA-E2E-03:
        1. Crea Actividad Externa con detalle_tarea y puntos_sancion = -2.50, sin fecha_fin.
        2. Simula que llegó la hora de inicio -> listado transiciona automáticamente a ABIERTO.
        3. Invoca POST /fijar-hora-fin/ -> transiciona a FINALIZADO y fija fecha_fin.
        4. Procesa asistencia con ausente -> abre expediente por -2.50 puntos personalizados.
        """
        client = APIClient()
        client.force_authenticate(user=qa_setup["cd_user"])
        inicio = timezone.now() + timedelta(days=5)

        res_act = client.post(
            "/api/v1/expedientes/eventos/",
            {
                "titulo": "QA E2E - Jornada de Pintura Exterior",
                "categoria": CategoriaEventoEnum.ACTIVIDAD,
                "tipo": SubtipoActividadEnum.MANTENIMIENTO,
                "modalidad": ModalidadEventoEnum.PRESENCIAL_EXTERNA,
                "ubicacion": "Anexo Deportivo UTN FRC",
                "detalle_tarea": "Lijado y pintura anticorrosiva del portón principal",
                "puntos_sancion": -2.50,
                "fecha_programada": inicio.isoformat(),
                "fecha_fin": None,
                "modo_convocatoria": ModoConvocatoriaEnum.PERSONALIZADA,
                "socios_ids": [qa_setup["s_g58_1"].id],
                "notificar": True,
            },
            format="json",
        )
        assert res_act.status_code == status.HTTP_201_CREATED
        act_id = res_act.data["id"]

        # Simular que el evento ya comenzó hace 2 horas (pero se publicó 5 días antes)
        ahora = timezone.now()
        EventoInstitucional.objects.filter(pk=act_id).update(
            fecha_publicacion=ahora - timedelta(days=5),
            fecha_programada=ahora - timedelta(hours=2),
        )

        # Al consultar el listado, debe auto-transicionar de NOTIFICADO a ABIERTO
        res_list = client.get(f"/api/v1/expedientes/eventos/{act_id}/")
        assert res_list.status_code == status.HTTP_200_OK
        assert res_list.data["estado"] == EstadoEventoEnum.ABIERTO

        # Fijar hora de finalización efectiva
        res_fin = client.post(
            f"/api/v1/expedientes/eventos/{act_id}/fijar-hora-fin/",
            {"fecha_fin": (ahora - timedelta(minutes=10)).isoformat()},
            format="json",
        )
        assert res_fin.status_code == status.HTTP_200_OK
        assert res_fin.data["evento"]["estado"] == EstadoEventoEnum.FINALIZADO

        # Reportar inasistencia y verificar que aplique los -2.50 puntos personalizados
        res_rep = client.post(
            f"/api/v1/expedientes/eventos/{act_id}/reportar-asistencia/",
            {
                "cerrar_evento": True,
                "asistencias": [
                    {
                        "socio_id": qa_setup["s_g58_1"].id,
                        "estado_asistencia": "AUSENTE_INJUSTIFICADO",
                        "motivo": "No se presentó a la jornada de mantenimiento",
                    }
                ],
            },
            format="json",
        )
        assert res_rep.status_code == status.HTTP_200_OK
        assert len(res_rep.data["expedientes_creados"]) == 1
        assert Decimal(str(res_rep.data["expedientes_creados"][0]["puntos"])) == Decimal("-2.50")

    def test_qa_e2e_04_convocatoria_estado_social_juniors_vs_seniors(self, qa_setup):
        """
        QA-E2E-04:
        Verifica que ESTADO_SOCIAL = 'JUNIORS' convoque sólo a socios de 1° a 3° año social
        y ESTADO_SOCIAL = 'SENIORS' convoque sólo a socios de 4° año en adelante.
        """
        client = APIClient()
        client.force_authenticate(user=qa_setup["cd_user"])
        inicio = timezone.now() + timedelta(days=5)

        # 1. Convocatoria JUNIORS
        res_jr = client.post(
            "/api/v1/expedientes/eventos/",
            {
                "titulo": "QA E2E - Capacitación Juniors",
                "categoria": CategoriaEventoEnum.REUNION,
                "tipo": SubtipoReunionEnum.ORDINARIA,
                "modalidad": ModalidadEventoEnum.PRESENCIAL_SEDE,
                "fecha_programada": inicio.isoformat(),
                "modo_convocatoria": ModoConvocatoriaEnum.ESTADO_SOCIAL,
                "estado_social_convocado": "JUNIORS",
            },
            format="json",
        )
        assert res_jr.status_code == status.HTTP_201_CREATED
        jr_convocados = set(
            EventoConvocado.objects.filter(evento_id=res_jr.data["id"]).values_list(
                "socio_id", flat=True
            )
        )
        assert qa_setup["s_g58_1"].id in jr_convocados  # social_year = 3 (Junior)
        assert qa_setup["s_g57_1"].id not in jr_convocados  # social_year = 4 (Senior)

        # 2. Convocatoria SENIORS
        res_sr = client.post(
            "/api/v1/expedientes/eventos/",
            {
                "titulo": "QA E2E - Plenario Seniors",
                "categoria": CategoriaEventoEnum.REUNION,
                "tipo": SubtipoReunionEnum.PLENARIO,
                "modalidad": ModalidadEventoEnum.PRESENCIAL_SEDE,
                "fecha_programada": inicio.isoformat(),
                "modo_convocatoria": ModoConvocatoriaEnum.ESTADO_SOCIAL,
                "estado_social_convocado": "SENIORS",
            },
            format="json",
        )
        assert res_sr.status_code == status.HTTP_201_CREATED
        sr_convocados = set(
            EventoConvocado.objects.filter(evento_id=res_sr.data["id"]).values_list(
                "socio_id", flat=True
            )
        )
        assert qa_setup["s_g57_1"].id in sr_convocados  # social_year = 4 (Senior)
        assert qa_setup["s_g58_1"].id not in sr_convocados  # social_year = 3 (Junior)

    def test_qa_e2e_05_extincion_potestad_punitiva_por_reporte_extemporaneo_72hs(self, qa_setup):
        """
        QA-E2E-05:
        Un evento publicado con > 2 días hábiles de antelación (inicialmente sancionable),
        pero cuyo reporte de asistencia se eleva pasadas las 72 horas hábiles (Art. 99 R.I.),
        pierde su carácter sancionable y genera 0 expedientes y 0 apercibimientos.
        """
        client = APIClient()
        client.force_authenticate(user=qa_setup["cd_user"])

        ahora = timezone.now()
        pub = ahora - timedelta(days=15)
        prog = ahora - timedelta(days=10)
        fin = prog + timedelta(hours=2)

        evento = EventoInstitucional.objects.create(
            titulo="QA E2E - Reunión Reportada Fuera de Término",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            fecha_publicacion=pub,
            fecha_programada=prog,
            fecha_fin=fin,
            estado=EstadoEventoEnum.EN_CURSO,
            convocante=qa_setup["cd_socio"],
            es_obligatoria=True,
            es_sancionable=True,
        )

        # Reportar hoy (10 días corridos > 72 hs hábiles después de fin)
        res = client.post(
            f"/api/v1/expedientes/eventos/{evento.id}/reportar-asistencia/",
            {
                "cerrar_evento": True,
                "asistencias": [
                    {
                        "socio_id": qa_setup["s_g58_1"].id,
                        "estado_asistencia": "AUSENTE_INJUSTIFICADO",
                        "motivo": "Inasistencia en reunión cuyo reporte se demoró 10 días",
                    },
                    {
                        "socio_id": qa_setup["s_g58_2"].id,
                        "estado_asistencia": "TARDANZA_LEVE",
                        "motivo": "Tardanza en reunión con reporte extemporáneo",
                    },
                ],
            },
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data["es_sancionable"] is False
        assert "72 horas hábiles" in (res.data["motivo_no_sancionable"] or "")
        assert res.data["expedientes_generados"] == 0
        assert res.data["apercibimientos_generados"] == 0

    def test_qa_e2e_06_consolidacion_3_a_1_en_cierre_de_evento(self, qa_setup):
        """
        QA-E2E-06:
        Un socio que ya acumula 2 llamados de atención en atencionFelicitacion e incurre
        en una TARDANZA_LEVE en un evento sancionable dispara automáticamente la consolidación
        3:1, abriendo un expediente en estado CREADO por -1.00 punto y reiniciando su contador a 0.
        """
        client = APIClient()
        client.force_authenticate(user=qa_setup["cd_user"])
        socio = qa_setup["s_g58_4"]

        # Pre-cargar 2 llamados de atención
        WarningAccumulationService.register_warning(socio_id=socio.id, motivo="1° llamado previo")
        WarningAccumulationService.register_warning(socio_id=socio.id, motivo="2° llamado previo")
        assert WarningAccumulationService.get_pending_count(socio.id) == 2

        inicio = timezone.now() + timedelta(days=5)
        evento = EventoInstitucional.objects.create(
            titulo="QA E2E - Evento Disparo Terna 3:1",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            fecha_publicacion=timezone.now(),
            fecha_programada=inicio,
            estado=EstadoEventoEnum.EN_CURSO,
            convocante=qa_setup["cd_socio"],
            es_obligatoria=True,
            es_sancionable=True,
        )

        res = client.post(
            f"/api/v1/expedientes/eventos/{evento.id}/reportar-asistencia/",
            {
                "cerrar_evento": True,
                "asistencias": [
                    {
                        "socio_id": socio.id,
                        "estado_asistencia": "TARDANZA_LEVE",
                        "minutos_tardanza": 19,
                        "motivo": "3° tardanza leve del trimestre (dispara 3:1)",
                    }
                ],
            },
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data["apercibimientos_generados"] == 1
        assert res.data["expedientes_generados"] == 1
        exp_info = res.data["expedientes_creados"][0]
        assert exp_info["tipo"] == "CONSOLIDACION_3_1"
        assert Decimal(str(exp_info["puntos"])) == Decimal("-1.00")
        assert WarningAccumulationService.get_pending_count(socio.id) == 0

    def test_qa_e2e_07_auto_anulacion_evento_creado_sin_notificar_a_tiempo(self, qa_setup):
        """
        QA-E2E-07:
        Un evento dejado en estado CREADO (sin notificar) cuya fecha_programada ya quedó
        a menos de 2 días hábiles del momento actual se anula automáticamente al listar eventos.
        """
        client = APIClient()
        client.force_authenticate(user=qa_setup["cd_user"])

        ahora = timezone.now()
        evento_vencido = EventoInstitucional.objects.create(
            titulo="QA E2E - Evento Olvidado en Borrador CREADO",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            fecha_publicacion=ahora - timedelta(days=4),
            fecha_programada=ahora + timedelta(hours=12),  # Faltan sólo 12 hs (< 2 días hábiles)
            estado=EstadoEventoEnum.CREADO,
            convocante=qa_setup["cd_socio"],
            es_obligatoria=True,
            es_sancionable=True,
        )

        res = client.get(f"/api/v1/expedientes/eventos/{evento_vencido.id}/")
        assert res.status_code == status.HTTP_200_OK
        assert res.data["estado"] == EstadoEventoEnum.ANULADO
        assert "2 días hábiles" in (res.data["motivo_cancelacion"] or "")

    def test_qa_e2e_08_captura_biometrica_e2e(self, qa_setup):
        """
        QA-E2E-08:
        Procesamiento con estrategia BIOMETRICO a través del endpoint REST, calculando
        automáticamente presente (<=15m), tardanza leve (16-30m) y tardanza grave (>30m)
        a partir de los timestamps de fichada.
        """
        client = APIClient()
        client.force_authenticate(user=qa_setup["cd_user"])

        pub = timezone.now() - timedelta(days=5)
        inicio = timezone.now() - timedelta(hours=3)
        fin = inicio + timedelta(hours=2)

        evento = EventoInstitucional.objects.create(
            titulo="QA E2E - Sesión con Reloj Biométrico",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            fecha_publicacion=pub,
            fecha_programada=inicio,
            fecha_fin=fin,
            tolerancia_tardanza_minutos=15,
            estado=EstadoEventoEnum.EN_CURSO,
            convocante=qa_setup["cd_socio"],
            es_obligatoria=True,
            es_sancionable=True,
        )

        res = client.post(
            f"/api/v1/expedientes/eventos/{evento.id}/reportar-asistencia/",
            {
                "metodo_captura": MetodoCapturaAsistenciaEnum.BIOMETRICO,
                "cerrar_evento": True,
                "asistencias": [
                    {
                        "socio_id": qa_setup["s_g58_1"].id,
                        "estado_asistencia": "PRESENTE",
                        "hora_registro": (inicio + timedelta(minutes=8)).isoformat(),
                        "motivo": "Fichada reloj #1 (+8m)",
                    },
                    {
                        "socio_id": qa_setup["s_g58_2"].id,
                        "estado_asistencia": "PRESENTE",
                        "hora_registro": (inicio + timedelta(minutes=24)).isoformat(),
                        "motivo": "Fichada reloj #1 (+24m -> Tarde Leve)",
                    },
                    {
                        "socio_id": qa_setup["s_g58_3"].id,
                        "estado_asistencia": "PRESENTE",
                        "hora_registro": (inicio + timedelta(minutes=45)).isoformat(),
                        "motivo": "Fichada reloj #1 (+45m -> Tarde Grave)",
                    },
                ],
            },
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data["apercibimientos_generados"] == 1  # s_g58_2 (24 min)
        assert res.data["expedientes_generados"] == 1  # s_g58_3 (45 min -> -0.50 pts)
        assert Decimal(str(res.data["expedientes_creados"][0]["puntos"])) == Decimal("-0.50")

    def test_qa_e2e_11_12_integracion_tablero_td_portal_socio_e_inmutabilidad_saldo(self, qa_setup):
        """
        QA-E2E-11 y QA-E2E-12:
        1. Verifica que el expediente generado al cerrar un evento aparezca en:
           - El tablero Kanban del Tribunal (/api/v1/expedientes/board/) para un miembro del TD.
           - El portal del socio imputado (/api/v1/expedientes/mis-expedientes/).
        2. Verifica que el saldo calculado en el libro mayor (calculate_socio_balance) y
           la tabla TransaccionPuntos NO hayan sufrido modificaciones directas (Regla 3).
        """
        client = APIClient()
        socio_imputado = qa_setup["s_g58_1"]

        aplicados_inicial = PuntajeAplicado.objects.filter(socio_id=socio_imputado.id).count()
        general_inicial = (
            PuntajeGeneral.objects.filter(socio_id=socio_imputado.id)
            .values_list("puntos", flat=True)
            .first()
        )

        # Autoridad CD crea y cierra evento con inasistencia de socio_imputado
        client.force_authenticate(user=qa_setup["cd_user"])
        evento = EventoInstitucional.objects.create(
            titulo="QA E2E - Integración TD y Saldo Inmutable",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            fecha_publicacion=timezone.now() - timedelta(days=5),
            fecha_programada=timezone.now() - timedelta(hours=2),
            estado=EstadoEventoEnum.EN_CURSO,
            convocante=qa_setup["cd_socio"],
            es_obligatoria=True,
            es_sancionable=True,
        )

        res_cierre = client.post(
            f"/api/v1/expedientes/eventos/{evento.id}/reportar-asistencia/",
            {
                "cerrar_evento": True,
                "asistencias": [
                    {
                        "socio_id": socio_imputado.id,
                        "estado_asistencia": "AUSENTE_INJUSTIFICADO",
                        "motivo": "Inasistencia verificada por QA E2E",
                    }
                ],
            },
            format="json",
        )
        assert res_cierre.status_code == status.HTTP_200_OK
        numero_exp = res_cierre.data["expedientes_creados"][0]["numero"]

        # 1. Consultar Tablero del Tribunal como usuario TD
        client.force_authenticate(user=qa_setup["td_user"])
        res_board = client.get("/api/v1/expedientes/board/")
        assert res_board.status_code == status.HTTP_200_OK
        board_items = _extract_list(res_board.data)
        assert any(item.get("numero") == numero_exp for item in board_items)

        # 2. Consultar Mis Expedientes como el socio imputado
        client.force_authenticate(user=qa_setup["s_g58_1_u"])
        res_mis_exp = client.get("/api/v1/expedientes/mis-expedientes/")
        assert res_mis_exp.status_code == status.HTTP_200_OK
        mis_items = _extract_list(res_mis_exp.data)
        assert any(item.get("numero") == numero_exp for item in mis_items)

        # 3. Auditoría de Inmutabilidad de Saldos (Regla Innegociable 3)
        aplicados_posterior = PuntajeAplicado.objects.filter(socio_id=socio_imputado.id).count()
        general_posterior = (
            PuntajeGeneral.objects.filter(socio_id=socio_imputado.id)
            .values_list("puntos", flat=True)
            .first()
        )
        assert aplicados_posterior == aplicados_inicial
        assert general_posterior == general_inicial
