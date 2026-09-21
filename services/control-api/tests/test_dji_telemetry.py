from app.dji_telemetry import (
    latest_camera_gimbal_telemetry,
    normalize_camera_gimbal_message,
)


def test_normalizes_camera_and_gimbal_from_dji_osd() -> None:
    payload = {
        "timestamp": 1790013000123,
        "data": {
            "cameras": [
                {
                    "payload_index": "67-0-0",
                    "camera_mode": 0,
                    "recording_state": 1,
                    "zoom_factor": 4.0,
                    "wide_iso": 3,
                    "wide_shutter_speed": 12,
                }
            ],
            "67-0-0": {
                "payload_index": "67-0-0",
                "gimbal_pitch": -45.2,
                "gimbal_roll": 0.1,
                "gimbal_yaw": 12.3,
                "zoom_factor": 4.0,
            },
        },
    }

    telemetry = normalize_camera_gimbal_message(
        "thing/product/1581ABC/osd",
        payload,
    )

    assert telemetry == [
        {
            "device_sn": "1581ABC",
            "payload_index": "67-0-0",
            "camera": {
                "camera_mode": 0,
                "recording_state": 1,
                "zoom_factor": 4.0,
                "wide_iso": 3,
                "wide_shutter_speed": 12,
            },
            "gimbal": {
                "gimbal_pitch": -45.2,
                "gimbal_roll": 0.1,
                "gimbal_yaw": 12.3,
            },
            "source_topic": "thing/product/1581ABC/osd",
            "timestamp_ms": 1790013000123,
        }
    ]


def test_uses_payload_key_for_gimbal_struct_without_payload_index() -> None:
    payload = {
        "data": {
            "67-0-0": {
                "gimbal_pitch": -90,
                "gimbal_yaw": 5.5,
            }
        }
    }

    telemetry = normalize_camera_gimbal_message(
        "thing/product/1581ABC/state",
        payload,
    )

    assert telemetry[0]["payload_index"] == "67-0-0"
    assert telemetry[0]["gimbal"] == {
        "gimbal_pitch": -90.0,
        "gimbal_yaw": 5.5,
    }


def test_latest_telemetry_keeps_newest_values_and_fills_missing_fields() -> None:
    events = [
        {
            "source": "mqtt",
            "topic": "thing/product/1581ABC/state",
            "payload": {
                "timestamp": 2000,
                "data": {
                    "cameras": [
                        {
                            "payload_index": "67-0-0",
                            "zoom_factor": 8.0,
                        }
                    ],
                    "67-0-0": {
                        "gimbal_pitch": -30.0,
                    },
                },
            },
        },
        {
            "source": "mqtt",
            "topic": "thing/product/1581ABC/osd",
            "payload": {
                "timestamp": 1000,
                "data": {
                    "cameras": [
                        {
                            "payload_index": "67-0-0",
                            "camera_mode": 1,
                            "zoom_factor": 2.0,
                        }
                    ],
                    "67-0-0": {
                        "gimbal_pitch": -70.0,
                        "gimbal_roll": 0.2,
                        "gimbal_yaw": 15.0,
                    },
                },
            },
        },
        {
            "source": "fh2",
            "topic": "thing/product/1581ABC/osd",
            "payload": {
                "data": {
                    "cameras": [
                        {
                            "payload_index": "67-0-0",
                            "zoom_factor": 99.0,
                        }
                    ]
                }
            },
        },
    ]

    telemetry = latest_camera_gimbal_telemetry(events)

    assert len(telemetry) == 1
    assert telemetry[0]["camera"]["zoom_factor"] == 8.0
    assert telemetry[0]["camera"]["camera_mode"] == 1
    assert telemetry[0]["gimbal"]["gimbal_pitch"] == -30.0
    assert telemetry[0]["gimbal"]["gimbal_roll"] == 0.2
    assert telemetry[0]["gimbal"]["gimbal_yaw"] == 15.0
    assert telemetry[0]["timestamp_ms"] == 2000


def test_unscoped_gimbal_values_are_not_assigned_to_a_payload() -> None:
    payload = {
        "timestamp": 3000,
        "data": {
            "gimbal_pitch": -20.0,
            "gimbal_roll": 0.0,
            "gimbal_yaw": 3.0,
        },
    }

    telemetry = normalize_camera_gimbal_message(
        "thing/product/1581ABC/drc/up",
        payload,
    )

    assert telemetry[0]["payload_index"] is None
    assert telemetry[0]["gimbal"]["gimbal_pitch"] == -20.0


def test_ignores_unrelated_topics_and_invalid_payloads() -> None:
    assert normalize_camera_gimbal_message(
        "m4/fh2/verify",
        {"data": {"gimbal_pitch": -10}},
    ) == []
    assert normalize_camera_gimbal_message(
        "thing/product/1581ABC/osd",
        "not-json-object",
    ) == []
