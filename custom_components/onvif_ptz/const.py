"""Constants for onvif_ptz."""
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

NAME = "ONVIF PTZ"
DOMAIN = "onvif_ptz"
VERSION = "0.0.0"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"

DEFAULT_PORT = 80

CONF_DEVICE_ID = "deviceid"
CONF_SNAPSHOT_AUTH = "snapshot_auth"

ATTR_PAN = "pan"
ATTR_TILT = "tilt"
ATTR_ZOOM = "zoom"
ATTR_DISTANCE = "distance"
ATTR_SPEED = "speed"
ATTR_MOVE_MODE = "move_mode"
ATTR_CONTINUOUS_DURATION = "continuous_duration"
ATTR_PRESET = "preset"

DIR_UP = "UP"
DIR_DOWN = "DOWN"
DIR_LEFT = "LEFT"
DIR_RIGHT = "RIGHT"
ZOOM_OUT = "ZOOM_OUT"
ZOOM_IN = "ZOOM_IN"
PAN_FACTOR = {DIR_RIGHT: 1, DIR_LEFT: -1}
TILT_FACTOR = {DIR_UP: 1, DIR_DOWN: -1}
ZOOM_FACTOR = {ZOOM_IN: 1, ZOOM_OUT: -1}
CONTINUOUS_MOVE = "ContinuousMove"
RELATIVE_MOVE = "RelativeMove"
ABSOLUTE_MOVE = "AbsoluteMove"
GOTOPRESET_MOVE = "GotoPreset"
STOP_MOVE = "Stop"

SERVICE_RELATIVE_MOVE_PTZ = "ptz_relative"
SERVICE_ABSOLUTE_MOVE_PTZ = "ptz_absolute"
SERVICE_CONTINUOUS_MOVE_PTZ = "ptz_continuous"
SERVICE_STOP_PTZ = "ptz_stop"
