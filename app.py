from flask import Flask, url_for, redirect, render_template, request, flash
import json
import subprocess
import shlex
import logging
from datetime import datetime

from flask_ldap3_login import LDAP3LoginManager
from flask_ldap3_login.forms import LDAPLoginForm
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    current_user,
)
from simple_openid_connect.data import TokenErrorResponse
from simple_openid_connect.exceptions import AuthenticationFailedError

from PasswordForm import ChangePassword
from simple_openid_connect.client import OpenidClient

logger = logging.getLogger("passworttool")


def create_app():
    app = Flask(__name__)
    app.config.from_file("config.json", load=json.load)

    login_manager = LoginManager(app)
    login_manager.login_view = "login"
    ldap_manager = LDAP3LoginManager(app)
    oidc = OpenidClient.from_issuer_url(
        url=app.config["OIDC_ISSUER"],
        authentication_redirect_uri=None,
        client_id=app.config["OIDC_CLIENT_ID"],
        client_secret=app.config["OIDC_CLIENT_SECRET"],
        scope=app.config.get("OIDC_SCOPE") or "openid",
    )

    users = {}

    class User(UserMixin):
        def __init__(self, dn, username, data):
            self.dn = dn
            self.username = username
            self.data = data

        def __repr__(self):
            return self.dn

        def get_id(self):
            return self.dn

    @login_manager.user_loader
    def load_user(id):
        if id in users:
            return users[id]
        else:
            return None

    @ldap_manager.save_user
    def save_user(dn, username, data, memberships):
        user = User(dn, username, data)
        users[dn] = user
        return user

    @app.route("/login-callback", methods=("GET",))
    def login_oidc_callback():
        try:
            auth_result = oidc.authorization_code_flow.handle_authentication_result(
                request.url
            )
            if isinstance(auth_result, TokenErrorResponse):
                flash(
                    f"Login with Keycloak did not succeed: {auth_result.error_description}",
                    category="error",
                )
                return redirect(url_for("login"))
        except AuthenticationFailedError as e:
            flash(f"Login with Keycloak did not succeed: {e}", category="error")
            return redirect(url_for("login"))

        id_token = oidc.decode_id_token(
            auth_result.id_token, min_iat=datetime.utcnow().timestamp() - 30
        )
        user = load_user(id_token.sub)

        if user is None:
            logger.error(
                f"login with keycloak did not succeed because a user object for id {id_token.sub} could not be loaded"
            )
            flash(
                "Login with Keycloak did not succeed: Could not load user object for user id that was received from Keycloak",
                category="error",
            )
            return redirect(url_for("login"))

        login_user(user)
        return redirect("/")

    @app.route("/login", methods=("GET", "POST"))
    def login():
        if oidc.authentication_redirect_uri is None:
            oidc.authentication_redirect_uri = url_for(
                "login_oidc_callback", _external=True
            )

        form = LDAPLoginForm()
        if form.validate_on_submit():
            login_user(form.user)
            return redirect("/")
        return render_template(
            "login.html",
            form=form,
            oidc_login_url=oidc.authorization_code_flow.start_authentication(),
        )

    @app.route("/", methods=("GET", "POST"))
    @login_required
    def index():
        """
        What's in here?
        1) take mailadress from ldap
        2) if the form was sent, do more
        3) strip @queer-lexikon.net from ldap-mail-blurb because "uberspace mail" likes them better
        4) check if there is a mailbox with that name here locally
        5) no mailbox? run command with "add"-verb
        6) yes mailbox? run command with "password"-verb
        7) flash any console output (stdout and -err) so users have some kind of error message, if things go wrong
        8) if returncode is zero, flash success-message
        """

        mailuser = current_user.data.get("mail")[0]
        domain = app.config["DOMAIN"]
        isLocalMail = domain in mailuser
        form = ChangePassword()
        if request.method == "POST":
            if form.validate_on_submit():
                pw = request.form.get("password")
                user = mailuser.split("@")[0]
                app.logger.info(f"Passwortreset für {user}")
                # check user exists, create otherwise
                command = shlex.split("/usr/bin/uberspace mail user list")
                c = subprocess.run(command, capture_output=True)
                if user in c.stdout.decode():
                    verb = "password"
                    app.logger.info(f"{user} existiert, passwort wird geändert")
                else:
                    verb = "add"
                    app.logger.info(f"{user} existiert noch nicht, wird angelegt")
                command = shlex.split(
                    f"/usr/bin/uberspace mail user {verb} -p {pw} {user}"
                )

                d = subprocess.run(command, capture_output=True)
                if d.stdout:
                    out = d.stdout.decode()
                    app.logger.info(f"da sind Dinge im stdout: {out}")
                    flash(out)
                if d.stderr:
                    err = d.stderr.decode()
                    app.logger.error(f"da sind Dinge im stderr: {err}")
                    flash(err)
                if d.returncode == 0:
                    flash("Das hat vermutlich geklappt.")
                    app.logger.info("Reset für {user} hat vermutlich geklappt")
                else:
                    flash("Die Passwörter waren nicht gleich, versuch das mal nochmal")
                    app.logger.info(f"Reset für {user} hat vermutlich nicht geklappt.")

        return render_template(
            "form.html",
            form=form,
            mailuser=mailuser,
            isLocalMail=isLocalMail,
            host=app.config["UBERSPACE_HOST"],
            domain=app.config["DOMAIN"],
        )

    @app.route("/favicon.ico")
    def favicon():
        return redirect(url_for("static", filename="favicon.ico"))

    @app.errorhandler(404)
    def file_not_found(error):
        return redirect(url_for("index"))

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app = create_app()

    from waitress import serve

    serve(app, listen="*:8008")
