from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def init_db(app):
    basedir = os.path.abspath(os.path.dirname(__file__))
    database_dir = os.path.join(basedir, 'data/database/')
    if not os.path.exists(database_dir):
        os.makedirs(database_dir)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(database_dir, 'tevila.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()

class Hours(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    relay = db.Column(db.String(20), nullable=False)  # 'heating' or 'filtering'
    day = db.Column(db.String(10), nullable=False)     # 'Monday', ..., 'Sunday', 'Holiday'
    start_time = db.Column(db.String(8), nullable=False)  # 'HH:MM:SS'
    end_time = db.Column(db.String(8), nullable=False)    # 'HH:MM:SS'

    def __repr__(self):
        return f'<Hours {self.relay} {self.day}: {self.start_time} - {self.end_time}>'

class Dates(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False, unique=True)  # 'YYYY-MM-DD'

    def __repr__(self):
        return f'<Date {self.date}>'

def add_hours(relay, day, start_time, end_time):
    new_hours = Hours(relay=relay, day=day, start_time=start_time, end_time=end_time)
    db.session.add(new_hours)
    db.session.commit()
    return new_hours

def get_hours_by_relay(relay):
    return Hours.query.filter_by(relay=relay).all()

def get_hours_by_relay_and_day(relay, day):
    return Hours.query.filter_by(relay=relay, day=day).all()

def get_all_hours():
    return Hours.query.all()

def delete_hours(hours_id):
    hours = Hours.query.get(hours_id)
    if hours:
        db.session.delete(hours)
        db.session.commit()
        return True
    return False

def add_date(date_str):
    existing_date = Dates.query.filter_by(date=date_str).first()
    if existing_date:
        return existing_date
    new_date = Dates(date=date_str)
    db.session.add(new_date)
    db.session.commit()
    return new_date

def get_all_dates():
    return Dates.query.all()

def delete_date(date_id):
    date = Dates.query.get(date_id)
    if date:
        db.session.delete(date)
        db.session.commit()
        return True
    return False
