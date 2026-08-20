# Mindclade

Mindclade develops frontier AI systems for programmable biology: models, data systems, and
scientific infrastructure for understanding and designing proteins, nucleic acids, small
molecules, and biomolecular complexes.

## Internal engineering estate

Mindclade's control plane is intentionally separated by authority:

- `.github` provides shared workflow implementations and organization-wide contributor UX.
- `github-config` governs GitHub Enterprise repositories, teams, rulesets, environments, and access.
- `bootstrap` owns only Ring-0 state, automation trust, seed projects, and recovery.
- `infrastructure-live` owns normal Google Cloud infrastructure.
- `gitops` owns Argo CD and Kubernetes desired state.
- `mindclade-internal-monorepo` owns product, model, training, data, serving, and build source.

Internal documentation must not contain credentials, customer data, restricted biological data,
private model weights, or production secrets.
