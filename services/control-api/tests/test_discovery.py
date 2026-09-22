from app.discovery import DeviceRegistry


def test_update_topo_registers_gateway_and_subdevice_without_secrets() -> None:
    registry = DeviceRegistry()

    public = registry.apply_update_topo(
        "RC-PRO-001",
        {
            "type": 119,
            "sub_type": 0,
            "thing_version": "1.1.2",
            "device_secret": "gateway-secret",
            "nonce": "gateway-nonce",
            "sub_devices": [
                {
                    "sn": "M3E-001",
                    "type": 60,
                    "sub_type": 0,
                    "index": "A",
                    "thing_version": "1.1.2",
                    "device_secret": "aircraft-secret",
                    "nonce": "aircraft-nonce",
                }
            ],
        },
    )

    assert registry.gateway_for("M3E-001") == "RC-PRO-001"
    assert public["gateway"]["sn"] == "RC-PRO-001"
    assert public["sub_devices"][0]["sn"] == "M3E-001"
    assert "device_secret" not in str(public)
    assert "nonce" not in str(public)


def test_empty_subdevice_list_marks_gateway_without_aircraft() -> None:
    registry = DeviceRegistry()
    registry.apply_update_topo(
        "RC-PRO-001",
        {"type": 119, "sub_devices": [{"sn": "M3E-001", "type": 60}]},
    )

    registry.apply_update_topo(
        "RC-PRO-001",
        {"type": 119, "sub_devices": []},
    )

    assert registry.gateway_for("M3E-001") is None
    snapshot = registry.snapshot()
    assert snapshot["gateways"][0]["sub_device_sns"] == []
