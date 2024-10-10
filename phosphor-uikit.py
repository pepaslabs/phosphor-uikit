#!/usr/bin/env python3

# Rasterize Phosphor SVG icons as PNG-based asset catalogs for use in UIKit projects.
# See https://github.com/pepaslabs/phosphor-uikit
# See https://phosphoricons.com

import os
import sys
import json
import shutil
import urllib.request
import subprocess


# Globals:

flags = {
    "--dry-run": False
}

valid_styles = set(["bold", "duotone", "fill", "light", "regular", "thin"])

default_styles = set(["regular"])
default_sizes = set([44])

default_options = {
    "renderer": "rsvg"
}
valid_options = list(default_options.keys()) + ["phosphor_core_path"]
valid_renderers = ["rsvg", "inkscape"]

did_warn_bad_phosphor_core_path = False


# Load a JSON config file.
def load_catalog_fpath(catalog_fpath):
    if not catalog_fpath.endswith(".json"):
        sys.stderr.write("❌ Error: config file does not have suffix '.json': %s\n" % catalog_fpath)
        sys.exit(1)
    # Try to open the file.
    try:
        fd = open(catalog_fpath)
    except Exception as e:
        sys.stderr.write("❌ Error: unable to open file '%s': %s\n" % (catalog_fpath, repr(e)))
        sys.exit(1)
    # Try to deserialize the file.
    try:
        config = json.load(fd)
        fd.close()
    except Exception as e:
        sys.stderr.write("❌ Error: unable to load file '%s': %s\n" % (catalog_fpath, repr(e)))
        sys.exit(1)
    # The top-level JSON element must be an array.
    if type(config) is not list:
        sys.stderr.write("❌ Error: %s: top-level JSON element must be an array.\n" % catalog_fpath)
        sys.exit(1)
    return config


# Parse all of the options from the config object.
def parse_options(config, catalog_fpath):
    # First, look for config options.
    options = default_options.copy()
    for e in config:
        if type(e) is dict:
            for k, v in e.items():
                # Is this a valid option name?
                if k not in valid_options:
                    sys.stderr.write("❌ Error: %s: unknown option name '%s'.\n" % (catalog_fpath, k))
                    sys.exit(1)
                options[k] = v
    # Validate the config options.
    for k, v in options.items():
        if k == "renderer":
            if v not in valid_renderers:
                    sys.stderr.write("❌ Error: %s: unknown renderer '%s'.\n" % (catalog_fpath, v))
                    sys.exit(1)
    return options


# Parse out all of the icon groups from the config object.
# Returns a set of (icon name, size, style) triples.:
# { ("person",44,"regular"), ("person",44,"bold") }
def parse_icon_groups(config, catalog_fpath):
    icons_set = set()
    for group in config:
        if type(group) is not list:
            # This is either a comment or a config option.  Skip.
            continue
        # Collect the names, sizes and styles in this group.
        group_icon_names = set()
        group_sizes = set()
        group_styles = set()
        for word in group:
            if type(word) is int:
                # This is a size.
                group_sizes.add(word)
            elif type(word) is str:
                if word in valid_styles:
                    # This is a style.
                    group_styles.add(word)
                else:
                    # This is an icon name.
                    group_icon_names.add(word)
            else:
                # Unrecognized junk in this group.
                sys.stderr.write("❌ Error: %s: unexpected value '%s'.\n" % (catalog_fpath, word))
                sys.exit(1)
        # If we didn't find any sizes or styles, use the defaults.
        if len(group_sizes) == 0:
            group_sizes = default_sizes.copy()
        if len(group_styles) == 0:
            group_styles = default_styles.copy()
        # Do the combinatorial explosion and add them to the set.
        for name in group_icon_names:
            for size in group_sizes:
                for style in group_styles:
                    triple = (name, size, style)
                    icons_set.add(triple)
    return icons_set


# Generate a .xcassets Contents.json file.
# An example:
# {
#   "info" : {
#     "author" : "xcode",
#     "version" : 1
#   }
# }
def make_xcasset_contents_json(catalog_dpath):
    # Ensure the top-level Contents.json exists.
    fpath = catalog_dpath + "/Contents.json"
    if not os.path.exists(fpath):
        d = {"info": {"author": "xcode", "version": 1}}
        j = json.dumps(d, sort_keys=True, indent=4, separators=(',', ': ')) + "\n"
        sys.stdout.write("⚙️  Creating 📄 %s\n" % fpath)
        if not flags["--dry-run"]:
            with open(fpath, "w+") as fd:
                fd.write(j)


