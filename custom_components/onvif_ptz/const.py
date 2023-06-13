"""Constants for onvif_ptz."""
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

NAME = "ONVIF PTZ"
DOMAIN = "onvif_ptz"
VERSION = "0.0.0"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

DEFAULT_PORT = 80

CONF_DEVICE_ID = "deviceid"

ATTR_TRANSLATION = "translation"
ATTR_SPEED = "speed"
ATTR_POSITION = "position"
ATTR_VELOCITY = "velocity"
ATTR_PANTILT = "pan_tilt"
ATTR_ZOOM = "zoom"
ATTR_TIMEOUT = "timeout"

SERVICE_RELATIVE_MOVE_PTZ = "ptz_relative"
SERVICE_ABSOLUTE_MOVE_PTZ = "ptz_absolute"
SERVICE_CONTINUOUS_MOVE_PTZ = "ptz_continuous"
SERVICE_STOP_PTZ = "ptz_stop"
