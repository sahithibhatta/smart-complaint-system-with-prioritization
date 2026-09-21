from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
import os
from datetime import timedelta
from werkzeug.utils import secure_filename
from models import db
from models.models import Complaint, Department, StatusHistory, Notification, User, ist_now
from utils.forms import StatusUpdateForm

admin_bp = Blueprint('admin', __name__)


@admin_bp.before_request
@login_required
def require_admin():
    if current_user.role != 'admin':
        flash('Access denied. Administrator privileges required.', 'danger')
        return redirect(url_for('main.index'))


@admin_bp.route('/dashboard')
def dashboard():
    complaints = Complaint.query.all()
    total = len(complaints)

    # Priority counts
    critical = sum(1 for c in complaints if c.priority == 'Critical')
    high = sum(1 for c in complaints if c.priority == 'High')
    medium = sum(1 for c in complaints if c.priority == 'Medium')
    low = sum(1 for c in complaints if c.priority == 'Low')

    # Status counts
    open_c = sum(1 for c in complaints if c.status == 'Open')
    progress_c = sum(1 for c in complaints if c.status == 'In Progress')
    resolved_c = sum(1 for c in complaints if c.status == 'Resolved')
    closed_c = sum(1 for c in complaints if c.status == 'Closed')

    # Category counts
    categories = {}
    for c in complaints:
        categories[c.category] = categories.get(c.category, 0) + 1

    recent_complaints = Complaint.query.order_by(
        Complaint.created_at.desc()
    ).limit(10).all()

    return render_template(
        'admin/dashboard.html',
        total=total,
        critical=critical,
        high=high,
        medium=medium,
        low=low,
        open_c=open_c,
        progress_c=progress_c,
        resolved_c=resolved_c,
        closed_c=closed_c,
        categories=categories,
        recent=recent_complaints
    )


@admin_bp.route('/api/stats')
def api_stats():
    range_filter = request.args.get('range', 'all')
    query = Complaint.query

    now = ist_now()
    if range_filter == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(Complaint.created_at >= start_date)
    elif range_filter == '7days':
        start_date = now - timedelta(days=7)
        query = query.filter(Complaint.created_at >= start_date)
    elif range_filter == 'this_month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(Complaint.created_at >= start_date)

    complaints = query.all()
    
    total = len(complaints)
    critical = sum(1 for c in complaints if c.priority == 'Critical')
    high = sum(1 for c in complaints if c.priority == 'High')
    medium = sum(1 for c in complaints if c.priority == 'Medium')
    low = sum(1 for c in complaints if c.priority == 'Low')
    
    resolved_c = sum(1 for c in complaints if c.status == 'Resolved')
    closed_c = sum(1 for c in complaints if c.status == 'Closed')
    
    categories = {}
    for c in complaints:
        categories[c.category] = categories.get(c.category, 0) + 1
        
    return jsonify({
        'total': total,
        'critical': critical,
        'high': high,
        'medium': medium,
        'low': low,
        'resolved_and_closed': resolved_c + closed_c,
        'categories': categories
    })


@admin_bp.route('/complaints')
def complaints_list():
    query = Complaint.query

    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    search_query = request.args.get('search')

    if status_filter:
        query = query.filter_by(status=status_filter)

    if priority_filter:
        query = query.filter_by(priority=priority_filter)

    if search_query:
        query = query.filter(
            Complaint.title.ilike(f"%{search_query}%")
        )

    complaints = query.order_by(
        Complaint.created_at.desc()
    ).all()

    return render_template(
        'admin/complaints.html',
        complaints=complaints
    )


