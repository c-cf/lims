# Step 3: Remove old fields and make WIP.equipment non-nullable.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("wip", "0005_migrate_wip_data"),
    ]

    operations = [
        # Remove old WIP.sample OneToOneField.
        migrations.RemoveField(
            model_name="wip",
            name="sample",
        ),
        # Remove old Dispatch.equipment ForeignKey.
        migrations.RemoveIndex(
            model_name="dispatch",
            name="dispatch_equipme_a6bbd1_idx",
        ),
        migrations.RemoveField(
            model_name="dispatch",
            name="equipment",
        ),
        # Make WIP.equipment non-nullable.
        migrations.AlterField(
            model_name="wip",
            name="equipment",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="wips",
                to="equipment.equipment",
            ),
        ),
    ]
