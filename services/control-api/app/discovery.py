from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Any


@dataclass(frozen=True)
class DiscoveredDevice:
    sn: str
    gateway_sn: str
    type: int | None = None
    sub_type: int | None = None
    index: str | None = None
    thing_version: str | None = None

    def as_public_dict(self) -> dict[str, object]:
        return {
            "sn": self.sn,
            "gateway_sn": self.gateway_sn,
            "type": self.type,
            "sub_type": self.sub_type,
            "index": self.index,
            "thing_version": self.thing_version,
        }


class DeviceRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._gateways: dict[str, dict[str, object]] = {}
        self._devices: dict[str, DiscoveredDevice] = {}

    def apply_update_topo(
        self,
        gateway_sn: str,
        data: dict[str, Any],
    ) -> dict[str, object]:
        gateway_public = {
            "sn": gateway_sn,
            "type": data.get("type"),
            "sub_type": data.get("sub_type"),
            "thing_version": data.get("thing_version"),
        }

        devices: list[DiscoveredDevice] = []
        for raw in data.get("sub_devices") or []:
            if not isinstance(raw, dict):
                continue
            sn = raw.get("sn")
            if not isinstance(sn, str) or not sn:
                continue
            devices.append(
                DiscoveredDevice(
                    sn=sn,
                    gateway_sn=gateway_sn,
                    type=raw.get("type") if isinstance(raw.get("type"), int) else None,
                    sub_type=(
                        raw.get("sub_type")
                        if isinstance(raw.get("sub_type"), int)
                        else None
                    ),
                    index=raw.get("index") if isinstance(raw.get("index"), str) else None,
                    thing_version=(
                        raw.get("thing_version")
                        if isinstance(raw.get("thing_version"), str)
                        else None
                    ),
                )
            )

        with self._lock:
            stale = [
                sn
                for sn, device in self._devices.items()
                if device.gateway_sn == gateway_sn
            ]
            for sn in stale:
                self._devices.pop(sn, None)

            for device in devices:
                self._devices[device.sn] = device

            self._gateways[gateway_sn] = {
                **gateway_public,
                "sub_device_sns": [device.sn for device in devices],
            }

        return {
            "gateway": gateway_public,
            "sub_devices": [device.as_public_dict() for device in devices],
        }

    def gateway_for(self, device_sn: str) -> str | None:
        with self._lock:
            device = self._devices.get(device_sn)
            return device.gateway_sn if device else None

    def snapshot(self) -> dict[str, object]:
        with self._lock:
            return {
                "gateways": list(self._gateways.values()),
                "devices": [
                    device.as_public_dict() for device in self._devices.values()
                ],
            }
