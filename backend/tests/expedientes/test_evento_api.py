"""Suite Integral de Pruebas de Integración para API REST de Eventos Institucionales,
Asistencias y Libro Mayor de Apercibimientos (TS3-06.9 a TS3-06.11 / SCRUM-50 / S3-06).

Cubre:
- CA1 / CA2: Sancionabilidad (2 días hábiles) e inhibición en extemporáneas (201).
- CA3: Graduación exacta en escala Decimal (1.5 extraordinaria, 1.0 ordinaria, 0.5 leve).
- CA4: Acumulación de apercibimientos en libro mayor y aislamiento RBAC por socio.
- CA5: Cero UPDATE manual de saldos en MySQL; expedientes generados en estado CREADO.
- CA7: Despacho automático de notificaciones por correo al Outbox con clave de idempotencia.
- CA8: Campos obligatorios y fecha_fin estrictamente opcional (None).
- CA9: Coherencia formal entre categorías (REUNION vs ACTIVIDAD) y subtipos condicionados.
- CA10: Modalidades (SEDE, EXTERNA, VIRTUAL) y obligatoriedad de motivo circunstanciado.
- RBAC: CD, TD, ADMIN y Fiscalizadora crean/editan; Socios ordinarios leen pero no editan (403).
"""

import uuid
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
    EstadoRegistroApercibimientoEnum,
    EventoInstitucional,
    ModalidadEventoEnum,
    ModoConvocatoriaEnum,
    RegistroApercibimiento,
    SubtipoActividadEnum,
    SubtipoReunionEnum,
)
from notifications.models import EmailOutbox
from socios.models import Role, Socio, Subcomision

User = get_user_model()


def _extract_results(data):
    """Extrae la lista de resultados tolerando respuestas paginadas o no paginadas."""
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    return data


@pytest.fixture
def subcomision_computos(db):
    sub, _ = Subcomision.objects.get_or_create(name="Cómputos")
    return sub


@pytest.fixture
def cd_user(db, subcomision_computos):
    user, _ = User.objects.get_or_create(
        username="cd_autoridad",
        defaults={"email": "cd@aveit.org.ar"},
    )
    user.set_password("secure_password_2026")
    user.save()
    socio, _ = Socio.objects.get_or_create(
        user=user,
        defaults={
            "first_name": "Carla",
            "last_name": "Directiva",
            "legajo": "CD-100",
            "email": "cd@aveit.org.ar",
            "subcomision": subcomision_computos,
            "social_year": 5,
            "role": Role.CD,
            "is_enabled": True,
        },
    )
    return user


@pytest.fixture
def td_user(db, subcomision_computos):
    user, _ = User.objects.get_or_create(
        username="td_miembro",
        defaults={"email": "td@aveit.org.ar"},
    )
    user.set_password("secure_password_2026")
    user.save()
    socio, _ = Socio.objects.get_or_create(
        user=user,
        defaults={
            "first_name": "Tomas",
            "last_name": "Disciplinario",
            "legajo": "TD-200",
            "email": "td@aveit.org.ar",
            "subcomision": subcomision_computos,
            "social_year": 5,
            "role": Role.TD,
            "is_enabled": True,
        },
    )
    return user


@pytest.fixture
def fiscalizadora_user(db, subcomision_computos):
    user, _ = User.objects.get_or_create(
        username="fiscalizadora_lider",
        defaults={"email": "fiscalizadora@aveit.org.ar"},
    )
    user.set_password("secure_password_2026")
    user.save()
    socio, _ = Socio.objects.get_or_create(
        user=user,
        defaults={
            "first_name": "Florencia",
            "last_name": "Fiscal",
            "legajo": "FISC-300",
            "email": "fiscalizadora@aveit.org.ar",
            "subcomision": subcomision_computos,
            "social_year": 4,
            "role": Role.FISCALIZADORA,
            "is_enabled": True,
        },
    )
    return user


