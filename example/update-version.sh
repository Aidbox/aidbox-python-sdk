#!/bin/sh
# NOTE: This file is run before build! Never run it locally!

VERSION=$1

# Shared
sed -i -e "s/__version__ = .*/__version__ = '$VERSION'/g" app/version.py
