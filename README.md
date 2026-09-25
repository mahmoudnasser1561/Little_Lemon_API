# Little Lemon API

Django REST API for restaurant operations: auth, role-based access, catalog CRUD, cart, and orders.
It includes pagination, search/ordering query support, and request throttling.

## Core Backend Features

- Token-based authentication (`/api/api-token-auth/`) with DRF auth classes
- Role-based access control using Django groups (`Manager`, `Delivery Crew`)
- Menu items + categories APIs with create/read/update/delete behavior
- Cart workflow (`GET/POST/DELETE /api/cart/menu-items`) and checkout to orders
- Order lifecycle with assignment/status updates on `/api/orders/<id>`
- Pagination enabled globally (`PAGE_SIZE = 2`)
- Search + ordering on menu list (`?search=`, `?ordering=price`, `?ordering=-price`)
- Request throttling:
  - Anonymous: `20/min`
  - Authenticated users: `100/min`

## Why I Built This

I built this to sharpen API design, permissions, and data modeling around a realistic ordering workflow.

## Stack

- Python `3.10`
- Django `5.2.11`
- Django REST Framework `3.16.1`
- Djoser `2.3.3`
- django-filter `25.2`
- Default DB: SQLite (`db.sqlite3`)

## Project Structure

- `LittleLemonAPI/` project settings, root URLs, WSGI/ASGI
- `restaurant/` app code: models, serializers, permissions, views, URLs, tests
- `manage.py` Django management entrypoint

## Data Model

- `Category`: `slug`, `title`
- `MenuItem`: `title`, `price`, `featured`, `category`
- `Cart`: `user`, `menuitem`, `quantity`, `unit_price`, `price`
- `Order`: `user`, `delivery_crew`, `status`, `total`, `date`
- `OrderItem`: order line items created from cart at checkout

Constraints:
- `Cart` is unique per `(user, menuitem)`
- `OrderItem` is unique per `(order, menuitem)`

## Authentication

Configured auth classes:
- `TokenAuthentication`
- `SessionAuthentication`

Token endpoint:
- `POST /api/api-token-auth/`

Example:

```bash
curl -X POST "http://127.0.0.1:8000/api/api-token-auth/" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"adminpass"}'
```

Response:

```json
{"token":"<token>"}
```

Also available via Djoser authtoken:
- `POST /token/login/`
- `POST /token/logout/`

## Role Model

Groups used in code:
- `Manager`
- `Delivery Crew`

Assignment endpoints:
- `POST /api/groups/manager/users`
- `DELETE /api/groups/manager/users/<int:userId>`
- `POST /api/groups/delivery-crew/users`
- `DELETE /api/groups/delivery-crew/users/<int:userId>`

Only managers can manage these groups.

## Role-Based Access Matrix

`Customer` means authenticated user with no group.

| Endpoint Group | Manager | Delivery Crew | Customer |
|---|---|---|---|
| `GET /api/categories/` | Yes | Yes | Yes |
| `POST /api/categories/` | Yes | No | No |
| `GET /api/menu-items/`, `GET /api/menu-items/<pk>` | Yes | Yes | Yes |
| `POST /api/menu-items/`, `PUT/PATCH/DELETE /api/menu-items/<pk>` | Yes (auth) | Yes (auth) | Yes (auth) |
| `GET/POST/DELETE /api/cart/menu-items` | Yes (own cart) | Yes (own cart) | Yes (own cart) |
| `GET /api/orders` | All orders | Assigned orders only | Own orders only |
| `POST /api/orders` | Yes | Yes | Yes |
| `GET /api/orders/<pk>` | Yes | Yes | Yes (auth) |
| `PUT/PATCH /api/orders/<pk>` | Yes | Yes | No (`Not Ok`) |
| Group management endpoints | Yes | No | No |

## API Overview

### Auth / Users

- `POST /api/api-token-auth/`
- `POST /token/login/`
- `POST /token/logout/`
- `POST /api/users/`
- `GET /api/users/me/`

Note:
- `DJOSER["SERIALIZERS"]["user_create"]` points to `restaurant.serializers.UserSerializer` (`id`, `username`, `email`). Password handling for signup is not fully wired in current code.

### Categories

- `GET /api/categories/`
- `POST /api/categories/`

### Menu

- `GET /api/menu-items/`
- `POST /api/menu-items/`
- `GET /api/menu-items/<int:pk>`
- `PUT/PATCH/DELETE /api/menu-items/<int:pk>`

### Cart

