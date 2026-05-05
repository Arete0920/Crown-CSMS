import os


def main() -> int:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")

    import django
    from django.core.management import call_command

    django.setup()
    call_command("bootstrap_superuser")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
