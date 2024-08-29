from django.db import models
import datetime
import datetime
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.models import UserManager
from django.utils.translation import gettext as _

class User(AbstractBaseUser, PermissionsMixin):
    firstname = models.CharField(max_length=50, blank=True)
    secondname = models.CharField(max_length=50, blank=True)
    register_date = models.DateField(default=datetime.date.today)
    is_active = models.BooleanField(default=True)
    username = models.CharField(max_length=40, unique=True)
    password = models.CharField(max_length=40, null=False)
    email = models.EmailField(blank=True)
    is_admin = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    code = models.CharField(_("Code"), max_length=100, blank=True)
    deleted = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ['firstname', 'secondname', 'email', 'is_admin']

    objects = UserManager()

    def get_full_name(self):
        return "%s %s" % (self.firstname, self.secondname)

    def delete(self):
        self.deleted = True
        self.is_active = False
        username = "%s (deleted %s)" % (self.username, str(datetime.datetime.now().strftime("%d/%m/%Y %H:%M")))
        self.username = username
        self.code = username
        self.is_admin = False
        self.save()
        
    class Meta:
        db_table = 'users'

    


