# HA-Periodic-Min-Max

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![Downloads][download-latest-shield]](Downloads)
[![License][license-shield]](LICENSE)
[![hacs][hacsbadge]][hacs]

# WORK IN PROGRESS
Do not use until there is a 1.x release, things are subject to breaking changes.  

Periodic Min Max Helpers for Home Assistant  

The helpers record the minimum or maximum of a sensor, until manually reset via the reset action.  

_Please :star: this repo if you find it useful_  
_If you want to show your support please_

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/yellow_img.png)](https://www.buymeacoffee.com/codechimp)

## Installation

### HACS

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=andrew-codechimp&repository=HA-Periodic-Min-Max&category=Integration)

Restart Home Assistant

In the HA UI go to "Configuration" -> "Devices & services" -> "Helpers" click "+" and search for "Periodic Min/Max"

### Manual Installation

<details>
<summary>Show detailed instructions</summary>

Installation via HACS is recommended, but a manual setup is supported.

1. Manually copy custom_components/periodic_min_max folder from latest release to custom_components folder in your config folder.
1. Restart Home Assistant.
1. In the HA UI go to "Configuration" -> "Devices & services" -> "Helpers" click "+" and search for "Periodic Min/Max"

</details>


### Translations
<details>
<summary>You can help by adding missing translations when you are a native speaker. Or add a complete new language when there is no language file available.</summary>

Periodic Min Max uses Crowdin to make contributing easy.

**Changing or adding to existing language**

First register and join the translation project

- If you don’t have a Crowdin account yet, create one at [https://crowdin.com](https://crowdin.com)
- Go to the [Periodic Min Max Crowdin project page](https://crowdin.com/project/periodic-min-max)
- Click Join.

Next translate a string

- Select the language you want to contribute to from the dashboard.
- Click Translate All.
- Find the string you want to edit, missing translation are marked red.
- Fill in or modify the translation and click Save.
- Repeat for other translations.

!!! info

    Periodic Min Max will automatically pull in latest changes to translations every day and create a Pull Request. After that is reviewed by a maintainer it will be included in the next release of Periodic Min Max.

**Adding a new language**

Create an [Issue](https://github.com/andrew-codechimp/HA-Periodic-Min-Max/issues/) requesting a new language. We will do the necessary work to add the new translation to the integration and Crowdin site, when it's ready for you to contribute we'll comment on the issue you raised.
</details>

---

[commits-shield]: https://img.shields.io/github/commit-activity/y/andrew-codechimp/HA-Periodic-Min-Max.svg?style=for-the-badge
[commits]: https://github.com/andrew-codechimp/HA-Periodic-Min-Max/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge
[exampleimg]: example.png
[license-shield]: https://img.shields.io/github/license/andrew-codechimp/HA-Periodic-Min-Max.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/andrew-codechimp/HA-Periodic-Min-Max.svg?style=for-the-badge
[releases]: https://github.com/andrew-codechimp/HA-Periodic-Min-Max/releases
[download-latest-shield]: https://img.shields.io/github/downloads/andrew-codechimp/HA-Periodic-Min-Max/latest/total?style=for-the-badge
