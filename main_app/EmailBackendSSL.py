"""
Custom Email Backend with SSL handling for password reset emails
"""
import ssl
import smtplib
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.core.mail.message import sanitize_address
from django.conf import settings


class SSLEmailBackend(SMTPEmailBackend):
    """
    Custom SMTP email backend that handles SSL certificate verification issues
    """
    
    def open(self):
        """
        Ensure an open connection to the email server. Return whether or not a
        new connection was required (True or False) or None if an exception
        occurred.
        """
        if self.connection:
            # Nothing to do if the connection is already open.
            return False
        
        try:
            # Create SSL context that doesn't verify certificates
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect to the SMTP server
            if self.use_ssl:
                self.connection = smtplib.SMTP_SSL(
                    self.host, 
                    self.port, 
                    timeout=self.timeout,
                    context=context
                )
            else:
                self.connection = smtplib.SMTP(
                    self.host, 
                    self.port, 
                    timeout=self.timeout
                )
                
            # Start TLS if needed
            if self.use_tls:
                self.connection.starttls(context=context)
                
            # Authenticate if credentials are provided
            if self.username and self.password:
                self.connection.login(self.username, self.password)
                
            return True
            
        except Exception as e:
            if not self.fail_silently:
                raise e
            return None
