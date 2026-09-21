from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import db
from models.models import User, PasswordResetToken, ist_now
from utils.forms import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
import os
import secrets
import smtplib
from email.message import EmailMessage
from datetime import timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))
            
        user = User(username=form.username.data, email=form.email.data, role='citizen')
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user)
        flash('Logged in successfully.', 'success')
        
        # Redirect admin to admin dashboard, citizen to citizen dashboard
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('citizen.dashboard'))
            
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

def send_reset_email(to_email, reset_url):
    mail_server = os.environ.get('MAIL_SERVER')
    if not mail_server:
        print(f"--- NO MAIL SERVER CONFIGURED ---")
        print(f"Password reset link for {to_email}: {reset_url}")
        print(f"---------------------------------")
        return
    
    mail_port = int(os.environ.get('MAIL_PORT', 587))
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')
    mail_use_tls = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    
    msg = EmailMessage()
    msg['Subject'] = 'Password Reset Request - Smart Complaint System'
    msg['From'] = mail_username or 'noreply@smartcomplaint.com'
    msg['To'] = to_email
    msg.set_content(f"You requested a password reset.\n\nClick the link below to reset your password:\n{reset_url}\n\nIf you did not request this, please ignore this email.")
    
    try:
        if mail_use_tls:
            server = smtplib.SMTP(mail_server, mail_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(mail_server, mail_port)
            
        if mail_username and mail_password:
            server.login(mail_username, mail_password)
            
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = secrets.token_urlsafe(32)
            expires = ist_now() + timedelta(minutes=30)
            reset_token = PasswordResetToken(token=token, user_id=user.id, expires_at=expires)
            db.session.add(reset_token)
            db.session.commit()
            
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            send_reset_email(user.email, reset_url)
            
        flash('If an account exists with this email, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
        
    reset_token = PasswordResetToken.query.filter_by(token=token).first()
    if not reset_token or reset_token.expires_at < ist_now():
        flash('Invalid reset link.', 'danger')
        return redirect(url_for('auth.forgot_password'))
        
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.get(reset_token.user_id)
        if user:
            user.set_password(form.password.data)
            db.session.delete(reset_token)
            db.session.commit()
            flash('Password reset successfully.', 'success')
            return redirect(url_for('auth.login'))
            
    return render_template('auth/reset_password.html', form=form)
