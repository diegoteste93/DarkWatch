from math import ceil


def success_response(data, message: str = "Success") -> dict:
    return {"data": data, "message": message}


def paginated_response(items, total: int, page: int, page_size: int) -> dict:
    pages = ceil(total / page_size) if total else 0
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


def error_response(detail: str, code: str, status: int) -> dict:
    return {"detail": detail, "code": code, "status": status}
