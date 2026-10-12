"""Carga socios de demostración para probar el login y el RBAC a mano.

Uso: python manage.py seed_demo
Sólo corre con DEBUG=1: son credenciales conocidas, no deben existir en
producción ni sobre datos reales del padrón.
Las altas usan Junior en años 1–2 y Senior en 3–6 mediante el modelo Socio.
Las cuentas existentes se omiten, conservando categoría, credenciales y permisos.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from socios.models import Role, Socio, Subcomision

UserModel = get_user_model()

DEMO_PASSWORD = "Aveit-Demo-2026!"

DEMO_SOCIOS: list[tuple[str, str, str, str, int]] = [
    ("74907", "Gastiaburu", "Lucas", Role.SOCIO, 2),
    ("85194", "Guillén", "Lucas Martín", Role.FISCALIZADORA, 4),
    ("87414", "Sánchez", "Diego Gabriel", Role.CD, 5),
    ("408917", "Rosales", "Nicolás", Role.TD, 6),
    ("403655", "Villegas", "Axel René", Role.ADMIN, 5),
]


class Command(BaseCommand):
    help = "Crea cinco socios de demostración, con categoría por año social y un rol RBAC cada uno."

    @transaction.atomic
    def handle(self, *args: object, **options: object) -> None:
        if not settings.DEBUG:
            raise CommandError("seed_demo sólo puede ejecutarse con DEBUG=1.")

        subcomision, _ = Subcomision.objects.get_or_create(name="Cómputos")

        for legajo, last_name, first_name, role, social_year in DEMO_SOCIOS:
            if Socio.objects.filter(legajo=legajo).exists():
                self.stdout.write(f"= {legajo} ya existe, se omite")
                continue

            email = f"{legajo}@aveit.test"
            user = UserModel.objects.create_user(
                username=legajo, email=email, password=DEMO_PASSWORD
            )
            socio = Socio.objects.create(
                user=user,
                legajo=legajo,
                first_name=first_name,
                last_name=last_name,
                email=email,
                subcomision=subcomision,
                social_year=social_year,
                role=role,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"+ {socio.legajo} {socio.last_name} "
                    f"rol={socio.role} categoria={socio.get_category_display()}"
                )
            )

        self.stdout.write(f"\nContraseña para todos: {DEMO_PASSWORD}")