# Generate a .imageset Contents.json file.
# An example:
# {
#   "images" : [
#     {
#       "filename" : "user.regular.44.png",
#       "idiom" : "universal",
#       "scale" : "1x"
#     },
#     {
#       "filename" : "user.regular.44@2x.png",
#       "idiom" : "universal",
#       "scale" : "2x"
#     },
#     {
#       "filename" : "user.regular.44@3x.png",
#       "idiom" : "universal",
#       "scale" : "3x"
#     }
#   ],
#   "info" : {
#     "author" : "xcode",
#     "version" : 1
#   }
# }
def make_imageset_contents_json(imageset_dpath, png_fnames):
    contents = {"info": {"author": "xcode", "version": 1}, "images": []}
    for png_fname in png_fnames:
        if "@3x" in png_fname:
            scale = "3x"
        elif "@2x" in png_fname:
            scale = "2x"
        else:
            scale = "1x"
        d = {
            "filename": png_fname,
            "idiom": "universal",
            "scale": scale
        }
        contents["images"].append(d)
    fpath = imageset_dpath + "/Contents.json"
    if not os.path.exists(fpath):
        j = json.dumps(contents, sort_keys=True, indent=4, separators=(',', ': ')) + "\n"
        sys.stdout.write("⚙️  Creating 📄 %s\n" % fpath)
        if not flags["--dry-run"]:
            with open(fpath, "w+") as fd:
                fd.write(j)


# Construct an SVG filename, given an icon name and style.
def svg_fname(name, style):
    if style == "regular":
        fname = "%s.svg" % name
    else:
        fname = "%s-%s.svg" % (name, style)
    return fname


# If we have a phosphor checkout, use that.
# If we have local HTTP cache, use that.
# Otherwise, fetch the SVG from github.
# In any case, return the path to the SVG file.
def get_svg_fpath(name, style, options):
    global did_warn_bad_phosphor_core_path
    fname = svg_fname(name, style)
    if "phosphor_core_path" in options and not did_warn_bad_phosphor_core_path:
        checkout_path = os.path.expanduser(options["phosphor_core_path"])
        dpath = checkout_path + "/assets/%s" % style
        fpath = "%s/%s" % (dpath, fname)
        if os.path.exists(fpath):
            return fpath
        else:
            if not did_warn_bad_phosphor_core_path:
                sys.stderr.write("⚠️ Warning: 'phosphor_core_path' supplied but SVG files not found, falling back to HTTP fetching.\n")
                did_warn_bad_phosphor_core_path = True
    # Local checkout didn't work, try HTTP cache.
    cache_path = os.path.expanduser("~/.phosphor-uikit/svg-cache")
    dpath = cache_path + "/assets/%s" % style
    fpath = "%s/%s" % (dpath, fname)
    if os.path.exists(fpath):
        return fpath
    # No HTTP cache, fetch the SVG and cache it.
    if not os.path.exists(dpath):
        sys.stdout.write("⚙️  Creating 📁 %s\n" % dpath)
        if not flags["--dry-run"]:
            os.makedirs(dpath, exist_ok=True)
    url = "https://raw.githubusercontent.com/phosphor-icons/core/refs/heads/main/assets/%s/%s" % (style, fname)
    sys.stdout.write("🛜 Fetching 🏞️  %s\n" % url)
    if not flags["--dry-run"]:
        urllib.request.urlretrieve(url, fpath)
    return fpath


# Rasterize a PNG, using the configured raster program.
def rasterize(name, size, style, png_fpath, options):
    resolution = size
    if "@2x" in png_fpath:
        resolution = size * 2
    elif "@3x" in png_fpath:
        resolution = size * 3
    svg_fpath = get_svg_fpath(name, style, options)
    rasterize_rsvg(name, style, resolution, svg_fpath, png_fpath, options)


# Rasterize a PNG, using librsvg.
def rasterize_rsvg(name, style, resolution, svg_fpath, png_fpath, options):
    cmd = "rsvg-convert"
    cmd += " --width=%s" % resolution
    cmd += " --height=%s" % resolution
    cmd += " --keep-aspect-ratio"
    cmd += " %s" % svg_fpath
    cmd += " > %s" % png_fpath
    sys.stdout.write("⚙️  Creating 🏞️  %s\n" % png_fpath)
    if not flags["--dry-run"]:
        try:
            subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            sys.stderr.write("❌ Error: rsvg-convert failed:\n")
            sys.stderr.write(e.output.decode())
            sys.exit(1)


