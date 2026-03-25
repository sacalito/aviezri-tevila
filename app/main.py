from flask import Flask
from routes import routes
from log_config import setup_logging
from database import init_db, get_all_hours, get_all_dates
from time import sleep
import datetime
from relayControl import activate_elevator_flow
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

logger = setup_logging()

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# Initialize the database
init_db(app)

def check_operating_hours():
    with app.app_context():
        now = datetime.datetime.now()
        current_date = now.strftime('%Y-%m-%d')  # e.g., '2025-04-28'
        current_day = now.strftime('%A')  # e.g., 'Monday'
        current_time = now.strftime('%H:%M:%S')  # e.g., '14:30:00'
        
        logger.info(f"Checking operating hours at {current_time}")
        
        # First check if today is a special date
        special_dates = get_all_dates()
        is_special_date = any(date.date == current_date for date in special_dates)
        
        if is_special_date:
            logger.info(f"Today ({current_date}) is marked as a special date")
            # Use 'Holiday' schedule instead of regular weekday
            current_day = 'Holiday'
        
        logger.info(f"Using schedule for: {current_day}")
        
        hours = get_all_hours()
        for hour in hours:
            if hour.day == current_day and hour.start_time <= current_time <= hour.end_time:
                logger.info(f"Current time ({current_time}) is within operating hours for {current_day}")
                activate_elevator_flow()
                return True
        
        logger.info(f"Current time ({current_time}) is outside operating hours for {current_day}")
        # You could add actions for outside operating hours here
        return False

# Initialize the scheduler
scheduler = BackgroundScheduler()

# Add job to run exactly at minutes 0, 10, 20, 30, 40, 50 of every hour
scheduler.add_job(
    func=check_operating_hours,
    trigger='cron',
    minute='0,10,20,30,40,50',  # Run at these minutes of every hour
    id='check_operating_hours_job',
    name='Check operating hours',
    misfire_grace_time=30  # Allow up to 30 seconds late
)

# Start the scheduler
scheduler.start()

# Register a function to shut down the scheduler when the app exits
atexit.register(lambda: scheduler.shutdown())



app.register_blueprint(routes)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)