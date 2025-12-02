update_verify_salon = "UPDATE business JOIN users ON business.uid=users.uid SET status=1 WHERE users.uid=%s"
delete_reject_salon = "DELETE FROM business WHERE uid=%s"

query_business_retention = """
select sub.x, count(sub.x) as y
from ( 
	select count(c.cid) as x
	from salon_app.customers c
	join salon_app.appointments a on c.cid=a.cid
	join salon_app.services s on a.sid=s.sid
	where s.bid=%s
	group by c.cid
	) as sub
group by sub.x
order by sub.x
"""

query_tot_active_users = """
SELECT COUNT(*) AS total_active_users
FROM users
WHERE last_active >= DATE_SUB(NOW(), INTERVAL 30 DAY);
"""

query_avg_salons_expl = """
SELECT ROUND(AVG(salon_count), 2) AS avg_salons_explored
FROM (
    SELECT cid, COUNT(DISTINCT bid) AS salon_count
    FROM visit_history
    GROUP BY cid
) t;
"""

query_avg_salon_views = """
SELECT ROUND(AVG(salon_views), 2) AS avg_salon_views
FROM visit_history;
"""

query_prod_views = """
SELECT ROUND(AVG(product_views), 2) AS avg_product_views
FROM visit_history;
"""

query_new_user_trend = """
SELECT month, new_users_count
FROM new_users_monthly
WHERE year = YEAR(CURDATE())
ORDER BY month;
"""

query_active_user_roles = """
SELECT r.name AS role, COUNT(DISTINCT u.uid) AS active_users
FROM users u
JOIN users_roles ur ON u.uid = ur.uid
JOIN roles r ON ur.rid = r.rid
WHERE u.last_active >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY r.name;
"""

query_active_user_trend = """
SELECT month, active_count
FROM active_users_monthly
WHERE year = YEAR(CURDATE())
ORDER BY month;
"""

query_tot_loyalty_progs = """
SELECT COUNT(*) AS active_loyalty_programs
FROM loyalty_programs;
"""

query_client_prog_percent = """
SELECT
ROUND((COUNT(DISTINCT clb.cid) / (SELECT COUNT(*) FROM customers)) * 100, 2) AS percent_participating
FROM customer_loyalty_points clb;
"""

query_average_saved = """
SELECT AVG(total_redeemed) AS avg_amount_saved_per_customer
FROM (
	SELECT cid, SUM(val_redeemed) AS total_redeemed
	FROM loyalty_transactions
	GROUP BY cid
) AS customer_totals;
"""

query_tot_saved = """
SELECT SUM(val_redeemed) AS total_savings
FROM loyalty_transactions;
"""

query_progs_by_salon = """
SELECT num_programs, COUNT(*) as num_salons
FROM (
	SELECT bid, COUNT(*) as num_programs
	FROM loyalty_programs
	GROUP BY bid
) AS program_counts
GROUP BY num_programs
ORDER BY num_programs;
"""

query_prog_types = """
SELECT
SUM(points_thresh) AS points,
SUM(price_thresh) AS price,
SUM(appts_thresh) AS appointments,
SUM(pdct_thresh) AS products
FROM loyalty_programs;
"""

query_savings_trend = """
SELECT MONTH(created_at) AS month, SUM(val_redeemed) AS total_redeemed
FROM loyalty_transactions
WHERE YEAR(created_at) = YEAR(CURDATE())
GROUP BY MONTH(created_at)
ORDER BY MONTH(created_at);
"""

query_tot_rev = """
SELECT ROUND(SUM(revenue), 2) AS total_revenue
FROM monthly_revenue;
"""

query_month_rev_change = """
SELECT 
ROUND(((this_month.rev - last_month.rev) / last_month.rev) * 100, 2) AS percent_change
FROM (
	SELECT SUM(revenue) AS rev FROM monthly_revenue
	WHERE month = MONTH(CURDATE())
) this_month,
(
	SELECT SUM(revenue) AS rev FROM monthly_revenue
	WHERE month = MONTH(CURDATE()) - 1
) last_month;
"""

query_year_rev_change = """
SELECT
ROUND(((this_yr.rev - last_yr.rev) / last_yr.rev) * 100, 2) AS percent_change
FROM (
	SELECT SUM(revenue) AS rev FROM monthly_revenue
	WHERE year = YEAR(CURDATE())
) this_yr,
(
	SELECT SUM(revenue) AS rev FROM monthly_revenue
	WHERE year = YEAR(CURDATE()) - 1
) last_yr;
"""

