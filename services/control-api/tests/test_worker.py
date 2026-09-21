from app.dji_cloud import parse_dji_cloud_topic, source_for_topic
from app.mqtt_worker import decode_payload


def test_decode_json_payload() -> None:
    assert decode_payload(b'{"online":true}') == {"online": True}


def test_decode_text_payload() -> None:
    assert decode_payload(b"plain-text") == "plain-text"


def test_parse_dji_cloud_thing_topic() -> None:
    parsed = parse_dji_cloud_topic("thing/product/ABC123/events")

    assert parsed is not None
    assert parsed.namespace == "thing"
    assert parsed.device_sn == "ABC123"
    assert parsed.channel == "events"


def test_parse_dji_cloud_nested_channel() -> None:
    parsed = parse_dji_cloud_topic("thing/product/ABC123/property/set_reply")

    assert parsed is not None
    assert parsed.channel == "property/set_reply"


def test_parse_dji_cloud_sys_status_topic() -> None:
    parsed = parse_dji_cloud_topic("sys/product/RC123/status")

    assert parsed is not None
    assert parsed.device_sn == "RC123"
    assert parsed.channel == "status"


def test_non_dji_topic_remains_generic_mqtt() -> None:
    assert parse_dji_cloud_topic("m4/fh2/test") is None
    assert source_for_topic("m4/fh2/test") == "mqtt"


def test_dji_topic_uses_cloud_api_source() -> None:
    assert source_for_topic("thing/product/ABC123/osd") == "dji-cloud-api"
