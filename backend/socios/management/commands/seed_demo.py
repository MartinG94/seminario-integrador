"""Carga socios de demostración para probar el login y el RBAC a mano.

Uso: python manage.py seed_demo
Sólo corre con DEBUG=1: son credenciales conocidas, no deben existir en
producción ni sobre datos reales del padrón.
"""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from socios.models import Role, Socio, Subcomision

UserModel = get_user_model()

DEMO_PASSWORD = "Aveit-Demo-2026!"

DEMO_SOCIOS = [
    ("74907", "Gastiaburu", "Lucas", Role.SOCIO, 2, True, False),
    ("85194", "Guillén", "Lucas Martín", Role.REVISORES, 4, True, False),
    ("87414", "Sánchez", "Diego Gabriel", Role.CD, 5, True, False),
    ("408917", "Rosales", "Nicolás", Role.TD, 6, True, False),
    ("403655", "Villegas", "Axel René", Role.ADMIN, 5, True, False),
    ("409953", "Urviola", "Luis", Role.AUTORIDAD_SC, 4, True, False),
    ("415327", "Quiroz", "Tomas Augusto", Role.SOCIO, 3, True, False),
    # Cuentas de ejemplo para verificación de estados operativos RBAC (S5-07.2)
    ("99001", "Baja", "Socio", Role.SOCIO, 4, False, False),
    ("99002", "Suspendido", "Socio", Role.SOCIO, 4, True, True),
]


class Command(BaseCommand):
    help = "Crea socios de demostración con un rol RBAC y estados operativos de ejemplo."

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo sólo puede ejecutarse con DEBUG=1.")

        subcomision, _ = Subcomision.objects.get_or_create(name="Cómputos")

        for legajo, last_name, first_name, role, social_year, is_enabled, is_suspended in DEMO_SOCIOS:
            if Socio.objects.filter(legajo=legajo).exists():
                self.stdout.write(f"= {legajo} ya existe, se omite")
                continue

            email = f"{legajo}@aveit.test"
            user, _ = UserModel.objects.get_or_create(
                username=legajo,
                defaults={"email": email},
            )
            user.set_password(DEMO_PASSWORD)
            user.save()

            socio = Socio.objects.create(
                user=user,
                legajo=legajo,
                first_name=first_name,
                last_name=last_name,
                email=email,
                subcomision=subcomision,
                social_year=social_year,
                role=role,
                is_enabled=is_enabled,
                is_suspended=is_suspended,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"+ {socio.legajo} {socio.last_name} "
                    f"rol={socio.role} enabled={socio.is_enabled} suspended={socio.is_suspended}"
                )
            )

        self.stdout.write(f"\nContraseña para todos: {DEMO_PASSWORD}")
        from django.core.management import call_command

        try:
            call_command("seed_production_data")
        except Exception as exc:
            self.stdout.write(
                f"Aviso: no se pudo sincronizar seed_production_data automáticamente: {exc}"
            )