@admin_bp.route('/complaint/<int:complaint_id>', methods=['GET', 'POST'])
def view_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    departments = Department.query.all()

    form = StatusUpdateForm()
    form.department_id.choices = [(d.id, d.name) for d in departments]

    if request.method == 'GET':
        form.status.data = complaint.status

        if complaint.department_id:
            form.department_id.data = complaint.department_id
        elif departments:
            form.department_id.data = departments[0].id

    if form.validate_on_submit():

        old_status = complaint.status
        new_status = form.status.data
        new_dept_id = form.department_id.data

        # Update complaint
        complaint.status = new_status
        complaint.department_id = new_dept_id

        if new_status == 'Resolved':
            complaint.resolution_remarks = form.remarks.data
            complaint.resolved_at = ist_now()
            
            if form.resolution_image.data:
                f = form.resolution_image.data
                filename = secure_filename(f.filename)
                unique_filename = f"resolution_{complaint.id}_{filename}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                f.save(filepath)
                complaint.resolution_image_path = f"uploads/{unique_filename}"

        # Add history
        history = StatusHistory(
            complaint_id=complaint.id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user.id,
            remarks=form.remarks.data
        )
        db.session.add(history)

        # Get department
        department = Department.query.get(new_dept_id)
        dept_name = department.name if department else "Not Assigned"

        # Create notification
        if new_status == "Open":
            message = (
                f"Your complaint '{complaint.title}' has been received and "
                f"assigned to {dept_name}."
            )

        elif new_status == "In Progress":
            message = (
                f"Your complaint '{complaint.title}' is now being processed "
                f"by {dept_name}."
            )

        elif new_status == "Resolved":
            message = (
                f"🎉 Great news! Your complaint '{complaint.title}' has been "
                f"resolved. Please visit the Track Complaint page to submit "
                f"your feedback."
            )

        elif new_status == "Closed":
            message = (
                f"Your complaint '{complaint.title}' has been closed. "
                f"Thank you for using Smart Complaint System."
            )

        else:
            message = (
                f"Complaint '{complaint.title}' updated to {new_status}."
            )

        notification = Notification(
            user_id=complaint.user_id,
            message=message
        )

        db.session.add(notification)

        db.session.commit()

        flash("Complaint updated successfully.", "success")

        return redirect(
            url_for(
                "admin.view_complaint",
                complaint_id=complaint.id
            )
        )

    history = complaint.status_history.order_by(
        StatusHistory.changed_at.desc()
    ).all()

    return render_template(
        "admin/view_complaint.html",
        complaint=complaint,
        history=history,
        form=form
    )


@admin_bp.route('/users')
def users_list():
    users = User.query.filter_by(role='citizen').all()
    return render_template(
        'admin/users.html',
        users=users
    )


@admin_bp.route('/api/complaint/<int:complaint_id>')
def api_get_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    departments = Department.query.all()
    
    return jsonify({
        'id': complaint.id,
        'title': complaint.title,
        'description': complaint.description,
        'category': complaint.category,
        'priority': complaint.priority,
        'priority_reason': complaint.priority_reason,
        'status': complaint.status,
        'created_at': complaint.created_at.strftime('%d %B %Y, %I:%M %p'),
        'author_username': complaint.author.username,
        'author_email': complaint.author.email,
        'image_path': url_for('static', filename=complaint.image_path) if complaint.image_path else None,
        'latitude': complaint.latitude,
        'longitude': complaint.longitude,
        'address': complaint.address,
        'landmark': complaint.landmark,
        'department_id': complaint.department_id,
        'departments': [{'id': d.id, 'name': d.name} for d in departments],
    })


@admin_bp.route('/api/complaint/<int:complaint_id>/update', methods=['POST'])
def api_update_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    
    new_status = request.form.get('status')
    new_dept_id = request.form.get('department_id')
    remarks = request.form.get('remarks')
    
    if not new_status:
        return jsonify({'error': 'Status is required'}), 400
        
    old_status = complaint.status
    complaint.status = new_status
    
    if new_dept_id:
        complaint.department_id = new_dept_id
        
    if new_status == 'Resolved':
        complaint.resolution_remarks = remarks
        complaint.resolved_at = ist_now()
        
        if 'resolution_image' in request.files:
            f = request.files['resolution_image']
            if f.filename:
                filename = secure_filename(f.filename)
                unique_filename = f"resolution_{complaint.id}_{filename}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                f.save(filepath)
                complaint.resolution_image_path = f"uploads/{unique_filename}"
                
    # Add history
    history = StatusHistory(
        complaint_id=complaint.id,
        old_status=old_status,
        new_status=new_status,
        changed_by=current_user.id,
        remarks=remarks
    )
    db.session.add(history)
    
    # Create notification
    department = Department.query.get(new_dept_id) if new_dept_id else None
    dept_name = department.name if department else "Not Assigned"
    
    if new_status == "Open":
        message = f"Your complaint '{complaint.title}' has been received and assigned to {dept_name}."
    elif new_status == "In Progress":
        message = f"Your complaint '{complaint.title}' is now being processed by {dept_name}."
    elif new_status == "Resolved":
        message = f"🎉 Great news! Your complaint '{complaint.title}' has been resolved. Please visit the Track Complaint page to submit your feedback."
    elif new_status == "Closed":
        message = f"Your complaint '{complaint.title}' has been closed. Thank you for using Smart Complaint System."
    else:
        message = f"Complaint '{complaint.title}' updated to {new_status}."
        
    notification = Notification(
        user_id=complaint.user_id,
        message=message
    )
    
    db.session.add(notification)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'status': complaint.status,
        'department_id': complaint.department_id
    })