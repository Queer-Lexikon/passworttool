from flask import Flask, url_for, redirect, render_template, request, flash
import json
import subprocess
import shlex

from flask_ldap3_login import LDAP3LoginManager
from flask_ldap3_login.forms import LDAPLoginForm
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    current_user,
)
from PasswordForm import ChangePassword


def create_app():
    app = Flask(__name__)
    app.config.from_file("config.json", load=json.load)

    login_manager = LoginManager(app)
    login_manager.login_view = "login"
    ldap_manager = LDAP3LoginManager(app)

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

    @app.route("/login", methods=("GET", "POST"))
    def login():
        form = LDAPLoginForm()
        if form.validate_on_submit():
            login_user(form.user)
            return redirect("/")
        return render_template("login.html", form=form)

    @app.route("/", methods=("GET", "POST"))
    @login_required
    def index():
        mailuser = current_user.data.get("mail")[0]
        user = mailuser.split("@")[0]
        if not app.config["DOMAIN"] in mailuser:
            command = shlex.split("uberspace mail user list")
            c = subprocess.run(command, capture_outout=True, text=True)
            if user in c.stdout:
                mailuser = f"{user}@{app.config['DOMAIN']}"
        form = ChangePassword()
        if request.method == "POST":
            if form.validate_on_submit():
                pw = request.form.get("password")

                command = shlex.split(
                    f"/usr/bin/uberspace mail user password -p {pw} {user}"
                )

                c = subprocess.run(command, capture_output=True)
                if c.stdout:
                    flash(c.stdout.decode())
                if c.stderr:
                    flash(c.stderr.decode())
                if c.returncode == 0:
                    flash("Das hat vermutlich geklappt.")
            else:
                flash("Die Passwörter waren nicht gleich, versuch das mal nochmal")

        return render_template(
            "form.html",
            form=form,
            mailuser=mailuser,
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
    app = create_app()

    from waitress import serve

    serve(app, listen="*:8008")
