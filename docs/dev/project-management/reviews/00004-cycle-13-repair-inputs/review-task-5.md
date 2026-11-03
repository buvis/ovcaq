CLOSURE | resolved | B3: _assert_retry_error hedges: the else branch (any nonzero code with "retry" anywhere in the JSON) is unreachable in the overlap scenario ... keeps the pre-fix loose assertion alive, so a changed code or message still passes | else branch removed; helper now asserts `result.returncode == 2`, `error["code"] == "state_io"`, and `error["message"] == f"publication busy; retry: {report_path}"` unconditionally

NO FINDINGS
