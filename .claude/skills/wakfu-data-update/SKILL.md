---
name: wakfu-data-update
description: Fetch the latest Wakfu game data (items, actions, equipmentItemTypes, itemProperties) from Ankama's official CDN and bump the project's DATA_VERSION. Triggers on "update wakfu data", "bump wakfu version", or reports of missing item icons.
---

Wakfu game data lives in `data/<version>/`, selected via `DATA_VERSION` in `settings.py`. Ankama publishes new versions periodically at `https://wakfu.cdn.ankama.com/gamedata/`.

## Steps

1. **Read current version** — grep `DATA_VERSION` in `settings.py`.

2. **Get live version** :
   ```
   curl -s https://wakfu.cdn.ankama.com/gamedata/config.json
   ```
   → returns `{"version": "1.X.Y.Z"}`. Extract with `jq -r .version` or similar.

3. **Compare**. If identical, tell the user "already up to date" and stop.

4. **Download the 4 files** for the new version into `data/<new_version>/` (create the dir):
   - `items.json` (~15 MB)
   - `actions.json`
   - `equipmentItemTypes.json`
   - `itemProperties.json`

   URL pattern: `https://wakfu.cdn.ankama.com/gamedata/<new_version>/<file>`.

   Save the **raw JSON as-is** — the app restructures it at load time in `wakutils.setupJson()`. Don't touch the format.

5. **Bump `DATA_VERSION`** in `settings.py` (single string replacement).

6. **Sanity check** — run the loader once to catch schema changes:
   ```
   python3 -c "import settings; from wakutils import setupJson; settings.initGlobal(); setupJson(); print(len(settings.ITEMS_DATA), 'items loaded')"
   ```
   Confirm the count is in the expected order of magnitude (~30k items).

7. **Warn about `data_overrides/item_pairings.json`** — item IDs there (Amakna/Brâkmar/Sufokia/Bonta épée+anneau pairs) may have changed. `wakutils.load_item_pairings()` silently drops stale groups, so verify the pairings still fire after update.

## Do not

- Restructure or transform the downloaded JSON — the raw Ankama format is what the app expects.
- Delete older `data/<version>/` folders — keep them as fallback until the new version is validated.
- Bump `DATA_VERSION` before all 4 files are on disk.
