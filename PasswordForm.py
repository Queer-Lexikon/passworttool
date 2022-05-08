from flask_wtf import FlaskForm
from wtforms import PasswordField
from wtforms.validators import InputRequired, EqualTo


class ChangePassword(FlaskForm):
    password = PasswordField(
        "Neues Passwort",
        [
            InputRequired(),
            EqualTo("confirm", message="Passwörter müssen übereinstimmen"),
        ],
    )
    confirm = PasswordField("Passwort bestätigen")
