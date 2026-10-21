import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name="report",
            name="reports_rep_latitud_bfcbfa_idx",
        ),
        migrations.RemoveField(
            model_name="report",
            name="address_text",
        ),
        migrations.RemoveField(
            model_name="report",
            name="is_anonymous",
        ),
        migrations.RemoveField(
            model_name="report",
            name="title",
        ),
        migrations.AddField(
            model_name="report",
            name="assigned_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="report",
            name="assigned_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="reports_assigned",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="report",
            name="union",
            field=models.CharField(default="", max_length=120),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="report",
            name="ward",
            field=models.CharField(default="", max_length=120),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="report",
            name="description",
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name="report",
            name="district",
            field=models.ForeignKey(
                help_text="Copied from the reporter's district at submit time.",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="reports",
                to="accounts.district",
            ),
        ),
        migrations.AlterField(
            model_name="report",
            name="latitude",
            field=models.DecimalField(
                blank=True, decimal_places=6, max_digits=9, null=True
            ),
        ),
        migrations.AlterField(
            model_name="report",
            name="longitude",
            field=models.DecimalField(
                blank=True, decimal_places=6, max_digits=9, null=True
            ),
        ),
        migrations.AlterField(
            model_name="report",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("assigned", "Assigned"),
                    ("in_progress", "In Progress"),
                    ("resolved", "Resolved"),
                    ("rejected", "Rejected"),
                ],
                db_index=True,
                default="pending",
                max_length=32,
            ),
        ),
        migrations.AlterField(
            model_name="reportmedia",
            name="file",
            field=models.ImageField(upload_to="reports/%Y/%m/"),
        ),
        migrations.AlterField(
            model_name="reportmedia",
            name="media_type",
            field=models.CharField(
                choices=[("image", "Image"), ("video", "Video")],
                default="image",
                max_length=16,
            ),
        ),
        migrations.AddIndex(
            model_name="report",
            index=models.Index(
                fields=["district", "status"],
                name="reports_rep_distric_e753f3_idx",
            ),
        ),
    ]
