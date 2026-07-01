class GatewayException(Exception):
    """Base exception for the Gateway"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundException(GatewayException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)

class UnauthorizedException(GatewayException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)

class ForbiddenException(GatewayException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)

class RateLimitExceededException(GatewayException):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status_code=429)

class UpstreamProviderException(GatewayException):
    def __init__(self, message: str = "Upstream provider error", status_code: int = 502):
        super().__init__(message, status_code=status_code)

class ConfigurationException(GatewayException):
    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, status_code=500)
