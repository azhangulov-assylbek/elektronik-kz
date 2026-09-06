from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import Group, Permission, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

phone_validator = RegexValidator(
    regex=r'^\+7\d{10}$',
    message=_('Номер телефона в формате +77001234567'),
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
    class Role(models.TextChoices):
        CUSTOMER = 'customer', _('Покупатель')
        SELLER = 'seller', _('Продавец')
        ADMIN = 'admin', _('Администратор')

    email = models.EmailField(_('email'), unique=True, null=True, blank=True)
    phone = models.CharField(
        _('телефон'), max_length=12, unique=True, null=True, blank=True,
        validators=[phone_validator],
    )
    first_name = models.CharField(_('имя'), max_length=100, blank=True)
    last_name = models.CharField(_('фамилия'), max_length=100, blank=True)
    role = models.CharField(_('роль'), max_length=20, choices=Role.choices, default=Role.CUSTOMER)
    is_active = models.BooleanField(_('активен'), default=True)
    is_staff = models.BooleanField(_('сотрудник'), default=False)
    date_joined = models.DateTimeField(_('дата регистрации'), auto_now_add=True)

    # mypy(assignment) на groups/user_permissions ниже — известная особенность
    # django-stubs: для переопределённых полей выводится менеджер, завязанный
    # на конкретный класс модели, что формально не совпадает с обобщённой
    # аннотацией в PermissionsMixin. Переопределение полей с другим
    # related_name — штатная рекомендация Django для кастомного User.
    groups = models.ManyToManyField(Group, verbose_name='группы', blank=True, related_name='accounts_user_set')  # type: ignore[assignment]  # noqa: E501
    user_permissions = models.ManyToManyField(  # type: ignore[assignment]
        Permission, verbose_name='права доступа', blank=True, related_name='accounts_user_set')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('пользователь')
        verbose_name_plural = _('пользователи')
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

    def save(self, *args, **kwargs):
        if self.role == self.Role.ADMIN:
            # роль "администратор" всегда даёт доступ в /admin/ — не нужно
            # отдельно выставлять is_staff вручную
            self.is_staff = True
        super().save(*args, **kwargs)

    @property
    def can_manage_catalog(self):
        """Продавец и администратор работают с карточками товаров."""
        return self.is_superuser or self.role in (self.Role.SELLER, self.Role.ADMIN)

    @property
    def can_bulk_import_catalog(self):
        """Только администратор загружает каталог файлом (CSV/Excel)."""
        return self.is_superuser or self.role == self.Role.ADMIN


class Address(models.Model):
    user = models.ForeignKey(
        User, verbose_name=_('пользователь'),
        related_name='addresses', on_delete=models.CASCADE,
    )
    city = models.CharField(_('город'), max_length=100)
    street = models.CharField(_('улица'), max_length=255)
    house = models.CharField(_('дом'), max_length=20)
    apartment = models.CharField(_('квартира/офис'), max_length=20, blank=True)
    postal_code = models.CharField(_('индекс'), max_length=20, blank=True)
    comment = models.CharField(_('комментарий курьеру'), max_length=255, blank=True)
    is_default = models.BooleanField(_('адрес по умолчанию'), default=False)

    class Meta:
        verbose_name = _('адрес доставки')
        verbose_name_plural = _('адреса доставки')
        ordering = ['-is_default', 'id']

    def __str__(self):
        parts = [self.city, self.street, self.house]
        if self.apartment:
            parts.append(f'{_("кв.")} {self.apartment}')
        return ', '.join(parts)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            Address.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
