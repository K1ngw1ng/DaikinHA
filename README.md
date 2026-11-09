# DaikinHA

A Home Assistant custom integration for Daikin One+, Daikin One Touch and Amana smart thermostats. It talks to the thermostat's Local API over your LAN.

It exists because the official Daikin integration and the Daikin HACS integrations target the older WiFi adapters (`/aircon/*` endpoints). The One+ thermostat exposes a different REST API (`/query/info`, `/control`), which this integration uses.

API reference: https://daikinac.com/dakin-one-local-api

> [!IMPORTANT]
> This project is an independent, open-source community integration and is not affiliated with, authorized, maintained, or endorsed by Daikin Comfort Technologies or any of its affiliates. Use this integration at your own risk. 

## Features

**Climate entity**
- HVAC modes: off, heat, cool, heat/cool (range), plus fan only and dry where the equipment supports them. Only modes the thermostat lists as available are shown.
- Heat and cool setpoints, with the min and max the thermostat reports.
- Fan setting: `off`, `on` (always on) and `schedule`.
- Current temperature, humidity, and a heating, cooling, fan or idle action.

**Sensors**
- Room temperature
- Room humidity
- Equipment state (cooling, overcooling, heating, fan, idle, waiting to cool, waiting to heat, aux heat)

## Requirements

- Home Assistant 2024.11 or newer.
- A thermostat on the latest firmware with Local API switched on.

Local API is off by default. Turn it on at the thermostat: Settings, Wi-Fi, Local API, ON. It cannot be enabled from the app.

## Install

**Manual** (works for Home Assistant OS, Container and Core):

1. Copy `custom_components/daikin_one_local` into your Home Assistant config folder, so you end up with `config/custom_components/daikin_one_local/manifest.json`. For a Docker install, the config folder is the host directory mapped to `/config`.
2. Restart Home Assistant.

**HACS**:

1. In HACS, open the menu, choose Custom repositories, and add `https://github.com/K1ngw1ng/DaikinHA` with type Integration.
2. Install Daikin One Local and restart Home Assistant.

## Set up

Go to Settings, Devices & Services, Add Integration, and search for Daikin One Local. Enter:

- **Host**: the thermostat's IP address. Give it a DHCP reservation on your router.
- **Port**: `80` on the unit this was tested against. Daikin's documentation also mentions `8081`, so try that if 80 fails.

To check that the thermostat is reachable before adding it:

```
curl http://THERMOSTAT_IP/query/info
```

From a Docker host, run the same command inside the container with `docker exec <container> curl ...` to confirm Home Assistant can reach it. On Windows PowerShell, use `curl.exe`.

## Limits

- The API reports Celsius only. Home Assistant converts to your unit system.
- Emergency heat (mode 4) is not exposed, since Home Assistant has no matching mode.
- Fan only and dry modes work only on VRV (P1P2) and single or multi split (S21) equipment.
- The API exposes room temperature, humidity, equipment state and fan state. It has no outdoor temperature, runtime, energy or filter data.
- The thermostat is polled every 30 seconds. The documentation gives no rate limit.
- The device is identified by `host:port`, because the REST API returns no MAC address. If the IP changes, Home Assistant sees a new device.
- Dry mode uses the cool setpoint. The documentation does not say which setpoint applies.
- Zones without a thermostat are not supported by Local API v1.0. Goodman Smart Thermostats and Daikin One Lite are not supported.

## Development

`tests/test_client.py` runs the API client against a mock thermostat

```
pip install aiohttp
python tests/test_client.py
```
