import sys
import os
from werkzeug.security import generate_password_hash

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():
    db.drop_all()  
    db.create_all()  

    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            full_name='Super Admin',
            password=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")
