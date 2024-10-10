#!/usr/bin/env python3

# Rasterize Phosphor SVG icons as PNG-based asset catalogs for use in UIKit projects.
# See https://github.com/pepaslabs/phosphor-uikit
# See https://phosphoricons.com

import os
import sys
import json
import shutil

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


# Load a JSON config file.
def load_config_fname(config_fname):
    if not config_fname.endswith(".json"):
        sys.stderr.write("❌ Error: config file does not have suffix '.json': %s\n" % config_fname)
        sys.exit(1)
    # Try to open the file.
    try:
        fd = open(config_fname)
    except Exception as e:
        sys.stderr.write("❌ Error: unable to open file '%s': %s\n" % (config_fname, repr(e)))
        sys.exit(1)
    # Try to deserialize the file.
    try:
        config = json.load(fd)
        fd.close()
    except Exception as e:
        sys.stderr.write("❌ Error: unable to load file '%s': %s\n" % (config_fname, repr(e)))
        sys.exit(1)
    # The top-level JSON element must be an array.
    if type(config) is not list:
        sys.stderr.write("❌ Error: %s: top-level JSON element must be an array.\n" % config_fname)
        sys.exit(1)
    return config


# Parse all of the options from the config object.
def parse_options(config, config_fname):
    # First, look for config options.
    options = default_options.copy()
    for e in config:
        if type(e) is dict:
            for k, v in e.items():
                # Is this a valid option name?
                if k not in valid_options:
                    sys.stderr.write("❌ Error: %s: unknown option name '%s'.\n" % (config_fname, k))
                    sys.exit(1)
                options[k] = v
    # Validate the config options.
    for k, v in options.items():
        if k == "renderer":
            if v not in valid_renderers:
                    sys.stderr.write("❌ Error: %s: unknown renderer '%s'.\n" % (config_fname, v))
                    sys.exit(1)
    return options


# Parse out all of the icon groups from the config object.
# Returns a set of (icon name, size, style) triples.:
# { ("person",44,"regular"), ("person",44,"bold") }
def parse_icon_groups(config, config_fname):
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
                sys.stderr.write("❌ Error: %s: unexpected value '%s'.\n" % (config_fname, word))
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
def make_imageset_contents_json():
    pass


# Generate a .xcassets Contents.json file.
# An example:
# {
#   "info" : {
#     "author" : "xcode",
#     "version" : 1
#   }
# }
def make_xcasset_contents_json(catalog_dname):
    # Ensure the top-level Contents.json exists.
    fpath = catalog_dname + "/Contents.json"
    if not os.path.exists(fpath):
        d = {"info": {"author": "xcode", "version": 1}}
        j = json.dumps(d, sort_keys=True, indent=4, separators=(',', ': ')) + "\n"
        sys.stdout.write("⚙️  Creating 📄 %s\n" % fpath)
        if not flags["--dry-run"]:
            with open(fpath, "w+") as fd:
                fd.write(j)


# Generate or update an asset catalog.
def update_asset_catalog(catalog_dname, icons_set):
    # Ensure the .xcassets directory exists.
    if not os.path.exists(catalog_dname):
        sys.stdout.write("⚙️  Creating 📁 %s\n" % catalog_dname)
        if not flags["--dry-run"]:
            os.mkdir(catalog_dname)
    # Ensure the top-level Contents.json exists.
    make_xcasset_contents_json(catalog_dname)
    # First, reconcile the .imageset directories.
    existing_imageset_dnames = set()
    if os.path.exists(catalog_dname):
        for dname in os.listdir(catalog_dname):
            dpath = os.path.join(catalog_dname, dname)
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
    for dname in imagesets_to_delete:
        dpath = os.path.join(catalog_dname, dname)
        sys.stdout.write("♻️  Deleting 📁 %s\n" % dpath)
        if not flags["--dry-run"]:
            shutil.rmtree(dpath)
    for dname in imagesets_to_create:
        dpath = os.path.join(catalog_dname, dname)
        sys.stdout.write("⚙️  Creating 📁 %s\n" % dpath)
        if not flags["--dry-run"]:
            os.mkdir(dpath)
    # Next, reconcile the png's within each imageset.
    for (name, size, style) in icons_set:
        existing_png_fnames = set()
        imageset_dname = "%s.%s.%s.imageset" % (name, size, style)
        dpath = os.path.join(catalog_dname, imageset_dname)
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
        for fname in pngs_to_delete:
            fpath = os.path.join(dpath, fname)
            sys.stdout.write("♻️  Deleting 🏞️  %s\n" % fpath)
            if not flags["--dry-run"]:
                os.remove(fpath)
        for fname in pngs_to_create:
            fpath = os.path.join(dpath, fname)
            sys.stdout.write("⚙️  Creating 🏞️  %s\n" % fpath)
            if not flags["--dry-run"]:
                os.open(fpath, "w+").close()


# Load and process a JSON config file.
def process_config_fname(config_fname):
    config = load_config_fname(config_fname)
    options = parse_options(config, config_fname)
    icons_set = parse_icon_groups(config, config_fname)
    catalog_dname = config_fname[:-(len(".json"))] + ".xcassets"
    update_asset_catalog(catalog_dname, icons_set)


def usage(fd):
    if fd != sys.stderr:
        fd.write("phosphor-uikit.py: generate PNG-based asset catalogs.\n")
    fd.write("Usage:\n")
    fd.write("  phosphor-uikit.py [--dry-run] config1.json config2.json ...\n")


if __name__ == "__main__":
    # Parse the command line flags.
    config_fnames = []
    for word in sys.argv[1:]:
        if word == "--dry-run":
            flags["--dry-run"] = True
        elif word == "--help":
            usage(sys.stdout)
            sys.exit(0)
        elif word.endswith(".json"):
            config_fnames += [word]
        else:
            sys.stderr.write("❌ Error: unrecognized argument '%s'.\n" % word)
            usage(sys.stderr)
            sys.exit(1)

    if len(config_fnames) == 0:
        sys.stderr.write("❌ Error: no config file arguments given.\n")
        usage(sys.stderr)
        sys.exit(1)

    for config_fname in config_fnames:
        process_config_fname(config_fname)
