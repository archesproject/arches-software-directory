# arches-software-directory

The community directory for [Arches](https://www.archesproject.org/) applications, extensions, other tools, and packages. Browse the directory at **[software-directory.archesproject.org](https://software-directory.archesproject.org/)**.

Individual authors are responsible for [regularly updating](#updating-an-existing-manifest) the metadata for their own submitted items. Items with outdated or inaccurate information may be removed. The Getty Conservation Institute, as sponsor of the Arches Project, retains editorial control over this directory.

---

## What belongs here

| Kind            | Description                                        | Examples                                                       |
| --------------- | -------------------------------------------------- | -------------------------------------------------------------- |
| `extension`   | Adds functionality to any Arches installation      | arches-modular-reports, arches-querysets, arches-component-lab |
| `application` | A domain-specific composition of core + extensions | arches-lingo, arches-her, arches-addressing                    |
| `tool`        | A developer utility that supplements or supports Arches functionality but is not installed as part of an Arches project | arches-containers |
| `package`     | A package repo that includes some or all of the following for loading into Arches: Resource Models, Controlled Lists, Ontologies, Example Business Data | ogee |

The directory is **discovery-only** — code stays in the author's own repository and on PyPI. This repo holds only the metadata manifests.

---

## Submission Criteria

Contributors are invited to submit applications, extensions, other Arches-specific tools, and data model packages through a pull request via the button below. Contributors are encouraged to share works-in-progress in order to provide visibility and promote alignment early in the development process. Although submissions of any status will be considered, there are [required fields of information](#2-create-a-manifest-file). Regardless of authorship or code location, all submitted solutions must be shared under an appropriate open-source licence (e.g., AGPL3).

---

## Installation

Clone the arches-software-directory repo and checkout the relevant branch:

If installing for development checkout the `development` branch.    
If installing for package submission checkout the `main` branch.

### If installing for development

With a virtual environment activated, navigate to the `arches-software-directory` directory from your terminal and run:
```
pip install -e .
```

To populate the Arches Software Directory with package data from the manifest YAML files, run:
```
python scripts/enrich.py --packages-dir packages --output site/src/_data/packages.json
```

Change directory to `site/` and run eleventy:
```
npm run dev
```

---

## Submitting a package

### 1. Fork this repository

Click **Fork** in the top right of this page.

### 2. Create a manifest file

Create a new file at `packages/<your-package-name>.yaml`. Use the schema below and the existing manifests in `packages/` as examples.

```yaml
name: your-package-name         # PyPI name or unique slug (lowercase, hyphens)
kind: application               # extension | application | tool | package
summary: One sentence that explains what your package does.
repository: https://github.com/you/your-package
pypi: your-package-name         # omit if not on PyPI
docs: https://your-docs-url     # omit if no docs site
license: AGPL-3.0-or-later      # SPDX identifier
maintainers:
  - your-github-username
arches_versions: ">=8.1,<9.0"  # PEP 440 version specifier
domains:
  - cultural-heritage           # high-level subject area(s)
tags:
  - your-tag                    # lowercase, hyphen-separated
status: planning            # planning | experimental | alpha | beta | stable | maintenance
```

**Full schema reference:** [`schema.json`](schema.json)

### 3. Open a pull request

Open a PR from your fork targeting `main`. The automated CI will:

- Validate your YAML against the manifest schema
- Check that `repository` and `docs` URLs resolve (HTTP 200)
- Verify the `license` value is a recognized SPDX identifier
- Confirm `pypi` (if provided) resolves on PyPI

PRs that pass CI will be reviewed by a maintainer within a few days. See [MAINTAINING.md](MAINTAINING.md) for the review checklist.

### A note on names

As an open-source community, contributors create their own software item names. Please choose names that are succinct while conveying the specific purpose or function of the software item. And please be conscientious of claiming a broad or generic namespace when a more specific name is appropriate. For example, "arches-zod-validation" is a better name than "arches-validation," which could apply to a range of software items.

---

## Updating an existing manifest

Open a PR that modifies the relevant `packages/<name>.yaml` file. The same CI validation applies.

---

## Removing a package

Open a PR that deletes the manifest file. Include a brief reason in the PR description (e.g. "package is abandoned and no longer compatible with current Arches versions").

---

## Manifest schema

See [`schema.json`](schema.json) for the full JSON Schema definition. Key fields:

| Field               | Required | Description                                                |
| ------------------- | -------- | ---------------------------------------------------------- |
| `name`            | Yes      | Package slug (matches PyPI name if published)              |
| `kind`            | Yes      | `extension`, `application`, `tool`, or `package`   |
| `summary`         | Yes      | One-sentence description, 140 chars max                    |
| `repository`      | Yes      | Source repository URL                                      |
| `license`         | Yes      | SPDX license identifier                                    |
| `maintainers`     | Yes      | GitHub usernames/orgs                                      |
| `arches_versions` | Yes      | PEP 440 specifier for compatible Arches versions           |
| `status`          | Yes      | `planning`, `experimental`, `alpha`, `beta`, `stable`, or `maintenance` |
| `pypi`            | No       | PyPI package name                                          |
| `docs`            | No       | Documentation URL                                          |
| `domains`         | No       | High-level subject domains                                 |
| `tags`            | No       | Freeform search tags (lowercase, hyphen-separated)         |

---

## Local validation

You can validate your manifest locally before opening a PR:

```bash
pip install check-jsonschema
check-jsonschema --schemafile schema.json packages/your-package-name.yaml
```

---




---

## License

Manifest data in this repository is released under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) — no rights reserved. Each listed package carries its own license.
