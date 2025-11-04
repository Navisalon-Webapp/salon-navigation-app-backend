query_upcoming_appointments="""
select c.cid, cu.first_name as customer_first, cu.last_name as customer_last, auth.email,
e.eid, eu.first_name as employee_first, eu.last_name as employee_last,
b.bid, b.name as salon, ba.street, ba.city, ba.state, ba.country, ba.zip_code,
s.sid, s.name as service, s.durationMin,
a.aid, a.start_time, a.expected_end_time
from salon_app.appointments as a
join salon_app.email_subscription as email on a.cid=email.cid
join salon_app.customers c on a.cid=c.cid
join salon_app.users cu on c.uid=cu.uid
join salon_app.authenticate auth on cu.uid=auth.uid
join salon_app.employee e on a.eid=e.eid
join salon_app.users eu on eu.uid=e.uid
join salon_app.services s on a.sid=s.sid
join salon_app.business b on s.bid=b.bid
join salon_app.addresses ba on b.aid=ba.aid
where email.appointment = true and a.start_time > CURRENT_TIMESTAMP()
order by start_time;
"""