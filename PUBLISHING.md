# Publication checklist

This directory is a fresh, allowlisted source export, not a clone or fork of the
production repository. Do not copy old commits, Git config, branches, tags,
issues, logs, artifacts, local `.env` files, or token files into it.

Release checklist (initial publication and subsequent updates):

1. Review `release-files.txt` and every listed file. New paths require an explicit
   manifest change. Keep demonstration data synthetic. Do not include production
   databases, account handles beyond the public brand, private endpoints, or assets.
2. Run tests, lint, the offline demo, and `python scripts/check_public.py` in a
   clean release directory. Run `gitleaks dir . --redact` as a separate local scan.
   After creating commits, also scan the new Git history with `gitleaks git . --redact`.
3. Preserve the MIT license and confirm redistribution rights for any new code
   or assets. Dependency licenses continue to apply to their respective packages.
4. Initialize a **new** Git repository. Configure its repository-local commit
   identity to use a GitHub noreply address or the approved public brand email,
   not a private inherited email. Inspect commit author and committer metadata.
5. Stage only manifest-listed files. Inspect `git diff --cached`, staged paths,
   and the scanner results. Never use `git push --mirror` from a private repo.
6. Publish approved changes only to `ouckah/reposter`. Do not change production
   repository visibility or copy production history into this repository.
7. Enable GitHub secret scanning/push protection where available, protect the
   default branch with reviews and required checks, and use minimal token access.
   Add no production secrets. Public workflows should only test synthetic inputs.

For updates, bring over selected code changes for review; do not automatically
mirror the private source. Test with mocks first. Live validation requires the
owner's credentials and explicit upload approval in a private environment.
