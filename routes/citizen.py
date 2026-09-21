import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db
from models.models import Complaint, Feedback, Notification, StatusHistory
from utils.forms import ComplaintForm, FeedbackForm
from ai.priority_engine import analyze_priority

citizen_bp = Blueprint('citizen', __name__)

@citizen_bp.before_request
@login_required
def require_citizen():
    if current_user.role != 'citizen':
        flash('Access denied. Citizen role required.', 'danger')
        return redirect(url_for('main.index'))

@citizen_bp.route('/dashboard')
def dashboard():
    complaints = Complaint.query.filter_by(user_id=current_user.id).order_by(Complaint.created_at.desc()).all()
    stats = {
        'total': len(complaints),
        'open': sum(1 for c in complaints if c.status == 'Open'),
        'in_progress': sum(1 for c in complaints if c.status == 'In Progress'),
        'resolved': sum(1 for c in complaints if c.status == 'Resolved'),
        'closed': sum(1 for c in complaints if c.status == 'Closed')
    }
    notifications = current_user.notifications.order_by(Notification.created_at.desc()).limit(5).all()
    return render_template('citizen/dashboard.html', complaints=complaints, stats=stats, notifications=notifications)

@citizen_bp.route('/submit', methods=['GET', 'POST'])
def submit_complaint():
    form = ComplaintForm()
    if form.validate_on_submit():
        image_path = None
        if form.image.data:
            f = form.image.data
            filename = secure_filename(f.filename)
            unique_filename = f"{current_user.id}_{filename}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            f.save(filepath)
            image_path = f"uploads/{unique_filename}"
            
        # AI Prioritization
        priority, reason = analyze_priority(form.title.data, form.description.data, form.category.data)
        
        # Location Details
        address = request.form.get('address')
        landmark = request.form.get('landmark')
        try:
            latitude = float(request.form.get('latitude')) if request.form.get('latitude') else None
            longitude = float(request.form.get('longitude')) if request.form.get('longitude') else None
        except ValueError:
            latitude = None
            longitude = None
        
        complaint = Complaint(
            title=form.title.data,
            description=form.description.data,
            category=form.category.data,
            priority=priority,
            priority_reason=reason,
            image_path=image_path,
            user_id=current_user.id,
            address=address,
            landmark=landmark,
            latitude=latitude,
            longitude=longitude
        )
        db.session.add(complaint)
        db.session.commit()
        
        # Initial status history
        history = StatusHistory(complaint_id=complaint.id, new_status='Open', remarks='Complaint submitted')
        db.session.add(history)
        
        # Initial notification
        notif = Notification(user_id=current_user.id, message=f"Your complaint '{complaint.title}' has been submitted. Priority assigned: {priority}")
        db.session.add(notif)
        db.session.commit()
        
        flash('Complaint submitted successfully!', 'success')
        return redirect(url_for('citizen.dashboard'))
        
    return render_template('citizen/submit.html', form=form)

@citizen_bp.route('/track/<int:complaint_id>')
def track_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    if complaint.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('citizen.dashboard'))
        
    history = complaint.status_history.order_by(StatusHistory.changed_at.desc()).all()
    feedback_form = FeedbackForm()
    
    return render_template('citizen/track.html', complaint=complaint, history=history, feedback_form=feedback_form)

@citizen_bp.route('/feedback/<int:complaint_id>', methods=['POST'])
def submit_feedback(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    if complaint.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('citizen.dashboard'))
        
    form = FeedbackForm()
    if form.validate_on_submit():
        if complaint.feedback:
            flash('Feedback already submitted for this complaint.', 'warning')
        else:
            feedback = Feedback(complaint_id=complaint.id, rating=int(form.rating.data), comments=form.comments.data)
            db.session.add(feedback)
            db.session.commit()
            flash('Thank you for your feedback!', 'success')
            
    return redirect(url_for('citizen.track_complaint', complaint_id=complaint_id))
@citizen_bp.route('/delete/<int:complaint_id>', methods=['POST'])
def delete_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)

    # Check ownership
    if complaint.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('citizen.dashboard'))

    # Allow deletion only when complaint is Open
    if complaint.status != 'Open':
        flash('Only Open complaints can be deleted.', 'warning')
        return redirect(url_for('citizen.dashboard'))

    # Delete status history
    StatusHistory.query.filter_by(complaint_id=complaint.id).delete()

    # Delete feedback if it exists
    if complaint.feedback:
        db.session.delete(complaint.feedback)

    # Delete notifications related to this complaint
    Notification.query.filter(
        Notification.user_id == current_user.id,
        Notification.message.contains(complaint.title)
    ).delete(synchronize_session=False)

    # Delete uploaded image
    if complaint.image_path:
        image_file = os.path.join(current_app.static_folder, complaint.image_path)
        if os.path.exists(image_file):
            os.remove(image_file)

    # Delete complaint
    db.session.delete(complaint)
    db.session.commit()

    flash('Complaint deleted successfully.', 'success')
    return redirect(url_for('citizen.dashboard'))

@citizen_bp.route('/profile')
def profile():
    return render_template('citizen/profile.html', user=current_user)
