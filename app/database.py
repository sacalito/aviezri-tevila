from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def init_db(app):
    basedir = os.path.abspath(os.path.dirname(__file__))
    database_dir = os.path.join(basedir, 'data/database/')    
    # Create directory if it doesn't exist
    if not os.path.exists(database_dir):
        os.makedirs(database_dir)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(database_dir, 'elevador.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    # Create tables
    with app.app_context():
        db.create_all()

# Define Hours model
class Hours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(10), nullable=False)  # e.g., 'Monday', 'Tuesday', etc.
    start_time = db.Column(db.String(8), nullable=False)  # e.g., '09:00:00'
    end_time = db.Column(db.String(8), nullable=False)    # e.g., '17:00:00'
    
    def __repr__(self):
        return f'<Hours {self.day}: {self.start_time} - {self.end_time}>'

# Define Dates model
class Dates(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False, unique=True)  # e.g., '2025-04-27'
    
    def __repr__(self):
        return f'<Date {self.date}>'
        
# Database utility functions
def add_hours(day, start_time, end_time):
    """Add a new hours entry to the database."""
    new_hours = Hours(day=day, start_time=start_time, end_time=end_time)
    db.session.add(new_hours)
    db.session.commit()
    return new_hours

def get_hours_by_day(day):
    """Get hours for a specific day."""
    return Hours.query.filter_by(day=day).first()

def get_all_hours():
    """Get all hours."""
    return Hours.query.all()

def update_hours(day, start_time=None, end_time=None):
    """Update hours for a specific day."""
    hours = Hours.query.filter_by(day=day).first()
    if not hours:
        return None
    
    if start_time:
        hours.start_time = start_time
    if end_time:
        hours.end_time = end_time
    
    db.session.commit()
    return hours

# This should go in database.py
def delete_hours(hours_id):
    """Delete hours by ID."""
    hours = Hours.query.get(hours_id)
    if hours:
        db.session.delete(hours)
        db.session.commit()
        return True
    return False

def add_date(date_str):
    """Add a new date entry to the database."""
    # Check if date already exists
    existing_date = Dates.query.filter_by(date=date_str).first()
    if existing_date:
        return existing_date
        
    # Create new date if it doesn't exist
    new_date = Dates(date=date_str)
    db.session.add(new_date)
    db.session.commit()
    return new_date

def get_date(date_str):
    """Get a specific date entry."""
    return Dates.query.filter_by(date=date_str).first()

def get_all_dates():
    """Get all date entries."""
    return Dates.query.all()

def delete_date(date_id):
    """Delete a date entry by its ID."""
    date = Dates.query.get(date_id)
    if date:
        db.session.delete(date)
        db.session.commit()
        return True
    return False