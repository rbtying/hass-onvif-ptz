import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_platform, config_validation as cv
from homeassistant.components.button import ButtonEntity

from .base import ONVIFBaseEntity
from .const import (
    ATTR_TRANSLATION,
    ATTR_POSITION,
    ATTR_VELOCITY,
    ATTR_SPEED,
    ATTR_PANTILT,
    ATTR_ZOOM,
    ATTR_TIMEOUT,
    SERVICE_RELATIVE_MOVE_PTZ,
    SERVICE_ABSOLUTE_MOVE_PTZ,
    SERVICE_CONTINUOUS_MOVE_PTZ,
    SERVICE_STOP_PTZ,
    DOMAIN,
)
from .device import ONVIFDevice
from .models import Profile


PTZ_SCHEMA = vol.Schema(
    {
        vol.Optional("PanTilt"): vol.Schema(
            {
                vol.Required("x"): vol.Coerce(float),
                vol.Required("y"): vol.Coerce(float),
            }
        ),
        vol.Optional("Zoom"): vol.Coerce(float),
    }
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the ONVIF camera video stream."""
    platform = entity_platform.async_get_current_platform()

    # Create PTZ service
    platform.async_register_entity_service(
        SERVICE_RELATIVE_MOVE_PTZ,
        {
            vol.Required(ATTR_TRANSLATION): PTZ_SCHEMA,
            vol.Optional(ATTR_SPEED): PTZ_SCHEMA,
        },
        "async_perform_ptz_relative",
    )
    platform.async_register_entity_service(
        SERVICE_ABSOLUTE_MOVE_PTZ,
        {
            vol.Required(ATTR_POSITION): PTZ_SCHEMA,
            vol.Optional(ATTR_SPEED): PTZ_SCHEMA,
        },
        "async_perform_ptz_absolute",
    )
    platform.async_register_entity_service(
        SERVICE_CONTINUOUS_MOVE_PTZ,
        {
            vol.Required(ATTR_VELOCITY): PTZ_SCHEMA,
            vol.Optional(ATTR_TIMEOUT): cv.positive_float,
        },
        "async_perform_ptz_continuous",
    )
    platform.async_register_entity_service(
        SERVICE_STOP_PTZ,
        {
            vol.Optional(ATTR_PANTILT): cv.boolean,
            vol.Optional(ATTR_ZOOM): cv.boolean,
        },
        "async_perform_ptz_stop",
    )

    device = hass.data[DOMAIN][config_entry.unique_id]
    async_add_entities(
        [ONVIFCameraPTZEntity(device, profile) for profile in device.profiles]
    )


class ONVIFCameraPTZEntity(ONVIFBaseEntity, ButtonEntity):
    """Representation of an ONVIF camera's PTZ controls."""

    def __init__(self, device: ONVIFDevice, profile: Profile) -> None:
        """Initialize ONVIF camera entity."""
        ONVIFBaseEntity.__init__(self, device)
        ButtonEntity.__init__(self)
        self.profile = profile

    @property
    def name(self) -> str:
        """Return the name of this camera PTZ control."""
        return f"{self.device.name} {self.profile.name} PTZ Controls"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self.mac_or_serial}_{self.profile.name} PTZ Controls"

    @property
    def entity_registry_enabled_default(self) -> bool:
        """Return if the entity should be enabled when first added to the entity registry."""
        return True

    async def async_press(self) -> None:
        await self.device.async_perform_ptz_stop(self.profile)

    async def async_perform_ptz_relative(self, translation, speed=None) -> None:
        """Perform a RelativeMove PTZ action on the camera."""
        await self.device.async_perform_ptz_relative(self.profile, translation, speed)

    async def async_perform_ptz_absolute(self, position, speed=None) -> None:
        """Perform an AbsoluteMove PTZ action on the camera."""
        await self.device.async_perform_ptz_absolute(self.profile, position, speed)

    async def async_perform_ptz_continuous(self, velocity, timeout=None) -> None:
        """Perform an ContinuousMove PTZ action on the camera."""
        await self.device.async_perform_ptz_continuous(self.profile, velocity, timeout)

    async def async_perform_ptz_stop(self, pan_tilt=None, zoom=None) -> None:
        """Perform a Stop PTZ action on the camera."""
        await self.device.async_perform_ptz_stop(
            self.profile, pan_tilt=pan_tilt, zoom=zoom
        )
