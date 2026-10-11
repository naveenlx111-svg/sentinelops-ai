# Project map

Where everything is and how it connects. The first half is written for the
person who has to wire and operate the system without having written the
application code.

## Repository layout

```
README.md
docs/                      everything in the documentation index
services/shop/             the demo application SentinelOps monitors
  pyproject.toml           dependencies and tool settings
  uv.lock                  exact resolved versions; builds install from this
  .python-version          3.14
  db/init/                 SQL that creates and seeds the database
    001_schema.sql
    002_seed.sql
  scripts/smoke.sh         end-to-end check through the gateway
  src/shop/
    common/                code shared by the four services
      config.py            environment variables -> typed settings; fail fast
      db.py                connection pool, per-request sessions, 503 on DB loss
      health.py            /healthz and /readyz
      upstream.py          calling another service; timeout -> 504, down -> 502
      lifecycle.py         release resources on shutdown
      logs.py              JSON-lines logging to stdout
    gateway/app.py         public entry point; forwards to the others
    users/app.py           owns the users table
    catalog/app.py         owns the products table and stock
    checkout/app.py        owns the orders table; places orders
  tests/                   pytest suite
```

Not yet present: container build files, Compose files, Kubernetes manifests,
the SentinelOps platform itself.

## The shop: one package, four processes

All four services live in one Python package and install from one lockfile.
What makes them four services is that each is **started as its own process**
with its own configuration ([ADR-0002](adr/0002-shop-one-package-four-processes.md)).

```mermaid
flowchart LR
    client["Client"] -->|HTTP| gateway
    gateway -->|"USERS_URL"| users
    gateway -->|"CATALOG_URL"| catalog
    gateway -->|"CHECKOUT_URL"| checkout
    checkout -->|"USERS_URL"| users
    checkout -->|"CATALOG_URL"| catalog
    users -->|"DATABASE_URL"| db[("PostgreSQL")]
    catalog -->|"DATABASE_URL"| db
    checkout -->|"DATABASE_URL"| db
```

Each arrow is a connection the dialling side opens, labelled with the
environment variable that tells it where to dial.

## Connection contract

This table is the complete interface between the application and whatever
runs it.

| Service | Starts with | Dials | Required environment | Optional environment |
|---|---|---|---|---|
| gateway | `uvicorn shop.gateway.app:create_app --factory` | users, catalog, checkout | `USERS_URL`, `CATALOG_URL`, `CHECKOUT_URL` | `UPSTREAM_TIMEOUT_SECONDS` (default 5.0) |
| users | `uvicorn shop.users.app:create_app --factory` | PostgreSQL | `DATABASE_URL` | — |
| catalog | `uvicorn shop.catalog.app:create_app --factory` | PostgreSQL | `DATABASE_URL` | — |
| checkout | `uvicorn shop.checkout.app:create_app --factory` | users, catalog, PostgreSQL | `DATABASE_URL`, `USERS_URL`, `CATALOG_URL` | `UPSTREAM_TIMEOUT_SECONDS` (default 2.0) |

- **Listening address and port** are not in the code. They are uvicorn's
  `--host` and `--port` arguments, chosen by whoever starts the process.
- **`*_URL` values** are base URLs such as `http://some-host:8000`. A trailing
  slash is tolerated.
- **`DATABASE_URL`** has the form
  `postgresql+psycopg://USER:PASSWORD@HOST:PORT/DATABASE`. It contains a
  password, so it is a secret.
- **No authentication** exists between services, or between a client and the
  gateway. Anything that can reach a port can call it.
- **Nothing has a default address.** A service missing a required variable
  exits at startup with a message naming it.

### HTTP endpoints

| Service | Method and path | Purpose |
|---|---|---|
| every service | `GET /healthz` | Liveness: the process is serving HTTP. Checks nothing else. |
| every service | `GET /readyz` | Readiness: 200 or 503. users, catalog and checkout check that the database answers and that their own table exists; the gateway is ready as soon as it serves. |
| gateway | `GET /api/products`, `GET /api/products/{id}` | → catalog |
| gateway | `GET /api/users/{id}` | → users |
| gateway | `POST /api/orders`, `GET /api/orders/{id}` | → checkout |
| users | `GET /users/{id}` | Look up a user |
| catalog | `GET /products`, `GET /products/{id}` | Read products |
| catalog | `POST /products/{id}/reserve` | Take units out of stock atomically; 409 if not enough |
| checkout | `POST /orders`, `GET /orders/{id}` | Place and read orders |

