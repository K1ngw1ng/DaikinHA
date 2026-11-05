import asyncio
import os
import socket
import sys
import types

import aiohttp
from aiohttp import web

PKG_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "custom_components", "daikin_one_local"
)
# Load the package without running its __init__ (which needs Home Assistant).
pkg = types.ModuleType("dk")
pkg.__path__ = [PKG_DIR]
sys.modules["dk"] = pkg

from dk.api import (  # noqa: E402
    DaikinOneClient,
    DaikinOneConnectionError,
    DaikinOneRequestError,
)

STATE = {
    "name": "Office", "mode": 0, "availableModes": [0, 1, 2, 3], "state": 5,
    "fan": 0, "fanState": 0, "tempUnits": 0, "spaceTemp": 25,
    "heatSetpoint": 25, "coolSetpoint": 27,
    "coolSetpointMax": 32.2, "coolSetpointMin": 10,
    "heatSetpointMax": 32.2, "heatSetpointMin": 10,
    "setpointDelta": 2, "spaceHum": 50,
}
SEEN = {"content_type": None}


async def root(_):
    return web.json_response(
        {"api_ver": 1, "type": "residential", "model": "oneplus",
         "brand": "daikin", "firmware": "1.0.0"}
    )


async def info(_):
    return web.json_response(STATE)


async def control(request):
    SEEN["content_type"] = request.content_type
    form = await request.post()
    new = dict(STATE)
    for key, cast in (("mode", int), ("fan", int), ("heatSetpoint", float), ("coolSetpoint", float)):
        if key in form:
            new[key] = cast(form[key])
    for key, prefix in (("heatSetpoint", "heat"), ("coolSetpoint", "cool")):
        lo, hi = new[prefix + "SetpointMin"], new[prefix + "SetpointMax"]
        if not lo <= new[key] <= hi:
            return web.json_response({"error": True, "reason": f"{key} out of range"})
    if new["mode"] == 3 and new["coolSetpoint"] - new["heatSetpoint"] < new["setpointDelta"]:
        return web.json_response({"error": True, "reason": "setpoints too close"})
    STATE.update(new)
    return web.json_response({"error": False})


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


async def main():
    app = web.Application()
    app.router.add_get("/", root)
    app.router.add_get("/query/info", info)
    app.router.add_post("/control", control)
    runner = web.AppRunner(app)
    await runner.setup()
    port = free_port()
    await web.TCPSite(runner, "127.0.0.1", port).start()

    async with aiohttp.ClientSession() as session:
        client = DaikinOneClient(session, "127.0.0.1", port)

        assert (await client.get_api_info())["model"] == "oneplus"
        assert (await client.get_status())["spaceTemp"] == 25

        await client.set_control(mode=3, heatSetpoint=20.5, coolSetpoint=24)
        s = await client.get_status()
        assert (s["mode"], s["heatSetpoint"], s["coolSetpoint"]) == (3, 20.5, 24.0), s
        assert SEEN["content_type"] == "application/x-www-form-urlencoded", SEEN

        await client.set_control(fan=1)
        s = await client.get_status()
        assert (s["mode"], s["fan"], s["heatSetpoint"]) == (3, 1, 20.5), s

        for bad in ({"heatSetpoint": 99}, {"heatSetpoint": 23.5}):
            try:
                await client.set_control(**bad)
            except DaikinOneRequestError as err:
                print("rejected as expected:", bad, "->", err)
            else:
                raise AssertionError(f"{bad} should have been rejected")

        dead = DaikinOneClient(session, "127.0.0.1", free_port())
        try:
            await dead.get_status()
        except DaikinOneConnectionError as err:
            print("connection error as expected:", type(err).__name__)
        else:
            raise AssertionError("dead port should raise")

    await runner.cleanup()
    print("ALL CLIENT CHECKS PASSED")


asyncio.run(main())
