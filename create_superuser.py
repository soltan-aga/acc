from django.contrib.auth.models import User
from django.db.utils import IntegrityError

try:
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='giltmole'
    )
    print('Superuser created successfully')
except IntegrityError:
    print('Superuser already exists')
