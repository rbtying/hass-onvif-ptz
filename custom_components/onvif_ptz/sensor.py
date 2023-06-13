import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_platform, config_validation as cv
from homeassistant.components.sensor import SensorEntity

from .base import ONVIFBaseEntity
from .const import ATTR_TRANSLATION, ATTR_SPEED, SERVICE_RELATIVE_MOVE_PTZ, DOMAIN
from .device import ONVIFDevice
from .models import Profile


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    platform = entity_platform.async_get_current_platform()

    device = hass.data[DOMAIN][config_entry.unique_id]
    # async_add_entities(
    #     [ONVIFCameraPTZEntity(device, profile) for profile in device.profiles]
    # )
