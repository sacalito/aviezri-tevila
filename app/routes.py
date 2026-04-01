from flask import Blueprint, request, render_template, session
from relayControl import get_relay_state, turn_on, turn_off, RELAY_PINS
from api import require_token
import logging
from datetime import datetime
from database import (
    get_all_hours, add_hours, get_hours_by_relay, delete_hours, update_hours,
    get_all_dates, add_date, delete_date,
    get_all_erev_jag_dates, add_erev_jag_date, delete_erev_jag_date,
    set_bypass, get_all_bypasses, clear_bypass
)

routes = Blueprint('routes', __name__)

WEB_PASSWORD = '5582101378'

@routes.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    password = data.get('password', '')
    if password == WEB_PASSWORD:
        session['authenticated'] = True
        return {'success': True}
    return {'success': False, 'error': 'Wrong password'}, 401

@routes.route('/check_session', methods=['GET'])
def check_session():
    if session.get('authenticated'):
        return {'authenticated': True}
    return {'authenticated': False}, 401

@routes.route('/api/status', methods=['GET', 'POST'])
@require_token
def api_status():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    heating_on = not get_relay_state('heating')
    filtering_on = not get_relay_state('filtering')
    return {
        'status': 'online',
        'time': current_time,
        'heating': 'on' if heating_on else 'off',
        'filtering': 'on' if filtering_on else 'off'
    }

@routes.route('/relay/on', methods=['POST'])
@require_token
def relay_on():
    try:
        data = request.get_json()
        relay_name = data.get('relay')
        if relay_name not in RELAY_PINS:
            return {'error': f'Unknown relay: {relay_name}. Use "heating" or "filtering"'}, 400
        turn_on(relay_name)
        return {'success': True, 'relay': relay_name, 'state': 'on'}
    except Exception as e:
        logging.error(f'Error turning on relay: {e}', exc_info=True)
        return {'error': 'Failed to turn on relay'}, 500

@routes.route('/relay/off', methods=['POST'])
@require_token
def relay_off():
    try:
        data = request.get_json()
        relay_name = data.get('relay')
        if relay_name not in RELAY_PINS:
            return {'error': f'Unknown relay: {relay_name}. Use "heating" or "filtering"'}, 400
        turn_off(relay_name)
        return {'success': True, 'relay': relay_name, 'state': 'off'}
    except Exception as e:
        logging.error(f'Error turning off relay: {e}', exc_info=True)
        return {'error': 'Failed to turn off relay'}, 500

@routes.route('/relay/status', methods=['POST'])
@require_token
def relay_status():
    try:
        data = request.get_json()
        relay_name = data.get('relay')
        if relay_name not in RELAY_PINS:
            return {'error': f'Unknown relay: {relay_name}. Use "heating" or "filtering"'}, 400
        is_on = not get_relay_state(relay_name)
        return {'relay': relay_name, 'state': 'on' if is_on else 'off'}
    except Exception as e:
        logging.error(f'Error checking relay: {e}', exc_info=True)
        return {'error': 'Failed to check relay status'}, 500

# --- Schedule endpoints ---

@routes.route('/hours', methods=['POST'])
@require_token
def get_hours():
    try:
        data = request.get_json()
        relay = data.get('relay')

        if relay:
            hours_data = get_hours_by_relay(relay)
        else:
            hours_data = get_all_hours()

        result = []
        for hour in hours_data:
            result.append({
                'id': hour.id,
                'relay': hour.relay,
                'day': hour.day,
                'start_time': hour.start_time,
                'end_time': hour.end_time
            })

        day_order = {
            'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
            'Friday': 4, 'Saturday': 5, 'Sunday': 6, 'YomTov': 7, 'ErevJag': 8
        }
        result.sort(key=lambda x: (x['relay'], day_order.get(x['day'], 99), x['start_time']))

        return {'hours': result}
    except Exception as e:
        logging.error(f'Error fetching hours: {e}', exc_info=True)
        return {'error': 'Failed to retrieve hours data'}, 500

@routes.route('/add_hours', methods=['POST'])
@require_token
def add_hours_route():
    try:
        data = request.get_json()
        relay = data.get('relay')
        day = data.get('day')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        if not all([relay, day, start_time, end_time]):
            return {'error': 'Missing required fields (relay, day, start_time, end_time)'}, 400

        if relay not in RELAY_PINS:
            return {'error': f'Unknown relay: {relay}. Use "heating" or "filtering"'}, 400

        new_hours = add_hours(relay, day, start_time, end_time)

        return {
            'success': True,
            'hours': {
                'id': new_hours.id,
                'relay': new_hours.relay,
                'day': new_hours.day,
                'start_time': new_hours.start_time,
                'end_time': new_hours.end_time
            }
        }
    except Exception as e:
        logging.error(f'Error adding hours: {e}', exc_info=True)
        return {'error': 'Failed to add hours data'}, 500

@routes.route('/update_hours', methods=['POST'])
@require_token
def update_hours_route():
    try:
        data = request.get_json()
        hour_id = data.get('hour_id')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        day = data.get('day')

        if not hour_id:
            return {'error': 'Missing required field (hour_id)'}, 400

        updated = update_hours(hour_id, start_time=start_time, end_time=end_time, day=day)
        if updated:
            return {
                'success': True,
                'hours': {
                    'id': updated.id,
                    'relay': updated.relay,
                    'day': updated.day,
                    'start_time': updated.start_time,
                    'end_time': updated.end_time
                }
            }
        else:
            return {'error': f'No hours found with ID {hour_id}'}, 404
    except Exception as e:
        logging.error(f'Error updating hours: {e}', exc_info=True)
        return {'error': 'Failed to update hours'}, 500

