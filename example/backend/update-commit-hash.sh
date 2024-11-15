#!/bin/sh
# NOTE: This file is run before build! Never run it locally!

BUILD_COMMIT_HASH=$CI_COMMIT_SHORT_SHA

# Shared
sed -i -e "s/__build_commit_hash__ = .*/__build_commit_hash__ = '$BUILD_COMMIT_HASH'/g" app/version.py