# ONVIF PTZ

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]

[![hacs][hacsbadge]][hacs]

_Integration to integrate with ONVIF cameras that support pan/tilt/zoom controls_

This integration is intended to extend the existing core ONVIF integration with
the ability to correctly call various camera's PTZ commands.

**This integration will set up the following platforms.**

Platform | Description
-- | --
`button` | Each camera profile which supports PTZ will create a fake button entity which supports PTZ commands.

Services | Description
-- | --
ptz_relative | ONVIF RelativeMove command, moves the camera relative to the current position
ptz_absolute | ONVIF AbsoluteMove command, moves the camera to a specified position
ptz_continuous | ONVIF ContinuousMove command, moves the camera at a specified velocity
ptz_stop | Stops camera movement

## Installation

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
1. If you do not have a `custom_components` directory (folder) there, you need to create it.
1. In the `custom_components` directory (folder) create a new folder called `onvif_ptz`.
1. Download _all_ the files from the `custom_components/onvif_ptz/` directory (folder) in this repository.
1. Place the files you downloaded in the new directory (folder) you created.
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "ONVIF PTZ"

## Configuration is done in the UI

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[onvif_ptz]: https://github.com/rbtying/hass-onvif-ptz
[commits-shield]: https://img.shields.io/github/commit-activity/y/rbtying/hass-onvif-ptz.svg?style=for-the-badge
[commits]: https://github.com/rbtying/hass-onvif-ptz/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/rbtying/hass-onvif-ptz.svg?style=for-the-badge
[releases]: https://github.com/rbtying/hass-onvif-ptz/releases
