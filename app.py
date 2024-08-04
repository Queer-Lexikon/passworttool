from flask import Flask, url_for, redirect, render_template, request, flash, session
import json
import subprocess
import shlex
import logging

from flask_oidc import OpenIDConnect

from PasswordForm import ChangePassword


def create_app():
    app = Flask(__name__)
    app.config.from_file("config.json", load=json.load)

    oidc = OpenIDConnect()

    oidc.init_app(app)

    @app.route("/", methods=("GET", "POST"))
    @oidc.require_login
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

        mailuser = session["oidc_auth_profile"].get("email")
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
