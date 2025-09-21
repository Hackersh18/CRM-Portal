from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create a superuser if it does not exist'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Check if superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(
                self.style.WARNING('Superuser already exists')
            )
            return
        
        # Create superuser
        try:
            user = User.objects.create_superuser(
                email='admin@example.com',
                password='admin123'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser: {user.email}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {str(e)}')
            )
