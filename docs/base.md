# base

Compatibility shim for modules that import `base` at top-level.

Some app modules import `from base import BaseApp`. In the test
environment `apps.base` is the real implementation; expose a small
shim so those imports resolve.

## Minimal apps.yaml snippet

```yaml
base:
  module: base
  class: base
  # options:
```