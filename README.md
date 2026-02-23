# Badge Chess

A single-player chess game for the [BeagleBadge](https://www.beagleboard.org/boards/beaglebadge), powered by the [Sunfish](https://github.com/thomasahle/sunfish) chess engine running on MicroPython with an [LVGL](https://lvgl.io/) UI. The game runs entirely offline on the badge hardware.

## Background

This project is a port of the Sunfish chess engine — a compact, pure-Python chess engine — adapted for microcontroller use. It was originally ported to MicroPython for the Pimoroni Badger 2040 by Quan Lin and later modified by Jerzy Glowacki. This version has been further adapted to run on the BeagleBadge using LVGL for display rendering.

## Deployment

No build step is required. Copy `chess.py` to the BeagleBadge running MicroPython and it will run as part of the badge application framework.

## Credits

- **Sunfish chess engine**: [Thomas Ahle](https://github.com/thomasahle/sunfish)
- **Original MicroPython port (Badger 2040)**: Quan Lin
- **Badger 2040 modifications**: Jerzy Glowacki
- **BeagleBadge LVGL port**: Yogesh Hegde

## License

The source code is licensed under the [GNU General Public License v3.0](LICENSE).

Chess piece images in the `assets/chess/` folder are from [Green Chess](https://greenchess.net/info.php?item=downloads), used under the [Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)](https://creativecommons.org/licenses/by-sa/3.0/) license. See [`assets/chess/LICENSE`](assets/chess/LICENSE) for details.
