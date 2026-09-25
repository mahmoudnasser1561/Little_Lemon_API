from django.db import models, transaction
from django.contrib.auth.models import User, Group, UserManager
from django.contrib.auth.password_validation import validate_password

class Category(models.Model):
    slug = models.SlugField()
    title = models.CharField(max_length=255, db_index=True)
    def __str__(self): return self.title

class MenuItem(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)
    featured = models.BooleanField(db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    def __str__(self): return self.title

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_crew = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="delivery_crew", null=True)
    status = models.BooleanField(db_index=True, default=0)
    total = models.DecimalField(max_digits=6, decimal_places=2)
    date = models.DateField(db_index=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    # SET_NULL, not CASCADE: deleting a menu item must not delete the order history that
    menuitem = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        unique_together = ('order', 'menuitem')

# Staff roles: a User that belongs to the role's group, created and validated through the role model
class RoleUserManager(UserManager):
    use_in_migrations = False
    role = None

    def get_queryset(self):
        return super().get_queryset().filter(groups__name=self.role)

    def create_user(self, username, password, email=None, **extra_fields):
        user = self.model(username=username, email=self.normalize_email(email), **extra_fields)
        validate_password(password, user)
        user.set_password(password)
        user.full_clean()
        with transaction.atomic():
            user.save(using=self._db)
            user.groups.add(Group.objects.get(name=self.role))
        return user

class ManagerUserManager(RoleUserManager):
    role = 'Manager'

class ManagerUser(User):
    objects = ManagerUserManager()

    class Meta:
        proxy = True