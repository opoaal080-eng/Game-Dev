from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("portal", "0006_nightwell_studio_brand")]

    operations = [
        migrations.AddField(
            model_name="post", name="content_mode",
            field=models.CharField(
                choices=[("markdown", "Текст и Markdown"), ("code", "Скрипт целиком")],
                default="markdown", max_length=12, verbose_name="Формат содержимого",
            ),
        ),
        migrations.AddField(
            model_name="post", name="code_language",
            field=models.CharField(blank=True, default="", max_length=32, verbose_name="Язык кода"),
        ),
    ]
