# PRD 00051 assumptions

## 1: Validate Unicode scalars in shared observation models

- Initial Tess assumed generic exception rejection and direct list equality; corrected to static ValueError and serialized payload comparisons during quality retries.
- The valid-control fixture assumed total_tokens remained unredacted for general event kinds; corrected without changing the existing credential policy.
- Ivan and the bounded fixture correction reported no assumptions.
