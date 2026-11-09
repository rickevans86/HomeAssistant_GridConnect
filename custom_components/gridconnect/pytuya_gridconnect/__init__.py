"""Grid Connect (Arlec) cloud client.

Grid Connect is Arlec's Australian smart-home brand; its devices run on Tuya's
platform under the app ``com.arlec.gridconnect``. This package speaks the Tuya
mobile-app ("api.json") protocol the Grid Connect app itself uses, so you can log
in with your Grid Connect account, enumerate the devices you own, read their
local keys, and read/write datapoints — all for interoperability with Home
Assistant.

Nothing here talks to Tuya's *developer* IoT cloud; it uses the same app-level
credentials embedded in the public APK (see ``const.py`` for provenance), exactly
as community projects such as tinytuya and LocalTuya do.
"""

from .api import GridConnectCloud, GridConnectError, Device
from .const import REGIONS

__all__ = ["GridConnectCloud", "GridConnectError", "Device", "REGIONS"]
