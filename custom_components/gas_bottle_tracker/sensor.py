"""Sensors for the Gas Bottle Tracker integration."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import logging
from statistics import median

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import dt as dt_util

from .const import DOMAIN, SIGNAL_UPDATE
from .storage import GasBottleStorage


_LOGGER = logging.getLogger(__name__)


def _as_date(value) -> date | None:
    """Convert a value to a date."""

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
            pass

        parsed = dt_util.parse_datetime(value)

        if parsed is not None:
            return parsed.date()

    return None


def _get_calculations(
    storage: GasBottleStorage,
    bottle_size: float,
) -> dict:
    """Calculate all gas bottle values."""

    current_change = _as_date(
        storage.current_bottle_change
    )

    previous_changes = (
        storage.previous_bottle_changes
    )

    if current_change is None:
        return {}

    dates = []

    for value in previous_changes:
        parsed = _as_date(value)

        if parsed is not None:
            dates.append(parsed)

    dates.append(current_change)

    dates = sorted(set(dates))

    lifespans = []

    for index in range(len(dates) - 1):
        days = (
            dates[index + 1] - dates[index]
        ).days

        if days > 0:
            lifespans.append(days)

    today = dt_util.now().date()

    current_age = max(
        (today - current_change).days,
        0,
    )

    if lifespans:
        average_lifespan = (
            sum(lifespans) / len(lifespans)
        )

        shortest_lifespan = min(lifespans)
        longest_lifespan = max(lifespans)
        median_lifespan = median(lifespans)

        average_daily_usage = (
            bottle_size / average_lifespan
            if bottle_size > 0
            else 0
        )

        estimated_days_remaining = max(
            average_lifespan - current_age,
            0,
        )

        remaining_percentage = max(
            min(
                (
                    estimated_days_remaining
                    / average_lifespan
                ) * 100,
                100,
            ),
            0,
        )

        estimated_next_change = (
            current_change
            + timedelta(
                days=round(average_lifespan)
            )
        )

    else:
        average_lifespan = 0
        shortest_lifespan = 0
        longest_lifespan = 0
        median_lifespan = 0
        average_daily_usage = 0
        estimated_days_remaining = 0
        remaining_percentage = 0
        estimated_next_change = None

    return {
        "current_bottle_age": current_age,
        "average_bottle_lifespan": round(
            average_lifespan,
            1,
        ),
        "average_daily_usage": round(
            average_daily_usage,
            3,
        ),
        "estimated_days_remaining": round(
            estimated_days_remaining,
            1,
        ),
        "remaining_percentage": round(
            remaining_percentage,
            1,
        ),
        "estimated_next_change": (
            estimated_next_change
            if estimated_next_change
            else None
        ),
        "shortest_bottle_lifespan": (
            shortest_lifespan
        ),
        "longest_bottle_lifespan": (
            longest_lifespan
        ),
        "median_bottle_lifespan": round(
            median_lifespan,
            1,
        ),
        "history_count": len(lifespans),
        "spare_bottles": storage.spare_bottles,
    }


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Gas Bottle Tracker sensors."""

    storage = hass.data[DOMAIN][entry.entry_id][
        "storage"
    ]

    bottle_size = float(
        entry.data.get("bottle_size", 0)
    )

    sensors = [
        GasBottleSensor(
            hass,
            entry.entry_id,
            storage,
            bottle_size,
            "bottle_size",
            "Bottle Size",
            "kg",
            "mdi:gas-cylinder",
        ),
        GasBottleSensor(
            hass,
            entry.entry_id,
            storage,
            bottle_size,
            "current_bottle_age",
            "Current Bottle Age",
            "days",
            "mdi:gas-cylinder",
        ),
        GasBottleSensor(
            hass,
            entry.entry_id,
            storage,
            bottle_size,
            "average_bottle_lifespan",
            "Average Bottle Lifespan",
            "days",
            "mdi:chart-timeline-variant",
        ),
        GasBottleSensor(
            hass,
            entry.entry_id,
            storage,
            bottle_size,
            "average_daily_usage",
            "Average Daily Usage",
            "kg/day",
            "mdi:scale",
        ),
        GasBottleSensor(
            hass,
            entry.entry_id,
            storage,
            bottle_size,
            "estimated_days_remaining",
            "Estimated Days Remaining",
            "days",
            "mdi:timer-sand",
        ),
        GasBottleSensor(
            hass,
            entry.entry_id,
            storage,
            bottle_size,
            "remaining_percentage",
            "Remaining Percentage",
            "%",
            "mdi:percent",
        ),
        GasBottleSensor(
            hass,
            entry.entry_id,
            storage,
            bottle_size,
            "estimated_next_change",
            "Estimated Next Change",
            None,
            "mdi:calendar-clock",
            device_class="date",
        ),
        GasBottleSensor(
            hass,
            entry.entry_id,
            storage,
            bottle_size,
            "shortest_bottle_lifespan",
            "Shortest Bottle Lifespan",
            "days",
            "mdi:arrow-collapse-down",
        ),
        GasBottleSensor(
            hass,
            entry.entry_id,
            storage,
            bottle_size,
            "longest_bottle_lifespan",
            "Longest Bottle Lifespan",
            "days",
            "mdi:arrow-collapse-up",
        ),
        GasBottleSensor(
            hass,
            entry.entry_id,
            storage,
            bottle_size,
            "median_bottle_lifespan",
            "Median Bottle Lifespan",
            "days",
            "mdi:chart-bell-curve",
        ),
        GasBottleSensor(
            hass,
            entry.entry_id,
            storage,
            bottle_size,
            "history_count",
            "Bottle History Count",
            "changes",
            "mdi:history",
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        GasBottleSensor(
            hass,
            entry.entry_id,
            storage,
            bottle_size,
            "spare_bottles",
            "Spare Bottles",
            "bottles",
            "mdi:gas-cylinder",
        ),
    ]

    async_add_entities(sensors)


class GasBottleSensor(SensorEntity):
    """Gas Bottle Tracker sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        storage: GasBottleStorage,
        bottle_size: float,
        sensor_key: str,
        name: str,
        unit: str | None,
        icon: str,
        device_class: str | None = None,
        entity_category: EntityCategory | None = None,
    ) -> None:
        """Initialize the sensor."""

        self.hass = hass
        self.entry_id = entry_id
        self.storage = storage
        self.bottle_size = bottle_size
        self.sensor_key = sensor_key

        self._attr_name = name

        self._attr_unique_id = (
            f"{entry_id}_{sensor_key}"
        )

        self._attr_icon = icon

        if unit:
            self._attr_native_unit_of_measurement = unit

        if device_class:
            self._attr_device_class = device_class

        if entity_category:
            self._attr_entity_category = entity_category

    async def async_added_to_hass(self) -> None:
        """Register for storage updates."""

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                SIGNAL_UPDATE,
                self._handle_update,
            )
        )

    def _handle_update(
        self,
        entry_id: str,
    ) -> None:
        """Handle an integration data update."""

        if entry_id != self.entry_id:
            return

        self.async_write_ha_state()

    @property
    def native_value(self):
        """Return the current sensor value."""

        if self.sensor_key == "bottle_size":
            return self.bottle_size

        calculations = _get_calculations(
            self.storage,
            self.bottle_size,
        )

        return calculations.get(
            self.sensor_key
        )

    async def async_update(self) -> None:
        """Update the sensor."""

        self.async_write_ha_state()