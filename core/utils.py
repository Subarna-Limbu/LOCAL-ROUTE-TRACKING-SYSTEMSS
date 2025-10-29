def bfs_find_routes(graph, start, end):
    visited = set()
    queue = [[start]]

    if start == end:
        return [start]

    while queue:
        path = queue.pop(0)
        node = path[-1]

        if node not in visited:
            neighbours = graph.get(node, [])

            for neighbour in neighbours:
                new_path = list(path)
                new_path.append(neighbour)
                queue.append(new_path)

                if neighbour == end:
                    return new_path
            visited.add(node)
    return []

from django.core.mail import send_mail
from django.conf import settings
from .models import EmailOTP

def send_otp_email(email, otp_code, purpose='registration'):
    """Send OTP verification email
    
    Args:
        email: Recipient email address
        otp_code: 6-digit OTP code
        purpose: 'registration' or 'password_reset'
    """
    if purpose == 'password_reset':
        subject = 'Smart Transport - Password Reset Code'
        message = f'''
Hello,

You requested to reset your password for your Smart Transport account.

Your password reset code is:

{otp_code}

This code will expire in {getattr(settings, 'OTP_EXPIRY_MINUTES', 10)} minutes.

If you didn't request this, please ignore this email and your password will remain unchanged.

Best regards,
Smart Transport Team
        '''
    else:
        # Default registration message
        subject = 'Smart Transport - Email Verification'
        message = f'''
Hello,

Your verification code for Smart Transport registration is:

{otp_code}

This code will expire in {getattr(settings, 'OTP_EXPIRY_MINUTES', 10)} minutes.

If you didn't request this code, please ignore this email.

Best regards,
Smart Transport Team
        '''
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False