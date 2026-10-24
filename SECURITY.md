# Security and privacy

Do not post credentials, OAuth codes, cookies, API responses, account identifiers,
screenshots of private dashboards, or unredacted logs in issues or pull requests.
Report suspected sensitive exposure privately to ouckah@gmail.com without
including the credential value. If a credential was exposed, revoke/rotate it;
removing a file or rewriting history alone is not sufficient.

This project previews by default. `--upload` authorizes a real upload, and
`--privacy public` also requires `--confirm-public`. The offline demo needs no
credentials. The public repository must not contain production account secrets.

`.gitignore` is a convenience, not a security boundary. `check_public.py` blocks
unapproved release files and a small set of risky patterns. It is not a complete
secret detector. Run a maintained scanner such as Gitleaks locally before each
release and inspect the exact diff. Neither tool can guarantee absence of leaks.

Do not enable secret-bearing jobs for forks or use `pull_request_target` to run
contributor code. Review and pin any version used by a separate private runner.
Library-level exceptions may contain provider details; the command-line entry
point suppresses them. Keep runtime logs private even when metadata is disabled.
