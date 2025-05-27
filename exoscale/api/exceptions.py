class ExoscaleAPIException(Exception):
    """
    Base exception for exoscale API errors.
    Base for all other exception classes, it allows to catch all exoscale exceptions with a single except block.
    """

    def __init__(self, message, response=None):
        super().__init__(message)
        self.response = response


class ExoscaleAPIClientException(ExoscaleAPIException):
    """
    For client-side errors (4xx).
    Shows that the client sent a bad request.
    """

    pass


class ExoscaleAPIServerException(ExoscaleAPIException):
    """
    For server-side errors (5xx).
    Shows the server encountered an error while processing the request.
    """

    pass


class ExoscaleAPIAuthException(ExoscaleAPIException):
    """
    For authentication-related errors (403).
    Shows the server encountered an error while processing the request.
    """

    pass
