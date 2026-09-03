# Maintaining the Arches Software Directory

This document is for repository maintainers reviewing community-submitted pull requests.

---

## PR review checklist

Before merging any manifest PR, verify the following:

### Automated checks (must all pass)

CI runs automatically on every PR. Do not merge until all checks are green:

- [ ] **Schema validation** — YAML is valid and all required fields are present and typed correctly
- [ ] **URL resolution** — `repository` and `docs` (if present) return HTTP 200
- [ ] **SPDX license** — `license` field is a recognized SPDX identifier
- [ ] **PyPI presence** — `pypi` field (if present) resolves to a real package on pypi.org

### Manual review

- [ ] **`summary` is accurate** — one sentence, describes what the package actually does, ≤140 chars
- [ ] **`kind` is correct** — `extension` (standalone feature), `application` (domain composition), `tool` (supplements or supports Arches but is not installed as part of an Arches project), or `package` (a repo of Resource Models, Controlled Lists, Ontologies, and/or example business data for loading into Arches)
- [ ] **`arches_versions` is plausible** — matches what the package's own `pyproject.toml` declares; not so broad it misleads users
- [ ] **`status` is honest** — `planning` for not-yet-usable work, `experimental` for rough or untested-at-scale code, `alpha` for feature-incomplete but installable releases, `beta` for feature-complete releases still stabilizing, `stable` only for production-ready packages, `maintenance` for items that still work but are no longer developed
- [ ] **`tags` are useful** — lowercase, hyphen-separated, relevant to search; no spam tags
- [ ] **No duplicate** — check `packages/` for an existing manifest with the same name or PyPI package
- [ ] **Open-source licence** — the `license` is an accepted open-source licence (e.g. AGPL-3.0-or-later); proprietary or source-available-only licences are not eligible
- [ ] **`name` is specific** — succinct while conveying the purpose or function of the item, and not claiming a broad or generic namespace where a more specific name would do (prefer `arches-zod-validation` over `arches-validation`)
- [ ] **Item exists** — the `repository` URL points to a real, accessible repository containing the code or data the manifest describes

### Red flags (request changes or close)

- Repository is private or returns 404
- Repository has no code or data (empty repo, placeholder)
- `summary` is promotional copy rather than a factual description
- `status: stable` for a package on PyPI with a pre-release version (0.x.y, alpha, beta)
- No Arches dependency or Arches-specific content visible in the repository
- `license` is proprietary or otherwise not open source

---

## Merge process

1. Ensure all automated CI checks pass
2. Complete the manual review checklist above
3. Approve the PR and merge using **Squash and merge**
4. The site build workflow will trigger automatically and deploy within a few minutes

---

## Adding a maintainer

Edit `.github/CODEOWNERS` to add a GitHub username to the `packages/` line. Maintainers receive review requests on every new manifest PR.

---

## Deprecating or removing entries

Authors are responsible for keeping their own manifest metadata current. If an entry appears abandoned, incompatible with all current Arches versions, or has outdated or inaccurate metadata:

1. Change `status` to `maintenance` in the manifest (prefer this for items that still work but are no longer developed)
2. Remove the manifest file if the repository is deleted, the item causes harm to users who install it, or the metadata is inaccurate and the author does not respond to a request to correct it

Open a PR with a brief explanation in the description. Any maintainer can merge deprecation/removal PRs without a second review.

The Getty Conservation Institute, as sponsor of the Arches Project, retains editorial control over this directory.
