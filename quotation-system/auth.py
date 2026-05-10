import hmac
import os
from urllib.parse import urlparse

from flask import redirect, render_template, request, session, url_for


AUTH_EXEMPT_ENDPOINTS = {'auth.login', 'auth.logout', 'static'}


def auth_is_enabled():
    return bool(os.environ.get('QUOTE_ADMIN_USER') and os.environ.get('QUOTE_ADMIN_PASSWORD'))


def is_safe_redirect_url(target):
    if not target:
        return False
    parsed = urlparse(target)
    return not parsed.netloc and parsed.scheme == ''


def register_auth(app):
    from flask import Blueprint

    bp = Blueprint('auth', __name__)

    @bp.route('/login', methods=['GET', 'POST'])
    def login():
        if not auth_is_enabled():
            return render_template('login.html', auth_enabled=False), 503

        error = None
        next_url = request.args.get('next') or request.form.get('next') or url_for('pages.index')
        if not is_safe_redirect_url(next_url):
            next_url = url_for('pages.index')

        if request.method == 'POST':
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            expected_user = os.environ.get('QUOTE_ADMIN_USER', '')
            expected_password = os.environ.get('QUOTE_ADMIN_PASSWORD', '')

            if hmac.compare_digest(username, expected_user) and hmac.compare_digest(password, expected_password):
                session['quote_admin_logged_in'] = True
                return redirect(next_url)

            error = '账号或密码不正确'

        return render_template('login.html', auth_enabled=True, error=error, next_url=next_url)

    @bp.route('/logout')
    def logout():
        session.pop('quote_admin_logged_in', None)
        return redirect(url_for('auth.login'))

    @app.before_request
    def require_login():
        if not auth_is_enabled():
            return None
        if request.endpoint in AUTH_EXEMPT_ENDPOINTS:
            return None
        if request.endpoint and request.endpoint.startswith('static'):
            return None
        if session.get('quote_admin_logged_in'):
            return None
        return redirect(url_for('auth.login', next=request.full_path.rstrip('?')))

    app.register_blueprint(bp)
