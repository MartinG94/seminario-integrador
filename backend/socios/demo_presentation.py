"""Contenido ficticio verosímil; las claves técnicas permanecen fuera de los textos visibles."""

from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class ScenePresentation:
    title: str
    reason: str
    place: str = "Sede AVEIT"
    witnesses: str = "Responsables de la actividad que participaron en su organización."
    causal: str = "Actuación informada por la comisión organizadora"

    @property
    def case_text(self) -> str:
        return f"{self.title}\n\n{self.reason}"


SCENE_PRESENTATIONS = MappingProxyType(
    {
        "cause.created.low": ScenePresentation(
            "Demora en devolver equipo prestado",
            "Al cerrar el taller de informática quedó pendiente la devolución de un equipo "
            "entregado al socio para preparar la actividad. La comisión solicita revisar "
            "los antecedentes disponibles y escuchar su explicación antes de resolver.",
            "Laboratorio de informática de la sede",
        ),
        "cause.created.normal": ScenePresentation(
            "Faltantes en el inventario del encuentro",
            "La revisión del material utilizado en el encuentro institucional detectó "
            "elementos sin registrar. Se solicita aclarar la entrega a cargo del socio "
            "y contrastarla con los antecedentes de la comisión organizadora.",
            "Depósito de materiales de la sede",
        ),
        "cause.created.urgent.multi": ScenePresentation(
            "Uso del taller sin autorización",
            "La comisión informó que los dos socios involucrados utilizaron el taller "
            "fuera del horario acordado. Se solicita verificar el acceso, el estado del "
            "equipamiento y la explicación de cada participante de manera individual.",
            "Taller de la sede",
        ),
        "t01.cd.draft": ScenePresentation(
            "Revisión del material del encuentro anual",
            "La comisión prepara una solicitud sobre diferencias en el inventario del "
            "encuentro anual. El borrador queda pendiente de identificar a los socios "
            "involucrados y completar la documentación antes de emitirlo.",
            "Depósito de materiales de la sede",
        ),
        "t01.authority.draft": ScenePresentation(
            "Ausencia en la guardia de recepción",
            "La comisión informó un turno de recepción sin cobertura. Se solicita "
            "verificar el aviso previo del socio responsable y los cambios acordados "
            "con la comisión antes de finalizar esta solicitud.",
            "Mesa de recepción de la sede",
        ),
        "t01.cd.issued.multi": ScenePresentation(
            "Entrega pendiente del material del encuentro",
            "La comisión organizadora informó que el material asignado a los dos socios "
            "no fue entregado al finalizar el encuentro. Cada involucrado debe aclarar "
            "su participación y aportar las constancias de devolución que tuviera.",
            "Salón de actividades de la sede",
            "Integrantes de la comisión que recibieron el material al cierre del encuentro.",
        ),
        "t01.authority.issued": ScenePresentation(
            "Retiro anticipado de la jornada comunitaria",
            "La organización de la jornada informó que el socio se retiró antes de completar "
            "el turno asignado. Se solicita su explicación y la constancia de cualquier "
            "cambio de horario autorizado por los responsables de la actividad.",
            "Jornada comunitaria en la sede",
        ),
        "advanced.review.01": ScenePresentation(
            "Daño informado en un equipo de la biblioteca",
            "Tras una actividad se informó una falla en el equipo que había utilizado "
            "el socio. El Tribunal revisa los antecedentes disponibles y la explicación "
            "del socio, si la hubiera, para distinguir el estado previo del equipo "
            "de lo ocurrido durante su uso.",
            "Biblioteca de la sede",
        ),
        "advanced.review.02": ScenePresentation(
            "Inasistencia al armado del stand institucional",
            "La organización del encuentro informó que el socio no se presentó al "
            "turno de armado acordado. Se revisan los antecedentes disponibles "
            "y la explicación del socio, si la hubiera.",
            "Stand institucional del encuentro",
        ),
        "advanced.review.03": ScenePresentation(
            "Turno de limpieza compartido sin completar",
            "Al finalizar el encuentro quedó pendiente una tarea asignada a ambos "
            "socios. Se revisan las responsabilidades de cada participante y los "
            "avisos a la comisión, sin atribuir automáticamente la misma conducta a los dos.",
            "Salón de actividades de la sede",
        ),
        "advanced.signature.01": ScenePresentation(
            "Entrega fuera de término del informe de comisión",
            "La comisión presentó el informe sobre una entrega realizada fuera del "
            "plazo acordado. Luego de revisar los antecedentes disponibles, "
            "el texto de la resolución quedó preparado para su suscripción.",
            "Secretaría de la sede",
        ),
        "advanced.dispatch.01": ScenePresentation(
            "Faltantes en el registro de elementos prestados",
            "La revisión de los antecedentes disponibles concluyó con una "
            "resolución sobre los elementos a cargo del socio. El expediente permanece "
            "pendiente de comunicar el acto a sus destinatarios.",
            "Depósito de materiales de la sede",
        ),
        "advanced.dispatch.02": ScenePresentation(
            "Ausencia en el turno de atención al público",
            "Se revisaron los antecedentes sobre la falta de cobertura del turno. "
            "La resolución se encuentra preparada y el expediente "
            "permanece pendiente de su comunicación, sin aplicar todavía puntos.",
            "Mesa de atención de la sede",
        ),
        "advanced.emitted.01": ScenePresentation(
            "Reconocimiento por organizar la colecta solidaria",
            "La comisión documentó la participación del socio en la organización y "
            "entrega de la colecta. La resolución emitida individualiza el reconocimiento "
            "y su aplicación de dos puntos a este destinatario.",
            "Jornada de colecta en la sede",
        ),
        "advanced.emitted.02": ScenePresentation(
            "Sanción por incumplir el turno de guardia",
            "El Tribunal revisó los antecedentes sobre la falta de cobertura del turno. "
            "La resolución emitida individualiza la sanción de un punto "
            "y respalda la decisión para este destinatario.",
            "Mesa de recepción de la sede",
        ),
        "advanced.emitted.03": ScenePresentation(
            "Sanción por retirar equipos sin autorización",
            "Los antecedentes disponibles permitieron resolver sobre el "
            "retiro de equipos a cargo del socio. El acto emitido individualiza "
            "la sanción de dos puntos y su destinatario.",
            "Laboratorio de informática de la sede",
        ),
        "advanced.emitted.04": ScenePresentation(
            "Reconocimiento por colaborar en las tutorías",
            "La coordinación de tutorías dejó constancia de la colaboración del socio "
            "en las actividades de apoyo. La resolución emitida individualiza "
            "el reconocimiento de un punto y su aplicación al destinatario.",
            "Aula de tutorías de la sede",
        ),
    }
)


def legacy_scene_reason(key: str) -> str:
    """Plantilla heredada exacta que puede reemplazar el upgrade autorizado."""
    return f"SCRUM-77 [{key}]: causa ficticia para demostrar los recorridos institucionales."


def scene_presentation(key: str) -> ScenePresentation:
    return SCENE_PRESENTATIONS[key]
