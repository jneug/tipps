
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField, SelectField
from wtforms.validators import DataRequired

from .model import Template, DEFAULT_TEMPLATE


class LoginForm(FlaskForm):
    username = StringField("Name", validators=[DataRequired()])
    password = PasswordField("Passwort", validators=[DataRequired()])
    submit = SubmitField("Anmelden")


class ConfirmDeleteForm(FlaskForm):
    tipp = HiddenField("tipp", validators=[DataRequired()])
    submit = SubmitField("Löschen")
    cancel = SubmitField("Abbrechen")


class FilterForm(FlaskForm):
    class Meta:
        csrf = False

    search = StringField("Suche")
    template = SelectField("Vorlage", default=DEFAULT_TEMPLATE.name)
    sort = SelectField("Sortierung", choices=[("created", "Erstellt"), ("compiled", "Modifiziert")], default="compiled")
    submit = SubmitField("Filtern")
