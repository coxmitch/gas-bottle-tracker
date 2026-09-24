"""Constants for the Gas Bottle Tracker integration."""

DOMAIN = "gas_bottle_tracker"

SIGNAL_UPDATE = f"{DOMAIN}_update"


# Notification options

CONF_NOTIFICATION_ENABLED = "notification_enabled"
CONF_NOTIFICATION_SERVICES = "notification_services"
CONF_WARNING_DAYS = "warning_days"
CONF_CRITICAL_DAYS = "critical_days"
CONF_NOTIFY_OVERDUE = "notify_overdue"
CONF_NOTIFY_SPARES_EMPTY = "notify_spares_empty"


# Notification types

NOTIFICATION_WARNING = "warning"
NOTIFICATION_CRITICAL = "critical"
NOTIFICATION_OVERDUE = "overdue"
NOTIFICATION_SPARES_EMPTY = "spares_empty"


# Default notification settings

DEFAULT_NOTIFICATION_ENABLED = True
DEFAULT_WARNING_DAYS = 20
DEFAULT_CRITICAL_DAYS = 10
DEFAULT_NOTIFY_OVERDUE = True
DEFAULT_NOTIFY_SPARES_EMPTY = True