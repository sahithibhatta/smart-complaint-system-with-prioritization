from flask import Flask, render_template_string
from utils.forms import ComplaintForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'
app.config['WTF_CSRF_ENABLED'] = False
with app.app_context():
    with app.test_request_context('/'):
        form = ComplaintForm()
        html = render_template_string("{{ form.title.label(class_='form-label fw-bold translate') }}", form=form)
        print('OUTPUT1:', html)
        html2 = render_template_string("{{ form.title(class_='form-control form-control-lg translate') }}", form=form)
        print('OUTPUT2:', html2)
        html3 = render_template_string("{{ form.category(class_='form-select form-select-lg translate') }}", form=form)
        print('OUTPUT3:', html3)
