<!--
Thanks for contributing to glance.

The component contract is small on purpose. Please read
`docs/component-contract.md` before changing anything in `glance/core/`.

For new trackers, prefer `glance scaffold` over hand-written components.
-->

## What this changes

<!-- One sentence. -->

## Why

<!-- One sentence. The "what" is in the diff; "why" goes here. -->

## Type

- [ ] Bug fix (no contract changes)
- [ ] New tracker / component
- [ ] Core framework change (please link the issue and read `docs/component-contract.md`)
- [ ] Docs / DX
- [ ] Tests / CI

## Checklist

- [ ] `pytest glance/` passes locally
- [ ] `ruff check glance/ examples/` is clean
- [ ] If this changes the component contract, `docs/component-contract.md` updated
- [ ] If user-facing, `CHANGELOG.md` updated under `[Unreleased]`
