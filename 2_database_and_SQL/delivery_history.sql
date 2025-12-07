---- delivery_history.sql
-- Successful delivery history per user for September 2025
-- Output: user_id, user_name, user_email, user_phone, delivery_date,
--         product_name, product_categories, quantity, delivery_address, total (progressive sum per user)

WITH delivered AS (
    SELECT
        u.id AS user_id,
        u.name AS user_name,
        u.email AS user_email,
        u.phone AS user_phone,
        od.delivery_date AS delivery_date,
        p.name AS product_name,
        COALESCE(string_agg(DISTINCT c.name, ', ' ORDER BY c.name), '') AS product_categories,
        od.quantity AS quantity,
        ul.address AS delivery_address,
        od.id AS od_id
    FROM ku_order_detail od
    JOIN ku_order o ON od.order_id = o.id
    JOIN ku_order_status os ON o.status = os.id
    JOIN ku_order_detail_status ods ON od.status = ods.id
    JOIN ku_user u ON o.user_id = u.id
    LEFT JOIN ku_user_location ul ON od.user_location_id = ul.id
    JOIN ku_product p ON od.product_id = p.id
    LEFT JOIN ku_product_category pc ON p.id = pc.product_id
    LEFT JOIN ku_category c ON pc.category_id = c.id
    WHERE
      os.name = 'success'
      AND ods.name = 'delivered'
      AND od.delivery_date BETWEEN DATE '2025-09-01' AND DATE '2025-09-30'
    GROUP BY
      u.id, u.name, u.email, u.phone,
      od.delivery_date, p.name, od.quantity, ul.address, od.id
)
SELECT
    user_id,
    user_name,
    user_email,
    user_phone,
    delivery_date,
    product_name,
    product_categories,
    quantity,
    delivery_address,
    SUM(quantity) OVER (
        PARTITION BY user_id
        ORDER BY delivery_date, od_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS total
FROM delivered
ORDER BY delivery_date, user_id, od_id;

