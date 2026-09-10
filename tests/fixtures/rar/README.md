# RAR reference fixtures

These small archives contain generated test data, not patient information.

- `test_rar.rar`, `test_rar_pwd.rar`, `test_corrupted.rar`: from [unrar2-cffi 0.5.0](https://pypi.org/project/unrar2-cffi/0.5.0/) source distribution, `tests/`. Apache 2.0 license is included as `UNRAR2-CFFI-LICENSE`. The first fixture includes genuine RAR4 compressed data; the other two exercise encryption and CRC failure.
- `rar5-compressed.rar`, `rar5-solid.rar`: decoded from [libarchive v3.8.5](https://github.com/libarchive/libarchive/tree/v3.8.5/libarchive/test), `test_read_format_rar5_compressed.rar.uu` and `test_read_format_rar5_multiple_files_solid.rar.uu`. License is included as `LIBARCHIVE-COPYING`.

RAR5 expected bytes follow libarchive's `test_read_format_rar5.c` / `generate_testdata()`: each little-endian uint32 is `max(0, k*k - 3*k + 1 + magic)` for one-based `k`. The compressed fixture has 1200 bytes with magic 0; the solid archive contains four 4096-byte files with magic 1 through 4.

Malformed-path and synthetic DICOM tests use `tests/rar_fixture.py`, a minimal stored RAR4 fixture writer. Actual compressed RAR4/5 decoding and solid dictionary continuity are verified against the upstream fixtures above.
