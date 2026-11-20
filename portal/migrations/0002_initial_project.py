from django.db import migrations


def add_project(apps, schema_editor):
    Project = apps.get_model("portal", "Project")
    Project.objects.get_or_create(slug="main", defaults={"title": "Основной проект", "description": "Рабочее пространство команды"})


class Migration(migrations.Migration):
    dependencies = [("portal", "0001_initial")]
    operations = [migrations.RunPython(add_project, migrations.RunPython.noop)]