Each service also serves interactive API documentation at `/docs`.

### Database

One PostgreSQL database holds three tables, each owned by one service:
`users` (users), `products` (catalog), `orders` (checkout). There are no
foreign keys across owners; a service reaches another's data only through its
API.

The tables and seed rows come from the SQL files in `services/shop/db/init/`,
run in filename order against an empty database. The services never create or
alter tables themselves, and they expect the tables to exist.

## One request, hop by hop

`POST /api/orders` with `{"user_id": 1, "product_id": 2, "quantity": 1}`:

1. **Client → gateway.** `place_order` in `gateway/app.py` forwards the body
   to `CHECKOUT_URL/orders`.
2. **Gateway → checkout.** `place_order` in `checkout/app.py` validates the
   body; an invalid quantity is rejected here with 422 and nothing else is
   called.
3. **Checkout → users.** `GET USERS_URL/users/1`. users reads its table and
   answers 200 or 404.
4. **Checkout → catalog.** `POST CATALOG_URL/products/2/reserve`. catalog runs
   one `UPDATE … WHERE stock >= quantity` and answers 200, 404 or 409.
5. **Checkout → PostgreSQL.** Inserts the order row. Checkout borrows a
   database connection only at this step, not while waiting on steps 3 and 4.
6. **Back out.** checkout answers 201; the gateway passes status and body
   through unchanged.

## How failures show up

"Live run" means observed on 2026-10-11 with the four services running as
local processes against a real PostgreSQL. "Unit test" means covered by the
test suite with the other side simulated, and not yet seen happening for real.

| What breaks | What a client sees | What gets logged | Verified by |
|---|---|---|---|
| A service's process is gone | Routes that need it: 502 `{"detail": "<service> unreachable"}`. Other routes keep working. | A WARNING line from the caller naming the service, method and URL | Live run |
| The database is down | 503 `{"detail": "database unavailable"}`; that service's `/readyz` turns 503 while `/healthz` stays 200 | An ERROR line with the driver's reason | Live run |
| A required variable is missing | The process exits with code 1 at startup | `ConfigError: cannot start, bad environment configuration: NAME: Field required` | Live run |
| The database is up but has no tables | 500 from the service that owns the missing table; its `/readyz` is 503 | A WARNING line `not ready: relation "users" does not exist`, and on each request a traceback containing `UndefinedTable` | Live run |
| A service answers too slowly | 504 `{"detail": "<service> timed out"}` | A WARNING line from the caller | Unit test |
| users or catalog answers checkout with an unexpected status | 502 `{"detail": "<service> returned <status>"}` | A WARNING line from checkout | Unit test |

The gateway never rewrites a response it receives: whatever status and body
an internal service returns, including an error, reaches the client as is.

Timeouts nest: the gateway waits up to 5 s per phase for checkout, and
checkout waits up to 2 s per phase for each of users and catalog. The outer
limit is deliberately the longer one. The limits apply separately to
connecting, sending and reading, not to a call as a whole.

Application logs are one JSON object per line on stdout. Uvicorn's own
startup and access lines are plain text on the same streams.

## Where to look when something is wrong

| Symptom | First things to check |
|---|---|
| A service exits immediately | Its last log line: a `ConfigError` names the missing variable |
| 502 "unreachable" | Is the target process running? Is the `*_URL` the caller was given correct *from the caller's point of view*? Is the target listening on an address the caller can reach? |
| 504 "timed out" | The target is reachable but slow: check its logs and what it is waiting on |
| 503 "database unavailable" | The service's ERROR line gives the host, port and reason |
| `/healthz` is 200 but `/readyz` is 503 | The process is fine; its database is not. The service logs a `not ready:` line with the reason: unreachable, or reachable but missing its table |
| 500 with a traceback containing `UndefinedTable` | The database is reachable but was never initialised from `db/init/` |

## Known limitations

- **Stock can leak.** If checkout reserves stock and then fails to store the
  order, the reservation is not undone.
- **Orders are not idempotent.** Sending the same order twice places it twice.
- **No retries** on calls between services.
- **No authentication** anywhere.
- **Two log formats** on one stream until Phase 2.

These are left in on purpose for now: several make good failure scenarios
later, and each is revisited when its phase arrives.

## For the next developer

Start with this file, then `checkout/app.py`: it is the only service that
uses every shared piece. Each `app.py` has two functions: `build_app`, which
takes settings and wires the routes, and `create_app`, which reads the
environment and is what uvicorn calls.
