from fastapi import HTTPException


class APIError(HTTPException):
    def __init__(self, status_code: int, detail: str, code: str):
        super().__init__(status_code=status_code, detail=detail)
        self.code = code


class ProviderUnavailableError(Exception):
    pass


class ScanAlreadyRunningError(APIError):
    def __init__(self):
        super().__init__(status_code=409, detail="Scan already running", code="SCAN_ALREADY_RUNNING")
