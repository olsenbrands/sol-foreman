# Existing runs and version changes

Do not swap this workflow into an active legacy v0.3 guarded program. Keep that
program on its pinned skill version and original guard semantics until its writers,
pending reviews and recovery state are reconciled. Preserve the old installation
and ledger; never reset attempts or translate state by renaming fields.

Use this workflow for new runs after that boundary. Existing required repository
guards remain binding, including original ownership and retry history. If a
project guard contradicts a proposed action, resolve the conflict explicitly
rather than bypassing it. A new skill version is not new authorization.

Before installing an update, inventory active runs and local modifications on
each machine. Preserve local patches separately, test their behavior, and make
an explicit incorporation or deferral decision. Do not overwrite a symlinked
development checkout as if it were an expendable installed copy.

## Operational upgrade boundary

1. Resolve the installed path/symlink, exact source revision, dirty modifications,
   and genuinely active runs on that machine. A leftover run directory alone is
   not proof of activity. If activity cannot be resolved, do not replace the path.
2. Preserve the exact old skill tree, including local patches and required helper
   dependencies, at an explicit versioned archive path outside skill autodiscovery
   (for example, a project-local `.foreman/skill-versions/sol-foreman-v0.3.0-patched/`).
   Record hashes and old link target. Do not overwrite a pre-existing archive.
3. At a reconciled safe checkpoint, bind any continuing legacy run's recorded
   helper/skill paths to that preserved version. Verify its ledger status and
   recovery operations still work there without resetting or migrating history.
   If safe rebinding is not supported, leave the installation unchanged until the
   run ends. Never silently redirect active helper calls to the new version.
4. Stage and validate the new standalone tree separately. Check rollback using a
   disposable link and fixture before changing the real installation. Replace only
   the validated install/link target, never the symlinked development checkout.
5. Read back the installed version/content and retain the old target and archive
   for rollback. A rollback is also a version transition: reconcile new-version
   writers first and do not feed new state to old guards.

These are operator requirements, not an implemented transactional installer or
guarantee of migration safety. Test the actual machine's transition before release.
