# Search-only directory probe

Fresh local macOS/Python probe on a temporary mode-0111 directory, restored to 0700 and removed by TemporaryDirectory afterwards.

```
O_RDONLY open failed: errno 13
O_SEARCH open and fsync succeeded
O_EXEC open and fsync succeeded
O_EVTONLY open failed: errno 13
O_PATH unavailable
```

The probe exercises OS descriptor modes, not OVCAQ and not a code repair. It supplies an alternative to durable ownership bookkeeping for a later authorized fix; an OVCAQ regression check must still verify directory identity and retry/replay guarantees. No production files or workflow state were changed.

