from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            return None
        # Normalize email to lower-case for case-insensitive auth
        normalized_email = username.strip().lower()
        try:
            user = UserModel.objects.get(email__iexact=normalized_email)
        except UserModel.DoesNotExist:
            return None
        else:
            if user.check_password(password):
                return user
        return None