- `GET /api/cart/menu-items` — the whole cart in one response: `{"items": [...], "total": "..."}`, no pagination. Each item shows the menu item's id, title, current unit price and quantity; prices are always read live from the menu, never from a stored copy.
- `POST /api/cart/menu-items` — body: `{"menuitem": <id>, "quantity": <n>}`. Adding an item already in the cart adds to its quantity instead of failing. Quantity is capped at 99 per line.
- `PATCH /api/cart/menu-items/<menuitem_id>` — body: `{"quantity": <n>}`. Sets a single line's quantity.
- `DELETE /api/cart/menu-items/<menuitem_id>` — removes a single line.
- `DELETE /api/cart/menu-items` — clears the whole cart.

### Orders

- `GET /api/orders`
- `POST /api/orders`
- `GET /api/orders/<int:pk>`
- `PUT/PATCH /api/orders/<int:pk>`

## Order Lifecycle

1. Add menu items to cart via `POST /api/cart/menu-items`.
2. Create an order via `POST /api/orders` (cart rows are converted into `OrderItem` records).
3. The cart is cleared after successful order creation.
4. Manager or delivery crew updates `delivery_crew` and `status` on `PATCH /api/orders/<id>`.
5. Delivery crew sees only assigned orders in `GET /api/orders`.

## Pagination, Search, Ordering, Throttling

Global DRF config:
- Pagination: page-number, `PAGE_SIZE = 2`
- Throttle rates:
  - anonymous: `20/min`
  - authenticated user: `100/min`

Menu list query params:
- `?page=<n>`
- `?search=<category_title>` (searches `category__title`)
- `?ordering=price` or `?ordering=-price`

Note:
- `ordering_fields` includes `inventory`, but `MenuItem` has no `inventory` field.

## Example Requests

```bash
BASE_URL="http://127.0.0.1:8000"
TOKEN="<paste-token>"
```

1. List menu items (public):

```bash
curl "$BASE_URL/api/menu-items/?page=1&search=desserts&ordering=-price"
```

2. Create category (manager only):

```bash
curl -X POST "$BASE_URL/api/categories/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"slug":"mains","title":"Mains"}'
```

3. Create menu item (any authenticated user in current code):

```bash
curl -X POST "$BASE_URL/api/menu-items/" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Greek Salad","price":"12.50","featured":true,"category_id":1}'
```

4. Add user to delivery crew (manager only):

```bash
curl -X POST "$BASE_URL/api/groups/delivery-crew/users" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"delivery_user"}'
```

5. Add item to cart (the price is always taken from the menu, never from the request):

```bash
curl -X POST "$BASE_URL/api/cart/menu-items" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"menuitem":1,"quantity":2}'
```

6. Create order from cart:

```bash
curl -X POST "$BASE_URL/api/orders" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"date":"2026-02-13"}'
```

7. Update order status/assignment (manager or delivery crew):

```bash
curl -X PATCH "$BASE_URL/api/orders/1" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"delivery_crew":2,"status":true}'
```

8. Clear cart:

```bash
curl -X DELETE "$BASE_URL/api/cart/menu-items" \
  -H "Authorization: Token $TOKEN"
```

## Caching

A cache-aside layer sits in front of Postgres for the public catalog only: `GET /api/menu-items/`
(including every `?search=`/`?ordering=`/`?page=` combination) and `GET /api/categories/`. Cart and
orders are intentionally not cached - they're per-user, mutate on nearly every request, and are
already cheap single-user-scoped queries.

- **Read path**: a request checks Redis first. On a hit, the cached response is returned as-is; on a
  miss, it falls through to Postgres as normal and the result is cached before responding.
- **Every cached response carries `X-Cache: HIT` or `X-Cache: MISS`** so the behavior is directly
  observable with `curl -i`.
- **Invalidation is versioned, not scanned.** List caches are keyed as `...:v{N}:{query-hash}`. Any
  menu item write bumps the menu-list version, instantly orphaning every previously cached page
  (they just expire on their own TTL, nothing is scanned or deleted). A menu item's own detail key
  (`menu:item:{id}`) is deleted directly on its update/delete. A category write bumps both the
  category-list version and the menu-list version, since menu item responses embed a snapshot of
  their category.
- **TTLs are a safety net on top of invalidation**, not the primary mechanism - they catch anything
  that writes to the DB outside the API (e.g. the Django admin or a shell). Default 5 minutes each,
  configurable via `CACHE_TTL_MENU_LIST` / `CACHE_TTL_MENU_ITEM` / `CACHE_TTL_CATEGORY_LIST`.
  See `restaurant/caching.py`.
