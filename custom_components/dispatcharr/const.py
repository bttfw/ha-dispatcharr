"""Constants for the independently developed Dispatcharr integration."""

DOMAIN = "dispatcharr"
VERSION = "0.2.1"
PLATFORMS = ["sensor", "binary_sensor", "switch"]
CONF_CONTROL = "enable_control"
CONF_ALIASES = "device_aliases"
CONF_POLL = "poll_interval"
CONF_METADATA = "metadata_interval"
CONF_EPG = "epg_interval"
DEFAULTS = {
    CONF_CONTROL: False,
    CONF_ALIASES: {},
    CONF_POLL: 10,
    CONF_METADATA: 900,
    CONF_EPG: 60,
}
CARD_URL = f"/dispatcharr_static/dispatcharr-card.js?v={VERSION}"
