"""Client tests."""
import json
import os

import pytest
from unittest.mock import AsyncMock, Mock, patch

from aiohttp.web import HTTPForbidden
from src.pymelcloud import DEVICE_TYPE_ATA

from src.pymelcloud.const import ACCESS_LEVEL
from src.pymelcloud.ata_device import (AtaDevice)


def _build_device(device_conf_name: str, device_state_name: str) -> AtaDevice:
    test_dir = os.path.join(os.path.dirname(__file__), "samples")
    with open(os.path.join(test_dir, device_conf_name), "r") as json_file:
        device_conf = json.load(json_file)

    with open(os.path.join(test_dir, device_state_name), "r") as json_file:
        device_state = json.load(json_file)

    with patch("src.pymelcloud.client.Client") as _client:
        _client.update_confs = AsyncMock()
        _client.device_confs.__iter__ = Mock(return_value=[device_conf].__iter__())
        _client.fetch_device_units = AsyncMock(return_value=[])
        _client.fetch_device_state = AsyncMock(return_value=device_state)
        _client.fetch_energy_report = AsyncMock(return_value=None)
        client = _client

    return AtaDevice(device_conf, client)


@pytest.mark.asyncio
async def test_ata_guest():
    device = _build_device("ata_guest_listdevices.json", "ata_guest_get.json")
    assert device.device_type == DEVICE_TYPE_ATA
    assert device.access_level == ACCESS_LEVEL["GUEST"]

    request_info = Mock()
    request_info.real_url = "https://example.test/Device/ListDeviceUnits"

    device._client.fetch_device_units = AsyncMock(side_effect=HTTPForbidden)

    with pytest.raises(HTTPForbidden) as exc:
        await device.update()
    assert exc.value.status == 403


@pytest.mark.asyncio
async def test_ata_energy_report_403():
    device = _build_device("ata_listdevice.json", "ata_get.json")
    device._client.fetch_device_state = AsyncMock(return_value={})
    device._client.fetch_device_units = AsyncMock(return_value=None)

    request_info = Mock()
    request_info.real_url = "https://example.test/EnergyCost/Report"

    device._client.fetch_energy_report = AsyncMock(side_effect=HTTPForbidden)

    with pytest.raises(HTTPForbidden) as exc:
        await device.update()
    assert exc.value.status == 403


@pytest.mark.asyncio
async def test_ata_device_units_403():
    device = _build_device("ata_listdevice.json", "ata_get.json")
    assert device.access_level == ACCESS_LEVEL["OWNER"]
    device._client.fetch_device_state = AsyncMock(return_value={})

    request_info = Mock()
    request_info.real_url = "https://example.test/Device/ListDeviceUnits"

    device._client.fetch_device_units = AsyncMock(side_effect=HTTPForbidden)

    with pytest.raises(HTTPForbidden) as exc:
        await device.update()
    assert exc.value.status == 403
