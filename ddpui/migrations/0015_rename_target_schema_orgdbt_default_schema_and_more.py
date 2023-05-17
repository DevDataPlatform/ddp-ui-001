# Generated by Django 4.1.7 on 2023-05-15 08:39

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ddpui", "0014_alter_orgdbt_target_schema"),
    ]

    operations = [
        migrations.RenameField(
            model_name="orgdbt",
            old_name="target_schema",
            new_name="default_schema",
        ),
        migrations.RemoveField(
            model_name="orgdbt",
            name="target_name",
        ),
        migrations.AddField(
            model_name="orgdataflow",
            name="flow_id",
            field=models.CharField(max_length=36, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="orgdataflow",
            name="cron",
            field=models.CharField(max_length=36, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name="orgdataflow",
            name="deployment_id",
            field=models.CharField(max_length=36, null=True, unique=True),
        ),
    ]
