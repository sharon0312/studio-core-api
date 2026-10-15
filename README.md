# Studio Core API

A Django REST Framework backend for managing studios, scheduled classes,
member credits, bookings, and class waitlists.

## Features

-   OTP-based authentication for staff and members (development OTP:
    `123456`, if enabled in the current configuration).
-   Staff/member role separation.
-   Studio and class listing.
-   Credit-pack management and credit spending.
-   Class booking and cancellation.
-   Waitlist join/leave and promotion when a place becomes available.
-   PostgreSQL database and Docker Compose development setup.


## Technology

-   Python and Django
-   Django REST Framework
-   PostgreSQL
-   Docker and Docker Compose

## Project structure

The current project is organised around the Django project `studio_core`
and the apps used for studio/class workflows. The exact directory layout
may vary; inspect the repository for the authoritative structure.

``` text
studio_core/
├── manage.py
├── studio_core/       # Django settings and root URL configuration
├── studios/           # Studio models and APIs
├── classes/           # Classes, bookings, waitlists, and credit-pack workflows
├── users/              # Authentication and user/profile roles, if present
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Requirements

-   Docker Engine
-   Docker Compose v2 (`docker compose`)
-   Git

You do not need to install Python or PostgreSQL on your host when using
Docker.

## Configuration

1.  Copy the example environment file:

    ``` bash
    cp .env.example .env
    ```

    On Windows PowerShell:

    ``` powershell
    Copy-Item .env.example .env
    ```

2.  Replace development-only values before using the project outside
    local development. Do not commit `.env`.

The Compose configuration uses these database settings:

-   `DB_NAME`
-   `DB_USER`
-   `DB_PASSWORD`
-   `DB_HOST` (use `db` when connecting from the Django container)

If the Django settings require additional variables, add them to
`.env.example` with safe placeholder values and document them here.

## Start the application

From the repository root, run:

``` bash
docker compose up --build
```

The Django container should apply migrations and start the development
server as configured by `docker-compose.yml`. If the compose file does
not run migrations automatically, run them in another terminal:

``` bash
docker compose exec web python manage.py migrate
```

Open the API using the host port mapped in `docker-compose.yml`. If the
project uses the suggested mapping `8001:8000`, the base URL is:

``` text
http://localhost:8001/
```

If your compose file maps a different port, use that port instead.

To stop the stack:

``` bash
docker compose down
```

To remove the local database volume as well (this deletes local database
data):

``` bash
docker compose down -v
```

## Main workflow walkthrough

Use the API paths configured by the project. The end-to-end workflow for
a reviewer should be:

1.  **Authenticate** as a staff user or member using the configured OTP
    authentication endpoint.
2.  **Grant credits** to a member using a staff-authorised endpoint.
3.  **Browse classes** and check each class's available spots and credit
    cost.
4.  **Book a class** as a member. Send the required `Idempotency-Key`
    header if the booking endpoint requires it.
5.  **Fill the class** by booking until the available capacity is
    reached.
6.  **Join the waitlist** as another member once the class is full.
7.  **Cancel a booking** within the studio's cancellation cutoff to
    exercise the refund path.
8.  **Verify waitlist promotion** after a place is released, including
    credit deduction for the promoted member.
9.  **Inspect booking history, waitlist entries, credit packs, and
    ledger/balance endpoints** if implemented.

### Business rules to verify

-   Credits are spent from the earliest-expiring valid packs first
    (FEFO).
-   Expired packs cannot be used to pay for a booking.
-   A class cannot have more confirmed bookings than its capacity.
-   Cancellation refund eligibility uses the studio's local timezone and
    configured cutoff.
-   Repeated booking requests with the same idempotency key do not
    create duplicate bookings.
-   Members can only access their own bookings, waitlist entries, and
    credit information.
-   Waitlist promotion selects the earliest waiting member who can
    afford the class; members who cannot afford it remain waiting.
-   Credit grants, deductions, and refunds are recorded in the ledger if
    the ledger feature is implemented.

## API documentation and collection

Use the project's configured API documentation route (for example, a
generated OpenAPI/Swagger route if `drf-spectacular` or another schema
tool is installed). Confirm the exact URL in the root URL configuration
before sharing it with reviewers.

Include the Postman collection in the repository, or provide a generated
OpenAPI schema. The collection should demonstrate the complete workflow:
authenticate, grant credits, book a class, fill capacity, join the
waitlist, cancel a booking, and verify promotion.

## Tests

Run Django's test suite inside the web container:

``` bash
docker compose exec web python manage.py test
```

If the repository uses pytest instead, use the configured pytest command
(commonly `docker compose exec web pytest`). Prefer the test command
that is actually configured in the repository.

## Linting and type checking

The assignment requires a linter and strict type checking to be
configured and clean. Run the commands configured in the repository (for
example, Ruff and mypy only if those tools and their configuration are
present). Add the exact commands here once confirmed, such as:

``` bash
docker compose exec web ruff check .
docker compose exec web mypy .
```

Do not leave example commands in the final submission if the
corresponding tools are not installed/configured; configure them or
replace these commands with the actual project commands.

## Continuous integration

The assignment requires CI to run linting, type checking, and tests.
Document the CI provider and workflow file once configured (for example,
a GitHub Actions workflow under `.github/workflows/`). Confirm that the
workflow passes on the submitted branch.

## Design and implementation notes

-   **Django ORM and DRF serializers/views:** use framework-native
    validation, relationships, and request handling instead of
    duplicating those capabilities.
-   **Database transactions and row locks:** use transactions and
    appropriate row-level locking around capacity checks, credit
    deductions, cancellations, and waitlist promotion to protect state
    changes.
-   **FEFO credit allocation:** spend from the earliest-expiring
    eligible credit packs first.
-   **Idempotency:** use the request idempotency key to make booking
    retries safe.

These are design intentions; ensure each item is present in the code
before describing it as fully implemented.
