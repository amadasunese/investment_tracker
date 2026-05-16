from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)

        if current_user.role not in ["admin", "superadmin"]:
            abort(403)

        return func(*args, **kwargs)

    return wrapper


def superadmin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)

        if current_user.role != "superadmin":
            abort(403)

        return func(*args, **kwargs)

    return wrapper


def user_can_access_investment(user, investment):
    if user.role in ["admin", "superadmin"]:
        return True

    return investment.user_id == user.id