from __future__ import annotations

from dataclasses import dataclass


THING_UPLINK_CHANNELS = {
    "osd",
    "state",
    "services_reply",
    "events",
    "requests",
    "property/set_reply",
    "drc/up",
}


@dataclass(frozen=True)
class DJICloudTopic:
    namespace: str
    device_sn: str
    channel: str


def parse_dji_cloud_topic(topic: str) -> DJICloudTopic | None:
    parts = topic.split("/")
    if len(parts) < 4 or parts[1] != "product":
        return None

    namespace = parts[0]
    device_sn = parts[2]
    channel = "/".join(parts[3:])

    if namespace == "thing" and channel in THING_UPLINK_CHANNELS:
        return DJICloudTopic(namespace, device_sn, channel)

    if namespace == "sys" and channel == "status":
        return DJICloudTopic(namespace, device_sn, channel)

    return None


def source_for_topic(topic: str) -> str:
    return "dji-cloud-api" if parse_dji_cloud_topic(topic) else "mqtt"
