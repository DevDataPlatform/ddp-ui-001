# Generated by Django 4.2 on 2025-01-15 11:27

import ddpui.models.llm
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("ddpui", "0115_remove_org_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="assistantprompt",
            name="type",
            field=models.CharField(
                choices=[
                    ("log_summarization", "LOG_SUMMARIZATION"),
                    ("long_text_summarization", "LONG_TEXT_SUMMARIZATION"),
                    ("chat_with_data_assistant", "CHAT_WITH_DATA_ASSISTANT"),
                ],
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name="llmsession",
            name="session_type",
            field=models.CharField(
                choices=[
                    ("log_summarization", "LOG_SUMMARIZATION"),
                    ("long_text_summarization", "LONG_TEXT_SUMMARIZATION"),
                    ("chat_with_data_assistant", "CHAT_WITH_DATA_ASSISTANT"),
                ],
                default=ddpui.models.llm.LlmAssistantType["LOG_SUMMARIZATION"],
                max_length=100,
            ),
        ),
        migrations.AlterField(
            model_name="userprompt",
            name="type",
            field=models.CharField(
                choices=[
                    ("log_summarization", "LOG_SUMMARIZATION"),
                    ("long_text_summarization", "LONG_TEXT_SUMMARIZATION"),
                    ("chat_with_data_assistant", "CHAT_WITH_DATA_ASSISTANT"),
                ],
                default=ddpui.models.llm.LlmAssistantType["LONG_TEXT_SUMMARIZATION"],
                max_length=100,
            ),
        ),
        migrations.CreateModel(
            name="Thread",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_created=True, default=django.utils.timezone.now),
                ),
                ("uuid", models.UUIDField(editable=False, unique=True)),
                ("session_id", models.CharField(max_length=200, null=True)),
                ("meta", models.JSONField(null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("open", "OPEN"), ("close", "CLOSE")],
                        default="open",
                        max_length=50,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "orguser",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="ddpui.orguser"
                    ),
                ),
            ],
            options={
                "db_table": "ddpui_threads",
            },
        ),
        migrations.CreateModel(
            name="Message",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_created=True, default=django.utils.timezone.now),
                ),
                ("content", models.TextField()),
                (
                    "type",
                    models.CharField(
                        choices=[("ai", "AI"), ("human", "HUMAN"), ("system", "SYSTEM")],
                        default="human",
                        max_length=50,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "recipient",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="recipient",
                        to="ddpui.orguser",
                    ),
                ),
                (
                    "sender",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sender",
                        to="ddpui.orguser",
                    ),
                ),
                (
                    "thread",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="ddpui.thread"
                    ),
                ),
            ],
            options={
                "db_table": "ddpui_messages",
            },
        ),
    ]