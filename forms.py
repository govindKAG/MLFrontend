from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired

class BuildForm(FlaskForm):
    #password = PasswordField('Password', validators=[DataRequired()])
    #remember_me = BooleanField('Remember Me')

    version           = StringField('version', validators           = [DataRequired()])
    github_user       = StringField('github user', validators      = [DataRequired()])
    github_revision   = StringField('github revision', validators   = [DataRequired()])
    github_repo       = StringField('github repo', validators       = [DataRequired()])
    docker_user       = StringField('docker user', validators       = [DataRequired()])
    train_name        = StringField('train name', validators        = [DataRequired()])
    docker_image_name = StringField('docker image name', validators = [DataRequired()])
    build             = SubmitField('Build')

class TrainForm(FlaskForm):
    #password = PasswordField('Password', validators=[DataRequired()])
    #remember_me = BooleanField('Remember Me')

    version           = StringField('version', validators           = [DataRequired()])
    docker_user       = StringField('docker user', validators       = [DataRequired()])
    train_name        = StringField('train name', validators        = [DataRequired()])
    docker_image_name = StringField('docker image name', validators = [DataRequired()])
    command           = StringField('command', validators           = [DataRequired()])
    args              = TextAreaField('args', validators            = [DataRequired()])
    train             = SubmitField('Train')
