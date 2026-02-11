from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Test email configuration by sending a test email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email address to send test email to')

    def handle(self, *args, **options):
        try:
            send_mail(
                subject='Test Email from Real Estate App',
                message='This is a test email to verify your email configuration is working correctly.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[options['email']],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('Successfully sent test email'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to send email: {str(e)}')) 