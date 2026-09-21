import unittest
import io
from app import create_app
from models import db
from models.models import User, Complaint, Department

class SmartComplaintTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.client = self.app.test_client()
        
        with self.app.app_context():
            pass # app.py create_app already seeds db


    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def register_and_login(self):
        # Register
        self.client.post('/auth/register', data=dict(
            username='citizen_test',
            email='citizen@test.com',
            password='password123',
            confirm_password='password123'
        ), follow_redirects=True)
        
        # Login
        response = self.client.post('/auth/login', data=dict(
            email='citizen@test.com',
            password='password123'
        ), follow_redirects=True)
        self.assertIn(b'Citizen Dashboard', response.data)

    def test_full_flow(self):
        self.register_and_login()
        
        # 1. Submit Critical Complaint
        res1 = self.client.post('/citizen/submit', data=dict(
            title='Massive fire at building',
            category='Emergency/Safety',
            description='There is a massive fire at the main street building!'
        ), follow_redirects=True)
        self.assertIn(b'Complaint submitted successfully', res1.data)
        
        # 2. Submit High Complaint
        res2 = self.client.post('/citizen/submit', data=dict(
            title='Severe water leakage',
            category='Utilities (Water/Electricity)',
            description='Water leakage in the downtown area causing flooding.'
        ), follow_redirects=True)
        
        # 3. Submit Medium Complaint
        res3 = self.client.post('/citizen/submit', data=dict(
            title='Garbage not collected',
            category='Sanitation & Waste',
            description='Garbage collection has been missed for 3 days.'
        ), follow_redirects=True)
        
        # 4. Submit Low Complaint
        res4 = self.client.post('/citizen/submit', data=dict(
            title='Park suggestion',
            category='General Queries',
            description='Suggestion to add more benches to the park.'
        ), follow_redirects=True)
        
        # Verify AI Priorities in DB
        with self.app.app_context():
            complaints = Complaint.query.order_by(Complaint.id).all()
            self.assertEqual(len(complaints), 4)
            self.assertEqual(complaints[0].priority, 'Critical')
            self.assertEqual(complaints[1].priority, 'High')
            self.assertEqual(complaints[2].priority, 'Medium')
            self.assertEqual(complaints[3].priority, 'Low')
            
            c_id = complaints[0].id
            
        # Test Track Complaint
        track_res = self.client.get(f'/citizen/track/{c_id}')
        self.assertIn(b'Massive fire', track_res.data)
        self.assertIn(b'Critical', track_res.data)
        
        # Logout citizen
        self.client.get('/auth/logout')
        
        # Login as Admin
        admin_res = self.client.post('/auth/login', data=dict(
            email='admin@smartcomplaint.com',
            password='admin123'
        ), follow_redirects=True)
        self.assertIn(b'Admin Dashboard', admin_res.data)
        
        # Test Admin Dashboard Analytics
        dash_res = self.client.get('/admin/dashboard')
        self.assertIn(b'Total Complaints', dash_res.data)
        
        # Test Status Update
        with self.app.app_context():
            dept = Department.query.first()
            dept_id = dept.id
            
        update_res = self.client.post(f'/admin/complaint/{c_id}', data=dict(
            status='In Progress',
            department_id=dept_id,
            remarks='Fire trucks deployed.'
        ), follow_redirects=True)
        self.assertIn(b'Complaint updated successfully', update_res.data)
        
        with self.app.app_context():
            updated_c = Complaint.query.get(c_id)
            self.assertEqual(updated_c.status, 'In Progress')
            
        # Test CSV Export
        csv_res = self.client.get('/export/csv')
        self.assertEqual(csv_res.status_code, 200)
        self.assertIn(b'Massive fire', csv_res.data)
        
        # Test PDF Export
        pdf_res = self.client.get('/export/pdf')
        self.assertEqual(pdf_res.status_code, 200)
        self.assertTrue(pdf_res.data.startswith(b'%PDF-'))
        
if __name__ == '__main__':
    unittest.main()
