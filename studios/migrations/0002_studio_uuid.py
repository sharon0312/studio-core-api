
import uuid

from django.db import migrations, models


def populate_studio_uuids(apps, schema_editor):
    Studio = apps.get_model("studios", "Studio")

    for studio in Studio.objects.filter(uuid__isnull=True).iterator():
        studio.uuid = uuid.uuid4()
        studio.save(update_fields=["uuid"])


class Migration(migrations.Migration):
    dependencies = [
        ("studios", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="studio",
            name="uuid",
            field=models.UUIDField(
                null=True,
                editable=False,
            ),
        ),
        migrations.RunPython(
            populate_studio_uuids,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="studio",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
            ),
        ),
    ]
