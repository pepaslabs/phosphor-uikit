#!/usr/bin/env python3

# Rasterize Phosphor SVG icons as PNG-based asset catalogs for use in UIKit projects.
# See https://github.com/pepaslabs/phosphor-uikit
# See https://phosphoricons.com

import os
import sys
import json

# Globals:

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
    if config_fname[-5:] != ".json":
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
# Returns a dict of icon name to set of style-size tuples:
# { "person": { (regular,44), (bold,44) } }
def parse_icon_groups(config, config_fname):
    icon_groups_dict = {}
    for group in config:
        if type(group) is not list:
            continue
        group_icon_names = set()
        group_styles = set()
        group_sizes = set()
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
                sys.stderr.write("❌ Error: %s: unexpected value '%s'.\n" % (config_fname, word))
                sys.exit(1)
        if len(group_styles) == 0:
            group_styles = default_styles.copy()
        if len(group_sizes) == 0:
            group_sizes = default_sizes.copy()
        # Make a set of all of the (style, size) pairs:
        style_size_set = set()
        for style in group_styles:
            for size in group_sizes:
                t = (style, size)
                style_size_set.add(t)
        # Union the set with any existint set:
        for icon_name in group_icon_names:
            if icon_name in icon_groups_dict:
                style_size_set = style_size_set.union(icon_groups_dict[icon_name])
            icon_groups_dict[icon_name] = style_size_set
    return icon_groups_dict


# Generate or update an asset catalog.
def update_asset_catalog(catalog_dname, icon_groups_dict):
    # Ensure the .xcassets director exists.
    if not os.path.exists(catalog_dname):
        os.mkdir(catalog_dname)
    # Ensure the top-level Contents.json exists.
    contents_fname = catalog_dname + "/Contents.json"
    if not os.path.exists(contents_fname):
        d = {"info": {"author": "xcode", "version": 1}}
        j = json.dumps(d, sort_keys=True, indent=4, separators=(',', ': ')) + "\n"
        with open(contents_fname, "w+") as fd:
            fd.write(j)
    # generate a set of all of the filenames which should be present.
    expected_filenames = set()
    for icon_name, style_size_tuples in icon_groups_dict.items():
        for (style, size) in style_size_tuples:
            fname1 = "%s.%s.%s"


# Load and process a JSON config file.
def process_config_fname(config_fname):
    config = load_config_fname(config_fname)
    options = parse_options(config, config_fname)
    icon_groups_dict = parse_icon_groups(config, config_fname)
    catalog_dname = config_fname[:-5] + ".xcassets"
    update_asset_catalog(catalog_dname, icon_groups_dict)


if __name__ == "__main__":
    # Treat the command line arguments as a json config files.
    config_fnames = sys.argv[1:]

    for config_fname in config_fnames:
        process_config_fname(config_fname)
