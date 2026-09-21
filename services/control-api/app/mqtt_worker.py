from __future__ import annotations

import json
import signal
import threading
from typing import Any

import paho.mqtt.client as mqtt

from .config import Settings
from .db import ensure_schema, store_event, touch_heartbeat

STOP = threading.Event()


def decode_payload(payload: bytes) -> Any:
    text = payload.decode("utf-8", errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def on_connect(
    client: mqtt.Client,
    userdata: Any,
    flags: Any,
    reason_code: Any,
    properties: Any = None,
) -> None:
    settings = Settings.from_env()
    if reason_code != 0:
        return
    for topic in settings.dji_mqtt_topics:
        client.subscribe(topic, qos=1)


def on_message(
    client: mqtt.Client,
    userdata: Any,
    message: mqtt.MQTTMessage,
) -> None:
    store_event(
        source="mqtt",
        topic=message.topic,
        payload=decode_payload(message.payload),
    )


def stop_handler(signum: int, frame: Any) -> None:
    STOP.set()


def main() -> None:
    settings = Settings.from_env()
    ensure_schema()

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id="m4-integration-worker",
    )
    client.on_connect = on_connect
    client.on_message = on_message

    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)

    while not STOP.is_set():
        try:
            client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=30)
            client.loop_start()
            touch_heartbeat("integration-worker")
            while not STOP.wait(10):
                touch_heartbeat("integration-worker")
            client.loop_stop()
            client.disconnect()
        except (OSError, RuntimeError):
            if STOP.wait(5):
                break


if __name__ == "__main__":
    main()
