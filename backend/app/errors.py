"""Application-level errors that map to clean JSON HTTP responses."""


class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400, code: str = "bad_request") -> None:
        super().__init__(message)
        self.message, self.status_code, self.code = message, status_code, code


class LLMUnavailable(AppError):
    def __init__(self, message: str = "LLM is not configured or failed.") -> None:
        super().__init__(message, 503, "llm_unavailable")


class EmbeddingError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, 502, "embedding_failed")
