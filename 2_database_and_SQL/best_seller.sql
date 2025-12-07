-- best_seller.sql
-- Best selling products based on successful delivery in July-September 2025
-- Output: product_name, total_gmv, total_quantity, unique_user_count
WITH successful_orders AS (
    SELECT
        od.product_id,
        od.quantity,
        p.price,
        o.user_id
    FROM ku_order_detail od
    JOIN ku_order o ON od.order_id = o.id
    JOIN ku_order_status os ON o.status = os.id
    JOIN ku_order_detail_status ods ON od.status = ods.id
    JOIN ku_product p ON od.product_id = p.id
    WHERE
        os.name = 'success'
        AND ods.name = 'delivered'
        AND od.delivery_date BETWEEN DATE '2025-07-01' AND DATE '2025-09-30'
)
SELECT
    p.name AS product_name,
    SUM(so.price * so.quantity) AS total_gmv,
    SUM(so.quantity) AS total_quantity,
    COUNT(DISTINCT so.user_id) AS unique_user_count
FROM successful_orders so
JOIN ku_product p ON so.product_id = p.id
GROUP BY p.name
ORDER BY total_gmv DESC, total_quantity DESC;

