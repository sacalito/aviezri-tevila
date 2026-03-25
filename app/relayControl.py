from gpiozero import LED
import threading
import logging

logger = logging.getLogger(__name__)

RELAY_PINS = {
    'heating': 24,
    'filtering': 23
}

# Initialize all relays once at module load
relays = {}
for _name, _pin in RELAY_PINS.items():
    relays[_name] = LED(_pin)
    relays[_name].on()  # default state: relay open (off)
    logger.info(f"Initialized relay '{_name}' on GPIO {_pin}")

def _get_relay(relay_name):
    if relay_name not in relays:
        raise ValueError(f"Unknown relay: {relay_name}")
    return relays[relay_name]

def get_relay_state(relay_name):
    relay = _get_relay(relay_name)
    return relay.is_active

def turn_on(relay_name):
    relay = _get_relay(relay_name)
    relay.off()  # closing the relay circuit = turning ON
    logger.info(f"Relay '{relay_name}' turned ON")
    return True

def turn_off(relay_name):
    relay = _get_relay(relay_name)
    relay.on()  # opening the relay circuit = turning OFF
    logger.info(f"Relay '{relay_name}' turned OFF")
    return True

def turn_on_for_time(relay_name, seconds):
    turn_on(relay_name)
    timer = threading.Timer(float(seconds), turn_off, args=[relay_name])
    timer.start()
    logger.info(f"Relay '{relay_name}' turned ON for {seconds} seconds")

def turn_off_for_time(relay_name, seconds):
    turn_off(relay_name)
    timer = threading.Timer(float(seconds), turn_on, args=[relay_name])
    timer.start()
    logger.info(f"Relay '{relay_name}' turned OFF for {seconds} seconds")
