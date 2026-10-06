"""Normalize server-reported playback without guessing identities or quality."""

import re
from datetime import datetime, timezone

from .api import InvalidResponse
from .models import current_program, number


def obj(value):
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise InvalidResponse("invalid_sessions")
    return value


def objects(value):
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise InvalidResponse("invalid_sessions")
    return value


def optional_id(value, validate):
    return validate(value) if value is not None and value != "" else None


def scaled(value, divisor):
    parsed = number(value)
    return parsed / divisor if parsed is not None else None


def resolution(width, height):
    width, height = number(width), number(height)
    if width and height and width.is_integer() and height.is_integer():
        return f"{int(width)}x{int(height)}"
    return None


def selected(rows):
    chosen = [row for row in rows if row.get("selected") in (True, 1, "1")]
    return chosen[0] if len(chosen) == 1 else rows[0] if len(rows) == 1 else {}


def normalize_emby_session(raw, text, validate):
    item, state = obj(raw.get("NowPlayingItem")), obj(raw.get("PlayState"))
    source_id = state.get("MediaSourceId")
    sources = objects(item.get("MediaSources"))
    matching = [s for s in sources if source_id is not None and s.get("Id") == source_id]
    source = (
        matching[0]
        if len(matching) == 1
        else sources[0]
        if source_id is None and len(sources) == 1
        else {}
    )
    streams = objects(
        source.get("MediaStreams")
        if source
        else []
        if source_id is not None and sources
        else item.get("MediaStreams")
    )
    videos = [s for s in streams if s.get("Type") == "Video"]
    audios = [s for s in streams if s.get("Type") == "Audio"]
    video = videos[0] if len(videos) == 1 else {}
    selected_audio = [s for s in audios if s.get("Index") == state.get("AudioStreamIndex")]
    audio = (
        selected_audio[0]
        if len(selected_audio) == 1
        else audios[0]
        if state.get("AudioStreamIndex") is None and len(audios) == 1
        else {}
    )
    transcode = obj(raw.get("TranscodingInfo"))
    programme = obj(item.get("CurrentProgram"))
    now = datetime.now(timezone.utc).timestamp()
    row = {
        "session_id": validate(raw.get("Id")),
        "item_id": optional_id(item.get("Id"), validate),
        "user_id": optional_id(raw.get("UserId"), validate),
        "username": text(raw.get("UserName")),
        "device_id": text(raw.get("DeviceId")),
        "device_name": text(raw.get("DeviceName")),
        "client": text(raw.get("Client")),
        "title": text(item.get("Name")),
        "series_title": text(item.get("SeriesName")),
        "season": number(item.get("ParentIndexNumber")),
        "episode": number(item.get("IndexNumber")),
        "media_type": text(item.get("Type")),
        "channel_id": optional_id(item.get("ChannelId"), validate),
        "channel_name": text(item.get("ChannelName")),
        "playback_status": (
            "paused"
            if state.get("IsPaused") is True
            else "playing"
            if state.get("IsPaused") is False
            else None
        ),
        "position_seconds": scaled(state.get("PositionTicks"), 10_000_000),
        "duration_seconds": scaled(item.get("RunTimeTicks"), 10_000_000),
        "observed_at": now,
        "play_method": text(state.get("PlayMethod")),
        "source_resolution": resolution(video.get("Width"), video.get("Height")),
        "source_fps": number(video.get("AverageFrameRate")),
        "source_bitrate_kbps": scaled(source.get("Bitrate"), 1000),
        "video_codec": text(video.get("Codec")),
        "audio_codec": text(audio.get("Codec")),
        "output_resolution": resolution(transcode.get("Width"), transcode.get("Height")),
        "output_bitrate_kbps": scaled(transcode.get("Bitrate"), 1000),
        "output_video_codec": text(transcode.get("VideoCodec")),
        "output_audio_codec": text(transcode.get("AudioCodec")),
        "can_stop": raw.get("SupportsRemoteControl") is True and bool(item.get("Id")),
        "programme": current_program(
            {
                "title": text(programme.get("Name")),
                "start_time": programme.get("StartDate"),
                "end_time": programme.get("EndDate"),
            },
            now,
        ),
    }
    poster_id = row["item_id"]
    tag = text(obj(item.get("ImageTags")).get("Primary"))
    if not tag and item.get("SeriesPrimaryImageTag") and item.get("SeriesId"):
        poster_id = validate(item["SeriesId"])
        tag = text(item["SeriesPrimaryImageTag"])
    poster = None
    if poster_id and tag and re.fullmatch(r"[A-Fa-f0-9]{1,128}", tag):
        poster = (
            f"/Items/{poster_id}/Images/Primary",
            {"maxWidth": 256, "quality": 80, "tag": tag},
        )
    return row, poster


def normalize_plex_session(raw, text, validate):
    session, user, player = obj(raw.get("Session")), obj(raw.get("User")), obj(raw.get("Player"))
    media = selected(objects(raw.get("Media")))
    parts = selected(objects(media.get("Part")))
    streams = objects(parts.get("Stream"))
    video = selected([s for s in streams if s.get("streamType") == 1])
    audio = selected([s for s in streams if s.get("streamType") == 2])
    transcode = obj(raw.get("TranscodeSession"))
    row = {
        # The termination API requires Session.id, not sessionKey or Player.id.
        "session_id": optional_id(session.get("id"), validate),
        "session_key": validate(raw.get("sessionKey")),
        "item_id": optional_id(raw.get("ratingKey"), validate),
        "user_id": optional_id(user.get("id"), validate),
        "username": text(user.get("title")),
        "device_id": text(player.get("machineIdentifier")),
        "device_name": text(player.get("title")),
        "client": text(player.get("product")),
        "title": text(raw.get("title")),
        "series_title": text(raw.get("grandparentTitle")) if raw.get("type") == "episode" else None,
        "season": number(raw.get("parentIndex")),
        "episode": number(raw.get("index")),
        "media_type": text(raw.get("type")),
        "channel_id": text(raw.get("channelIdentifier")),
        "channel_name": text(raw.get("channelTitle")),
        "playback_status": player.get("state")
        if player.get("state") in ("playing", "paused", "buffering")
        else None,
        "position_seconds": scaled(raw.get("viewOffset"), 1000),
        "duration_seconds": scaled(raw.get("duration"), 1000),
        "observed_at": datetime.now(timezone.utc).timestamp(),
        "play_method": text(parts.get("decision")),
        "source_resolution": resolution(media.get("width"), media.get("height")),
        "source_fps": number(video.get("frameRate")),
        "source_bitrate_kbps": number(media.get("bitrate")),
        "video_codec": text(video.get("codec") or media.get("videoCodec")),
        "audio_codec": text(audio.get("codec") or media.get("audioCodec")),
        "output_resolution": resolution(transcode.get("width"), transcode.get("height")),
        "output_bitrate_kbps": None,
        "output_video_codec": text(transcode.get("videoCodec")),
        "output_audio_codec": text(transcode.get("audioCodec")),
        "can_stop": bool(raw.get("ratingKey") and session.get("id")),
        "programme": None,
    }
    thumb = raw.get("thumb")
    poster = None
    # Never follow arbitrary URLs, proxy paths, query strings or access tokens.
    if isinstance(thumb, str) and re.fullmatch(
        r"/library/metadata/[0-9]+/thumb(?:/[0-9]+)?", thumb
    ):
        poster = (thumb, {})
    return row, poster
