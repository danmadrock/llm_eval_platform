class DomainError(Exception):
    """Base class for service-layer domain errors."""

    code = "domain_error"
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    code = "resource_not_found"
    status_code = 404


class ConflictError(DomainError):
    code = "resource_conflict"
    status_code = 409