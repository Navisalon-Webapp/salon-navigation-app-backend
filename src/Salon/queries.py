query_future_appointments = """
select c.uid as c_uid, c.cid, cu.first_name as customer_first, cu.last_name as customer_last, auth.email,
e.uid as e_uid, e.eid, eu.first_name as employee_first, eu.last_name as employee_last,
s.sid, s.name as service, s.durationMin,
a.aid, a.start_time, a.expected_end_time,
an.note_text as note
from salon_app.appointments as a
join salon_app.customers c on a.cid=c.cid
join salon_app.users cu on c.uid=cu.uid
join salon_app.authenticate auth on cu.uid=auth.uid
left join salon_app.employee e on a.eid=e.eid
left join salon_app.users eu on eu.uid=e.uid
join salon_app.services s on a.sid=s.sid
join salon_app.business b on s.bid=b.bid
left join salon_app.appointment_notes an on a.aid=an.aid
where a.start_time >= CURRENT_TIMESTAMP() and b.bid = %s
order by start_time;
"""

query_past_appointments = """
select c.uid as c_uid, c.cid, cu.first_name as customer_first, cu.last_name as customer_last, auth.email,
e.uid as e_uid, e.eid, eu.first_name as employee_first, eu.last_name as employee_last,
s.sid, s.name as service, s.durationMin,
a.aid, a.start_time, a.end_time,
an.note_text as note
from salon_app.appointments as a
join salon_app.customers c on a.cid=c.cid
join salon_app.users cu on c.uid=cu.uid
join salon_app.authenticate auth on cu.uid=auth.uid
left join salon_app.employee e on a.eid=e.eid
left join salon_app.users eu on eu.uid=e.uid
join salon_app.services s on a.sid=s.sid
join salon_app.business b on s.bid=b.bid
left join salon_app.appointment_notes an on a.aid=an.aid
where a.start_time < CURRENT_TIMESTAMP() and b.bid = %s
order by start_time;
"""

delete_appointment = """
    delete from appointments
    where aid = %s;
"""