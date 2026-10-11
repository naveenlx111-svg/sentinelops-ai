-- Seed data. Ids are assigned 1, 2, 3 in the order listed.

INSERT INTO users (email, name) VALUES
    ('asha@example.com',  'Asha'),
    ('ravi@example.com',  'Ravi'),
    ('meera@example.com', 'Meera');

INSERT INTO products (name, price_cents, stock) VALUES
    ('Mechanical keyboard', 549900, 25),
    ('USB-C hub',           189900, 100),
    ('Laptop stand',        129900, 3);
