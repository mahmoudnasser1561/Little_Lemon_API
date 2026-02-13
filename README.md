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

- `GET /api/cart/menu-items`
- `POST /api/cart/menu-items`
- `DELETE /api/cart/menu-items`

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

5. Add item to cart:

```bash
curl -X POST "$BASE_URL/api/cart/menu-items" \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"menuitem":1,"unit_price":"12.50","quantity":2}'
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

## Local Setup (Pipenv)

```bash
pipenv install
pipenv run python manage.py migrate
pipenv run python manage.py createsuperuser
pipenv run python manage.py shell -c "from django.contrib.auth.models import Group; Group.objects.get_or_create(name='Manager'); Group.objects.get_or_create(name='Delivery Crew')"
pipenv run python manage.py runserver
```

## Environment Variables

No custom `.env` variables are read in current code.

- `DJANGO_SETTINGS_MODULE` is set internally to `LittleLemonAPI.settings`
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, and `DATABASES` are currently hardcoded in `LittleLemonAPI/settings.py`

## Running Tests

```bash
pipenv run python manage.py makemigrations --check --dry-run
pipenv run python manage.py check
pipenv run python manage.py test -v 2
```

## Roadmap (Backend)

- Fix Djoser user-create serializer to include password flow
- Tighten object-level permissions for order detail/update
- Add dedicated filterset fields for menu queries
- Expand test coverage for auth, roles, cart, and orders
