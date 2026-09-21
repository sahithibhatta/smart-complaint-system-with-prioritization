import os
import pandas as pd
from flask import Blueprint, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from models.models import Complaint
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import tempfile

export_bp = Blueprint('export', __name__)

@export_bp.before_request
@login_required
def require_admin():
    if current_user.role != 'admin':
        flash('Access denied. Administrator privileges required.', 'danger')
        return redirect(url_for('main.index'))

@export_bp.route('/csv')
def export_csv():
    complaints = Complaint.query.all()
    data = []
    for c in complaints:
        data.append({
            'ID': c.id,
            'Title': c.title,
            'Category': c.category,
            'Priority': c.priority,
            'Status': c.status,
            'Date Submitted': c.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    df = pd.DataFrame(data)
    
    # Create temp file
    temp = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
    df.to_csv(temp.name, index=False)
    temp.close()
    
    return send_file(temp.name, as_attachment=True, download_name='complaints_export.csv')

@export_bp.route('/pdf')
def export_pdf():
    complaints = Complaint.query.all()
    
    temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    c = canvas.Canvas(temp.name, pagesize=letter)
    width, height = letter
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Smart Complaint System - All Complaints Report")
    
    c.setFont("Helvetica", 10)
    y = height - 80
    
    for comp in complaints:
        text = f"ID: {comp.id} | Priority: {comp.priority} | Status: {comp.status} | Title: {comp.title[:50]}"
        c.drawString(50, y, text)
        y -= 20
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 50
            
    c.save()
    temp.close()
    
    return send_file(temp.name, as_attachment=True, download_name='complaints_export.pdf')
