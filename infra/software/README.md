# Software Engine (Vendor as Separate Stack)

This directory is reserved for pulling the **official Software Docker stack** as a separate component.
To avoid mixing GPLv2 code directly into EVENTSEC, use Software as an external service and connect
through the backend integration modules.

## Recommended setup

1. Add Software docker repo as a subtree or submodule:

```bash
git submodule add https://github.com/software/software-docker.git infra/software/software-docker
```

2. Keep the Software repository `LICENSE` intact.
3. Start the Software stack separately (see docs/software_parity/RUNBOOK.md).

> NOTE: The environment used for this change could not clone Software repos due to network restrictions.
> Add the Software docker repo here when you have network access or a local ZIP.
