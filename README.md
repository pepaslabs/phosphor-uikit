# UIKit support for Phosphor icons

If you haven't yet migrated to SwiftUI, you may prefer to stick with PNG's (rather than SVG's) for your Xcode [asset catalogs](https://developer.apple.com/documentation/xcode/managing-assets-with-asset-catalogs).

`phosphor-uikit.py` is a script which uses [Phosphor icons](https://phosphoricons.com/) to generate PNG-based asset catalogs for Xcode based on JSON configuration files.


## Demo

![](media/screenshot.jpg)


## Installation

`phosphor-uikit.py` relies on [rsvg-convert](https://gitlab.gnome.org/GNOME/librsvg/) to rasterize SVG files.  Install it with `brew install librsvg`.

`phosphor-uikit.py` itself has no Python dependencies.  Simply download and call it.


## Usage

```
$ ./phosphor-uikit.py --help
phosphor-uikit.py: generate PNG-based asset catalogs.
Usage:
  phosphor-uikit.py [--dry-run] config1.json config2.json ...
```


## JSON configuration files

See [Tutorial.json](examples/Tutorial.json)


## License

[MIT](https://opensource.org/license/mit)