@routes.route('/delete_hours', methods=['POST'])
@require_token
def delete_hours_route():
    try:
        data = request.get_json()
        hour_id = data.get('hour_id')
        result = delete_hours(hour_id)
        if result:
            return {'success': True, 'message': f'Hours with ID {hour_id} deleted'}
        else:
            return {'error': f'No hours found with ID {hour_id}'}, 404
    except Exception as e:
        logging.error(f'Error deleting hours: {e}', exc_info=True)
        return {'error': 'Failed to delete hours'}, 500

# --- Special dates endpoints ---

@routes.route('/dates', methods=['GET', 'POST'])
@require_token
def get_dates():
    try:
        dates = get_all_dates()
        result = [{'id': d.id, 'date': d.date} for d in dates]
        return {'dates': result}
    except Exception as e:
        logging.error(f'Error fetching dates: {e}', exc_info=True)
        return {'error': 'Failed to retrieve dates data'}, 500

@routes.route('/add_date', methods=['POST'])
@require_token
def add_date_route():
    try:
        data = request.get_json()
        date_str = data.get('date')
        if not date_str:
            return {'error': 'Missing required field (date)'}, 400
        new_date = add_date(date_str)
        return {'success': True, 'date': {'id': new_date.id, 'date': new_date.date}}
    except Exception as e:
        logging.error(f'Error adding date: {e}', exc_info=True)
        return {'error': 'Failed to add date'}, 500

@routes.route('/delete_date', methods=['POST'])
@require_token
def delete_date_route():
    try:
        data = request.get_json()
        date_id = data.get('date_id')
        result = delete_date(date_id)
        if result:
            return {'success': True, 'message': f'Date with ID {date_id} deleted'}
        else:
            return {'error': f'No date found with ID {date_id}'}, 404
    except Exception as e:
        logging.error(f'Error deleting date: {e}', exc_info=True)
        return {'error': 'Failed to delete date'}, 500

# --- Bypass endpoints ---

@routes.route('/api/bypasses', methods=['GET'])
@require_token
def get_bypasses():
    try:
        bypasses = get_all_bypasses()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result = []
        for b in bypasses:
            if b.until > now:
                result.append({'relay': b.relay, 'state': b.state, 'until': b.until})
            else:
                clear_bypass(b.relay)
        return {'bypasses': result}
    except Exception as e:
        logging.error(f'Error fetching bypasses: {e}', exc_info=True)
        return {'error': 'Failed to retrieve bypasses'}, 500

@routes.route('/relay/bypass', methods=['POST'])
@require_token
def set_bypass_route():
    try:
        data = request.get_json()
        relay = data.get('relay')
        state = data.get('state')
        until = data.get('until')

        if not all([relay, state, until]):
            return {'error': 'Missing required fields (relay, state, until)'}, 400
        if relay not in RELAY_PINS:
            return {'error': f'Unknown relay: {relay}'}, 400
        if state not in ('on', 'off'):
            return {'error': 'State must be "on" or "off"'}, 400

        bypass = set_bypass(relay, state, until)

        if state == 'on':
            turn_on(relay)
        else:
            turn_off(relay)

        logging.info(f'Bypass set: {relay} {state} until {until}')
        return {
            'success': True,
            'bypass': {'relay': bypass.relay, 'state': bypass.state, 'until': bypass.until}
        }
    except Exception as e:
        logging.error(f'Error setting bypass: {e}', exc_info=True)
        return {'error': 'Failed to set bypass'}, 500

@routes.route('/relay/clear_bypass', methods=['POST'])
@require_token
def clear_bypass_route():
    try:
        data = request.get_json()
        relay = data.get('relay')
        if not relay:
            return {'error': 'Missing relay field'}, 400
        result = clear_bypass(relay)
        if result:
            logging.info(f'Bypass cleared for {relay}')
            return {'success': True, 'message': f'Bypass cleared for {relay}'}
        return {'error': 'No active bypass for this relay'}, 404
    except Exception as e:
        logging.error(f'Error clearing bypass: {e}', exc_info=True)
        return {'error': 'Failed to clear bypass'}, 500

# --- Erev Jag dates endpoints ---

@routes.route('/erev_jag_dates', methods=['GET'])
@require_token
def get_erev_jag_dates():
    try:
        dates = get_all_erev_jag_dates()
        result = [{'id': d.id, 'date': d.date} for d in dates]
        return {'dates': result}
    except Exception as e:
        logging.error(f'Error fetching erev jag dates: {e}', exc_info=True)
        return {'error': 'Failed to retrieve erev jag dates'}, 500

@routes.route('/add_erev_jag_date', methods=['POST'])
@require_token
def add_erev_jag_date_route():
    try:
        data = request.get_json()
        date_str = data.get('date')
        if not date_str:
            return {'error': 'Missing required field (date)'}, 400
        new_date = add_erev_jag_date(date_str)
        return {'success': True, 'date': {'id': new_date.id, 'date': new_date.date}}
    except Exception as e:
        logging.error(f'Error adding erev jag date: {e}', exc_info=True)
        return {'error': 'Failed to add erev jag date'}, 500

@routes.route('/delete_erev_jag_date', methods=['POST'])
@require_token
def delete_erev_jag_date_route():
    try:
        data = request.get_json()
        date_id = data.get('date_id')
        result = delete_erev_jag_date(date_id)
        if result:
            return {'success': True, 'message': f'Erev Jag date with ID {date_id} deleted'}
        else:
            return {'error': f'No erev jag date found with ID {date_id}'}, 404
    except Exception as e:
        logging.error(f'Error deleting erev jag date: {e}', exc_info=True)
        return {'error': 'Failed to delete erev jag date'}, 500
