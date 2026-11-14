**Unofficial build** of [WadaMesh](https://github.com/ALLFATHER-BV/wadamesh) (GPL-3.0) with one added feature: a **GPS city locator**. Built from the latest WadaMesh code (beta_105) by GitHub Actions; the source is this repository.

## What it does

- With a GPS fix, the radio checks every 10 seconds which city, town or community you are in, using official US Census boundaries stored on the SD card.
- Crossing into a new place pops up **"Now in Roseville"**, and the Home screen's top-left corner shows the place name instead of your node name.
- A new place has to be seen twice in a row (about 20 s), so GPS wobble on a boundary does not make it flicker.
- Works offline. Nothing is sent over the mesh; your position stays on the device.

Tested on all three devices below. Details: [CITY_LOCATOR.md](https://github.com/Languskhan/wadamesh/blob/main/CITY_LOCATOR.md).

## Downloads

| Device | Firmware |
| --- | --- |
| Heltec WiFi LoRa 32 V4-R8 + Expansion Kit V2 | `wadamesh-city-heltec-v4-r8-merged.bin` |
| LilyGo T-Deck Plus (needs GPS, so not the plain T-Deck) | `wadamesh-city-tdeck-merged.bin` |
| Elecrow ThinkNode M9 | `wadamesh-city-thinknode-m9-merged.bin` |

`-merged.bin` is the full image to flash at address **0x0**. The plain `.bin` files are app-only images (address 0x10000) for people who already know they want them.

City files: there is one for every US state, plus DC and Puerto Rico (full list at the bottom).
Pick the one for where you are and rename it to `cities.bin`. There is also
`cities-sacramento-foothills.bin`, a smaller file for the Sacramento area.

## Install

1. Back up anything important on the device first. Flashing does not erase your identity, contacts or settings, but a full **erase** does, so do not tick "Erase".
2. Flash the `-merged.bin` for your device at **0x0** with PlatformIO, `esptool.py`, or Espressif's [ESP Web Tool](https://espressif.github.io/esptool-js/) in Chrome or Edge.
3. Copy the city file to the SD card's top folder as `cities.bin`. On the ThinkNode M9 (internal card), upload it with the **Transfer** app to **Files (/transfer)** instead.
4. Restart, turn on GPS, and go outside. Within about a minute of a fix you should see "Now in …".

To go back, flash the official WadaMesh build from its web flasher.

## Notes

- Census-designated places (like Orangevale or Fair Oaks) are statistical areas, not legal city limits.
- Only one city file is used at a time. If you travel across states, swap the file and restart.
- Boundary data: US Census Bureau TIGER/Line 2024 (public domain). Firmware: WadaMesh by ALLFATHER-BV and contributors, GPL-3.0. This build is not affiliated with or supported by the WadaMesh project.
