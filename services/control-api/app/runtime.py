from __future__ import annotations

import socket
import threading
from uuid import uuid4

import paho.mqtt.client as mqtt
import psycopg

from app.config import Settings


def database_reachable(settings: Settings, timeout_seconds: int = 2) -> bool:
    try:
        with psycopg.connect(
            settings.database_url,
            connect_timeout=timeout_seconds,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone() == (1,)
    except psycopg.Error:
        return False


def mqtt_reachable(settings: Settings, timeout_seconds: float = 2.0) -> bool:
    connected = threading.Event()
    state = {"ok": False}

    client = mqtt.Client(
        mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"m4-ready-{uuid4().hex[:12]}",
        protocol=mqtt.MQTTv311,
    )
    client.username_pw_set(
        settings.mqtt_service_username,
        settings.mqtt_service_password,
    )

    def on_connect(client, userdata, flags, reason_code, properties=None):
        state["ok"] = reason_code == 0
        connected.set()

    client.on_connect = on_connect

    previous_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout_seconds)
        client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=5)
        client.loop_start()
        connected.wait(timeout_seconds)
        return state["ok"]
    except (OSError, RuntimeError, ValueError):
        return False
    finally:
        socket.setdefaulttimeout(previous_timeout)
        try:
            client.loop_stop()
            client.disconnect()
        except Exception:
            pass
