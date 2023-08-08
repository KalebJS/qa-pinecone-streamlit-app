class BadRequestException(Exception):
    """
    Exception for bad requests.

    Attributes:
        message -- explanation of the error
        status_code -- HTTP status code
    """

    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code


class BadPayloadException(BadRequestException):
    """
    Exception for bad payloads.

    Attributes:
        message -- explanation of the error
        status_code -- HTTP status code
    """


class ExceededRateLimitException(BadRequestException):
    """
    Exception for exceeding rate limits.

    Attributes:
        message -- explanation of the error
        status_code -- HTTP status code
    """


class UnauthorizedException(BadRequestException):
    """
    Exception for unauthorized requests.

    Attributes:
        message -- explanation of the error
        status_code -- HTTP status code
    """


class ServerSideException(BadRequestException):
    """
    Exception for server-side errors.

    Attributes:
        message -- explanation of the error
        status_code -- HTTP status code
    """


class NoSuchUser(Exception):
    """
    Exception for when a user does not exist.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message: str):
        super().__init__(message)


class NoSuchFolderException(Exception):
    """
    Exception for when a folder does not exist.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message: str):
        super().__init__(message)
