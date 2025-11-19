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

query_new_customers = """
select count(sub.cid)
from (
	select a.cid, min(a.start_time) start
	from salon_app.appointments a 
	join salon_app.services s on a.sid=s.sid 
	where s.bid = %s
	group by a.cid
	) sub
where month(sub.start) = %s and year(sub.start) = %s;
"""

query_old_customers = """
select count(sub.cid)
from (
	select a.cid, min(a.start_time) start
	from salon_app.appointments a 
	join salon_app.services s on a.sid=s.sid 
	where s.bid = %s
	group by a.cid
	) sub
where month(sub.start) < %s and year(sub.start) <= %s;
"""

#count all customers of a business at end of period
query_end_period = """
select count(sub.cid)
from (
	select distinct a.cid
	from salon_app.appointments a
	join salon_app.services s on a.sid=s.sid
	where s.bid = %s and month(a.start_time) = %s and year(a.start_time) = %s
	) sub;
"""

query_customer_satisfaction = """
select avg(rating)
from salon_app.reviews
where bid=%s;
"""