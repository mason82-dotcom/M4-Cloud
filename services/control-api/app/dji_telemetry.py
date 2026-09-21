from __future__ import annotations

import re
from typing import Any


_CAMERA_FIELDS = (
    "remain_photo_num",
    "remain_record_duration",
    "record_time",
    "camera_mode",
    "photo_state",
    "screen_split_enable",
    "recording_state",
    "zoom_factor",
    "ir_zoom_factor",
    "liveview_world_region",
    "photo_storage_settings",
    "video_storage_settings",
    "wide_exposure_mode",
    "wide_iso",
    "wide_shutter_speed",
    "wide_exposure_value",
    "zoom_exposure_mode",
    "zoom_iso",
    "zoom_shutter_speed",
    "zoom_exposure_value",
    "zoom_focus_mode",
    "zoom_focus_value",
    "zoom_max_focus_value",
    "zoom_min_focus_value",
    "zoom_calibrate_farthest_focus_value",
    "zoom_calibrate_nearest_focus_value",
    "zoom_focus_state",
    "ir_metering_mode",
    "ir_metering_point",
    "ir_metering_area",
)
_GIMBAL_FIELDS = ("gimbal_pitch", "gimbal_roll", "gimbal_yaw")
_PAYLOAD_INDEX_RE = re.compile(r"^\d+-\d+-\d+$")


def normalize_camera_gimbal_message(
    topic: str | None,
    payload: Any,
) -> list[dict[str, Any]]:
    """Normalize one persisted DJI MQTT message into payload-scoped telemetry.

    M4 only extracts read-only state. Missing payload associations remain
    unscoped instead of being inferred from aircraft or camera model names.
    """
    device_sn = _device_sn_from_topic(topic)
    if device_sn is None or not isinstance(payload, dict):
        return []

    data = payload.get("data")
    if not isinstance(data, dict):
        return []

    timestamp_ms = _int_or_none(payload.get("timestamp"))
    snapshots: dict[str, dict[str, Any]] = {}

    cameras = data.get("cameras")
    if isinstance(cameras, list):
        for camera in cameras:
            if not isinstance(camera, dict):
                continue
            payload_index = _optional_text(camera.get("payload_index"))
            if payload_index is None:
                continue

            item = _snapshot(
                snapshots,
                device_sn=device_sn,
                payload_index=payload_index,
                topic=topic,
                timestamp_ms=timestamp_ms,
            )
            item["camera"].update(
                {field: camera[field] for field in _CAMERA_FIELDS if field in camera}
            )

    for key, value in data.items():
        if not isinstance(value, dict):
            continue
        if not any(field in value for field in _GIMBAL_FIELDS):
            continue

        payload_index = _optional_text(value.get("payload_index"))
        if payload_index is None and _PAYLOAD_INDEX_RE.fullmatch(str(key)):
            payload_index = str(key)

        item = _snapshot(
            snapshots,
            device_sn=device_sn,
            payload_index=payload_index,
            topic=topic,
            timestamp_ms=timestamp_ms,
        )
        item["gimbal"].update(
            {
                field: number
                for field in _GIMBAL_FIELDS
                if (number := _float_or_none(value.get(field))) is not None
            }
        )
        if "zoom_factor" in value and "zoom_factor" not in item["camera"]:
            item["camera"]["zoom_factor"] = value["zoom_factor"]

    if any(field in data for field in _GIMBAL_FIELDS):
        payload_index = _optional_text(data.get("payload_index"))
        item = _snapshot(
            snapshots,
            device_sn=device_sn,
            payload_index=payload_index,
            topic=topic,
            timestamp_ms=timestamp_ms,
        )
        item["gimbal"].update(
            {
                field: number
                for field in _GIMBAL_FIELDS
                if (number := _float_or_none(data.get(field))) is not None
            }
        )

    return [
        item
        for item in snapshots.values()
        if item["camera"] or item["gimbal"]
    ]


def latest_camera_gimbal_telemetry(
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Merge newest-first persisted events into latest payload snapshots."""
    latest: dict[tuple[str, str | None], dict[str, Any]] = {}

    for event in events:
        if event.get("source") != "mqtt":
            continue

        observations = normalize_camera_gimbal_message(
            _optional_text(event.get("topic")),
            event.get("payload"),
        )
        for observation in observations:
            key = (observation["device_sn"], observation["payload_index"])
            current = latest.get(key)
            if current is None:
                latest[key] = {
                    **observation,
                    "camera": dict(observation["camera"]),
                    "gimbal": dict(observation["gimbal"]),
                }
                continue

            # recent_events() is newest-first. Older messages only fill fields
            # that were absent from the newer snapshot.
            for field, value in observation["camera"].items():
                current["camera"].setdefault(field, value)
            for field, value in observation["gimbal"].items():
                current["gimbal"].setdefault(field, value)

    return list(latest.values())


def _snapshot(
    snapshots: dict[str, dict[str, Any]],
    *,
    device_sn: str,
    payload_index: str | None,
    topic: str | None,
    timestamp_ms: int | None,
) -> dict[str, Any]:
    key = payload_index or "__device__"
    item = snapshots.get(key)
    if item is None:
        item = {
            "device_sn": device_sn,
            "payload_index": payload_index,
            "camera": {},
            "gimbal": {},
            "source_topic": topic,
            "timestamp_ms": timestamp_ms,
        }
        snapshots[key] = item
    return item


def _device_sn_from_topic(topic: str | None) -> str | None:
    if not topic:
        return None

    parts = topic.split("/")
    if len(parts) < 4 or parts[0:2] != ["thing", "product"]:
        return None
    if parts[3] not in {"osd", "state", "drc"}:
        return None
    return _optional_text(parts[2])


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _float_or_none(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
