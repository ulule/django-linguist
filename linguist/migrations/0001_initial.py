# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Translation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                        primary_key=True,
                    ),
                ),
                (
                    "identifier",
                    models.CharField(
                        help_text="The registered model identifier.",
                        max_length=100,
                        verbose_name="identifier",
                        db_index=True,
                    ),
                ),
                (
                    "object_id",
                    models.IntegerField(
                        help_text="The object ID of this translation",
                        verbose_name="The object ID",
                        db_index=True,
                    ),
                ),
                (
                    "language",
                    models.CharField(
                        default=b"en",
                        choices=[
                            (b"en", "English"),
                            (b"de", "German"),
                            (b"fr", "French"),
                            (b"es", "Spanish"),
                            (b"it", "Italian"),
                            (b"pt", "Portuguese"),
                        ],
                        max_length=10,
                        help_text="The language for this translation",
                        verbose_name="language",
                        db_index=True,
                    ),
                ),
                (
                    "field_name",
                    models.CharField(
                        help_text="The model field name for this translation.",
                        max_length=100,
                        verbose_name="field name",
                        db_index=True,
                    ),
                ),
                (
                    "field_value",
                    models.TextField(
                        help_text="The translated content for the field.",
                        null=True,
                        verbose_name="field value",
                    ),
                ),
            ],
            options={
                "abstract": False,
                "verbose_name": "translation",
                "verbose_name_plural": "translations",
            },
        ),
        migrations.AlterUniqueTogether(
            name="translation",
            unique_together=set(
                [("identifier", "object_id", "language", "field_name")]
            ),
        ),
        migrations.AlterIndexTogether(
            name="translation", index_together=set([("identifier", "object_id")])
        ),
    ]
