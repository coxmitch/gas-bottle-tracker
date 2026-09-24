"""Push notification support for Gas Bottle Tracker."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CRITICAL_DAYS,
    CONF_NOTIFICATION_ENABLED,
    CONF_NOTIFICATION_SERVICES,
    CONF_NOTIFY_OVERDUE,
    CONF_NOTIFY_SPARES_EMPTY,
    CONF_WARNING_DAYS,
    DEFAULT_CRITICAL_DAYS,
    DEFAULT_NOTIFICATION_ENABLED,
    DEFAULT_NOTIFY_OVERDUE,
    DEFAULT_NOTIFY_SPARES_EMPTY,
    DEFAULT_WARNING_DAYS,
    NOTIFICATION_CRITICAL,
    NOTIFICATION_OVERDUE,
    NOTIFICATION_SPARES_EMPTY,
    NOTIFICATION_WARNING,
)
from .storage import GasBottleStorage


_LOGGER = logging.getLogger(__name__)

CHECK_INTERVAL = timedelta(hours=1)


def _as_date(value) -> date | None:
    """Convert a value into a date."""

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            parsed = dt_util.parse_datetime(value)

            if parsed is not None:
                return parsed.date()

    return None


def _calculate_days_remaining(
    storage: GasBottleStorage,
    bottle_size: float,
) -> tuple[float, date | None]:
    """Calculate estimated days remaining and next change date."""

    current_change = _as_date(
        storage.current_bottle_change
    )

    if current_change is None:
        return 0, None

    dates: list[date] = []

    for value in storage.previous_bottle_changes:
        parsed = _as_date(value)

        if parsed is not None:
            dates.append(parsed)

    dates.append(current_change)

    dates = sorted(set(dates))

    lifespans: list[int] = []

    for index in range(len(dates) - 1):
        days = (
            dates[index + 1] - dates[index]
        ).days

        if days > 0:
            lifespans.append(days)

    if not lifespans:
        return 0, None

    average_lifespan = (
        sum(lifespans) / len(lifespans)
    )

    today = dt_util.now().date()

    current_age = max(
        (today - current_change).days,
        0,
    )

    estimated_days_remaining = max(
        average_lifespan - current_age,
        0,
    )

    estimated_next_change = (
        current_change
        + timedelta(
            days=round(average_lifespan)
        )
    )

    return (
        round(estimated_days_remaining, 1),
        estimated_next_change,
    )


def _get_notification_state(
    storage: GasBottleStorage,
) -> dict:
    """Get persistent notification state."""

    state = storage.data.setdefault(
        "notification_state",
        {
            "bottle_change": None,
            "sent": [],
            "spares_empty_sent": False,
        },
    )

    state.setdefault(
        "bottle_change",
        None,
    )

    state.setdefault(
        "sent",
        [],
    )

    state.setdefault(
        "spares_empty_sent",
        False,
    )

    return state


def _get_notification_data(
    icon: str,
    icon_color: str,
    background_color: str,
) -> dict:
    """Return Gas Bottle Tracker notification styling."""

    return {
        "notification_icon": icon,
        "notification_icon_color": icon_color,
        "color": background_color,
    }


async def _send_notification(
    hass: HomeAssistant,
    services: list[str],
    title: str,
    message: str,
    icon: str = "mdi:gas-cylinder",
    icon_color: str = "#FFFFFF",
    background_color: str = "#1976D2",
) -> bool:
    """Send a branded notification to all selected mobile devices."""

    sent_successfully = False

    notification_data = _get_notification_data(
        icon,
        icon_color,
        background_color,
    )

    for service in services:
        try:
            await hass.services.async_call(
                "notify",
                service,
                {
                    "title": title,
                    "message": message,
                    "data": notification_data,
                },
                blocking=True,
            )

            sent_successfully = True

            _LOGGER.info(
                "Sent Gas Bottle Tracker notification "
                "to notify.%s",
                service,
            )

        except Exception:
            _LOGGER.exception(
                "Failed to send Gas Bottle Tracker "
                "notification to notify.%s",
                service,
            )

    return sent_successfully


async def async_check_notifications(
    hass: HomeAssistant,
    entry: ConfigEntry,
    storage: GasBottleStorage,
) -> None:
    """Check whether any notifications need to be sent."""

    options = entry.options

    enabled = options.get(
        CONF_NOTIFICATION_ENABLED,
        DEFAULT_NOTIFICATION_ENABLED,
    )

    if not enabled:
        return

    services = options.get(
        CONF_NOTIFICATION_SERVICES,
        [],
    )

    if not services:
        _LOGGER.debug(
            "Gas Bottle Tracker notifications enabled "
            "but no notification devices are selected."
        )
        return

    bottle_change = storage.current_bottle_change

    if not bottle_change:
        return

    state = _get_notification_state(
        storage
    )

    if state["bottle_change"] != bottle_change:
        state["bottle_change"] = bottle_change
        state["sent"] = []

        await storage.async_save()

    bottle_size = float(
        entry.data.get(
            "bottle_size",
            0,
        )
    )

    days_remaining, next_change = (
        _calculate_days_remaining(
            storage,
            bottle_size,
        )
    )

    warning_days = int(
        options.get(
            CONF_WARNING_DAYS,
            DEFAULT_WARNING_DAYS,
        )
    )

    critical_days = int(
        options.get(
            CONF_CRITICAL_DAYS,
            DEFAULT_CRITICAL_DAYS,
        )
    )

    sent_notifications = state["sent"]

    # ---------------------------------------------------------
    # OVERDUE
    # ---------------------------------------------------------

    if (
        days_remaining <= 0
        and options.get(
            CONF_NOTIFY_OVERDUE,
            DEFAULT_NOTIFY_OVERDUE,
        )
        and NOTIFICATION_OVERDUE not in sent_notifications
    ):
        message = (
            "Your gas bottle has reached its "
            "estimated replacement date."
        )

        if next_change:
            message += (
                f" Estimated change date: "
                f"{next_change.strftime('%d %B %Y')}."
            )

        if await _send_notification(
            hass,
            services,
            "Gas Bottle Overdue",
            message,
            icon="mdi:gas-cylinder-off",
            icon_color="#FFFFFF",
            background_color="#D32F2F",
        ):
            sent_notifications.append(
                NOTIFICATION_OVERDUE
            )
            await storage.async_save()

    # ---------------------------------------------------------
    # CRITICAL
    # ---------------------------------------------------------

    elif (
        days_remaining <= critical_days
        and days_remaining > 0
        and NOTIFICATION_CRITICAL not in sent_notifications
    ):
        remaining = max(
            round(days_remaining),
            1,
        )

        message = (
            f"Your gas bottle is estimated to "
            f"have {remaining} day"
            f"{'s' if remaining != 1 else ''} remaining."
        )

        if next_change:
            message += (
                f" Estimated change date: "
                f"{next_change.strftime('%d %B %Y')}."
            )

        if await _send_notification(
            hass,
            services,
            "Gas Bottle Critical",
            message,
            icon="mdi:gas-cylinder-alert",
            icon_color="#FFFFFF",
            background_color="#E65100",
        ):
            sent_notifications.append(
                NOTIFICATION_CRITICAL
            )
            await storage.async_save()

    # ---------------------------------------------------------
    # WARNING
    # ---------------------------------------------------------

    elif (
        days_remaining <= warning_days
        and days_remaining > critical_days
        and NOTIFICATION_WARNING not in sent_notifications
    ):
        remaining = max(
            round(days_remaining),
            1,
        )

        message = (
            f"Your gas bottle is estimated to "
            f"have {remaining} days remaining."
        )

        if next_change:
            message += (
                f" Estimated change date: "
                f"{next_change.strftime('%d %B %Y')}."
            )

        if await _send_notification(
            hass,
            services,
            "Gas Bottle Warning",
            message,
            icon="mdi:gas-cylinder",
            icon_color="#FFFFFF",
            background_color="#F57C00",
        ):
            sent_notifications.append(
                NOTIFICATION_WARNING
            )
            await storage.async_save()

    # ---------------------------------------------------------
    # SPARES EMPTY
    # ---------------------------------------------------------

    if (
        storage.spare_bottles <= 0
        and options.get(
            CONF_NOTIFY_SPARES_EMPTY,
            DEFAULT_NOTIFY_SPARES_EMPTY,
        )
        and not state["spares_empty_sent"]
    ):
        message = (
            "You have no full spare gas bottles "
            "recorded."
        )

        if await _send_notification(
            hass,
            services,
            "Gas Bottle Spares Empty",
            message,
            icon="mdi:gas-cylinder-outline",
            icon_color="#FFFFFF",
            background_color="#616161",
        ):
            state["spares_empty_sent"] = True
            await storage.async_save()

    elif storage.spare_bottles > 0:
        if state["spares_empty_sent"]:
            state["spares_empty_sent"] = False
            await storage.async_save()


async def async_setup_notifications(
    hass: HomeAssistant,
    entry: ConfigEntry,
    storage: GasBottleStorage,
):
    """Set up periodic Gas Bottle Tracker notifications."""

    async def _scheduled_check(now) -> None:
        """Run the notification check."""

        await async_check_notifications(
            hass,
            entry,
            storage,
        )

    await async_check_notifications(
        hass,
        entry,
        storage,
    )

    return async_track_time_interval(
        hass,
        _scheduled_check,
        CHECK_INTERVAL,
    )