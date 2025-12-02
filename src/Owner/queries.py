get_salon_products = """
SELECT pid, name, price, stock, description, image
FROM salon_app.products
WHERE bid = %s
"""

create_product = """
INSERT INTO salon_app.products (bid, name, price, stock, description, image)
VALUES (%s, %s, %s, %s, %s, %s)
"""

update_product_stock = """
UPDATE salon_app.products
SET stock = %s
WHERE pid = %s
"""

get_product_by_id_query = """
SELECT pid, bid, name, price, stock, description, image
FROM salon_app.products
WHERE pid = %s
"""

delete_product_query = """
DELETE FROM salon_app.products
WHERE pid = %s
"""

get_salon_details = """
SELECT b.bid, b.name, b.status, a.street, a.city, a.state, a.zip_code
FROM salon_app.business b
LEFT JOIN salon_app.addresses a ON b.aid = a.aid
WHERE b.uid = %s
"""

update_salon_basic = """
UPDATE salon_app.business
SET name = %s, status = %s
WHERE uid = %s
"""

update_salon_address = """
UPDATE salon_app.addresses a
JOIN salon_app.business b ON a.aid = b.aid
SET a.street = %s, a.city = %s, a.state = %s, a.zip_code = %s
WHERE b.uid = %s
"""