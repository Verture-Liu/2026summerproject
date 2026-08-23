#!/bin/zsh
set -euo pipefail

APP="${1:?usage: sign_development.sh /path/to/PaleoRigor.app}"

while IFS= read -r -d '' FILE; do
  if /usr/bin/file -b "$FILE" | /usr/bin/grep -q 'Mach-O'; then
    codesign --force --sign - "$FILE"
  fi
done < <(/usr/bin/find "$APP/Contents" -type f -print0)

codesign --force --sign - "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"
