query_email_subscriptions = """
select promotion, appointment
from salon_app.email_subscription as es
join salon_app.users u on es.uid=u.uid
where u.uid = %s;
"""

query_customers_business = """
select u.uid, c.cid, u.first_name, u.last_name, auth.email
from salon_app.customers c
join salon_app.appointments a on c.cid=a.cid
join salon_app.users u on c.uid=u.uid
join salon_app.authenticate auth on u.uid=auth.uid
join salon_app.services s on a.sid=s.sid
where s.bid=%s;
"""