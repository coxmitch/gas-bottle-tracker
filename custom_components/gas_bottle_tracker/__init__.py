"""Gas Bottle Tracker integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .notifications import async_setup_notifications
from .services import async_setup_services
from .storage import GasBottleStorage

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up Gas Bottle Tracker."""
    await async_setup_services(hass)
    return True


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Set up Gas Bottle Tracker from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    storage = GasBottleStorage(hass, entry.entry_id)
    await storage.async_load()
    await storage.async_migrate_from_config(entry.data)

    hass.data[DOMAIN][entry.entry_id] = {
        "entry": entry,
        "storage": storage,
    }

    await hass.config_entries.async_forward_entry_setups(
        entry,
        PLATFORMS,
    )

    notification_unsub = await async_setup_notifications(
        hass,
        entry,
        storage,
    )

    hass.data[DOMAIN][entry.entry_id]["notification_unsub"] = (
        notification_unsub
    )

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> bool:
    """Unload Gas Bottle Tracker."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry,
        PLATFORMS,
    )

    if unload_ok:
        entry_data = hass.data[DOMAIN].get(entry.entry_id)

        if entry_data:
            notification_unsub = entry_data.get("notification_unsub")

            if notification_unsub:
                notification_unsub()

        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
