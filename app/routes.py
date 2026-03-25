# routes.py
from flask import Blueprint, request, render_template, current_app
from relayControl import *
from functions import *
from api import require_token
import logging
from datetime import datetime
from database import get_all_hours, add_hours, get_hours_by_day, delete_hours, get_all_dates, add_date, delete_date
from time import sleep

routes = Blueprint('routes', __name__)

@routes.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@routes.route('/time', methods=['GET', 'POST'])
@require_token
def time():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {'status': 'online', 'time': current_time}

@routes.route('/api/status', methods=['GET', 'POST'])
@require_token
def api_status():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {'status': 'online', 'time': current_time}

# @routes.route('/status', methods=['POST'])
# @require_token
# def status():
#     relayStatus = {}
#     for relay in relays:
#         relayStatus[relays[relay]['name']] = 'open' if checkRelayState(relays[relay]['id']) else 'closed'
#     return relayStatus

@routes.route('/check', methods=['POST'])
@require_token
def check():
    try:
        data = request.get_json()
        relay_id = data.get('relay')
        status = checkRelayState(relay_id)
        return {'relay': status}
    except (KeyError, TypeError):
        return {'error': 'Invalid request format'}, 400

@routes.route('/open', methods=['POST'])
@require_token
def open():
    try:
        data = request.get_json()
        relay_id = data.get('relay')
        seconds = data.get('seconds')
        if seconds is not None:
            opened = openRelayForTime(relay_id, seconds)
            return {'relay': opened}
        else:
            opened = openRelay(relay_id)
            return {'relay': opened}
    except (KeyError, TypeError) as e:
        logging.error(f'Exception occurred: {e}')
        logging.error('Exception occurred', exc_info=True)
        return {'error': 'Invalid request format:'}, 400

@routes.route('/close', methods=['POST'])
@require_token
def close():
    try:
        data = request.get_json()
        relay_id = data.get('relay')
        seconds = data.get('seconds')
        if seconds is not None:
            closed = closeRelayForTime(relay_id, seconds)
            return {'relay': closed}
        else:
            closed = closeRelay(relay_id)
            return {'relay': closed}
    except (KeyError, TypeError) as e:
        logging.error(f'Exception occurred: {e}')
        logging.error('Exception occurred', exc_info=True)
        return {'error': 'Invalid request format:'}, 400
    

@routes.route('/hours', methods=['POST'])
@require_token
def get_hours():
    try:
        data = request.get_json()
        day = data.get('day')
        if day:
            hours_data = get_hours_by_day(day)
            if not hours_data:
                return {'error': 'No hours found for the specified day'}, 404
            result = {
                'id': hours_data.id,
                'day': hours_data.day,
                'start_time': hours_data.start_time,
                'end_time': hours_data.end_time
            }
            return {'hours': result}
        
        hours_data = get_all_hours()
        result = []
        for hour in hours_data:
            result.append({
                'id': hour.id,
                'day': hour.day,
                'start_time': hour.start_time,
                'end_time': hour.end_time
            })
        
        # Define day order for sorting
        day_order = {
            'Monday': 0,
            'Tuesday': 1,
            'Wednesday': 2,
            'Thursday': 3,
            'Friday': 4,
            'Saturday': 5,
            'Sunday': 6,
            'Holiday': 7
        }
        
        # Sort the result by day according to predefined order
        result.sort(key=lambda x: (day_order.get(x['day'], 99), x['start_time']))
        
        return {'hours': result}
    except Exception as e:
        logging.error(f'Exception occurred when fetching hours: {e}')
        logging.error('Exception details:', exc_info=True)
        return {'error': 'Failed to retrieve hours data'}
    

@routes.route('/add_hours', methods=['POST'])
@require_token
def add_hours_route():
    try:
        data = request.get_json()
        day = data.get('day')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        # Validate input data
        if not all([day, start_time, end_time]):
            return {'error': 'Missing required fields (day, start_time, end_time)'}, 400
            
        # Add hours to database
        new_hours = add_hours(day, start_time, end_time)
        
        return {
            'success': True,
            'hours': {
                'id': new_hours.id,
                'day': new_hours.day,
                'start_time': new_hours.start_time,
                'end_time': new_hours.end_time
            }
        }
    except Exception as e:
        logging.error(f'Exception occurred when adding hours: {e}')
        logging.error('Exception details:', exc_info=True)
        return {'error': 'Failed to add hours data'}, 500
    
@routes.route('/delete_hours', methods=['POST'])
@require_token
def delete_hours_route():
    try:
        data = request.get_json()
        hour_id = data.get('hour_id')
        result = delete_hours(hour_id)
        if result:
            return {'success': True, 'message': f'Hours with ID {hour_id} deleted successfully'}
        else:
            return {'error': f'No hours found with ID {hour_id}'}, 404
    except Exception as e:
        logging.error(f'Exception occurred when deleting hours: {e}')
        logging.error('Exception details:', exc_info=True)
        return {'error': 'Failed to delete hours'}, 500
    
@routes.route('/dates', methods=['GET', 'POST'])
@require_token
def get_dates():
    try:
        dates = get_all_dates()
        result = []
        for date in dates:
            result.append({
                'id': date.id,
                'date': date.date,
            })
        return {'dates': result}
    except Exception as e:
        logging.error(f'Exception occurred when fetching dates: {e}')
        logging.error('Exception details:', exc_info=True)
        return {'error': 'Failed to retrieve dates data'}
    
@routes.route('/add_date', methods=['POST'])
@require_token
def add_date_route():
    try:
        data = request.get_json()
        date_str = data.get('date')
        
        # Validate input data
        if not date_str:
            return {'error': 'Missing required field (date)'}, 400
        
        # Add date to database
        new_date = add_date(date_str)
        
        return {
            'success': True,
            'date': {
                'id': new_date.id,
                'date': new_date.date
            }
        }
    except Exception as e:
        logging.error(f'Exception occurred when adding date: {e}')
        logging.error('Exception details:', exc_info=True)
        return {'error': 'Failed to add date'}, 500
    
@routes.route('/delete_date', methods=['POST'])
@require_token
def delete_date_route():
    try:
        data = request.get_json()
        date_id = data.get('date_id')
        result = delete_date(date_id)
        if result:
            return {'success': True, 'message': f'Date with ID {date_id} deleted successfully'}
        else:
            return {'error': f'No Date found with ID {date_id}'}, 404
    except Exception as e:
        logging.error(f'Exception occurred when deleting Date: {e}')
        logging.error('Exception details:', exc_info=True)
        return {'error': 'Failed to delete hours'}, 500
    
@routes.route('/test', methods=['POST'])
@require_token
def test_elevator():
    try:
        activate_elevator_flow()
        return {'success': True, 'message': f' Tested successfully'}
    except Exception as e:
        logging.error(f'Exception occurred when Testing: {e}')
        logging.error('Exception details:', exc_info=True)
        return {'error': 'Failed to test'}, 500
    
@routes.route('/test_floor', methods=['POST'])
@require_token
def test_floor():
    try:
        data = request.get_json()
        relay_id = data.get('relay_id')
        closeRelayForTime(relay_id, 1)
        return {'success': True, 'message': f' Tested successfully'}
    except Exception as e:
        logging.error(f'Exception occurred when Testing: {e}')
        logging.error('Exception details:', exc_info=True)
        return {'error': 'Failed to test'}, 500