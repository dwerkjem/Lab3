-- version 0.2
-- Allow services.charge_by to accept 'daily attendees'

PRAGMA foreign_keys = OFF;

CREATE TABLE services_new (
    service_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    cost_cents INTEGER NOT NULL,
    charge_by TEXT NOT NULL DEFAULT 'one time'
        CHECK (charge_by IN ('one time', 'daily', 'attendees', 'daily attendees'))
);

INSERT INTO services_new (
    service_id,
    name,
    description,
    cost_cents,
    charge_by
)
SELECT
    service_id,
    name,
    description,
    cost_cents,
    charge_by
FROM services;

DROP TABLE services;

ALTER TABLE services_new RENAME TO services;

INSERT INTO schema_migrations (version)
VALUES ('002_services_add_daily_attendees');

PRAGMA foreign_keys = ON;