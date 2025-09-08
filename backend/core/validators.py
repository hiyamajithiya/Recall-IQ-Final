# core/validators.py
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class CustomPasswordValidator:
    def __init__(self, min_length=12, require_uppercase=True, require_lowercase=True,
                 require_digits=True, require_symbols=True):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_symbols = require_symbols

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _(f"Password must be at least {self.min_length} characters long."),
                code="password_too_short",
            )

        if self.require_uppercase and not re.search(r"[A-Z]", password):
            raise ValidationError(_("Password must contain at least one uppercase letter."), code="password_no_upper")

        if self.require_lowercase and not re.search(r"[a-z]", password):
            raise ValidationError(_("Password must contain at least one lowercase letter."), code="password_no_lower")

        if self.require_digits and not re.search(r"\d", password):
            raise ValidationError(_("Password must contain at least one digit."), code="password_no_digit")

        if self.require_symbols and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValidationError(_("Password must contain at least one special character."), code="password_no_symbol")

    def get_help_text(self):
        return _(
            f"Your password must be at least {self.min_length} characters long, "
            f"and include uppercase, lowercase, digits, and special characters."
        )
