from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0005_deliverycrewuser_manageruser'),
    ]

    operations = [
        # The Cart model now lives in the cart app: keep the table and its rows, only rename the table
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.AlterModelTable(name='cart', table='cart_cart'),
            ],
            state_operations=[
                migrations.DeleteModel(name='Cart'),
            ],
        ),
    ]
