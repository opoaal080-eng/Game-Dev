from django.db import migrations


def rebrand_ashfall_default(apps, schema_editor):
    Page = apps.get_model("portal", "PublicGamePage")
    # Change only the original default, never a custom value entered by a developer.
    Page.objects.filter(
        eyebrow="NIGHTWELL · ИГРОВОЙ ПРОЕКТ"
    ).update(eyebrow="NIGHTWELL STUDIO · ИГРОВОЙ ПРОЕКТ")


class Migration(migrations.Migration):
    dependencies = [("portal", "0005_public_game_site")]

    operations = [
        migrations.RunPython(rebrand_ashfall_default, migrations.RunPython.noop),
    ]
