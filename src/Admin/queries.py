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