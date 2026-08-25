from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import Group, Permission, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models

phone_validator = RegexValidator(
    regex=r'^\+7\d{10}$',
    message='Номер телефона в формате +77001234567',
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email=None, phone=None, password=None, **extra_fields):
        if not email and not phone:
            raise ValueError('Нужно указать email или телефон')
        email = self.normalize_email(email) if email else None
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, phone=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, phone, password, **extra_fields)

    def create_superuser(self, email=None, phone=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('У суперпользователя должен быть is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('У суперпользователя должен быть is_superuser=True')
        return self._create_user(email, phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField('email', unique=True, null=True, blank=True)
    phone = models.CharField(
        'телефон', max_length=12, unique=True, null=True, blank=True,
        validators=[phone_validator],
    )
    first_name = models.CharField('имя', max_length=100, blank=True)
    last_name = models.CharField('фамилия', max_length=100, blank=True)
    is_active = models.BooleanField('активен', default=True)
    is_staff = models.BooleanField('сотрудник', default=False)
    date_joined = models.DateTimeField('дата регистрации', auto_now_add=True)

    groups = models.ManyToManyField(Group, verbose_name='группы', blank=True, related_name='accounts_user_set')
    user_permissions = models.ManyToManyField(
        Permission, verbose_name='права доступа', blank=True, related_name='accounts_user_set',
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(email__isnull=False) | models.Q(phone__isnull=False),
                name='user_has_email_or_phone',
            ),
        ]

    def __str__(self):
        return self.email or self.phone or f'User #{self.pk}'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or str(self)

    def get_short_name(self):
        return self.first_name or str(self)


class Address(models.Model):
    user = models.ForeignKey(
        User, verbose_name='пользователь',
        related_name='addresses', on_delete=models.CASCADE,
    )
    city = models.CharField('город', max_length=100)
    street = models.CharField('улица', max_length=255)
    house = models.CharField('дом', max_length=20)
    apartment = models.CharField('квартира/офис', max_length=20, blank=True)
    postal_code = models.CharField('индекс', max_length=20, blank=True)
    comment = models.CharField('комментарий курьеру', max_length=255, blank=True)
    is_default = models.BooleanField('адрес по умолчанию', default=False)

    class Meta:
        verbose_name = 'адрес доставки'
        verbose_name_plural = 'адреса доставки'
        ordering = ['-is_default', 'id']

    def __str__(self):
        parts = [self.city, self.street, self.house]
        if self.apartment:
            parts.append(f'кв. {self.apartment}')
        return ', '.join(parts)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            Address.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
