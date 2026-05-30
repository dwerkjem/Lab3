CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL UNIQUE,
    auto_approval INTEGER NOT NULL DEFAULT 0,
    is_deleted INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS rooms (
    room_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    day_rate_cents INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS reservations (
    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    attendees INTEGER NOT NULL,
    event_name TEXT NOT NULL,
    event_type TEXT NOT NULL DEFAULT 'other',
    start_datetime TEXT NOT NULL,
    end_datetime TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending approval'
        CHECK (status IN ('pending approval', 'approved')),
    notes TEXT,

    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);

CREATE TABLE IF NOT EXISTS services (
    service_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    cost_cents INTEGER NOT NULL,
   charge_by TEXT NOT NULL DEFAULT 'one time'
    CHECK (charge_by IN ('one time', 'daily', 'attendees', 'daily attendees'))

);

CREATE TABLE IF NOT EXISTS reservation_services (
    reservation_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,

    PRIMARY KEY (reservation_id, service_id),
    FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id),
    FOREIGN KEY (service_id) REFERENCES services(service_id)
);