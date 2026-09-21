from app.dji_cloud import parse_dji_cloud_topic, source_for_topic
from app.mqtt_worker import decode_payload


def test_decode_json_payload() -> None:
    assert decode_payload(b'{"online":true}') == {"online": True}


def test_decode_text_payload() -> None:
    assert decode_payload(b"plain-text") == "plain-text"


def test_dji_topic_parsing() -> None:
    parsed = parse_dji_cloud_topic("thing/product/ABC123/events")
    assert parsed is not None
    assert parsed.device_sn == "ABC123"
    assert parsed.channel == "events"
    assert source_for_topic("thing/product/ABC123/osd") == "dji-cloud-api"


def test_generic_topic_remains_mqtt() -> None:
    assert parse_dji_cloud_topic("m4/fh2/test") is None
    assert source_for_topic("m4/fh2/test") == "mqtt"