# Generate or update an asset catalog.
def update_asset_catalog(catalog_dpath, icons_set, options):
    # Ensure the .xcassets directory exists.
    if not os.path.exists(catalog_dpath):
        sys.stdout.write("⚙️  Creating 📁 %s\n" % catalog_dpath)
        if not flags["--dry-run"]:
            os.mkdir(catalog_dpath)
    # Ensure the top-level Contents.json exists.
    make_xcasset_contents_json(catalog_dpath)
    # First, reconcile the .imageset directories.
    existing_imageset_dnames = set()
    if os.path.exists(catalog_dpath):
        for dname in os.listdir(catalog_dpath):
            dpath = os.path.join(catalog_dpath, dname)
            if dname.endswith(".imageset"):
                existing_imageset_dnames.add(dname)
    expected_imageset_dnames = set()
    for (name, size, style) in icons_set:
        imageset_dname = "%s.%s.%s.imageset" % (name, size, style)
        expected_imageset_dnames.add(imageset_dname)
    # Create the plan.
    imagesets_to_create = expected_imageset_dnames.difference(existing_imageset_dnames)
    imagesets_to_delete = existing_imageset_dnames.difference(expected_imageset_dnames)
    # Do the work.
    for dname in sorted(imagesets_to_delete):
        dpath = os.path.join(catalog_dpath, dname)
        sys.stdout.write("♻️  Deleting 📁 %s\n" % dpath)
        if not flags["--dry-run"]:
            shutil.rmtree(dpath)
    for dname in sorted(imagesets_to_create):
        dpath = os.path.join(catalog_dpath, dname)
        sys.stdout.write("⚙️  Creating 📁 %s\n" % dpath)
        if not flags["--dry-run"]:
            os.mkdir(dpath)
    # Next, reconcile the png's within each imageset.
    for (name, size, style) in sorted(icons_set):
        existing_png_fnames = set()
        imageset_dname = "%s.%s.%s.imageset" % (name, size, style)
        dpath = os.path.join(catalog_dpath, imageset_dname)
        if os.path.exists(dpath):
            for fname in os.listdir(dpath):
                if fname.endswith(".png"):
                    existing_png_fnames.add(fname)
        expected_png_fnames = set()
        fname1x = "%s.%s.%s.png" % (name, size, style)
        fname2x = "%s.%s.%s@2x.png" % (name, size, style)
        fname3x = "%s.%s.%s@3x.png" % (name, size, style)
        expected_png_fnames.update([fname1x, fname2x, fname3x])
        # Create the plan.
        pngs_to_create = expected_png_fnames.difference(existing_png_fnames)
        pngs_to_delete = existing_png_fnames.difference(expected_png_fnames)
        # Do the work.
        for fname in sorted(pngs_to_delete):
            fpath = os.path.join(dpath, fname)
            sys.stdout.write("♻️  Deleting 🏞️  %s\n" % fpath)
            if not flags["--dry-run"]:
                os.remove(fpath)
        for fname in sorted(pngs_to_create):
            fpath = os.path.join(dpath, fname)
            rasterize(name, size, style, fpath, options)
        make_imageset_contents_json(dpath, [fname1x, fname2x, fname3x])


# Load and process a JSON config file.
def process_catalog_fpath(catalog_fpath):
    config = load_catalog_fpath(catalog_fpath)
    options = parse_options(config, catalog_fpath)
    icons_set = parse_icon_groups(config, catalog_fpath)
    catalog_dpath = catalog_fpath[:-(len(".json"))] + ".xcassets"
    update_asset_catalog(catalog_dpath, icons_set, options)


def usage(fd):
    if fd != sys.stderr:
        fd.write("phosphor-uikit.py: generate PNG-based asset catalogs.\n")
    fd.write("Usage:\n")
    fd.write("  phosphor-uikit.py [--dry-run] config1.json config2.json ...\n")


if __name__ == "__main__":
    # Parse the command line flags.
    catalog_fpaths = []
    for word in sys.argv[1:]:
        if word == "--dry-run":
            flags["--dry-run"] = True
        elif word == "--help":
            usage(sys.stdout)
            sys.exit(0)
        elif word.endswith(".json"):
            catalog_fpaths += [word]
        else:
            sys.stderr.write("❌ Error: unrecognized argument '%s'.\n" % word)
            usage(sys.stderr)
            sys.exit(1)

    if len(catalog_fpaths) == 0:
        sys.stderr.write("❌ Error: no config file arguments given.\n")
        usage(sys.stderr)
        sys.exit(1)

    for catalog_fpath in catalog_fpaths:
        process_catalog_fpath(catalog_fpath)
