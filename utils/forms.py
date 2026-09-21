from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ComplaintForm(FlaskForm):
    title = StringField('Complaint Title', validators=[DataRequired(), Length(min=5, max=150)])
    category = SelectField('Category', choices=[
        ('Public Infrastructure', 'Public Infrastructure'),
        ('Sanitation & Waste', 'Sanitation & Waste'),
        ('Utilities (Water/Electricity)', 'Utilities (Water/Electricity)'),
        ('Emergency/Safety', 'Emergency/Safety'),
        ('General Queries', 'General Queries'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    description = TextAreaField('Detailed Description', validators=[DataRequired(), Length(min=10)])
    image = FileField('Upload Image (Optional)', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Submit Complaint')

class StatusUpdateForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('Open', 'Open'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Closed', 'Closed')
    ], validators=[DataRequired()])
    department_id = SelectField('Assign Department', coerce=int, validators=[DataRequired()])
    remarks = TextAreaField('Remarks / Action Taken', validators=[DataRequired()])
    resolution_image = FileField('Resolution Photo (Optional)', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Update Status')

class FeedbackForm(FlaskForm):
    rating = SelectField('Rating (1-5)', choices=[(str(i), str(i)) for i in range(1, 6)], validators=[DataRequired()])
    comments = TextAreaField('Comments', validators=[DataRequired()])
    submit = SubmitField('Submit Feedback')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('password', message='Passwords do not match.')])
    submit = SubmitField('Reset Password')
