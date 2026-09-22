import json

from app.telemetry import normalize_dji_telemetry


def test_normalize_osd_message() -> None:
    event = normalize_dji_telemetry(
        "thing/product/AIRCRAFT123/osd",
        json.dumps(
            {
                "gateway": "RC123",
                "data": {
                    "latitude": 49.1,
                    "longitude": 8.5,
                    "height": 32.4,
                },
            }
        ).encode(),
    )

    assert event is not None
    assert event["kind"] == "osd"
    assert event["device_sn"] == "AIRCRAFT123"
    assert event["gateway_sn"] == "RC123"
    assert event["source"] == "dji_cloud_api"


def test_normalize_state_message() -> None:
    event = normalize_dji_telemetry(
        "thing/product/RC123/state",
        b'{"gateway":"RC123","data":{"is_cloud_control_auth":false}}',
    )

    assert event is not None
    assert event["kind"] == "state"
    assert event["device_sn"] == "RC123"


def test_normalize_status_message() -> None:
    event = normalize_dji_telemetry(
        "sys/product/RC123/status",
        b'{"method":"update_topo","data":{}}',
    )

    assert event is not None
    assert event["kind"] == "status"
    assert event["method"] == "update_topo"


def test_ignore_non_telemetry_topic() -> None:
    assert (
        normalize_dji_telemetry(
            "thing/product/RC123/services_reply",
            b'{"data":{"result":0}}',
        )
        is None
    )


def test_invalid_json_is_preserved_as_raw_text() -> None:
    event = normalize_dji_telemetry(
        "thing/product/AIRCRAFT123/osd",
        b"not-json",
    )

    assert event is not None
    assert event["payload"] == {"raw": "not-json"}
