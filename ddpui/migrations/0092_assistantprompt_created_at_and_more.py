# Generated by Django 4.2 on 2024-08-27 08:44

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("ddpui", "0091_prefectflowrun_retries"),
    ]

    operations = [
        migrations.AddField(
            model_name="assistantprompt",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="assistantprompt",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="canvaslock",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="canvaslock",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="datafloworgtask",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="datafloworgtask",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="dbtedge",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="dbtedge",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="invitation",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="invitation",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="org",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="org",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="orgdataflowv1",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="orgdataflowv1",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="orgdbt",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="orgdbt",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="orgdbtmodel",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="orgdbtmodel",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="orgdbtoperation",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="orgdbtoperation",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="orgprefectblockv1",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="orgprefectblockv1",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="orgschemachange",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="orgschemachange",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="orgtask",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="orgtask",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="orguser",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="orguser",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="orgwarehouse",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="orgwarehouse",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="prefectflowrun",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="prefectflowrun",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="tasklock",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="userattributes",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
        migrations.AddField(
            model_name="userattributes",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="userpreferences",
            name="created_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="userpreferences",
            name="updated_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name="llmsession",
            name="created_at",
            field=models.DateTimeField(
                auto_created=True, default=django.utils.timezone.now
            ),
        ),
    ]