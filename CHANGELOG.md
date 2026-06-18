<!--
SPDX-FileCopyrightText: Fondation RERO+
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Changelog

<!-- version list -->

## v2.0.1 (2026-06-18)

### Bug Fixes

- **bnf**: Silence expected 500 responses in debug log
  ([`d6f2cea`](https://github.com/rero/rero-invenio-thumbnails/commit/d6f2cea4796a5bd26a3f0a576bed496fa9979084))

### Build System

- Add semantic release shortcut commands
  ([`83b596e`](https://github.com/rero/rero-invenio-thumbnails/commit/83b596ea3360ffdf1c90769fda7cc82e60206970))

### Code Style

- Replace verbose license headers with SPDX tags
  ([`80e2d7e`](https://github.com/rero/rero-invenio-thumbnails/commit/80e2d7eb54cf6cdcec8b43a2fd18799aaa3529a3))

### Continuous Integration

- Add automatic release publication
  ([`620e27e`](https://github.com/rero/rero-invenio-thumbnails/commit/620e27ebb4ad385b147efd31256fce9d23766bfb))


## [v2.0.0](https://github.com/rero/rero-invenio-thumbnails/tree/v2.0.0) (2026-04-24)

[Full Changelog](https://github.com/rero/rero-invenio-thumbnails/compare/v1.1.0...v2.0.0)

**Breaking changes:**

- chore!: bump Python support to 3.12–3.14 [#4](https://github.com/rero/rero-invenio-thumbnails/pull/4) (by @PascalRepond)

## [v1.1.0](https://github.com/rero/rero-invenio-thumbnails/tree/v1.1.0) (2026-04-16)

[Full Changelog](https://github.com/rero/rero-invenio-thumbnails/compare/v1.0.0...v1.1.0)

**New features:**

- feat(internet archive): add Internet Archive cover provider [#8](https://github.com/rero/rero-invenio-thumbnails/pull/8) (by @rerowep)
- feat(bnf): switch to openapi.bnf.fr cover API [#10](https://github.com/rero/rero-invenio-thumbnails/pull/10) (by @rerowep)

**Fixes:**

- fix(dnb): resolve SSLEOFError on services.dnb.de [#9](https://github.com/rero/rero-invenio-thumbnails/pull/9) (by @rerowep)
- fix(bnf): add User-Agent header to fix connection reset errors [#5](https://github.com/rero/rero-invenio-thumbnails/pull/5) (by @rerowep)

**Other changes:**

- refactor(http): remove retry logic, add Amazon provider and cache cleanup [#11](https://github.com/rero/rero-invenio-thumbnails/pull/11) (by @rerowep)

## [v1.0.0](https://github.com/rero/rero-invenio-thumbnails/tree/v1.0.0) (2026-03-30)

[Full Changelog](https://github.com/rero/rero-invenio-thumbnails/compare/v0.1.0...v1.0.0)

**Changes:**

- refactor: remove type annotations, dynamic provider names, and class-based tests [#2](https://github.com/rero/rero-invenio-thumbnails/pull/2) (by @rerowep)

## [v0.1.0](https://github.com/rero/rero-invenio-thumbnails/tree/v0.1.0) (2026-02-25)

Initial release
