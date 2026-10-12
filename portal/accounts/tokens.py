import hashlib

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from django.utils.crypto import constant_time_compare


def invitation_digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def invitation_valid(invitation, digest):
    return bool(
        invitation and not invitation.consumed_at and invitation.expires_at > timezone.now()
        and constant_time_compare(invitation.token_digest, digest)
    )


class AccountResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        # Keep Django's token cryptography and include administrative revocation.
        return super()._make_hash_value(user, timestamp) + str(user.access_version)


reset_tokens = AccountResetTokenGenerator()
