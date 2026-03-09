# Proxy Manager

Fully-featured, application that transforms HAProxy configuration management from a tedious, error-prone process into an elegant visual experience. Instead of hand-editing sprawling config files, hunting for syntax errors, or losing track of what changed and when you get a sleek, dark-themed dashboard where every frontend, backend, ACL rule, server, and service section is just a few clicks away.

What sets it apart is the built-in **version control system**. Every change you make is tracked as a snapshot. You can review pending modifications with a field-level diff view, commit them with a message, browse the full history, compare any two versions side by side, and roll back to any previous state with a single click. Think of it as Git for your HAProxy config, but with a visual diff UI instead of command-line tools.

So, whether you're managing a single reverse proxy or orchestrating dozens of frontends across multiple backends with complex ACL routing, SSL termination, health checks, and stick-table replication, Proxy Manager keeps everything organized, versioned, and auditable.

![Version](https://img.shields.io/badge/version-1.5.3-blue)
![Python 3.12](https://img.shields.io/badge/Python-3.13-red)

### Dashboard

The interactive **flow topology diagram** on the dashboard gives you an instant birds-eye view of your entire traffic architecture: clients connecting to frontends, ACL rules routing to backends, servers resolving through DNS resolvers, and auxiliary services like peers, mailers, caches, and HTTP error pages, all rendered as an interactive SVG with hover-highlighting and connection tracing.

<img width="3822" height="1870" alt="Dashboard" src="https://github.com/user-attachments/assets/361ab21c-2baf-4d62-afa5-77ab0656241a" />

### Templates

Instead of building every section from scratch, Proxy Manager ships with ready-made templates for the most common HAProxy patterns, reverse proxies with SSL termination, HTTP-to-HTTPS redirects, stats dashboards, load-balanced backend pools, and more. Select a template, customize the parameters, and deploy a production-ready configuration in seconds.

<img width="2043" height="1463" alt="Predefined templates" src="https://github.com/user-attachments/assets/71dfb396-c314-45f2-b36f-3482b1f5891e" />

## History and Rollbacks

Every committed configuration state is stored as an immutable snapshot. The version history view lets you browse all previous commits with timestamps, authors, and commit messages. You can expand any version to inspect its full diff, compare two arbitrary versions side by side, or restore any historical snapshot with a single click giving you the confidence to experiment knowing you can always roll back.

<img width="3814" height="1834" alt="History management" src="https://github.com/user-attachments/assets/2e79292e-b151-46bb-b5bf-986a1f6965bf" />

### Changes Preview

Before committing, the pending changes panel shows you a precise, field-by-field diff of every modification across all sections. Each changed entity is listed with its old and new values highlighted, so you can review exactly what will be applied — no surprises, no guesswork.

<img width="2763" height="611" alt="Modification preview" src="https://github.com/user-attachments/assets/a5755689-cb8e-4695-a9ad-d4559e60832e" />

## Requirements

- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)

## Control Scripts

Proxy Manager includes helper scripts for building, deploying, and managing the service:

```bash
./proxy-manager help
# Display this help message.

./proxy-manager deploy [env]
# Deploy Proxy Manager to a remote server. Uses .env_<env> (default: prod).
# The ENV_NAME from the env file determines the image tag pulled from registry.

./proxy-manager build
# Build the Docker image and push it to the registry.

./proxy-manager start-docker [env]
# Start already built container. Uses .env_<env> (default: local).
# NOTE: that if the container is not built, this process will fail.

./proxy-manager rebuild-docker [env]
# This command will add a forced build attribute to docker compose.
# Uses .env_<env> (default: local). It should not affect stored data.

./proxy-manager kill-docker
# Forcefully kills all running docker containers (all containers!).

./proxy-manager enter [name|id]
# Allows us to enter any of the running docker containers if an ID or name is provided.
# If left empty, a listing will be displayed.
```

## License

Copyright 2025-2026, created by Patrik Čelko, see [LICENSE](LICENSE) for more details.
