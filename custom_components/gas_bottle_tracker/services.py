"""Services for the Gas Bottle Tracker integration."""

from __future__ import annotations

from datetime import date
import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, SIGNAL_UPDATE
from .notifications import _send_notification, async_check_notifications

_LOGGER = logging.getLogger(__name__)

SERVICE_NEW_BOTTLE = "new_bottle"
SERVICE_ADD_SPARE = "add_spare"
SERVICE_REMOVE_SPARE = "remove_spare"
SERVICE_TEST_NOTIFICATION = "test_notification"
SERVICE_CHECK_NOTIFICATIONS = "check_notifications"


def _get_entry(hass: HomeAssistant):
    """Get the configured Gas Bottle Tracker entry."""
    entries = hass.data.get(DOMAIN, {})

    if not entries:
        return None, None

    entry_id, entry_data = next(iter(entries.items()))
    return entry_id, entry_data


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register Gas Bottle Tracker services."""

    async def handle_new_bottle(call: ServiceCall) -> None:
        """Handle installation of a new gas bottle."""
        entry_id, entry_data = _get_entry(hass)

        if entry_data is None:
            return

        storage = entry_data["storage"]
        change_date = call.data.get("change_date")

        new_date = (
            date.fromisoformat(change_date)
            if change_date
            else date.today()
        )

        used_spare = call.data.get("used_spare", False)

        await storage.async_new_bottle(new_date, used_spare)

        async_dispatcher_send(hass, SIGNAL_UPDATE, entry_id)

    async def handle_add_spare(call: ServiceCall) -> None:
        """Add one spare bottle."""
        entry_id, entry_data = _get_entry(hass)

        if entry_data is None:
            return

        await entry_data["storage"].async_add_spare()
        async_dispatcher_send(hass, SIGNAL_UPDATE, entry_id)

    async def handle_remove_spare(call: ServiceCall) -> None:
        """Remove one spare bottle."""
        entry_id, entry_data = _get_entry(hass)

        if entry_data is None:
            return

        await entry_data["storage"].async_remove_spare()
        async_dispatcher_send(hass, SIGNAL_UPDATE, entry_id)

    async def handle_test_notification(call: ServiceCall) -> None:
        """Send a branded test notification."""
        entry_id, entry_data = _get_entry(hass)

        if entry_data is None:
            return

        entry = entry_data["entry"]
        options = entry.options

        if not options.get("notification_enabled", True):
            _LOGGER.warning(
                "Gas Bottle Tracker notifications are disabled."
            )
            return

        notification_services = options.get(
            "notification_services",
            [],
        )

        if not notification_services:
            _LOGGER.warning(
                "Gas Bottle Tracker has no notification devices selected."
            )
            return

        title = call.data.get(
            "title",
            "Gas Bottle Tracker Test",
        )
        message = call.data.get(
            "message",
            "Gas Bottle Tracker notifications are working correctly.",
        )

        await _send_notification(
            hass,
            notification_services,
            title,
            message,
            icon="mdi:gas-cylinder",
            icon_color="#FFFFFF",
            background_color="#1976D2",
        )

    async def handle_check_notifications(call: ServiceCall) -> None:
        """Manually run the notification check."""
        entry_id, entry_data = _get_entry(hass)

        if entry_data is None:
            return

        await async_check_notifications(
            hass,
            entry_data["entry"],
            entry_data["storage"],
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_NEW_BOTTLE,
        handle_new_bottle,
        schema=vol.Schema(
            {
                vol.Optional("change_date"): cv.string,
                vol.Optional("used_spare", default=False): cv.boolean,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_SPARE,
        handle_add_spare,
        schema=vol.Schema({}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_SPARE,
        handle_remove_spare,
        schema=vol.Schema({}),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_TEST_NOTIFICATION,
        handle_test_notification,
        schema=vol.Schema(
            {
                vol.Optional(
                    "title",
                    default="Gas Bottle Tracker Test",
                ): cv.string,
                vol.Optional(
                    "message",
                    default=(
                        "Gas Bottle Tracker notifications are "
                        "working correctly."
                    ),
                ): cv.string,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CHECK_NOTIFICATIONS,
        handle_check_notifications,
        schema=vol.Schema({}),
    )