@pytest.fixture
def socio_user_1(db, subcomision_computos):
    user, _ = User.objects.get_or_create(
        username="socio_martin",
        defaults={"email": "martin@aveit.org.ar"},
    )
    user.set_password("secure_password_2026")
    user.save()
    socio, _ = Socio.objects.get_or_create(
        user=user,
        defaults={
            "first_name": "Martin",
            "last_name": "Guillen",
            "legajo": "SOC-101",
            "email": "martin@aveit.org.ar",
            "subcomision": subcomision_computos,
            "social_year": 3,  # G58
            "role": Role.SOCIO,
            "is_enabled": True,
        },
    )
    return user


@pytest.fixture
def socio_user_2(db, subcomision_computos):
    user, _ = User.objects.get_or_create(
        username="socio_lucas",
        defaults={"email": "lucas@aveit.org.ar"},
    )
    user.set_password("secure_password_2026")
    user.save()
    socio, _ = Socio.objects.get_or_create(
        user=user,
        defaults={
            "first_name": "Lucas",
            "last_name": "Gomez",
            "legajo": "SOC-102",
            "email": "lucas@aveit.org.ar",
            "subcomision": subcomision_computos,
            "social_year": 3,  # G58
            "role": Role.SOCIO,
            "is_enabled": True,
        },
    )
    return user


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestEventoInstitucionalAPI:
    """Pruebas funcionales de los endpoints de Eventos Institucionales."""

    def test_crear_reunion_exitosa_cd_con_fecha_fin_opcional_y_outbox(
        self, api_client, cd_user, socio_user_1, socio_user_2
    ):
        """Creación por CD con fecha_fin=None, cálculo sancionable y outbox (CA1, CA7, CA8)."""
        api_client.force_authenticate(user=cd_user)
        ahora = timezone.now()
        inicio = ahora + timedelta(days=5)  # Holgadamente > 2 días hábiles

        payload = {
            "titulo": "Reunión Plenaria Ordinaria",
            "descripcion": "Tratamiento de presupuesto y planificación cuatrimestral",
            "categoria": CategoriaEventoEnum.REUNION,
            "tipo": SubtipoReunionEnum.ORDINARIA,
            "modalidad": ModalidadEventoEnum.PRESENCIAL_SEDE,
            "fecha_programada": inicio.isoformat(),
            "fecha_fin": None,  # Estrictamente opcional (CA8)
            "modo_convocatoria": ModoConvocatoriaEnum.PERSONALIZADA,
            "socios_ids": [socio_user_1.socio.id, socio_user_2.socio.id],
        }

        response = api_client.post("/api/v1/expedientes/eventos/", payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED, response.data
        data = response.data

        assert data["titulo"] == "Reunión Plenaria Ordinaria"
        assert data["categoria"] == CategoriaEventoEnum.REUNION
        assert data["tipo"] == SubtipoReunionEnum.ORDINARIA
        assert data["fecha_fin"] is None
        assert data["es_sancionable"] is True
        assert data["motivo_no_sancionable"] is None
        assert data["total_convocados"] == 2

        # Comprobar creación de registros de asistencia iniciales
        evento_id = data["id"]
        asistencias = AsistenciaEvento.objects.filter(evento_id=evento_id)
        assert asistencias.count() == 2

        # Comprobar encolado transaccional en EmailOutbox (CA7)
        outbox_items = EmailOutbox.objects.filter(
            idempotency_key__startswith=f"meeting_notice_{evento_id}_"
        )
        assert outbox_items.count() == 2
        emails_destino = [
            item.to[0] if isinstance(item.to, list) else item.to for item in outbox_items
        ]
        assert "martin@aveit.org.ar" in emails_destino
        assert "lucas@aveit.org.ar" in emails_destino

    def test_permisos_rbac_creacion_eventos(
        self, api_client, cd_user, td_user, fiscalizadora_user, socio_user_1
    ):
        """Autoridades (CD, TD, Fiscalizadora) pueden crear y socios son rechazados con 403."""
        ahora = timezone.now()
        inicio = ahora + timedelta(days=4)
        payload = {
            "titulo": "Reunión de Prueba RBAC",
            "categoria": CategoriaEventoEnum.REUNION,
            "tipo": SubtipoReunionEnum.ORDINARIA,
            "modalidad": ModalidadEventoEnum.PRESENCIAL_SEDE,
            "fecha_programada": inicio.isoformat(),
            "modo_convocatoria": ModoConvocatoriaEnum.PERSONALIZADA,
            "socios_ids": [socio_user_1.socio.id],
        }

        # 1. Anónimo -> 401
        res_anon = api_client.post("/api/v1/expedientes/eventos/", payload, format="json")
        assert res_anon.status_code == status.HTTP_401_UNAUTHORIZED

        # 2. Socio ordinario -> 403 Forbidden
        api_client.force_authenticate(user=socio_user_1)
        res_socio = api_client.post("/api/v1/expedientes/eventos/", payload, format="json")
        assert res_socio.status_code == status.HTTP_403_FORBIDDEN

        # 3. CD -> 201 Created
        api_client.force_authenticate(user=cd_user)
        res_cd = api_client.post("/api/v1/expedientes/eventos/", payload, format="json")
        assert res_cd.status_code == status.HTTP_201_CREATED

        # 4. TD -> 201 Created
        api_client.force_authenticate(user=td_user)
        payload["titulo"] = "Reunión convocada por TD"
        res_td = api_client.post("/api/v1/expedientes/eventos/", payload, format="json")
        assert res_td.status_code == status.HTTP_201_CREATED

        # 5. Fiscalizadora / Subcomisión -> 201 Created
        api_client.force_authenticate(user=fiscalizadora_user)
        payload["titulo"] = "Reunión convocada por Fiscalizadora"
        res_fisc = api_client.post("/api/v1/expedientes/eventos/", payload, format="json")
        assert res_fisc.status_code == status.HTTP_201_CREATED

    def test_socio_ordinario_puede_consultar_eventos(self, api_client, cd_user, socio_user_1):
        """Socio ordinario autenticado puede listar y ver el detalle (lectura pública)."""
        evento = EventoInstitucional.objects.create(
            titulo="Asamblea General Ordinaria",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ASAMBLEA,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            fecha_publicacion=timezone.now(),
            fecha_programada=timezone.now() + timedelta(days=10),
            convocante=cd_user.socio,
            es_obligatoria=True,
            es_sancionable=True,
        )

        api_client.force_authenticate(user=socio_user_1)
        res_list = api_client.get("/api/v1/expedientes/eventos/")
        assert res_list.status_code == status.HTTP_200_OK
        assert any(e["id"] == evento.id for e in _extract_results(res_list.data))

        res_detail = api_client.get(f"/api/v1/expedientes/eventos/{evento.id}/")
        assert res_detail.status_code == status.HTTP_200_OK
        assert res_detail.data["titulo"] == "Asamblea General Ordinaria"

    def test_validacion_coherencia_categoria_tipo(self, api_client, cd_user):
        """Verifica rechazo 400 ante incoherencia entre categoría y tipo (CA9)."""
        api_client.force_authenticate(user=cd_user)
        ahora = timezone.now()
        inicio = ahora + timedelta(days=4)

        # REUNION con tipo de ACTIVIDAD (MANTENIMIENTO)
        payload_incoherente = {
            "titulo": "Reunión Invalida",
            "categoria": CategoriaEventoEnum.REUNION,
            "tipo": SubtipoActividadEnum.MANTENIMIENTO,
            "modalidad": ModalidadEventoEnum.PRESENCIAL_SEDE,
            "fecha_programada": inicio.isoformat(),
        }
        res = api_client.post("/api/v1/expedientes/eventos/", payload_incoherente, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "tipo" in res.data

        # ACTIVIDAD con tipo de REUNION (ORDINARIA)
        payload_incoherente_2 = {
            "titulo": "Actividad Invalida",
            "categoria": CategoriaEventoEnum.ACTIVIDAD,
            "tipo": SubtipoReunionEnum.ORDINARIA,
            "modalidad": ModalidadEventoEnum.PRESENCIAL_SEDE,
            "fecha_programada": inicio.isoformat(),
        }
        res2 = api_client.post("/api/v1/expedientes/eventos/", payload_incoherente_2, format="json")
        assert res2.status_code == status.HTTP_400_BAD_REQUEST
        assert "tipo" in res2.data

    def test_validacion_fecha_fin_anterior_a_programada(self, api_client, cd_user):
        """Verifica rechazo 400 si fecha_fin es anterior a fecha_programada (CA8)."""
        api_client.force_authenticate(user=cd_user)
        ahora = timezone.now()
        inicio = ahora + timedelta(days=4)
        fin_invalida = inicio - timedelta(hours=2)

        payload = {
            "titulo": "Reunión Cronología Inválida",
            "categoria": CategoriaEventoEnum.REUNION,
            "tipo": SubtipoReunionEnum.ORDINARIA,
            "modalidad": ModalidadEventoEnum.PRESENCIAL_SEDE,
            "fecha_programada": inicio.isoformat(),
            "fecha_fin": fin_invalida.isoformat(),
        }
        res = api_client.post("/api/v1/expedientes/eventos/", payload, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "fecha_fin" in res.data

    def test_validacion_modalidad_ubicacion_requerida(self, api_client, cd_user):
        """Verifica requerimiento de ubicación para EXTERNA y enlace para VIRTUAL (CA10)."""
        api_client.force_authenticate(user=cd_user)
        ahora = timezone.now()
        inicio = ahora + timedelta(days=4)

        # EXTERNA sin ubicacion -> 400
        payload_ext = {
            "titulo": "Jornada en Predio",
            "categoria": CategoriaEventoEnum.ACTIVIDAD,
            "tipo": SubtipoActividadEnum.JORNADA,
            "modalidad": ModalidadEventoEnum.PRESENCIAL_EXTERNA,
            "ubicacion": "",
            "fecha_programada": inicio.isoformat(),
        }
        res_ext = api_client.post("/api/v1/expedientes/eventos/", payload_ext, format="json")
        assert res_ext.status_code == status.HTTP_400_BAD_REQUEST
        assert "ubicacion" in res_ext.data

        # VIRTUAL sin enlace -> 400
        payload_virt = {
            "titulo": "Reunión Virtual",
            "categoria": CategoriaEventoEnum.REUNION,
            "tipo": SubtipoReunionEnum.ORDINARIA,
            "modalidad": ModalidadEventoEnum.VIRTUAL,
            "ubicacion": "",
            "fecha_programada": inicio.isoformat(),
        }
        res_virt = api_client.post("/api/v1/expedientes/eventos/", payload_virt, format="json")
        assert res_virt.status_code == status.HTTP_400_BAD_REQUEST
        assert "ubicacion" in res_virt.data

        # VIRTUAL con enlace válido -> 201
        payload_virt["ubicacion"] = "https://meet.google.com/aveit-td-2026"
        res_virt_ok = api_client.post("/api/v1/expedientes/eventos/", payload_virt, format="json")
        assert res_virt_ok.status_code == status.HTTP_201_CREATED
        assert res_virt_ok.data["ubicacion"] == "https://meet.google.com/aveit-td-2026"

    def test_convocatoria_con_menos_de_2_dias_habiles_resulta_no_sancionable(
        self, api_client, cd_user
    ):
        """Convocatoria con antelación menor a 2 días hábiles es NO_SANCIONABLE (CA1, CA2)."""
        api_client.force_authenticate(user=cd_user)
        ahora = timezone.now()
        inicio_inmediato = ahora + timedelta(hours=3)  # Muy poco preaviso

        payload = {
            "titulo": "Reunión de Emergencia",
            "categoria": CategoriaEventoEnum.REUNION,
            "tipo": SubtipoReunionEnum.EXTRAORDINARIA,
            "modalidad": ModalidadEventoEnum.PRESENCIAL_SEDE,
            "fecha_programada": inicio_inmediato.isoformat(),
        }
        res = api_client.post("/api/v1/expedientes/eventos/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data["es_sancionable"] is False
        assert "2 días hábiles" in res.data["motivo_no_sancionable"]

    def test_filtros_y_busqueda_eventos(self, api_client, cd_user):
        """Verifica filtros por categoría, modalidad, estado y búsqueda textual."""
        EventoInstitucional.objects.create(
            titulo="Mantenimiento Sede Norte",
            categoria=CategoriaEventoEnum.ACTIVIDAD,
            tipo=SubtipoActividadEnum.MANTENIMIENTO,
            modalidad=ModalidadEventoEnum.PRESENCIAL_EXTERNA,
            ubicacion="Sede Norte",
            fecha_publicacion=timezone.now(),
            fecha_programada=timezone.now() + timedelta(days=6),
            convocante=cd_user.socio,
            estado=EstadoEventoEnum.PROGRAMADA,
            es_sancionable=True,
        )
        EventoInstitucional.objects.create(
            titulo="Reunión Extraordinaria Virtual",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.EXTRAORDINARIA,
            modalidad=ModalidadEventoEnum.VIRTUAL,
            ubicacion="https://meet.google.com/xyz",
            fecha_publicacion=timezone.now(),
            fecha_programada=timezone.now() + timedelta(days=7),
            convocante=cd_user.socio,
            estado=EstadoEventoEnum.PROGRAMADA,
            es_sancionable=False,
        )

        api_client.force_authenticate(user=cd_user)

        # Filtro categoría
        res_cat = api_client.get("/api/v1/expedientes/eventos/?categoria=ACTIVIDAD")
        assert res_cat.status_code == status.HTTP_200_OK
        data_cat = _extract_results(res_cat.data)
        assert all(e["categoria"] == CategoriaEventoEnum.ACTIVIDAD for e in data_cat)

        # Filtro modalidad
        res_mod = api_client.get("/api/v1/expedientes/eventos/?modalidad=VIRTUAL")
        assert res_mod.status_code == status.HTTP_200_OK
        data_mod = _extract_results(res_mod.data)
        assert any(e["modalidad"] == ModalidadEventoEnum.VIRTUAL for e in data_mod)

        # Filtro sancionable
        res_sanc = api_client.get("/api/v1/expedientes/eventos/?es_sancionable=false")
        assert res_sanc.status_code == status.HTTP_200_OK
        data_sanc = _extract_results(res_sanc.data)
        assert any(e["es_sancionable"] is False for e in data_sanc)

        # Búsqueda textual
        res_search = api_client.get("/api/v1/expedientes/eventos/?search=Norte")
        assert res_search.status_code == status.HTTP_200_OK
        data_search = _extract_results(res_search.data)
        assert len(data_search) == 1
        assert "Norte" in data_search[0]["titulo"]


@pytest.mark.django_db
class TestAsistenciasYSancionesAPI:
    """Pruebas funcionales de endpoints de asistencias, escala y motivo circunstanciado."""

    def test_reportar_asistencia_motivo_circunstanciado_obligatorio(
        self, api_client, cd_user, socio_user_1
    ):
        """Rechazo 400 si el motivo circunstanciado de algún convocado está en blanco (CA10)."""
        evento = EventoInstitucional.objects.create(
            titulo="Reunión Ordinaria",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            fecha_publicacion=timezone.now(),
            fecha_programada=timezone.now() + timedelta(days=5),
            convocante=cd_user.socio,
            es_sancionable=True,
        )

        api_client.force_authenticate(user=cd_user)
        payload_sin_motivo = {
            "asistencias": [
                {
                    "socio_id": socio_user_1.socio.id,
                    "estado_asistencia": EstadoAsistenciaEventoEnum.AUSENTE,
                    "motivo": "   ",  # En blanco
                }
            ]
        }
        res = api_client.post(
            f"/api/v1/expedientes/eventos/{evento.id}/reportar-asistencia/",
            payload_sin_motivo,
            format="json",
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "asistencias" in res.data

    def test_reportar_asistencia_escala_1_5_puntos_reunion_extraordinaria(
        self, api_client, cd_user, socio_user_1
    ):
        """
        Verifica que la inasistencia injustificada a una reunión extraordinaria genere
        un expediente por -1.50 puntos (CA3) sin alterar manualmente el saldo en MySQL (CA5).
        """
        evento = EventoInstitucional.objects.create(
            titulo="Reunión Extraordinaria de Presupuesto",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.EXTRAORDINARIA,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            fecha_publicacion=timezone.now() - timedelta(days=5),
            fecha_programada=timezone.now() + timedelta(days=3),
            convocante=cd_user.socio,
            es_sancionable=True,
        )
        AsistenciaEvento.objects.create(
            evento=evento,
            socio=socio_user_1.socio,
            estado_asistencia=EstadoAsistenciaEventoEnum.AUSENTE,
            motivo="Convocado",
        )

        api_client.force_authenticate(user=cd_user)
        payload = {
            "asistencias": [
                {
                    "socio_id": socio_user_1.socio.id,
                    "estado_asistencia": EstadoAsistenciaEventoEnum.AUSENTE,
                    "motivo": (
                        "Falta injustificada sin preaviso ni causa médica acreditada (Art. 85.b)."
                    ),
                }
            ],
            "cerrar_evento": True,
        }

        res = api_client.post(
            f"/api/v1/expedientes/eventos/{evento.id}/reportar-asistencia/",
            payload,
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.data

        assert data["es_sancionable"] is True
        assert len(data["expedientes_creados"]) == 1
        exp_info = data["expedientes_creados"][0]
        assert exp_info["socio_id"] == socio_user_1.socio.id
        assert Decimal(str(exp_info["puntos"])) == Decimal("-1.50")

        # Comprobar que en la base de datos el expediente se encuentra en estado CREADO
        from expedientes.models import Expediente

        expediente = Expediente.objects.get(numero=exp_info["numero"])
        assert expediente.estado == EstadoExpedienteEnum.CREADO
        assert expediente.puntos == Decimal("-1.50")

        # Regla 3 / CA5: Comprobar que el saldo del socio permanece inalterado
        socio_actualizado = Socio.objects.get(pk=socio_user_1.socio.id)
        # El saldo no se altera directamente con UPDATE en la emisión
        assert getattr(socio_actualizado, "saldo", Decimal("0.00")) == Decimal("0.00")

    def test_reportar_asistencia_evento_no_sancionable_no_crea_expedientes(
        self, api_client, cd_user, socio_user_1
    ):
        """Evento NO_SANCIONABLE registra la asistencia pero inhiba expedientes (CA2)."""
        evento = EventoInstitucional.objects.create(
            titulo="Reunión Extemporánea",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            fecha_publicacion=timezone.now(),
            fecha_programada=timezone.now() + timedelta(hours=2),
            convocante=cd_user.socio,
            es_sancionable=False,
            motivo_no_sancionable="Convocatoria sin preaviso",
        )

        api_client.force_authenticate(user=cd_user)
        payload = {
            "asistencias": [
                {
                    "socio_id": socio_user_1.socio.id,
                    "estado_asistencia": EstadoAsistenciaEventoEnum.AUSENTE,
                    "motivo": "Falta a reunión extemporánea.",
                }
            ]
        }
        res = api_client.post(
            f"/api/v1/expedientes/eventos/{evento.id}/reportar-asistencia/",
            payload,
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        data = res.data

        assert data["es_sancionable"] is False
        assert len(data["expedientes_creados"]) == 0
        assert len(data["apercibimientos_creados"]) == 0

        # La asistencia fue persistida para fines informativos
        asistencia = AsistenciaEvento.objects.get(evento=evento, socio=socio_user_1.socio)
        assert asistencia.estado_asistencia == EstadoAsistenciaEventoEnum.AUSENTE
        assert asistencia.expediente_generado is None

    def test_action_asistencias_get_y_post(self, api_client, cd_user, socio_user_1):
        """Verifica action /api/v1/expedientes/eventos/{id}/asistencias/ para GET y POST."""
        evento = EventoInstitucional.objects.create(
            titulo="Reunión Ordinaria de Cómputos",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            fecha_publicacion=timezone.now() - timedelta(days=4),
            fecha_programada=timezone.now() + timedelta(days=2),
            convocante=cd_user.socio,
            es_sancionable=True,
        )
        AsistenciaEvento.objects.create(
            evento=evento,
            socio=socio_user_1.socio,
            estado_asistencia=EstadoAsistenciaEventoEnum.AUSENTE,
            motivo="Convocado inicial",
        )

        api_client.force_authenticate(user=cd_user)

        # 1. GET asistencias
        res_get = api_client.get(f"/api/v1/expedientes/eventos/{evento.id}/asistencias/")
        assert res_get.status_code == status.HTTP_200_OK
        assert len(res_get.data) == 1
        assert res_get.data[0]["socio_id"] == socio_user_1.socio.id

        # 2. POST asistencias para marcar Presente
        payload_update = {
            "asistencias": [
                {
                    "socio_id": socio_user_1.socio.id,
                    "estado_asistencia": EstadoAsistenciaEventoEnum.PRESENTE,
                    "motivo": "Presente puntualmente en sala.",
                }
            ]
        }
        res_post = api_client.post(
            f"/api/v1/expedientes/eventos/{evento.id}/asistencias/",
            payload_update,
            format="json",
        )
        assert res_post.status_code == status.HTTP_200_OK

        asistencia = AsistenciaEvento.objects.get(evento=evento, socio=socio_user_1.socio)
        assert asistencia.estado_asistencia == EstadoAsistenciaEventoEnum.PRESENTE
        assert asistencia.motivo == "Presente puntualmente en sala."

    def test_action_procesar_asistencias(self, api_client, cd_user, socio_user_1):
        """Verifica action /api/v1/expedientes/eventos/{id}/procesar-asistencias/."""
        evento = EventoInstitucional.objects.create(
            titulo="Jornada Operativa",
            categoria=CategoriaEventoEnum.ACTIVIDAD,
            tipo=SubtipoActividadEnum.VOLUNTARIADO,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            fecha_publicacion=timezone.now() - timedelta(days=5),
            fecha_programada=timezone.now() + timedelta(days=3),
            convocante=cd_user.socio,
            es_sancionable=True,
        )
        AsistenciaEvento.objects.create(
            evento=evento,
            socio=socio_user_1.socio,
            estado_asistencia=EstadoAsistenciaEventoEnum.AUSENTE,
            motivo="Ausencia a voluntariado sin aviso",
        )

        api_client.force_authenticate(user=cd_user)
        res_proc = api_client.post(
            f"/api/v1/expedientes/eventos/{evento.id}/procesar-asistencias/",
            {},
            format="json",
        )
        assert res_proc.status_code == status.HTTP_200_OK
        assert res_proc.data["es_sancionable"] is True
        assert len(res_proc.data["expedientes_creados"]) == 1


@pytest.mark.django_db
class TestRegistroApercibimientosAPI:
    """Pruebas del libro de llamados de atención y control de acceso (CA4)."""

    def test_socio_no_puede_consultar_apercibimientos_de_otro_socio(
        self, api_client, socio_user_1, socio_user_2
    ):
        """Verifica que un socio ordinario reciba 403 al consultar apercibimientos ajenos."""
        AtencionFelicitacion.objects.create(
            socio=socio_user_2.socio,
            llamadosAtencion=1,
        )

        api_client.force_authenticate(user=socio_user_1)
        res = api_client.get(f"/api/v1/expedientes/socios/{socio_user_2.socio.id}/apercibimientos/")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_socio_consulta_propios_apercibimientos(self, api_client, socio_user_1):
        """Verifica que un socio pueda consultar su propio registro de llamados de atención."""
        AtencionFelicitacion.objects.create(
            socio=socio_user_1.socio,
            llamadosAtencion=1,
        )

        api_client.force_authenticate(user=socio_user_1)
        res = api_client.get(f"/api/v1/expedientes/socios/{socio_user_1.socio.id}/apercibimientos/")
        assert res.status_code == status.HTTP_200_OK
        assert len(res.data) == 1
        assert res.data[0]["socio_id"] == socio_user_1.socio.id
        assert res.data[0]["llamadosAtencion"] == 1

    def test_autoridades_consultan_apercibimientos_de_cualquier_socio(
        self, api_client, cd_user, td_user, socio_user_1
    ):
        """Verifica que CD y TD puedan consultar el libro de llamados de cualquier socio."""
        AtencionFelicitacion.objects.create(
            socio=socio_user_1.socio,
            llamadosAtencion=1,
        )

        # CD
        api_client.force_authenticate(user=cd_user)
        res_cd = api_client.get(
            f"/api/v1/expedientes/socios/{socio_user_1.socio.id}/apercibimientos/"
        )
        assert res_cd.status_code == status.HTTP_200_OK
        assert len(res_cd.data) == 1

        # TD
        api_client.force_authenticate(user=td_user)
        res_td = api_client.get(
            f"/api/v1/expedientes/socios/{socio_user_1.socio.id}/apercibimientos/"
        )
        assert res_td.status_code == status.HTTP_200_OK
        assert len(res_td.data) == 1

    def test_viewset_apercibimientos_filtrado_por_socio(
        self, api_client, cd_user, socio_user_1
    ):
        """Verifica filtros de socio en /api/v1/expedientes/apercibimientos/."""
        AtencionFelicitacion.objects.create(
            socio=socio_user_1.socio,
            llamadosAtencion=2,
            felicitaciones=1,
        )

        api_client.force_authenticate(user=cd_user)
        res = api_client.get(
            f"/api/v1/expedientes/apercibimientos/?socio_id={socio_user_1.socio.id}"
        )
        assert res.status_code == status.HTTP_200_OK
        data = _extract_results(res.data)
        assert len(data) == 1
        assert data[0]["llamadosAtencion"] == 2
        assert data[0]["felicitaciones"] == 1



@pytest.mark.django_db
class TestRutasDirectasEventosAPI:
    """Verifica compatibilidad con la ruta directa /api/v1/eventos/."""

    def test_ruta_directa_api_v1_eventos(self, api_client, cd_user):
        """Verifica que /api/v1/eventos/ resuelva correctamente a EventoInstitucionalViewSet."""
        evento = EventoInstitucional.objects.create(
            titulo="Reunión Directa",
            categoria=CategoriaEventoEnum.REUNION,
            tipo=SubtipoReunionEnum.ORDINARIA,
            modalidad=ModalidadEventoEnum.PRESENCIAL_SEDE,
            fecha_publicacion=timezone.now(),
            fecha_programada=timezone.now() + timedelta(days=5),
            convocante=cd_user.socio,
            es_sancionable=True,
        )

        api_client.force_authenticate(user=cd_user)
        res_list = api_client.get("/api/v1/eventos/")
        assert res_list.status_code == status.HTTP_200_OK
        data = _extract_results(res_list.data)
        assert any(e["id"] == evento.id for e in data)

        res_detail = api_client.get(f"/api/v1/eventos/{evento.id}/asistencias/")
        assert res_detail.status_code == status.HTTP_200_OK
