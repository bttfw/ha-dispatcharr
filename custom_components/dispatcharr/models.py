"""Normalize only documented, observed data. Never infer identities or quality."""

import hashlib
import json
import math
from datetime import datetime, timezone


def number(value):
    try:
        parsed = float(value)
        return (
            parsed
            if math.isfinite(parsed) and parsed >= 0 and not isinstance(value, bool)
            else None
        )
    except (ValueError, TypeError):
        return None


def identity(value):
    parsed = number(value)
    return str(int(parsed)) if parsed is not None and parsed > 0 and parsed.is_integer() else None


def timestamp(value):
    if isinstance(value, str) and "T" in value:
        try:
            date = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return date.timestamp() if date.tzinfo else None
        except ValueError:
            return None
    return number(value)


def device_key(client):
    """Opaque alias key for the observed IP + User-Agent pair, not a device ID."""
    ip, agent = client.get("ip_address"), client.get("user_agent")
    if not ip or not agent or ip == "unknown" or agent == "unknown":
        return None
    return hashlib.sha256(json.dumps([ip, agent], separators=(",", ":")).encode()).hexdigest()[:24]


def current_program(program, now):
    if not program:
        return None
    start, end = timestamp(program.get("start_time")), timestamp(program.get("end_time"))
    if start is None or end is None or not start <= now < end:
        return None
    return {"title": program.get("title"), "start": start, "end": end}


def viewers(channels, metadata, users, providers, profiles, programmes, aliases, text, now=None):
    now = now if now is not None else datetime.now(timezone.utc).timestamp()
    result = []
    for channel in channels:
        uuid = channel["channel_id"]
        meta = metadata.get(uuid, {})
        provider = providers.get(identity(channel.get("m3u_profile_id")), {})
        program = current_program(programmes.get(uuid), now)
        for client in channel["clients"]:
            user_id = identity(client.get("user_id"))
            alias_key = device_key(client)
            output_profile = identity(client.get("output_profile_id"))
            connected = timestamp(client.get("connected_at"))
            result.append(
                {
                    "client_id": client["client_id"],
                    "channel_uuid": uuid,
                    "user_id": user_id,
                    "username": users.get(user_id),
                    "device_key": alias_key,
                    "device_alias": text(aliases.get(alias_key)),
                    "device_description": text(client.get("user_agent")),
                    "channel_name": meta.get("name") or text(channel.get("channel_name")),
                    "channel_id": meta.get("id"),
                    "logo_id": meta.get("logo_id"),
                    "connected_at": connected if connected and connected <= now else None,
                    "connection_status": "connected",  # Observed membership, never a play/pause claim.
                    "playback_status": None,
                    "proxy_state": text(channel.get("state")),
                    "programme": program,
                    "source_resolution": text(channel.get("resolution")),
                    "source_fps": number(channel.get("source_fps")),
                    "average_bitrate_kbps": number(channel.get("avg_bitrate_kbps")),
                    "video_codec": text(channel.get("video_codec")),
                    "audio_codec": text(channel.get("audio_codec")),
                    "provider": provider.get("provider"),
                    "provider_profile": provider.get("profile"),
                    "stream_profile": text(channel.get("stream_profile")),
                    "output_profile": profiles.get(output_profile),
                    "output_profile_id": output_profile,
                    "output_format": text(client.get("output_format")),
                }
            )
    return sorted(result, key=lambda r: (r["channel_uuid"], r["client_id"]))
