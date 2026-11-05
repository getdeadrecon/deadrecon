# Releasing DeadRecon

How a release is cut, and the one-time PyPI setup that makes the automated
publish work.

## How a release works

Releases are driven by a git tag. Pushing a tag matching `v*.*.*` triggers
[`.github/workflows/publish.yml`](../.github/workflows/publish.yml), which:

1. **Build** — builds the sdist + wheel and **verifies the tag matches the
   package version** (`deadrecon.__version__` must equal the tag minus its
   `v`). A mismatch fails the run.
2. **Publish** — uploads the artifacts to PyPI using an **API token** stored in
   the `PYPI_API_TOKEN` repo secret. (Trusted publishing via OIDC is a supported
   alternative — see below — but token auth is what's wired up today.)

> **Note:** the workflow at the *tag's* commit is what runs, so a change to
> `publish.yml` only affects **future** tags. To ship a release whose tag
> predates a publish-workflow fix, build + upload locally instead:
> `python -m build && twine upload -u __token__ dist/*`, and paste the token at the
> hidden prompt so it stays out of your shell history.

### Cutting a release

```bash
# 1. Bump the version in BOTH places (they must match the tag)
#    - deadrecon/__init__.py  → __version__ = "X.Y.Z"
#    - setup.py                   → version="X.Y.Z"
#    Also update the version in docs/index.html and the What's New section in README.md,
#    and the Tor BUNDLE_VERSION and hashes in deadrecon/core/tor_service.py if a
#    newer signed bundle is out.
# 2. Move CHANGELOG [Unreleased] → [X.Y.Z] — <date>, add a fresh [Unreleased]
# 3. Commit, merge to main, then tag main:
git tag -a vX.Y.Z <main-commit> -m "DeadRecon vX.Y.Z — <headline>"
git push origin vX.Y.Z
# 4. Publish a GitHub Release (the workflow does NOT create one):
gh release create vX.Y.Z --title "vX.Y.Z — <headline>" --notes-file notes.md --latest
```

---

## PyPI auth: API token (current setup)

The publish job authenticates with a project-scoped PyPI API token stored as the
`PYPI_API_TOKEN` **repo secret**:

1. On PyPI (as a project Owner), create a token scoped to `deadrecon`:
   **Account settings → API tokens → Add API token**.
2. Store it as a GitHub Actions secret:
   ```bash
   gh secret set PYPI_API_TOKEN --repo getdeadrecon/deadrecon
   ```
   Paste the token at the hidden prompt, so it stays out of your shell history.
3. `publish.yml` passes it as `password: ${{ secrets.PYPI_API_TOKEN }}` (with
   `attestations: false`, since attestations need OIDC).

Rotate the token from the PyPI token page and re-run step 2 to update the secret.

---

## Alternative: PyPI trusted publisher (OIDC)

This isn't set up today. Trusted publishing lets GitHub Actions authenticate to
PyPI via OIDC, so there is no API token to store or rotate. Switching also means
changing `publish.yml`: give the publish job `environment: pypi` and
`permissions: id-token: write`, and remove its `password` and `attestations: false`.

The trusted-publisher config on PyPI **must exactly match** this repo's
workflow:

| Field | Value |
|-------|-------|
| PyPI project name | `deadrecon` |
| Owner | `getdeadrecon` |
| Repository name | `deadrecon` |
| Workflow name | `publish.yml` &nbsp;*(filename only, not a path)* |
| Environment name | `pypi` |

### Steps

1. **Log in to PyPI** at <https://pypi.org> as an owner/maintainer of the
   `deadrecon` project.

2. **Open the project's publishing settings:**
   <https://pypi.org/manage/project/deadrecon/settings/publishing/>
   (Project → *Manage* → *Publishing*).

3. Under **"Add a new trusted publisher" → GitHub**, fill in exactly:
   - **Owner:** `getdeadrecon`
   - **Repository name:** `deadrecon`
   - **Workflow name:** `publish.yml`
   - **Environment name:** `pypi`

   Then **Add**.

   > **New/unclaimed project?** If `deadrecon` doesn't exist on PyPI yet,
   > use <https://pypi.org/manage/account/publishing/> to add a
   > **pending** publisher with the same four values — it becomes active and
   > claims the name on the first successful upload.

4. **Create the GitHub environment** so the workflow's `environment: pypi`
   resolves cleanly (and you can add protection rules):
   GitHub → repo **Settings → Environments → New environment → `pypi`**.
   Optionally require a reviewer or restrict it to tag pushes.
   *(No secrets are needed — OIDC replaces the token.)*

### Verify it works

Re-run the publish for a tag that already built successfully (artifacts are
retained), or cut a fresh patch release:

```bash
# Re-run only the failed jobs of a previous tag run:
gh run list --workflow=publish.yml --limit 1        # find the run id
gh run rerun <run-id> --failed

# …or re-trigger from scratch by re-pushing the tag:
git push origin :refs/tags/vX.Y.Z && git push origin vX.Y.Z
```

A green **Publish to PyPI** job and the new version live at
<https://pypi.org/project/deadrecon/> confirm success.

---

## Notes / gotchas

- **Version must match the tag** — the Build step enforces it; bump
  `__init__.py` *and* `setup.py` before tagging.
- **The PyPI page comes from the package.** It shows `README.md` as uploaded, and a
  published version's page can't be edited, so changing it takes a new release. Use
  absolute links in the README, because relative ones break on PyPI.
- **PyPI versions can't be re-uploaded**, even after deleting a file, so a broken
  release needs a new version number.
- **`v1.28.0` was tagged but never reached PyPI**, because the token was invalid.
- The workflow doesn't open a GitHub Release; create it with
  `gh release create` (see above).

---

## Troubleshooting the publish

Two failures we actually hit, and what each means.

### `invalid-publisher: valid token, but no corresponding publisher`

The OIDC token was minted but **no trusted publisher on PyPI matched** the
workflow's claims. The publish job hasn't been configured on PyPI yet, or one of
the four values is wrong. The log prints the claims it presented — they must
match the [setup table](#alternative-pypi-trusted-publisher-oidc) exactly:

- `sub: repo:getdeadrecon/deadrecon:environment:pypi`
- `workflow_ref: …/publish.yml@refs/tags/vX.Y.Z`
- `environment: pypi`

Double-check owner, repository, workflow **filename** (`publish.yml`, not a
path), and environment name (`pypi`).

### `403 … OIDC scoped token is not valid for project 'deadrecon'`

Auth *succeeded* (a publisher matched) but the upload was refused. This is the
**pending-vs-project** gotcha: the publisher was added as a **pending publisher**
on the account page (<https://pypi.org/manage/account/publishing/>), which only
mints a token to **create a new project**. Because `deadrecon` **already
exists** on PyPI, that token isn't valid for it.

**Fix:** add the publisher on the **existing project** instead —
<https://pypi.org/manage/project/deadrecon/settings/publishing/> (you must
be a project *Owner*) — then remove the stray pending publisher. Re-run the
publish afterwards.
