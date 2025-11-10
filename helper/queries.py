query_user_role = """
select name 
from users u 
left join users_roles ur on u.uid=ur.uid 
left join roles r on ur.rid=r.rid 
where u.uid=%s;
"""

query_email = """
select email 
from users u 
left join authenticate a on u.uid=a.uid 
where u.uid=%s
"""

query_name = """
select first_name, last_name 
from users
where uid=%s
"""

query_appointment = """
select c.uid as c_uid, c.cid, cu.first_name as customer_first, cu.last_name as customer_last, auth.email,
e.uid as e_uid, e.eid, eu.first_name as employee_first, eu.last_name as employee_last,
b.uid as b_uid, b.bid, b.name as salon, ba.street, ba.city, ba.state, ba.country, ba.zip_code,
s.sid, s.name as service, s.durationMin,
a.aid, a.start_time, a.expected_end_time
from salon_app.appointments as a
join salon_app.customers c on a.cid=c.cid
join salon_app.users cu on c.uid=cu.uid
join salon_app.authenticate auth on cu.uid=auth.uid
left join salon_app.employee e on a.eid=e.eid
left join salon_app.users eu on eu.uid=e.uid
join salon_app.services s on a.sid=s.sid
join salon_app.business b on s.bid=b.bid
join salon_app.addresses ba on b.aid=ba.aid
where a.start_time > CURRENT_TIMESTAMP() and a.aid = %s
order by start_time;
"""