"""Constants for the Grid Connect integration."""

DOMAIN = "gridconnect"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_COUNTRY = "country_code"
CONF_REGION = "region"

DEFAULT_COUNTRY = "61"  # Australia
DEFAULT_REGION = "auto"  # probe all data centres and keep the one that works

# How often to poll the cloud for device state, in seconds.
DEFAULT_SCAN_INTERVAL = 30
