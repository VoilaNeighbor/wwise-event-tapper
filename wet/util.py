from collections.abc import Callable
from functools import wraps
from pathlib import Path
from threading import Lock

REPO_ROOT = Path(__file__).parent.parent


def once[**P, R](fn: Callable[P, R]) -> Callable[P, R | None]:
    lock = Lock()
    ran = False

    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R | None:
        nonlocal ran
        if not ran:
            with lock:
                if not ran:
                    ran = True
                    return fn(*args, **kwargs)
        return None

    return wrapper
