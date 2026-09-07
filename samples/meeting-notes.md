# Sprint 12 Retro

Facilitator: **Alice Owusu**. Notes are *unedited* — cleaned up after import.

## What went well

- Permission checks moved into a single dependency, so every route inherits them
- Import pipeline landed a day early
- Autosave conflict message is honest instead of silently overwriting

## What did not

1. Docker build was slow until the layer order was fixed
2. Migration ran twice on a fresh database before the enum bug was found
3. Cross-site cookie behavior cost an afternoon

## Actions

- Ship the version-history panel next
- Write the import edge cases into the integration suite
