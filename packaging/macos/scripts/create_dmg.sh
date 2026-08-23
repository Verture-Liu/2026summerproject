#!/bin/zsh
set -euo pipefail

APP="${1:?usage: create_dmg.sh /path/to/PaleoRigor.app /path/to/output.dmg}"
OUTPUT="${2:?usage: create_dmg.sh /path/to/PaleoRigor.app /path/to/output.dmg}"
STAGING="$(/usr/bin/mktemp -d /tmp/paleorigor-dmg.XXXXXX)"
trap '/bin/rm -rf "$STAGING"' EXIT

/usr/bin/ditto "$APP" "$STAGING/PaleoRigor.app"
/bin/ln -s /Applications "$STAGING/Applications"
/bin/mkdir -p "${OUTPUT:h}"
/bin/rm -f "$OUTPUT"
hdiutil create \
  -volname "PaleoRigor" \
  -srcfolder "$STAGING" \
  -format UDZO \
  -imagekey zlib-level=9 \
  -ov \
  "$OUTPUT"

echo "Created $OUTPUT"
