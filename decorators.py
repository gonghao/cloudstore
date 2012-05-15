# -*- coding: utf-8 -*-

from functools import wraps
from flask import redirect, session, url_for, abort

def login_required(only_superuser=False, only_group=False):

    def decorator(view_func):

        @wraps(view_func)
        def wrapper(*args, **kwargs):

            if only_group:
                if 'group' not in session:
                    session.pop('user', None)
                    return redirect(url_for('login', next=url_for(view_func.__name__), login_to_group=1))
            else:
                if 'user' not in session and 'group' not in session:
                    return redirect(url_for('login', next=url_for(view_func.__name__)))

            if only_superuser is True:
                user = None
                if 'user' in session:
                    user = session['user']

                if user is None or user.id != 1:
                    abort(404)

            return view_func(*args, **kwargs)

        return wrapper

    return decorator
