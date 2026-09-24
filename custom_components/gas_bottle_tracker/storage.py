"""Persistent storage for Gas Bottle Tracker."""

from __future__ import annotations

from datetime import date, datetime
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN


_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.storage"


class GasBottleStorage:
    """Manage persistent Gas Bottle Tracker data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
    ) -> None:
        """Initialize storage."""

        self.hass = hass
        self.entry_id = entry_id

        self.store = Store(
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY}_{entry_id}",
        )

        self.data: dict = {}

    async def async_load(self) -> dict:
        """Load stored data."""

        stored = await self.store.async_load()

        if stored is None:
            self.data = {
                "current_bottle_change": None,
                "previous_bottle_changes": [],
                "spare_bottles": 0,
                "notification_state": {
                    "bottle_change": None,
                    "sent": [],
                    "spares_empty_sent": False,
                },
            }
        else:
            self.data = stored

            # Ensure notification state exists for
            # installations that were created before
            # notification support was added.
            self.data.setdefault(
                "notification_state",
                {
                    "bottle_change": None,
                    "sent": [],
                    "spares_empty_sent": False,
                },
            )

            notification_state = self.data[
                "notification_state"
            ]

            notification_state.setdefault(
                "bottle_change",
                None,
            )

            notification_state.setdefault(
                "sent",
                [],
            )

            notification_state.setdefault(
                "spares_empty_sent",
                False,
            )

        return self.data

    async def async_save(self) -> None:
        """Save current data."""

        await self.store.async_save(
            self.data
        )

    async def async_migrate_from_config(
        self,
        config_data: dict,
    ) -> None:
        """Import existing config flow data if storage is empty."""

        if self.data.get(
            "current_bottle_change"
        ) is not None:
            return

        current_change = config_data.get(
            "current_bottle_change"
        )

        previous_changes = config_data.get(
            "previous_bottle_changes",
            [],
        )

        spare_bottles = config_data.get(
            "spare_bottles",
            0,
        )

        self.data = {
            "current_bottle_change": _serialize_date(
                current_change
            ),
            "previous_bottle_changes": [
                _serialize_date(value)
                for value in previous_changes
                if _serialize_date(value) is not None
            ],
            "spare_bottles": int(
                spare_bottles or 0
            ),
            "notification_state": {
                "bottle_change": _serialize_date(
                    current_change
                ),
                "sent": [],
                "spares_empty_sent": False,
            },
        }

        await self.async_save()

        _LOGGER.info(
            "Migrated existing Gas Bottle Tracker data "
            "into persistent storage."
        )

    @property
    def current_bottle_change(self) -> str | None:
        """Return current bottle change date."""

        return self.data.get(
            "current_bottle_change"
        )

    @property
    def previous_bottle_changes(
        self,
    ) -> list[str]:
        """Return previous bottle change dates."""

        return self.data.get(
            "previous_bottle_changes",
            [],
        )

    @property
    def spare_bottles(self) -> int:
        """Return number of spare bottles."""

        return int(
            self.data.get(
                "spare_bottles",
                0,
            )
        )

    async def async_set_current_bottle(
        self,
        change_date: date,
    ) -> None:
        """Set the current bottle change date."""

        self.data[
            "current_bottle_change"
        ] = change_date.isoformat()

        # A manually changed current bottle date
        # represents a new bottle state, so reset
        # notification history.
        self.data[
            "notification_state"
        ] = {
            "bottle_change": (
                change_date.isoformat()
            ),
            "sent": [],
            "spares_empty_sent": False,
        }

        await self.async_save()

    async def async_add_bottle_change(
        self,
        change_date: date,
    ) -> None:
        """Add a bottle change to history."""

        changes = list(
            self.previous_bottle_changes
        )

        changes.append(
            change_date.isoformat()
        )

        self.data[
            "previous_bottle_changes"
        ] = changes

        await self.async_save()

    async def async_new_bottle(
        self,
        change_date: date,
        used_spare: bool = False,
    ) -> None:
        """Record a new bottle installation."""

        current = (
            self.current_bottle_change
        )

        if current:
            await self.async_add_bottle_change(
                _deserialize_date(current)
            )

        self.data[
            "current_bottle_change"
        ] = change_date.isoformat()

        if used_spare:
            self.data[
                "spare_bottles"
            ] = max(
                self.spare_bottles - 1,
                0,
            )

        # A new bottle starts a new notification
        # cycle.
        self.data[
            "notification_state"
        ] = {
            "bottle_change": (
                change_date.isoformat()
            ),
            "sent": [],
            "spares_empty_sent": False,
        }

        await self.async_save()

    async def async_add_spare(
        self,
    ) -> None:
        """Add one spare bottle."""

        self.data[
            "spare_bottles"
        ] = self.spare_bottles + 1

        # Adding a spare means the empty-spares
        # notification can trigger again later.
        notification_state = self.data.setdefault(
            "notification_state",
            {
                "bottle_change": None,
                "sent": [],
                "spares_empty_sent": False,
            },
        )

        notification_state[
            "spares_empty_sent"
        ] = False

        await self.async_save()

    async def async_remove_spare(
        self,
    ) -> None:
        """Remove one spare bottle."""

        self.data[
            "spare_bottles"
        ] = max(
            self.spare_bottles - 1,
            0,
        )

        await self.async_save()


def _serialize_date(
    value,
) -> str | None:
    """Convert a date value into ISO format."""

    if value is None:
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value.date().isoformat()

    if isinstance(
        value,
        date,
    ):
        return value.isoformat()

    if isinstance(
        value,
        str,
    ):
        return value

    return None


def _deserialize_date(
    value: str,
) -> date:
    """Convert an ISO date string into a date."""

    return date.fromisoformat(
        value
    )