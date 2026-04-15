# Exocortex Host Control Daemon

A small Python HTTP service that runs **on the Windows host** (outside Docker) and
provides start/stop/restart controls for Exocortex-related containers.

## Why this exists

OSS and SWARMFISH run inside their own containers. Neither has access to the
Docker daemon, so neither can start or stop other containers. This daemon lives
on the host where Docker is installed and exposes a small HTTP API that the OSS
control panel can call to manage services without mounting the Docker socket into
any application container.

## Security

- **Localhost-only by default** — binds to `127.0.0.1` so nothing on the network can reach it
- **Token auth** — all mutations require the `X-Control-Token` header
- **Container whitelist** — only pre-declared containers in `SERVICES` can be touched
- **Zero dependencies** — pure Python stdlib, no `pip install` required

## Running

```bat
REM Windows
services\control\start_daemon.bat
```

Or directly:

```bash
python services/control/host_daemon.py
```

The daemon prints its bind address and listens on port `9900` by default.
Open `http://127.0.0.1:9900/` in a browser to see the bootstrap status page
(useful for starting services before the OSS panel is even running).

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `HOST_CONTROL_HOST` | `127.0.0.1` | Bind address. Keep localhost unless you know what you're doing. |
| `HOST_CONTROL_PORT` | `9900` | Listen port. |
| `HOST_CONTROL_TOKEN` | `dev_control_token` | Required in `X-Control-Token` header. Change for real use. |
| `DOCKER_BIN` | `docker` | Name or path of the docker CLI. |

## Registered services

| Service | Containers (start order) |
|---|---|
| `oss` | `oss_postgres`, `oss_app` |
| `swarmfish` | `swarmfish_postgres`, `swarmfish_redis`, `swarmfish_app` |
| `agent-zero` | `exocortex_v16` |

To add a new service, edit the `SERVICES` dict at the top of
`host_daemon.py` — that's the only place to change.

## Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/` | no | HTML status dashboard (bootstrap UI) |
| GET | `/health` | no | Liveness probe |
| GET | `/services` | yes | Full status of all services |
| GET | `/services/<name>` | yes | Status of one service |
| POST | `/services/<name>/start` | yes | Start containers in dependency order |
| POST | `/services/<name>/stop` | yes | Stop containers in reverse order |
| POST | `/services/<name>/restart` | yes | Stop then start |

## Bootstrap workflow

If everything is stopped and you want to start OSS:

1. Run the daemon: `start_daemon.bat`
2. Open `http://127.0.0.1:9900/` in your browser
3. Paste the control token into the token field (default: `dev_control_token`)
4. Click **Start** next to "OSS Intelligence"
5. Once OSS is up, open `http://localhost:<oss-port>/panel` for the normal panel
6. The panel's own Service Control section can then manage everything without
   needing this bootstrap UI

## Integration with the OSS panel

The OSS panel's Control tab includes a **Service Control** section that calls
this daemon via `http://localhost:9900/services/...`. The panel stores the
control token in `localStorage` under `host_control_token`.

If the daemon is unreachable, the Service Control section shows
`Daemon unreachable — start with services\control\start_daemon.bat` — so you
always know when to bootstrap.
