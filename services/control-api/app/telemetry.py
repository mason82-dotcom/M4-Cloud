from __future__ import annotations

import asyncio
import json
import time
from typing import Any

import paho.mqtt.client as mqtt

from app.config import Settings
from app.discovery import DeviceRegistry

DJI_TELEMETRY_TOPICS = (
    "thing/product/+/osd",
    "thing/product/+/state",
    "thing/product/+/events",
    "sys/product/+/status",
    # RC-Pro device documentation also shows thing/product/{gateway_sn}/status
    # for update_topo. Support both read-only forms.
    "thing/product/+/status",
)


def normalize_dji_telemetry(topic: str, payload: bytes) -> dict[str, object] | None:
    parts = topic.split("/")
    if len(parts) < 4 or parts[1] != "product":
        return None

    namespace = parts[0]
    device_sn = parts[2]
    suffix = "/".join(parts[3:])

    if namespace == "thing" and suffix in {"osd", "state", "events"}:
        kind = suffix
    elif namespace in {"sys", "thing"} and suffix == "status":
        kind = "status"
    else:
        return None

    text = payload.decode("utf-8", errors="replace")
    try:
        decoded: Any = json.loads(text)
    except json.JSONDecodeError:
        decoded = {"raw": text}

    gateway_sn = None
    method = None
    if isinstance(decoded, dict):
        gateway_sn = decoded.get("gateway")
        method = decoded.get("method")

    return {
        "type": "dji.telemetry",
        "source": "dji_cloud_api",
        "topic": topic,
        "kind": kind,
        "device_sn": device_sn,
        "gateway_sn": gateway_sn,
        "method": method,
        "received_at_ms": int(time.time() * 1000),
        "payload": decoded,
    }


class TelemetryHub:
    def __init__(
        self,
        settings: Settings,
        *,
        queue_size: int = 128,
        registry: DeviceRegistry | None = None,
    ) -> None:
        self.settings = settings
        self.queue_size = queue_size
        self.registry = registry or DeviceRegistry()
        self._client: mqtt.Client | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queues: set[asyncio.Queue[dict[str, object]]] = set()
        self._connected = False
        self._last_message_at_ms: int | None = None
        self._start_lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._start_lock:
            if self._client is not None:
                return

            self._loop = asyncio.get_running_loop()
            client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2,
                client_id="m4-telemetry",
                protocol=mqtt.MQTTv311,
            )
            client.username_pw_set(
                self.settings.mqtt_service_username,
                self.settings.mqtt_service_password,
            )
            client.on_connect = self._on_connect
            client.on_disconnect = self._on_disconnect
            client.on_message = self._on_message
            client.connect_async(
                self.settings.mqtt_host,
                self.settings.mqtt_port,
                keepalive=15,
            )
            client.loop_start()
            self._client = client

    async def stop(self) -> None:
        async with self._start_lock:
            client = self._client
            self._client = None
            self._connected = False
            if client is None:
                return
            try:
                client.disconnect()
            finally:
                client.loop_stop()

    def subscribe(self) -> asyncio.Queue[dict[str, object]]:
        queue: asyncio.Queue[dict[str, object]] = asyncio.Queue(
            maxsize=self.queue_size
        )
        self._queues.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, object]]) -> None:
        self._queues.discard(queue)

    @property
    def status(self) -> dict[str, object]:
        return {
            "started": self._client is not None,
            "mqtt_connected": self._connected,
            "subscribers": len(self._queues),
            "last_message_at_ms": self._last_message_at_ms,
            "topics": list(DJI_TELEMETRY_TOPICS),
            "read_only": True,
            "drc_enabled": False,
        }

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Any,
        reason_code: Any,
        properties: Any = None,
    ) -> None:
        self._connected = reason_code == 0
        if not self._connected:
            return
        for topic in DJI_TELEMETRY_TOPICS:
            client.subscribe(topic, qos=0)

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        disconnect_flags: Any,
        reason_code: Any,
        properties: Any = None,
    ) -> None:
        self._connected = False

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: Any,
        message: mqtt.MQTTMessage,
    ) -> None:
        event = normalize_dji_telemetry(message.topic, message.payload)
        if event is None:
            return

        payload = event.get("payload")
        if (
            event.get("kind") == "status"
            and event.get("method") == "update_topo"
            and isinstance(payload, dict)
            and isinstance(payload.get("data"), dict)
        ):
            public_topology = self.registry.apply_update_topo(
                str(event["device_sn"]),
                payload["data"],
            )
            event = {
                **event,
                "type": "dji.topology",
                "payload": {
                    "method": "update_topo",
                    "data": public_topology,
                },
            }

        self._last_message_at_ms = int(event["received_at_ms"])
        if self._loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._fanout(event), self._loop)

    async def _fanout(self, event: dict[str, object]) -> None:
        for queue in tuple(self._queues):
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass
