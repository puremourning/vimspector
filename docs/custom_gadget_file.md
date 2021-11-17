---
title: Configuration
---

This document describes how to use vimspector's `install_gadget.py` to install
custom debug adapters. This can be useful as a way to get an adapter working
that isn't officially supported by Vimspector, but otherwise can be made to work
by simply downloading the VScode extension into the gadget directory.

## Usage

```
./install_gadget.py --enable-custom=/path/to/a.json \
                    --enable-custom=/path/to/b.json`
```

This tells `install_gadget.py` to read `a.json` and `b.json` as _gadget
definitions_ and download/unpack the specified gadgets into the gadget dir, just
like the supported adapters.

## Gadget Definitions

A _gadget definition_ is a file containing a single JSON object definition,
describing the debug adapter and how to download and install it. This mechanism
is crude but can be effective.

The definition of the file format is
[on the wiki](https://github.com/puremourning/vimspector/wiki/languages).
