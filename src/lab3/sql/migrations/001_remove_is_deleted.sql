-- Delete customers previously soft-deleted.
DELETE FROM reservation_services
WHERE reservation_id IN (
    SELECT reservation_id
    FROM reservations
    WHERE customer_id IN (
        SELECT customer_id
        FROM customers
        WHERE is_deleted = 1
    )
);

DELETE FROM reservations
WHERE customer_id IN (
    SELECT customer_id
    FROM customers
    WHERE is_deleted = 1
);

DELETE FROM customers
WHERE is_deleted = 1;

-- SQLite cannot directly DROP COLUMN on older versions.
-- Rebuild customers table without is_deleted.

CREATE TABLE customers_new (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL UNIQUE,
    auto_approval INTEGER NOT NULL DEFAULT 0
);

INSERT INTO customers_new (
    customer_id,
    full_name,
    auto_approval
)
SELECT
    customer_id,
    full_name,
    auto_approval
FROM customers;

DROP TABLE customers;

ALTER TABLE customers_new RENAME TO customers;

INSERT INTO schema_migrations (version)
VALUES ('001_remove_is_deleted');