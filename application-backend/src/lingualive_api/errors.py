from dataclasses import dataclass, field


@dataclass
class ApiError(Exception):
    status: int
    code: str
    message: str
    retryable: bool = False
    details: dict = field(default_factory=dict)

    def body(self, request_id):
        return {"error": {"code": self.code, "message": self.message,
                          "details": self.details, "retryable": self.retryable},
                "request_id": request_id}


def unavailable():
    return ApiError(503, "FEATURE_NOT_CONFIGURED", "This feature is not configured yet.")
