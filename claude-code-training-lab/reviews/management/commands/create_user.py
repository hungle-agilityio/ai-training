from getpass import getpass
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError, CommandParser


class Command(BaseCommand):
    help = "Create an active user who is not staff; the password is asked twice."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("username")

    def handle(self, *args: Any, **options: Any) -> None:
        username: str = options["username"]
        users = get_user_model()
        if users.objects.filter(username=username).exists():
            raise CommandError(f"User {username} already exists.")
        password = getpass("Password: ")
        if getpass("Password (again): ") != password:
            raise CommandError("The two passwords differ.")
        user = users(username=username, is_active=True, is_staff=False)
        try:
            validate_password(password, user=user)
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from error
        user.set_password(password)
        user.save()
        self.stdout.write(f"Created user {username}.")
