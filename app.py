from flask import Flask, url_for, redirect, render_template, request, flash
import subprocess
import shlex


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        # don't do that:
        SECRET_KEY="bananenberg",
        live=True,
        host="aitne",  # enter uberspace-host here
    )

    @app.route("/", methods=("GET", "POST"))
    def index():
        mailuser = "<Name>"
        if request.method == "POST":
            if (
                request.form.get("user")
                and request.form.get("pass")
                and request.form.get("pass")
            ):
                user = request.form.get("user").split("@")[0]

                if request.form.get("pass") == request.form.get("safe"):
                    pw = request.form.get("pass")

                    command = shlex.split(
                        f"/usr/bin/uberspace mail user password -p {pw} {user}"
                    )
                    if True:
                        c = subprocess.run(command, capture_output=True)
                        if c.stdout:
                            flash(c.stdout.decode())
                        if c.stderr:
                            flash(c.stderr.decode())

                        if c.returncode == 0:
                            flash("Das hat vermutlich geklappt.")
                            mailuser = user
                    else:
                        flash(command)
                else:
                    flash("Die Passwörter waren nicht gleich, versuch das mal nochmal")
            else:
                flash("Da hat irgendwas gefehlt.")

        return render_template(
            "form.html", mailuser=mailuser, host=app.config.get("host")
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
