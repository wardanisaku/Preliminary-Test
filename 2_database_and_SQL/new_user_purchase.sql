-- new_user_purchase.sql
-- Details of new users who purchased within 7 days of registration
-- Output: user_id, user_name, order_id, delivery_date, product_name, product_price, quantity
WITH new_users AS (
    SELECT
        id AS user_id,
        name AS user_name,
        created_at AS registration_date
    FROM ku_user
),
successful_orders AS (
    SELECT
        o.id AS order_id,
        o.user_id,
        od.delivery_date,
        od.product_id,
        od.quantity,
        p.price AS product_price,
        p.name AS product_name
    FROM ku_order o
    JOIN ku_order_detail od ON od.order_id = o.id
    JOIN ku_order_status os ON o.status = os.id
    JOIN ku_order_detail_status ods ON od.status = ods.id
    JOIN ku_product p ON od.product_id = p.id
    WHERE
        os.name = 'success'
        AND ods.name = 'delivered'
)
SELECT
    nu.user_id,
    nu.user_name,
    so.order_id,
    so.delivery_date,
    so.product_name,
    so.product_price,
    so.quantity
FROM new_users nu
JOIN successful_orders so ON nu.user_id = so.user_id
WHERE so.delivery_date BETWEEN nu.registration_date AND nu.registration_date + INTERVAL '7 days'
ORDER BY nu.user_id, so.delivery_date;

