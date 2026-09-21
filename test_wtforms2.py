from flask import Flask, render_template_string
from utils.forms import ComplaintForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'
app.config['WTF_CSRF_ENABLED'] = False
with app.app_context():
    with app.test_request_context('/'):
        form = ComplaintForm()
        html = render_template_string("{{ form.title.label(class='form-label fw-bold translate') }}", form=form)
        print('OUTPUT1:', html)
