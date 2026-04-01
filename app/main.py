from flask import Flask
from routes import routes
from log_config import setup_logging
from database import init_db, get_all_dates, get_hours_by_relay_and_day, get_bypass, clear_bypass
from relayControl import turn_on, turn_off, get_relay_state, RELAY_PINS
import datetime
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

logger = setup_logging()

app = Flask(__name__,
            static_folder='static',
            template_folder='templates')
app.secret_key = 'tEvIlA_s3cr3t_k3y_2026!'

init_db(app)

def check_relay_schedule(relay_name):
    """Check if a relay should be on or off based on its schedule."""
    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    current_date = now.strftime('%Y-%m-%d')
    current_day = now.strftime('%A')
    current_time = now.strftime('%H:%M:%S')

    # Check for active bypass
    bypass = get_bypass(relay_name)
    if bypass:
        if bypass.until > now_str:
            # Bypass is active — enforce its state
            is_currently_on = not get_relay_state(relay_name)
            bypass_on = bypass.state == 'on'
            if bypass_on and not is_currently_on:
                logger.info(f"[{relay_name}] Bypass ON until {bypass.until}")
                turn_on(relay_name)
            elif not bypass_on and is_currently_on:
                logger.info(f"[{relay_name}] Bypass OFF until {bypass.until}")
                turn_off(relay_name)
            return
        else:
            # Bypass expired — clear it
            logger.info(f"[{relay_name}] Bypass expired, clearing")
            clear_bypass(relay_name)

    # Check if today is a special date
    special_dates = get_all_dates()
    is_special_date = any(d.date == current_date for d in special_dates)

    if is_special_date:
        current_day = 'Holiday'

    # Get schedule entries for this relay and day
    hours = get_hours_by_relay_and_day(relay_name, current_day)

    should_be_on = False
    for hour in hours:
        if hour.start_time <= current_time <= hour.end_time:
            should_be_on = True
            break

    # Check current state and act accordingly
    is_currently_on = not get_relay_state(relay_name)

    if should_be_on and not is_currently_on:
        logger.info(f"[{relay_name}] Turning ON (schedule: {current_day} {current_time})")
        turn_on(relay_name)
    elif not should_be_on and is_currently_on:
        logger.info(f"[{relay_name}] Turning OFF (outside schedule: {current_day} {current_time})")
        turn_off(relay_name)
    else:
        state = "ON" if is_currently_on else "OFF"
        logger.info(f"[{relay_name}] Already {state} (schedule: {current_day} {current_time})")

def check_all_schedules():
    """Check schedules for all relays."""
    with app.app_context():
        for relay_name in RELAY_PINS:
            check_relay_schedule(relay_name)

scheduler = BackgroundScheduler()
scheduler.add_job(
    func=check_all_schedules,
    trigger='cron',
    minute='*',
    id='check_schedules_job',
    name='Check relay schedules',
    misfire_grace_time=30
)

app.register_blueprint(routes)

scheduler.start()
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