- **Redis is a performance layer, not a source of truth.** The cache backend is configured with
  `IGNORE_EXCEPTIONS`, so if Redis is unreachable every cached endpoint just degrades to "always
  miss" and serves straight from Postgres - it never turns into a 500.
- **Security**: Redis requires a password (`REDIS_PASSWORD` in `.env`) and its port is not published
  to the host in `docker-compose.yml` - it's reachable only from the `api` service on the compose
  network.
- Without `REDIS_HOST` set (e.g. running locally via Pipenv, or in tests), `CACHES` falls back to
  Django's in-process `LocMemCache` automatically, so nothing extra is needed to run tests or
  `runserver` locally.

## Running with Docker

First, create your local secrets file (gitignored, never committed):

```bash
cp .env.example .env
# then edit .env: set POSTGRES_PASSWORD and SECRET_KEY to real values.
# generate a SECRET_KEY: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Then one command brings up the whole stack — the API and a real PostgreSQL database:

```bash
docker compose up
```

That builds the API image, starts Postgres and Redis, waits for both to be healthy, applies migrations automatically, and serves the API on `http://localhost:8000` via gunicorn. Data persists in named volumes across restarts (`docker compose stop` / `docker compose up` keeps it; `docker compose down -v` wipes it). Redis is not published to the host — only the `api` service can reach it, on the compose network.

`docker-compose.yml` reads `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD` and `SECRET_KEY` from `.env` and **refuses to start without it** — there are no fallback credentials baked into the tracked file. `DEBUG` and `ALLOWED_HOSTS` are also read from `.env` but do have sensible defaults if you leave them out.

Since there's no manager signup endpoint by design, create one inside the running container:

```bash
docker compose exec api python manage.py create_user --role manager --username boss --email boss@example.com
```

## Local Setup (Pipenv, no Docker)

Runs on SQLite, no Postgres needed — useful for quick local iteration:

```bash
pipenv install
pipenv run python manage.py migrate
pipenv run python manage.py createsuperuser
pipenv run python manage.py shell -c "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='Manager'); Group.objects.get_or_create(name='Delivery Crew')"
pipenv run python manage.py runserver
```

## Environment Variables

All optional; every one has a fallback that keeps local/test runs working with zero setup.

- `SECRET_KEY` — falls back to a hardcoded dev value if unset.
- `DEBUG` — `"True"` or `"False"`; defaults to `True` (matches `docker-compose.yml`'s explicit `False` for a more production-realistic container).
- `ALLOWED_HOSTS` — comma-separated; defaults to `[]` (fine locally, since Django allows `localhost`/`127.0.0.1` automatically when `DEBUG=True`).
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` — when `POSTGRES_DB` is set, the app connects to Postgres; otherwise it falls back to `db.sqlite3`. `docker-compose.yml` sets all of these.
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_DB` — when `REDIS_HOST` is set, `CACHES` connects to Redis; otherwise it falls back to Django's in-process `LocMemCache`. `docker-compose.yml` sets `REDIS_HOST`/`REDIS_PORT`, and reads `REDIS_PASSWORD` from `.env`.
- `CACHE_TTL_MENU_LIST`, `CACHE_TTL_MENU_ITEM`, `CACHE_TTL_CATEGORY_LIST` — seconds; all default to `300` (5 minutes). See [Caching](#caching).
- `DJANGO_SETTINGS_MODULE` is set internally to `LittleLemonAPI.settings`.

## Running Tests

```bash
pipenv run python manage.py makemigrations --check --dry-run
pipenv run python manage.py check
pipenv run python manage.py test            # the whole regression suite
pipenv run python manage.py test cart       # one module: restaurant, cart or delivery_crew
pipenv run python manage.py test -v 2       # list every test
```

Tests live next to the code they cover (`restaurant/tests/`, `cart/tests/`, `delivery_crew/tests/`) and share the helpers in `LittleLemonAPI/testing.py`. They use a separate in-memory test database and never touch `db.sqlite3`.

Tests marked `@known_bug('B..')` describe the desired behaviour of a bug or feature that is still open, so they are reported as expected failures. When you fix one, the runner reports an "unexpected success": remove the decorator and it becomes a normal regression test. `SHOW_KNOWN_BUGS=1 pipenv run python manage.py test` runs them as normal tests so you can see why they fail.

## Roadmap (Backend)

- Fix Djoser user-create serializer to include password flow
- Tighten object-level permissions for order detail/update
- Add dedicated filterset fields for menu queries
- Expand test coverage for auth, roles, cart, and orders
