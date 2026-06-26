"""Custom exceptions."""


class AppError(Exception):
    """Base application error."""
    code: str = "internal_error"


class ValidationError(AppError):
    code = "validation_error"


class LimitExceededError(AppError):
    code = "limit_exceeded"


class PermissionDeniedError(AppError):
    code = "permission_denied"


class PaymentError(AppError):
    code = "payment_error"


class ProcessingError(AppError):
    code = "processing_error"


class StorageError(AppError):
    code = "storage_error"


class FileTooLargeError(ValidationError):
    code = "file_too_large"


class InvalidImageError(ValidationError):
    code = "invalid_image"