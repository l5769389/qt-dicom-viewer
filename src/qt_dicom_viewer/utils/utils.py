from typing import Any


def _as_str(value: Any) -> str:
    if value is None:
        return ""

    return str(value)


def _as_int(value: Any) -> int | None:
    if value is None:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _transfer_syntax_name(dataset: Any) -> str:
    file_meta = getattr(dataset, "file_meta", None)
    transfer_syntax_uid = getattr(file_meta, "TransferSyntaxUID", None)

    if transfer_syntax_uid is None:
        return ""

    return getattr(transfer_syntax_uid, "name", str(transfer_syntax_uid))