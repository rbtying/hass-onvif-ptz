"""ONVIF device abstraction."""
from __future__ import annotations

from contextlib import suppress
import datetime as dt
import os
import time

from httpx import RequestError
import onvif
from onvif import ONVIFCamera
from onvif.exceptions import ONVIFError
from zeep.exceptions import Fault

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
import homeassistant.util.dt as dt_util

from .const import (
    LOGGER,
)
from .models import PTZ, Capabilities, DeviceInfo, Profile


class ONVIFDevice:
    """Manages an ONVIF device."""

    device: ONVIFCamera

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the device."""
        self.hass: HomeAssistant = hass
        self.config_entry: ConfigEntry = config_entry
        self.available: bool = True

        self.info: DeviceInfo = DeviceInfo()
        self.capabilities: Capabilities = Capabilities()
        self.profiles: list[Profile] = []
        self.max_resolution: int = 0

        self._dt_diff_seconds: float = 0

    @property
    def name(self) -> str:
        """Return the name of this device."""
        return self.config_entry.data[CONF_NAME]

    @property
    def host(self) -> str:
        """Return the host of this device."""
        return self.config_entry.data[CONF_HOST]

    @property
    def port(self) -> int:
        """Return the port of this device."""
        return self.config_entry.data[CONF_PORT]

    @property
    def username(self) -> str:
        """Return the username of this device."""
        return self.config_entry.data[CONF_USERNAME]

    @property
    def password(self) -> str:
        """Return the password of this device."""
        return self.config_entry.data[CONF_PASSWORD]

    async def async_setup(self) -> bool:
        """Set up the device."""
        self.device = get_device(
            self.hass,
            host=self.config_entry.data[CONF_HOST],
            port=self.config_entry.data[CONF_PORT],
            username=self.config_entry.data[CONF_USERNAME],
            password=self.config_entry.data[CONF_PASSWORD],
        )

        # Get all device info
        try:
            await self.device.update_xaddrs()
            await self.async_check_date_and_time()

            assert self.config_entry.unique_id

            # Fetch basic device info and capabilities
            self.info = await self.async_get_device_info()
            LOGGER.debug("Camera %s info = %s", self.name, self.info)
            self.capabilities = await self.async_get_capabilities()
            LOGGER.debug("Camera %s capabilities = %s", self.name, self.capabilities)
            self.profiles = await self.async_get_profiles()
            LOGGER.debug(
                "Camera %s media profiles with ptz = %s", self.name, self.profiles
            )

            # No camera ptz nodes to add
            if not self.profiles:
                return False

            if self.capabilities.ptz:
                await self.device.create_ptz_service()

        except RequestError as err:
            LOGGER.warning(
                "Couldn't connect to camera '%s', but will retry later. Error: %s",
                self.name,
                err,
            )
            self.available = False
            await self.device.close()
        except Fault as err:
            LOGGER.error(
                (
                    "Couldn't connect to camera '%s', please verify "
                    "that the credentials are correct. Error: %s"
                ),
                self.name,
                err,
            )
            return False

        return True

    async def async_stop(self, event=None):
        """Shut it all down."""
        await self.device.close()

    async def async_manually_set_date_and_time(self) -> None:
        """Set Date and Time Manually using SetSystemDateAndTime command."""
        device_mgmt = await self.device.create_devicemgmt_service()

        # Retrieve DateTime object from camera to use as template for Set operation
        device_time = await device_mgmt.GetSystemDateAndTime()

        system_date = dt_util.utcnow()
        LOGGER.debug("System date (UTC): %s", system_date)

        dt_param = device_mgmt.create_type("SetSystemDateAndTime")
        dt_param.DateTimeType = "Manual"
        # Retrieve DST setting from system
        dt_param.DaylightSavings = bool(time.localtime().tm_isdst)
        dt_param.UTCDateTime = device_time.UTCDateTime
        # Retrieve timezone from system
        dt_param.TimeZone = str(system_date.astimezone().tzinfo)
        dt_param.UTCDateTime.Date.Year = system_date.year
        dt_param.UTCDateTime.Date.Month = system_date.month
        dt_param.UTCDateTime.Date.Day = system_date.day
        dt_param.UTCDateTime.Time.Hour = system_date.hour
        dt_param.UTCDateTime.Time.Minute = system_date.minute
        dt_param.UTCDateTime.Time.Second = system_date.second
        LOGGER.debug("SetSystemDateAndTime: %s", dt_param)
        await device_mgmt.SetSystemDateAndTime(dt_param)

    async def async_check_date_and_time(self) -> None:
        """Warns if device and system date not synced."""
        LOGGER.debug("Setting up the ONVIF device management service")
        device_mgmt = await self.device.create_devicemgmt_service()

        LOGGER.debug("Retrieving current device date/time")
        try:
            system_date = dt_util.utcnow()
            device_time = await device_mgmt.GetSystemDateAndTime()
            if not device_time:
                LOGGER.debug(
                    """Couldn't get device '%s' date/time.
                    GetSystemDateAndTime() return null/empty""",
                    self.name,
                )
                return

            LOGGER.debug("Device time: %s", device_time)

            tzone = dt_util.DEFAULT_TIME_ZONE
            cdate = device_time.LocalDateTime
            if device_time.UTCDateTime:
                tzone = dt_util.UTC
                cdate = device_time.UTCDateTime
            elif device_time.TimeZone:
                tzone = dt_util.get_time_zone(device_time.TimeZone.TZ) or tzone

            if cdate is None:
                LOGGER.warning("Could not retrieve date/time on this camera")
            else:
                cam_date = dt.datetime(
                    cdate.Date.Year,
                    cdate.Date.Month,
                    cdate.Date.Day,
                    cdate.Time.Hour,
                    cdate.Time.Minute,
                    cdate.Time.Second,
                    0,
                    tzone,
                )

                cam_date_utc = cam_date.astimezone(dt_util.UTC)

                LOGGER.debug(
                    "Device date/time: %s | System date/time: %s",
                    cam_date_utc,
                    system_date,
                )

                dt_diff = cam_date - system_date
                self._dt_diff_seconds = dt_diff.total_seconds()

                if self._dt_diff_seconds > 5:
                    LOGGER.warning(
                        (
                            "The date/time on %s (UTC) is '%s', "
                            "which is different from the system '%s', "
                            "this could lead to authentication issues"
                        ),
                        self.name,
                        cam_date_utc,
                        system_date,
                    )
                    if device_time.DateTimeType == "Manual":
                        # Set Date and Time ourselves if Date and Time is set manually in the camera.
                        await self.async_manually_set_date_and_time()
        except RequestError as err:
            LOGGER.warning(
                "Couldn't get device '%s' date/time. Error: %s", self.name, err
            )

    async def async_get_device_info(self) -> DeviceInfo:
        """Obtain information about this device."""
        device_mgmt = await self.device.create_devicemgmt_service()
        device_info = await device_mgmt.GetDeviceInformation()

        # Grab the last MAC address for backwards compatibility
        mac = None
        try:
            network_interfaces = await device_mgmt.GetNetworkInterfaces()
            for interface in network_interfaces:
                if interface.Enabled:
                    mac = interface.Info.HwAddress
        except Fault as fault:
            if "not implemented" not in fault.message:
                raise fault

            LOGGER.debug(
                "Couldn't get network interfaces from ONVIF device '%s'. Error: %s",
                self.name,
                fault,
            )

        return DeviceInfo(
            device_info.Manufacturer,
            device_info.Model,
            device_info.FirmwareVersion,
            device_info.SerialNumber,
            mac,
        )

    async def async_get_capabilities(self):
        """Obtain information about the available services on the device."""
        ptz = False
        with suppress(ONVIFError, Fault, RequestError):
            self.device.get_definition("ptz")
            ptz = True

        return Capabilities(ptz)

    async def async_get_profiles(self) -> list[Profile]:
        """Obtain PTZ nodes for this device."""
        media_service = await self.device.create_media_service()
        result = await media_service.GetProfiles()
        profiles: list[Profile] = []

        if not isinstance(result, list):
            return profiles

        for key, onvif_profile in enumerate(result):
            profile = Profile(
                key,
                onvif_profile.token,
                onvif_profile.Name,
            )
            LOGGER.debug("media profile %s", onvif_profile)

            # Configure PTZ options
            if self.capabilities.ptz and onvif_profile.PTZConfiguration:
                profile.ptz = PTZ(
                    onvif_profile.PTZConfiguration.DefaultContinuousPanTiltVelocitySpace
                    is not None,
                    onvif_profile.PTZConfiguration.DefaultRelativePanTiltTranslationSpace
                    is not None,
                    onvif_profile.PTZConfiguration.DefaultAbsolutePantTiltPositionSpace
                    is not None,
                )

            profiles.append(profile)

        return profiles

    async def async_perform_ptz_stop(
        self,
        profile: Profile,
        pan_tilt: bool = None,
        zoom: bool = None,
    ):
        """Perform a Stop PTZ action on the camera."""
        LOGGER.debug("Calling Stop PTZ: pan_tilt: %s zoom: %s", pan_tilt, zoom)
        if not profile.ptz:
            LOGGER.warning("Stop not supported on device '%s'", self.name)
            return

        ptz_service = await self.device.create_ptz_service()
        try:
            req = ptz_service.create_type("Stop")
            req.ProfileToken = profile.token
            if pan_tilt is not None:
                req.PanTilt = pan_tilt
            if zoom is not None:
                req.Zoom = zoom
            LOGGER.debug("Making Stop request %s", req)
            await ptz_service.Stop(req)
        except ONVIFError as err:
            if "Bad Request" in err.reason:
                LOGGER.warning("Device '%s' doesn't support PTZ", self.name)
            else:
                LOGGER.error("Error trying to perform PTZ action: %s", err)

    async def async_perform_ptz_absolute(
        self,
        profile: Profile,
        position,
        speed=None,
    ):
        """Perform a AbsoluteMove PTZ action on the camera."""
        ptz_service = await self.device.create_ptz_service()

        LOGGER.debug(
            "Calling AbsoluteMove PTZ: position: %s speed: %s", position, speed
        )
        try:
            req = ptz_service.create_type("AbsoluteMove")
            req.ProfileToken = profile.token
            if not profile.ptz or not profile.ptz.absolute:
                LOGGER.warning("AbsoluteMove not supported on device '%s'", self.name)
                return

            req.Position = position
            req.Speed = speed
            LOGGER.debug("Making AbsoluteMove request %s", req)
            await ptz_service.AbsoluteMove(req)
        except ONVIFError as err:
            if "Bad Request" in err.reason:
                LOGGER.warning("Device '%s' doesn't support PTZ", self.name)
            else:
                LOGGER.error("Error trying to perform PTZ action: %s", err)

    async def async_perform_ptz_continuous(
        self,
        profile: Profile,
        velocity,
    ):
        """Perform a ContinuousMove PTZ action on the camera."""
        ptz_service = await self.device.create_ptz_service()

        LOGGER.debug("Calling ContinousMove PTZ: velocity: %s", velocity)
        try:
            req = ptz_service.create_type("ContinuousMove")
            req.ProfileToken = profile.token
            if not profile.ptz or not profile.ptz.continuous:
                LOGGER.warning("ContinuousMove not supported on device '%s'", self.name)
                return

            req.Velocity = velocity
            LOGGER.debug("Making ContinuousMove request %s", req)
            await ptz_service.ContinuousMove(req)
        except ONVIFError as err:
            if "Bad Request" in err.reason:
                LOGGER.warning("Device '%s' doesn't support PTZ", self.name)
            else:
                LOGGER.error("Error trying to perform PTZ action: %s", err)

    async def async_perform_ptz_relative(
        self,
        profile: Profile,
        translation,
        speed=None,
    ):
        """Perform a RelativeMove PTZ action on the camera."""
        ptz_service = await self.device.create_ptz_service()

        LOGGER.debug(
            "Calling RelativeMove PTZ: translation: %s speed: %s", translation, speed
        )
        try:
            req = ptz_service.create_type("RelativeMove")
            req.ProfileToken = profile.token
            if not profile.ptz or not profile.ptz.relative:
                LOGGER.warning("RelativeMove not supported on device '%s'", self.name)
                return

            req.Translation = translation
            req.Speed = speed
            LOGGER.debug("Making RelativeMove request %s", req)
            await ptz_service.RelativeMove(req)
        except ONVIFError as err:
            if "Bad Request" in err.reason:
                LOGGER.warning("Device '%s' doesn't support PTZ", self.name)
            else:
                LOGGER.error("Error trying to perform PTZ action: %s", err)


def get_device(hass, host, port, username, password) -> ONVIFCamera:
    """Get ONVIFCamera instance."""
    return ONVIFCamera(
        host,
        port,
        username,
        password,
        f"{os.path.dirname(onvif.__file__)}/wsdl/",
        no_cache=True,
    )
