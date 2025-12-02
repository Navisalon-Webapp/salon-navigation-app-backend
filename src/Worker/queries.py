query_eid = "select eid from salon_app.employee left join salon_app.users on employee.uid=users.uid where users.uid=%s;"
query_appointments = "select * from salon_app.appointments where eid = %s and start_time > CURRENT_TIMESTAMP();"
query_availability = "select * from salon_app.schedule where eid = %s"

query_employee_images = """
    select id, picture, active
    from employee_work_pictures p
    join employee e on p.uid=e.uid
    where e.eid=%s;
"""

query_employee_info = """
    select u.uid, u.first_name, u.last_name, e.profile_picture, b.bid, b.name, e.bio, u.phone, a.email, e.approved
    from employee e
    left join business b on e.bid=b.bid
    join users u on e.uid=u.uid
    join authenticate a on u.uid=a.uid
    where e.eid=%s;
"""

query_employee_expertise = """
    select e.exp_id, e.expertise
    from expertise e
    join employee_expertise ee on e.exp_id=ee.exp_id
    where ee.eid=%s;
"""

query_employee_reviews = """
    select r.rvw_id, r.cid, u.first_name, u.last_name, r.rating, r.comment
    from reviews r
    join customers c on r.cid=c.cid
    join users u on c.uid=u.uid
    join employee e on r.eid=e.eid
    where r.eid=%s;
"""

query_total_appointments = """
    select count(aid) as total_appointments
    from appointments
    where eid = %s;
"""

query_average_rating = """
    select avg(rating) as average_rating
    from reviews
    where eid = %s;
"""

update_employee_bio = """
    update employee
    set bio = %s
    where eid = %s;
"""

update_employee_name = """
    update users u
    join employee e on u.uid=e.uid
    set u.first_name = %s, u.last_name = %s
    where e.eid = %s;
"""

update_employee_business = """
    update employee
    set bid = %s, approved = false
    where eid = %s;
"""

update_employee_phone = """
    update users u
    join employee e on u.uid=e.uid
    set u.phone = %s
    where e.eid = %s;
"""

update_profile_picture = """
    update employee e
    set profile_picture = %s
    where eid = %s;
"""

insert_employee_picture = """
    insert into employee_work_pictures (eid, picture)
    values (%s, %s);
"""