"""Config flow for Gas Bottle Tracker."""

from __future__ import annotations

from datetime import date

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

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
    DOMAIN,
)


def _get_mobile_notification_services(hass):
    """Return available Home Assistant mobile notification services."""

    services = hass.services.async_services_for_domain(
        "notify"
    )

    mobile_services = []

    for service_name in services:
        if service_name.startswith("mobile_app_"):
            mobile_services.append(
                {
                    "value": service_name,
                    "label": service_name.replace(
                        "mobile_app_",
                        "",
                    ).replace(
                        "_",
                        " ",
                    ).title(),
                }
            )

    return sorted(
        mobile_services,
        key=lambda item: item["label"].lower(),
    )


class GasBottleTrackerConfigFlow(
    config_entries.ConfigFlow,
    domain=DOMAIN,
):
    """Handle a config flow for Gas Bottle Tracker."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input=None,
    ):
        """Handle the initial setup step."""

        if user_input is not None:
            self.user_input = user_input

            self.user_input[
                "previous_bottle_changes"
            ] = []

            if user_input["has_spares"]:
                return await self.async_step_spares()

            return await self.async_step_history()

        schema = vol.Schema(
            {
                vol.Required(
                    "name",
                    default="Gas Bottle",
                ): str,

                vol.Required(
                    "bottle_size",
                    default=9,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=100,
                        step=0.5,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="kg",
                    )
                ),

                vol.Required(
                    "current_bottle_change",
                    default=date.today(),
                ): selector.DateSelector(),

                vol.Required(
                    "has_spares",
                    default=False,
                ): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
        )

    async def async_step_spares(
        self,
        user_input=None,
    ):
        """Handle spare bottle setup."""

        if user_input is not None:
            self.user_input[
                "spare_bottles"
            ] = user_input["spare_bottles"]

            return await self.async_step_history()

        schema = vol.Schema(
            {
                vol.Required(
                    "spare_bottles",
                    default=1,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=20,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                )
            }
        )

        return self.async_show_form(
            step_id="spares",
            data_schema=schema,
        )

    async def async_step_history(
        self,
        user_input=None,
    ):
        """Handle previous bottle change date."""

        if user_input is not None:
            self.user_input[
                "previous_bottle_changes"
            ].append(
                user_input[
                    "previous_bottle_change"
                ]
            )

            return await self.async_step_history_more()

        schema = vol.Schema(
            {
                vol.Required(
                    "previous_bottle_change",
                    default=date.today(),
                ): selector.DateSelector(),
            }
        )

        return self.async_show_form(
            step_id="history",
            data_schema=schema,
        )

    async def async_step_history_more(
        self,
        user_input=None,
    ):
        """Ask whether another previous bottle change should be added."""

        if user_input is not None:
            if user_input["continue_history"]:
                return await self.async_step_history()

            return self.async_create_entry(
                title=self.user_input["name"],
                data=self.user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(
                    "continue_history",
                    default=True,
                ): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(
            step_id="history_more",
            data_schema=schema,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ):
        """Return the options flow."""

        return GasBottleTrackerOptionsFlow()


class GasBottleTrackerOptionsFlow(
    config_entries.OptionsFlowWithReload,
):
    """Handle Gas Bottle Tracker options."""

    async def async_step_init(
        self,
        user_input=None,
    ):
        """Manage notification settings."""

        if user_input is not None:
            return self.async_create_entry(
                title="",
                data=user_input,
            )

        current_options = self.config_entry.options

        notification_services = (
            _get_mobile_notification_services(
                self.hass
            )
        )

        current_services = current_options.get(
            CONF_NOTIFICATION_SERVICES,
            [],
        )

        available_service_values = {
            service["value"]
            for service in notification_services
        }

        selected_services = [
            service
            for service in current_services
            if service in available_service_values
        ]

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_NOTIFICATION_ENABLED,
                    default=current_options.get(
                        CONF_NOTIFICATION_ENABLED,
                        DEFAULT_NOTIFICATION_ENABLED,
                    ),
                ): selector.BooleanSelector(),

                vol.Optional(
                    CONF_NOTIFICATION_SERVICES,
                    default=selected_services,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=notification_services,
                        multiple=True,
                        mode=selector.SelectSelectorMode.LIST,
                    )
                ),

                vol.Required(
                    CONF_WARNING_DAYS,
                    default=current_options.get(
                        CONF_WARNING_DAYS,
                        DEFAULT_WARNING_DAYS,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=90,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="days",
                    )
                ),

                vol.Required(
                    CONF_CRITICAL_DAYS,
                    default=current_options.get(
                        CONF_CRITICAL_DAYS,
                        DEFAULT_CRITICAL_DAYS,
                    ),
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=14,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                        unit_of_measurement="days",
                    )
                ),

                vol.Required(
                    CONF_NOTIFY_OVERDUE,
                    default=current_options.get(
                        CONF_NOTIFY_OVERDUE,
                        DEFAULT_NOTIFY_OVERDUE,
                    ),
                ): selector.BooleanSelector(),

                vol.Required(
                    CONF_NOTIFY_SPARES_EMPTY,
                    default=current_options.get(
                        CONF_NOTIFY_SPARES_EMPTY,
                        DEFAULT_NOTIFY_SPARES_EMPTY,
                    ),
                ): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
        )