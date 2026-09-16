# Warren sibling-container runtime on Podman

The published Senshac agent image is selected only by Warren's Docker/Kubernetes
providers. The current Warren containers use the local provider, so they do not
consume `.warren/config.yaml`'s `agentImage` pin.

## Preconditions

- Warren v0.19.1 or newer.
- Rootless Podman socket: `/run/user/1000/podman/podman.sock`.
- A Linux Docker-compatible CLI available inside the Warren container.
- The Warren data directory mounted at the same absolute path in the control
  plane and sibling agent containers.
- The Warren control-plane container has `WARREN_RUNTIME=docker`.

## Migration sequence

Migrate one instance at a time. Preserve the existing data volume and secrets;
do not remove the old container until readiness and a test run succeed.

1. Stop only the selected Warren app container; leave its Caddy and Tailscale
   sidecars and data volume intact.
2. Recreate the app with the Podman socket mounted at
   `/var/run/docker.sock`, a Docker-compatible CLI at `/usr/bin/docker`, and
   `WARREN_RUNTIME=docker`.
3. Keep `WARREN_DATA_DIR` and the volume's in-container path unchanged.
4. Verify `/readyz` reports a healthy Docker CLI/provider.
5. Dispatch a documentation-only run against `senshac-runner`.
6. Confirm the run uses the pinned digest from `.warren/config.yaml`, creates a
   branch, and delivers a PR.
7. Repeat for the other Warren instance only after the first succeeds.

The agent image is pinned by digest in `.warren/config.yaml`:

```text
ghcr.io/nacosolutions/senshac-warren-agent@sha256:59d9810bb74a280821623e0eaa992e6e64cb8bc7c896c6467b7cb4805a3c9ded
```

Do not use `latest` for the migration test. Roll back by restoring the prior
Warren app container and leaving the data volume untouched.
Docker-provider runs require the control plane and sibling agents to share the same host-visible workspace path.
