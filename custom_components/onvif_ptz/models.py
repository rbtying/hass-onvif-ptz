"""ONVIF models."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DeviceInfo:
    """Represent device information."""

    manufacturer: str | None = None
    model: str | None = None
    fw_version: str | None = None
    serial_number: str | None = None
    mac: str | None = None


@dataclass
class PTZ:
    """Represents PTZ configuration on a profile."""

    continuous: bool
    relative: bool
    absolute: bool
    presets: list[str] | None = None


@dataclass
class Profile:
    """Represent a ONVIF Profile."""

    index: int
    token: str
    name: str
    ptz: PTZ | None = None


@dataclass
class Capabilities:
    """Represents Service capabilities."""

    ptz: bool = False
