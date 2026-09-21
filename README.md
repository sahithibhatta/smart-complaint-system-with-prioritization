# Smart Complaint System with AI Prioritization

A robust, production-ready Flask web application for managing citizen complaints, featuring an explainable AI prioritization engine.

## Features

- **Citizen Portal**: Register, submit complaints with images, track status, and provide feedback.
- **Admin Dashboard**: Comprehensive analytics (powered by Chart.js), complaint management, status updates, and department assignments.
- **AI Prioritization Engine**: Automatically classifies incoming complaints as Critical, High, Medium, or Low based on NLP keyword/heuristic analysis and provides reasoning.
- **Reporting**: Export complaint data to CSV (Pandas) and PDF (ReportLab).
- **Responsive Design**: Custom government-style aesthetic built on Bootstrap 5.

## Installation

1. **Clone or Download the Repository**

2. **Set up a Virtual Environment (Optional but Recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   python run.py
   ```
   The database tables will be automatically created on the first run, seeded with default departments and an admin user.

## Default Credentials
- **Admin**: `admin@smartcomplaint.com` / `admin123`
- **Citizen**: You can register a new citizen account via the registration page.

## Running Tests
Run the comprehensive test suite to verify the end-to-end functionality (Authentication, AI Engine, Admin Features, Exports):
```bash
python test_app.py
```
