"""Custom application exceptions."""
from __future__ import annotations


class AppError(Exception):
    """Base application error."""


class ConfigError(AppError):
    """Configuration error."""


class DatabaseError(AppError):
    """Database error."""


class UserNotFoundError(AppError):
    """User does not exist."""


class UserBannedError(AppError):
    """User is banned."""


class LimitExceededError(AppError):
    """Daily limit reached."""


class SubscriptionRequiredError(AppError):
    """Premium feature requested by free user."""


class PaymentError(AppError):
    """Payment processing error."""


class PaymentVerificationError(PaymentError):
    """Payment signature/verification failed."""


class ImageProcessingError(AppError):
    """Image processing error."""


class FileTooLargeError(AppError):
    """Uploaded file is too large."""


class InvalidFileError(AppError):
    """Invalid file format."""


class RateLimitError(AppError):
    """Rate limit exceeded."""


class AntiSpamTriggered(RateLimitError):
    """Anti-spam rule violated."""


class CaptchaFailedError(AppError):
    """CAPTCHA verification failed."""


class SubscriptionExpiredError(AppError):
    """User's subscription expired."""


class AIServiceError(AppError):
    """AI service unavailable or returned an error."""


class StorageError(AppError):
    """File storage operation failed."""


class NetworkError(AppError):
    """External network call failed."""


class PermissionDeniedError(AppError):
    """Insufficient permissions."""


class AdminRequiredError(PermissionDeniedError):
    """Admin permission required."""