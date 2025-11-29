from fastapi import HTTPException, status


class NotFoundException(HTTPException):
    """여러 엔드포인트에서 재사용하는 404 예외."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=message)
