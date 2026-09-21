from app.mqtt_worker import decode_payload


def test_decode_json_payload() -> None:
    assert decode_payload(b'{"online":true}') == {"online": True}


def test_decode_text_payload() -> None:
    assert decode_payload(b"plain-text") == "plain-text"
