# Agent context

@REFACTOR.md

This folder is a git-tracked mirror of `~/work` on the build machine (`ssh no-limit-2026-build`),
in the layout above. The build machine stays the place to work; the mirror is pulled down at
checkpoints with the `rsync` command in `docs/PROJECT.md` ("Where things live") and leaves out
venvs, files over 5 MB and the `first_bot` backup. Only the machine has `starter-kit/` (needed for
`poker-agent pack/play/check`) and the temporary compatibility symlinks. The API key, and so
`analysis/fetch_history.py` and submissions, live on this Mac.
