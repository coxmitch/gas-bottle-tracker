<p align="center">
  <img src="custom_components/gas_bottle_tracker/brand/logo.png" alt="Gas Bottle Tracker">
</p>

# Gas Bottle Tracker

A Home Assistant custom integration for **estimating** LPG gas bottle usage and remaining bottle life, storing bottle change history, tracking spare bottles, and sending push notifications.

> **Important:** Gas Bottle Tracker provides estimates only. It does **not** use physical sensors attached to your gas bottles and does **not** directly measure the amount of gas remaining.

## Features

- Gas bottle size and installation date
- Persistent bottle change history
- Average, median, shortest and longest bottle lifespan
- Estimated days remaining and replacement date
- Remaining percentage
- Average daily gas usage
- Spare bottle tracking
- New bottle and spare bottle services
- Configurable mobile push notifications
- Warning, critical, overdue and spare-empty notifications
- Home Assistant service icons
- Local integration branding
- Companion Lovelace card

## Gas Bottle Tracker Card

The **Gas Bottle Tracker Card** is the companion Lovelace card for this integration.

![Gas Bottle Tracker Card](GBT_Card%20Image.png)

It provides a visual dashboard card showing:

- Current bottle status
- Days remaining
- Bottle age
- Average lifespan
- Estimated next change
- Spare bottle count
- Bottle level graphic
- New Bottle controls
- Add/remove spare bottle controls

### Card Repository

[**Gas Bottle Tracker Card**](https://github.com/coxmitch/gas-bottle-tracker-card)

The card can be installed through HACS under:

**HACS → Frontend → Custom repositories**

Repository:

`https://github.com/coxmitch/gas-bottle-tracker-card`

Category:

`Dashboard`

The integration and card are designed to work together.

## Installation

### HACS

Add this repository as a custom repository in HACS:

Repository:

`https://github.com/coxmitch/gas-bottle-tracker`

Category:

`Integration`

Then install **Gas Bottle Tracker** and restart Home Assistant.

### Install the Companion Card

Install the companion:

[**Gas Bottle Tracker Card**](https://github.com/coxmitch/gas-bottle-tracker-card)

through HACS:

**HACS → Frontend → Custom repositories**

Repository:

`https://github.com/coxmitch/gas-bottle-tracker-card`

Category:

`Dashboard`

Then add the card to your Home Assistant dashboard.

### Manual

Copy the:

`custom_components/gas_bottle_tracker`

directory into your Home Assistant:

`config/custom_components`

directory and restart Home Assistant.

## Setup

Go to:

**Settings → Devices & services → Add Integration**

and search for **Gas Bottle Tracker**.

Configure:

- Bottle name
- Bottle size
- Current bottle change date
- Spare bottles
- Previous bottle history
- Notification devices and settings

Notification settings are available through the integration's **Options** menu.

## Services

- `gas_bottle_tracker.new_bottle`
- `gas_bottle_tracker.add_spare`
- `gas_bottle_tracker.remove_spare`
- `gas_bottle_tracker.test_notification`
- `gas_bottle_tracker.check_notifications`

## Important: Estimate Only

Gas Bottle Tracker provides **estimated gas bottle usage and remaining life only**.

It does **not**:

- Measure the actual gas level inside your bottle
- Use a physical gas bottle sensor
- Detect gas leaks
- Measure gas pressure
- Provide a gas safety alarm

Estimates are calculated from your recorded bottle change history and the configured bottle size. The accuracy of the estimate depends on having accurate and sufficient bottle change history.

Gas Bottle Tracker should **not be relied upon as a safety device, gas leak detector, gas level monitor, or replacement for physically checking your gas supply**.

## Companion Card

The card is maintained separately from the integration so it can be updated independently.

[**View / Install Gas Bottle Tracker Card →**](https://github.com/coxmitch/gas-bottle-tracker-card)

## License

MIT
