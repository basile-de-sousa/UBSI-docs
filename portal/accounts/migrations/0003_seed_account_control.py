from django.db import migrations


def seed_control(apps, schema_editor):
    apps.get_model("accounts", "AccountControl").objects.using(schema_editor.connection.alias).get_or_create(pk=1)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_ratebucket_user_access_version_and_more")]
    operations = [migrations.RunPython(seed_control, migrations.RunPython.noop)]
