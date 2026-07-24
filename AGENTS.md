# Senshac Runner

This is the focused CI and local-runner repository. It owns Flox
containerization, rootless Podman/Act execution, and runner image publishing.
It does not own the Astro application, Tina content, or media processing.

The live web repository remains the checkout supplied to the runner. Validate
runner changes against a clean web checkout before changing image tags or
workflow ownership.
