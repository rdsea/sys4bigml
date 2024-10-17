#!/bin/bash

VERSION_TO_INSTALL="0.3.10" # The version want to install

# Find Dockerfile in all subdirectories
find . -name Dockerfile -print0 | while IFS= read -r -d '' file; do
  echo "Updating version in $file"
  sed -i "s/qoa4ml==0.3.3/qoa4ml==$VERSION_TO_INSTALL/g" "$file"
done
