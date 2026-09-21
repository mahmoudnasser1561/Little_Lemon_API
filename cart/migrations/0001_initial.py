import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('restaurant', '0006_move_cart_to_cart_app'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # The cart_cart table already exists (renamed from restaurant_cart in restaurant 0006): state only
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Cart',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('quantity', models.SmallIntegerField()),
                        ('unit_price', models.DecimalField(decimal_places=2, max_digits=6)),
                        ('price', models.DecimalField(decimal_places=2, max_digits=6)),
                        ('menuitem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='restaurant.menuitem')),
                        ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'unique_together': {('menuitem', 'user')},
                    },
                ),
            ],
        ),
    ]
