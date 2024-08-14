from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class Product(models.Model):
    prod_id = models.CharField(max_length=50, primary_key=True, unique=True)
    name = models.CharField(max_length=50, default='')
    image_url = models.URLField(max_length=100)

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(verbose_name="email address", max_length=255, )
    role = models.CharField(max_length=20, default='')

    def __str__(self):
        return self.user.username
