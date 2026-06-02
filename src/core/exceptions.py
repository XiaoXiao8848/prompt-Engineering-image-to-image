"""自定义异常体系 — 统一错误码和 HTTP 状态码映射."""

from __future__ import annotations

from fastapi import HTTPException, status


class BaseAppException(Exception):
    """应用异常基类."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class NotFoundException(BaseAppException):
    """资源不存在."""

    def __init__(self, message: str = "资源不存在") -> None:
        super().__init__(message, code="NOT_FOUND")


class AlreadyExistsException(BaseAppException):
    """资源已存在."""

    def __init__(self, message: str = "资源已存在") -> None:
        super().__init__(message, code="ALREADY_EXISTS")


class AuthenticationException(BaseAppException):
    """认证失败."""

    def __init__(self, message: str = "认证失败") -> None:
        super().__init__(message, code="AUTHENTICATION_ERROR")


class AuthorizationException(BaseAppException):
    """权限不足."""

    def __init__(self, message: str = "权限不足") -> None:
        super().__init__(message, code="AUTHORIZATION_ERROR")


class ValidationException(BaseAppException):
    """参数校验失败."""

    def __init__(self, message: str = "参数校验失败") -> None:
        super().__init__(message, code="VALIDATION_ERROR")


class RateLimitException(BaseAppException):
    """触发限流."""

    def __init__(self, message: str = "请求过于频繁，请稍后再试") -> None:
        super().__init__(message, code="RATE_LIMITED")


class QuotaExceededException(BaseAppException):
    """配额已用完."""

    def __init__(self, message: str = "今日生成配额已用完") -> None:
        super().__init__(message, code="QUOTA_EXCEEDED")


class LLMException(BaseAppException):
    """LLM 调用失败."""

    def __init__(self, message: str = "AI 生成服务暂时不可用") -> None:
        super().__init__(message, code="LLM_ERROR")


def exception_to_http(exc: BaseAppException) -> HTTPException:
    """将应用异常转换为 FastAPI HTTPException."""
    if not isinstance(exc, BaseAppException):
        # 防御性处理：非应用异常转为 500
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": str(exc)},
        )
    status_map = {
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "ALREADY_EXISTS": status.HTTP_409_CONFLICT,
        "AUTHENTICATION_ERROR": status.HTTP_401_UNAUTHORIZED,
        "AUTHORIZATION_ERROR": status.HTTP_403_FORBIDDEN,
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "RATE_LIMITED": status.HTTP_429_TOO_MANY_REQUESTS,
        "QUOTA_EXCEEDED": status.HTTP_429_TOO_MANY_REQUESTS,
        "LLM_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
    }
    return HTTPException(
        status_code=status_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR),
        detail={"code": exc.code, "message": exc.message},
    )
