# Doubt Review: 00002-package-baseline-v1

## FIX

1. The personal-runtime baseline is stale and lacks an exact source revision:
   it records 1,428 Python-suite outcomes while the current clean source tree
   collects 1,438 tests. Refresh all baseline commands and record the source
   commit/tree identities.
2. `LOCAL_PACKAGING_TESTS` still exempts three files that are now committed,
   weakening the sdist committed-input assertion. Remove the exemption.

## VERIFY

None.

## KNOWN

None.

## Rubric

- D1: pass
- D2: pass
- D3: pass
- D4: pass
- D5: pass
