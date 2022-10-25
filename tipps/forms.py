from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Passwort", validators=[DataRequired()])
    submit = SubmitField("Anmelden")


class ConfirmDeleteForm(FlaskForm):
    tipp = HiddenField("tipp", validators=[DataRequired()])
    submit = SubmitField("Löschen")
    cancel = SubmitField("Abbrechen")
