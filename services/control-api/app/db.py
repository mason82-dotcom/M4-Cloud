from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row

from .config import Settings


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    settings = Settings.from_env()
    # Use keyword parameters so passwords with spaces or libpq special characters are handled safely.
    with psycopg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
        row_factory=dict_row,
    ) as conn:
        yield conn


def ensure_schema() -> None:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS integration_events (
                    id BIGSERIAL PRIMARY KEY,
                    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    source TEXT NOT NULL,
                    topic TEXT,
                    payload JSONB NOT NULL
                )
                """
            )
            cur.execute(
                """
                CREATE INDEX IF NOT EXISTS integration_events_received_at_idx
                ON integration_events (received_at DESC)
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS service_heartbeats (
                    service TEXT PRIMARY KEY,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        conn.commit()


def database_reachable() -> bool:
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone() is not None
    except psycopg.Error:
        return False


def store_event(source: str, topic: str | None, payload: Any) -> int:
    encoded = json.dumps(payload)
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO integration_events (source, topic, payload)
                VALUES (%s, %s, %s::jsonb)
                RETURNING id
                """,
                (source, topic, encoded),
            )
            row = cur.fetchone()
        conn.commit()
    return int(row["id"])


def recent_events(limit: int) -> list[dict[str, Any]]:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, received_at, source, topic, payload
                FROM integration_events
                ORDER BY id DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
    return [dict(row) for row in rows]


def touch_heartbeat(service: str) -> None:
    with connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO service_heartbeats (service, updated_at)
                VALUES (%s, NOW())
                ON CONFLICT (service)
                DO UPDATE SET updated_at = EXCLUDED.updated_at
                """,
                (service,),
            )
        conn.commit()


def get_worker_heartbeat() -> dict[str, Any] | None:
    try:
        with connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT service, updated_at,
                           updated_at > NOW() - INTERVAL '45 seconds' AS fresh
                    FROM service_heartbeats
                    WHERE service = 'integration-worker'
                    """
                )
                row = cur.fetchone()
        if row is None:
            return None
        result = dict(row)
        if isinstance(result.get("updated_at"), datetime):
            result["updated_at"] = result["updated_at"].astimezone(timezone.utc).isoformat()
        return result
    except psycopg.Error:
        return None
