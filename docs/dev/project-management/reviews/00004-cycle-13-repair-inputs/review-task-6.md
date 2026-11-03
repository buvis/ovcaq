CLOSURE | resolved | "B4: ORIGIN_CHECK.installed_origins asserts in-child (sys.prefix, site-packages) what every consumer re-asserts test-side through _assert_installed against installed.root; the in-child asserts are redundant" | prefix binding and both `assert path.is_relative_to(prefix)` / `assert "site-packages" in path.parts` lines removed from tests/packaging/rework_12_scripts.py; filename and "ovcaq" package-presence guards retained.

NO FINDINGS
