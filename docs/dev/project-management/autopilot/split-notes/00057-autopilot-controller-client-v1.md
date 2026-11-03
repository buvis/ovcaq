# Split note: 00057-autopilot-controller-client-v1.md
planned=5 prd_tasks=8 expansion=0.62 reasons=module_drift

## src/ovcaq (UNLISTED)

- 1 Bound _run cleanup end to end (R2): src/ovcaq/workflow_client.py
- 2 Classify post-spawn abnormal exits as unknown outcome (R4, R7): src/ovcaq/workflow_client.py
- 3 Keep the actor file opaque in redaction (R5): src/ovcaq/workflow_client.py
- 4 One digest definition for contract_bundle_sha256 and strict bundle validation (R3, R6): src/ovcaq/workflow_client.py, src/ovcaq/config.py, src/ovcaq/cli.py

## tests/workflow_client (UNLISTED)

- 5 Run transport conformance against the fake controller and record the integration evidence: tests/workflow_client/test_contract_conformance.py, tests/workflow_client/test_controller_boundary.py

## . (listed)

- 5 Run transport conformance against the fake controller and record the integration evidence: CHANGELOG.md

## docs (listed)

- 4 One digest definition for contract_bundle_sha256 and strict bundle validation (R3, R6): docs/operations.md

## tests/fixtures/workflow (listed)

- 4 One digest definition for contract_bundle_sha256 and strict bundle validation (R3, R6): tests/fixtures/workflow/controller-v1.json

## tools (listed)

- 4 One digest definition for contract_bundle_sha256 and strict bundle validation (R3, R6): tools/autopilot-prerequisites
