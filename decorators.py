# -*- coding: utf-8 -*-

from functools import wraps
from flask import redirect, session, url_for, abort

def login_required(only_superuser=False, next_url=None):

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if 'user' not in session:
                return redirect(next_url if next_url is not None else url_for('login', next=url_for(view_func.__name__)))

            if only_superuser is True:
                user = session['user']

                if user.id != 1:
                    abort(404)

            return view_func(*args, **kwargs)

        return wrapper

    return decorator
