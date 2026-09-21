import os
from flask import Flask
from config import Config
from models import db
from models.models import User, Department
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
        
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    with app.app_context():
        # Import routes
        from routes.auth import auth_bp
        from routes.citizen import citizen_bp
        from routes.admin import admin_bp
        from routes.export import export_bp
        from routes.main import main_bp
        
        # Register blueprints
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(citizen_bp, url_prefix='/citizen')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(export_bp, url_prefix='/export')
        
        # Create database tables
        db.create_all()
        
        # Seed default departments if none exist
        if not Department.query.first():
            depts = ['Public Works', 'Water Supply', 'Electricity Board', 'Sanitation', 'Traffic Police', 'Fire Department', 'General Administration']
            for d in depts:
                dept = Department(name=d)
                db.session.add(dept)
            db.session.commit()
            
        # Seed default admin
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', email='admin@smartcomplaint.com', role='admin')
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
