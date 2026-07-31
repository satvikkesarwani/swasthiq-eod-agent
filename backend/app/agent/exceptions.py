class NarrativeProviderError(Exception):
    code = "PROVIDER_ERROR"

    def __init__(self, message: str | None = None):
        super().__init__(message or self.code)


class NarrativeProviderDisabled(NarrativeProviderError):
    code = "PROVIDER_DISABLED"


class NarrativeProviderNotConfigured(NarrativeProviderError):
    code = "PROVIDER_NOT_CONFIGURED"


class NarrativeProviderTimeout(NarrativeProviderError):
    code = "PROVIDER_TIMEOUT"


class NarrativeProviderRateLimited(NarrativeProviderError):
    code = "PROVIDER_RATE_LIMITED"


class NarrativeProviderUnavailable(NarrativeProviderError):
    code = "PROVIDER_UNAVAILABLE"


class NarrativeProviderInvalidResponse(NarrativeProviderError):
    code = "MODEL_SCHEMA_INVALID"


class NarrativeProviderAuthenticationError(NarrativeProviderError):
    code = "PROVIDER_AUTHENTICATION_ERROR"

