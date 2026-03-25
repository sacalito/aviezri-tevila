from gpiozero import LED
from time import sleep
import threading

relays = {}

floors = {
    1: 4,
    5: 17,
    18: 27
}

def checkRelayState(relay_id):
    if relay_id not in relays:
        relays[relay_id] = LED(relay_id)
        relays[relay_id].on()
    relay_status = relays[relay_id].is_active
    if relay_status:
        return 'Relay is Open'
    else:
        return 'Relay is Closed'

def relayState(relay_id):
    if relay_id not in relays:
        relays[relay_id] = LED(relay_id)
        relays[relay_id].on()
    return relays[relay_id].is_active

def openRelay(relay_id):
    if relay_id not in relays:
        relays[relay_id] = LED(relay_id)
    relays[relay_id].on()
    return 'Relay Turned Open'

def closeRelay(relay_id):
    if relay_id not in relays:
        relays[relay_id] = LED(relay_id)
    relays[relay_id].off()
    return 'Relay Turned Closed'

def openRelayForTime(relay_id, seconds):
    state = relayState(relay_id)
    if state:
        return 'Relay was Open'
    openRelay(relay_id)
    timer = threading.Timer(float(seconds), closeRelay, args=[relay_id])
    timer.start()
    return 'Relay Turned Open for ' + str(seconds) + ' seconds'

def closeRelayForTime(relay_id, seconds):
    state = relayState(relay_id)
    if not state:
        return 'Relay was Closed'
    closeRelay(relay_id)
    timer = threading.Timer(float(seconds), openRelay, args=[relay_id])
    timer.start()
    return 'Relay Turned Closed for ' + str(seconds) + ' seconds'

def activatefloor(floor_id):
    relay_id = floors[floor_id]
    closeRelayForTime(relay_id, 1)

def activate_elevator_flow():
    activatefloor(5)
    sleep(10)
    activatefloor(18)
    sleep(30)
    activatefloor(5)
    # sleep(30)
    # activatefloor(1)
    # sleep(15)
    # activatefloor(5)


# Make specific items available for import
__all__ = [
    'relays',
    'checkRelayState',
    'openRelay',
    'closeRelay',
    'openRelayForTime',
    'closeRelayForTime',
    'activatefloor',
    'activate_elevator_flow',
]