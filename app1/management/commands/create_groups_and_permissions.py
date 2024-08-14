
#NOT USED FOR PROJECT JUST TO LEARN

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from app1.models import Product

class Command(BaseCommand):
    help = 'Create user groups and assign permissions'

    def handle(self, *args, **kwargs):
        # Create groups
        product_viewers, created = Group.objects.get_or_create(name='RetrofitUser')
        product_adders, created = Group.objects.get_or_create(name='Store')

        # Get product permissions
        content_type = ContentType.objects.get_for_model(Product)
        view_product_perm = Permission.objects.get(codename='view_product', content_type=content_type)
        add_product_perm = Permission.objects.get(codename='add_product', content_type=content_type)

        # Assign permissions to groups
        product_viewers.permissions.add(view_product_perm)
        product_adders.permissions.add(add_product_perm)

        self.stdout.write(self.style.SUCCESS('Successfully created groups and assigned permissions'))
