import ssl
from django.core.mail.backends.smtp import EmailBackend

class UnverifiedSSLEmailBackend(EmailBackend):
    """
    Subclass of SMTP EmailBackend to support unverified SSL context.
    Useful for Python 3.14+ SSL verification issues.
    """
    @property
    def connection_class(self):
        # We need to ensure that the connection is created with our context
        # but the base class doesn't easily allow passing context to the constructor 
        # of the connection class (smtplib.SMTP or smtplib.SMTP_SSL) via settings.
        # Instead we override the connection_class or the open() method.
        return super().connection_class

    def open(self):
        if self.connection:
            return False
        
        try:
            # We bypass the default open to inject our context
            import smtplib
            
            connection_params = {}
            if self.timeout is not None:
                connection_params['timeout'] = self.timeout
            
            # Use unverified context
            context = ssl._create_unverified_context()
            connection_params['context'] = context

            if self.use_ssl:
                self.connection = smtplib.SMTP_SSL(self.host, self.port, **connection_params)
            else:
                self.connection = smtplib.SMTP(self.host, self.port, **connection_params)
                if self.use_tls:
                    self.connection.starttls(context=context)
            
            if self.username and self.password:
                self.connection.login(self.username, self.password)
                
            return True
        except Exception:
            if not self.fail_silently:
                raise
            return False
