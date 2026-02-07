class EC2ServiceError(Exception):
    """Base exception for EC2 service errors."""
    pass

class InstanceNotFoundError(EC2ServiceError):
    """Raised when an EC2 instance is not found."""
    pass