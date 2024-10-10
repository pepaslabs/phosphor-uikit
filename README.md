# UIKit support for Phosphor icons

If you haven't yet migrated to SwiftUI, you may prefer to stick with PNG's (rather than SVG's) for your Xcode asset catalogs.

`phosphor-uikit.py` is a script which uses [Phosphor icons](https://phosphoricons.com/) to generates PNG-based asset catalogs for Xcode based on JSON configuration files.

## Demo

```
$ cat > Icons.json << EOF
> [
>     "icons for the tab bar",
>     [
>         "house", "book", "play",
>         25, "regular"
>     ]
> ]
> EOF
$ ./phosphor-uikit.py Icons.json 
⚙️  Creating 📁 Icons.xcassets
⚙️  Creating 📄 Icons.xcassets/Contents.json
⚙️  Creating 📁 Icons.xcassets/book.25.regular.imageset
⚙️  Creating 📁 Icons.xcassets/house.25.regular.imageset
⚙️  Creating 📁 Icons.xcassets/play.25.regular.imageset
⚙️  Creating 📁 /Users/cell/.phosphor-uikit/svg-cache/assets/regular
🛜 Fetching 🏞️  https://raw.githubusercontent.com/phosphor-icons/core/refs/heads/main/assets/regular/book.svg
⚙️  Creating 🏞️  Icons.xcassets/book.25.regular.imageset/book.25.regular.png
⚙️  Creating 🏞️  Icons.xcassets/book.25.regular.imageset/book.25.regular@2x.png
⚙️  Creating 🏞️  Icons.xcassets/book.25.regular.imageset/book.25.regular@3x.png
⚙️  Creating 📄 Icons.xcassets/book.25.regular.imageset/Contents.json
🛜 Fetching 🏞️  https://raw.githubusercontent.com/phosphor-icons/core/refs/heads/main/assets/regular/house.svg
⚙️  Creating 🏞️  Icons.xcassets/house.25.regular.imageset/house.25.regular.png
⚙️  Creating 🏞️  Icons.xcassets/house.25.regular.imageset/house.25.regular@2x.png
⚙️  Creating 🏞️  Icons.xcassets/house.25.regular.imageset/house.25.regular@3x.png
⚙️  Creating 📄 Icons.xcassets/house.25.regular.imageset/Contents.json
🛜 Fetching 🏞️  https://raw.githubusercontent.com/phosphor-icons/core/refs/heads/main/assets/regular/play.svg
⚙️  Creating 🏞️  Icons.xcassets/play.25.regular.imageset/play.25.regular.png
⚙️  Creating 🏞️  Icons.xcassets/play.25.regular.imageset/play.25.regular@2x.png
⚙️  Creating 🏞️  Icons.xcassets/play.25.regular.imageset/play.25.regular@3x.png
⚙️  Creating 📄 Icons.xcassets/play.25.regular.imageset/Contents.json
```

## Installation

`phosphor-uikit.py` has no dependencies.  Simply download and use it.


## JSON configuration files

See [Tutorial.json](examples/Tutorial.json)