query_avg_salon_rev = """
SELECT ROUND(AVG(revenue),2) AS avg_monthly_salon_revenue
FROM monthly_revenue;
"""

query_rev_trend = """
SELECT month, SUM(revenue) AS revenue
FROM monthly_revenue
WHERE year = YEAR(CURDATE())
GROUP BY month
ORDER BY month;
"""

query_rev_by_src = """
SELECT 'Appointments' AS source, SUM(amount) AS revenue
FROM transactions
WHERE aid IS NOT NULL
UNION ALL
SELECT 'Products', SUM(amount) AS revenue
FROM transactions
WHERE pid IS NOT NULL;
"""

query_top_services = """
SELECT sc.name, SUM(t.amount) AS revenue
FROM transactions t
JOIN appointments a ON t.aid = a.aid
JOIN services s ON a.sid = s.sid
JOIN service_categories sc ON s.cat_id = sc.cat_id
GROUP BY sc.name
ORDER BY revenue DESC
LIMIT 5;
"""

query_resched_rate = """
SELECT ROUND(
(SUM(status = 'rescheduled') / COUNT(*)) * 100, 2
) AS reschedule_rate
FROM appointments;
"""

query_cancel_rate = """
SELECT ROUND(
(SUM(status = 'cancelled') / COUNT(*)) * 100, 2
) AS cancellation_rate
FROM appointments;
"""

query_no_show_rate = """
SELECT ROUND(
(SUM(status = 'no_show') / COUNT(*)) * 100, 2
) AS no_show_rate
FROM appointments;
"""

query_appt_by_service = """
SELECT sc.name, COUNT(*) AS appt_count
FROM appointments a
JOIN services s ON a.sid = s.sid
JOIN service_categories sc ON s.cat_id = sc.cat_id
GROUP BY sc.name;
"""

query_appt_by_day = """
SELECT DAYNAME(start_time) AS day, COUNT(*) AS appt_count
FROM appointments
GROUP BY DAYNAME(start_time)
ORDER BY
	CASE day
		WHEN 'Monday' THEN 1
		WHEN 'Tuesday' THEN 2
		WHEN 'Wednesday' THEN 3
		WHEN 'Thursday' THEN 4
		WHEN 'Friday' THEN 5
		WHEN 'Saturday' THEN 6
		ELSE 7
	END,
	day ASC;
"""

query_appt_by_time = """
SELECT time_block, COUNT(*) AS appt_count
FROM (
	SELECT CASE
		WHEN HOUR(start_time) BETWEEN 5 AND 8 THEN 'Early Morning'
		WHEN HOUR(start_time) BETWEEN 9 AND 12 THEN 'Morning'
		WHEN HOUR(start_time) BETWEEN 13 AND 16 THEN 'Afternoon'
		WHEN HOUR(start_time) BETWEEN 17 AND 20 THEN 'Evening'
		ELSE 'Night'
	END AS time_block
	FROM appointments
) t
GROUP BY time_block;
"""

query_appt_trend = """
SELECT
MONTH(start_time) AS month,
COUNT(status='completed') AS completed_appointments
FROM appointments
WHERE YEAR(start_time) = YEAR(CURDATE())
GROUP BY MONTH(start_time)
ORDER BY MONTH(start_time);
"""

query_avg_income = """
SELECT ROUND(AVG(income), 2) AS avg_income
FROM customers;
"""

query_avg_salon_age = """
SELECT ROUND(AVG(YEAR(CURDATE()) - year_est), 2) AS avg_salon_age
FROM business;
"""

query_avg_worker_exp = """
SELECT ROUND(AVG(YEAR(CURDATE()) - start_year), 2) AS avg_worker_experience
FROM employee;
"""

query_gender_dist = """
SELECT gender, COUNT(*) AS count
FROM customers
GROUP BY gender;
"""

query_age_dist = """
SELECT
CONCAT(FLOOR(TIMESTAMPDIFF(YEAR, birthdate, CURDATE()) / 10) * 10, 's') AS age_range,
COUNT(*) AS count
FROM customers
WHERE birthdate IS NOT NULL
GROUP BY age_range;
"""

query_industry_dist = """
SELECT i.name, COUNT(*) AS client_count
FROM customers c
JOIN industries i ON c.ind_id = i.ind_id
GROUP BY i.name
ORDER BY client_count DESC
LIMIT 5;
"""