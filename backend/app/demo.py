"""A reproducible FOOD DELIVERY fixture, not an AI implementation."""


def field(name, type="string", description="", required=True):
    return dict(name=name, type=type, required=required, description=description or name.replace("_", " "))


def fixture(stage):
    if stage == "blueprint":
        return {
            key: fixture(key)
            for key in ("requirements", "architecture", "database", "apis", "implementation", "documentation")
        }
    features = [
        ("Browse restaurants", "Customer", "View available restaurants and menus", "GET", "/restaurants", "Restaurant"),
        ("Place an order", "Customer", "Submit menu items and delivery address", "POST", "/orders", "Order"),
        (
            "Track an order",
            "Customer",
            "View current delivery status and timeline",
            "GET",
            "/orders/{order_id}/tracking",
            "Order",
        ),
        (
            "Manage menu",
            "Restaurant manager",
            "Publish menu items and availability",
            "PUT",
            "/restaurants/{restaurant_id}/menu",
            "Restaurant",
        ),
        (
            "Update delivery",
            "Courier",
            "Update the delivery status of an assigned order",
            "PATCH",
            "/orders/{order_id}/status",
            "Order",
        ),
        (
            "Cancel an order",
            "Customer",
            "Cancel an order before preparation starts",
            "POST",
            "/orders/{order_id}/cancellation",
            "Order",
        ),
    ]
    requirements = dict(
        summary="A food delivery platform connecting customers, restaurants and couriers. This is a fixed demonstration blueprint.",
        actors=["Customer", "Restaurant manager", "Courier"],
        functional=[
            dict(
                id=f"FR-{i}",
                title=t,
                actor=a,
                description=d,
                priority="must",
                acceptance_criteria=[
                    f"Authorized {a.lower()} can {d.lower()}.",
                    "Invalid input returns a documented error without changing state.",
                ],
            )
            for i, (t, a, d, *_) in enumerate(features, 1)
        ],
        non_functional=[
            dict(
                id="NFR-1",
                category="Performance",
                target="p95 API latency below 500 ms at 100 concurrent users",
                verification="Load test with representative data",
            ),
            dict(
                id="NFR-2",
                category="Security",
                target="All order operations enforce object-level authorization",
                verification="Cross-account access tests return 403",
            ),
        ],
        assumptions=[
            "Payment is cash on delivery for the first release.",
            "Delivery updates are polled every 15 seconds.",
        ],
        questions=["Is online payment needed?", "Can restaurants operate in multiple locations?"],
        out_of_scope=["Route optimization", "Automated refunds"],
    )
    ids = [r["id"] for r in requirements["functional"]]
    architecture = dict(
        pattern="Modular monolith",
        components=[
            dict(
                id="C-1",
                name="Web application",
                technology="React + TypeScript",
                responsibility="Role-based customer and operations interfaces",
                requirement_ids=ids,
            ),
            dict(
                id="C-2",
                name="Application API",
                technology="FastAPI",
                responsibility="Authorization, ordering and delivery modules",
                requirement_ids=ids,
            ),
            dict(
                id="C-3",
                name="Transactional store",
                technology="PostgreSQL",
                responsibility="Orders, restaurants, accounts and audit events",
                requirement_ids=ids,
            ),
        ],
        decisions=[
            dict(
                title="Start with a modular monolith",
                choice="One API deployment with separated domain modules",
                rationale="Small team and cross-module transactions favor operational simplicity.",
                tradeoff="Module boundaries must be enforced in code; independent scaling is limited.",
            )
        ],
        communication=["Web client → HTTPS REST API", "API → parameterized PostgreSQL queries"],
        deployment="Containerized API and static frontend behind TLS; managed PostgreSQL with daily backups.",
        security=[
            "Password hashes with Argon2",
            "Short-lived sessions",
            "Order ownership and courier assignment checks",
            "Input validation and request throttling",
        ],
    )
    entities = [
        dict(
            id="E-1",
            name="Restaurant",
            description="Restaurant listing and its menu",
            fields=[field("id"), field("owner_id"), field("name"), field("menu", "array")],
            indexes=["PRIMARY KEY (id)", "INDEX (owner_id)"],
            requirement_ids=["FR-1", "FR-4"],
        ),
        dict(
            id="E-2",
            name="Order",
            description="Order aggregate with status and ownership",
            fields=[
                field("id"),
                field("restaurant_id"),
                field("customer_id"),
                field("courier_id", required=False),
                field("items", "array"),
                field("delivery_address"),
                field("status"),
                field("created_at"),
            ],
            indexes=["PRIMARY KEY (id)", "INDEX (customer_id, created_at)", "INDEX (courier_id, status)"],
            requirement_ids=["FR-2", "FR-3", "FR-5", "FR-6"],
        ),
        dict(
            id="E-3",
            name="Account",
            description="Identity record and role assignment",
            fields=[field("id"), field("email"), field("password_hash"), field("role")],
            indexes=["PRIMARY KEY (id)", "UNIQUE (email)"],
            requirement_ids=ids,
        ),
    ]
    database = dict(
        engine="PostgreSQL",
        entities=entities,
        relationships=[
            dict(source="E-1", target="E-2", cardinality="one-to-many", description="Restaurant receives orders"),
            dict(
                source="E-3",
                target="E-2",
                cardinality="one-to-many",
                description="Customer owns orders; courier is assigned",
            ),
        ],
    )
    endpoints = []
    for i, (title, actor, _, method, path, entity) in enumerate(features, 1):
        request_fields = []
        if i == 2:
            request_fields = [field("restaurant_id"), field("items", "array"), field("delivery_address")]
        elif i == 4:
            request_fields = [field("menu", "array")]
        elif i == 5:
            request_fields = [field("status")]
        endpoints.append(
            dict(
                id=f"API-{i}",
                method=method,
                path=path,
                summary=f"{title} ({actor})",
                authenticated=True,
                request_fields=request_fields,
                response_fields=[field("data", "object" if i != 1 else "array")],
                success_status=201 if i == 2 else 200,
                errors=[
                    "400: Invalid payload",
                    "401: Missing session",
                    "403: Not permitted",
                    "404: Resource missing",
                    "409: Invalid order state",
                ],
                entity_ids=["E-1" if entity == "Restaurant" else "E-2"],
                requirement_ids=[f"FR-{i}"],
            )
        )
    apis = dict(
        authentication="Secure HttpOnly session cookie; role and resource ownership checks on every request.",
        endpoints=endpoints,
    )
    implementation = dict(
        tasks=[
            dict(
                id=f"T-{i}",
                title=t,
                phase="Domain implementation",
                estimate_days=2,
                depends_on=[] if i == 1 else [f"T-{i - 1}"],
                requirement_ids=[f"FR-{i}"],
                verification=f"Integration tests cover {t.lower()}, authorization and failure cases.",
            )
            for i, (t, *_) in enumerate(features, 1)
        ],
        project_structure=[
            "frontend/src/features/",
            "backend/app/domains/",
            "backend/tests/integration/",
            "migrations/",
        ],
        risks=[
            "Concurrent order state transitions need transactional guards.",
            "Restaurant availability can change during checkout.",
        ],
    )
    documentation = dict(
        overview=requirements["summary"],
        setup=[
            "Create environment variables and provision PostgreSQL.",
            "Apply migrations and seed development accounts.",
            "Install API and web dependencies; run their development servers. These are proposed instructions, not generated application code.",
        ],
        development_guidelines=[
            "Keep domain rules in services.",
            "Review schema migrations and use parameterized queries.",
        ],
        testing_strategy=[
            "Test each acceptance criterion.",
            "Test cross-account authorization and invalid transitions.",
            "Load-test order tracking.",
        ],
        deployment_notes=["Build containers, apply migrations, configure TLS and test backup restore."],
    )
    return dict(
        requirements=requirements,
        architecture=architecture,
        database=database,
        apis=apis,
        implementation=implementation,
        documentation=documentation,
        critique=dict(findings=[], limitations=["Demo fixture: no independent LLM critique was performed."]),
    )[stage]
