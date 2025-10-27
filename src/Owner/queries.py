query_business_info = """select name, first_name, last_name, phone, street, city, state, country, zip_code from
salon_app.business
left join salon_app.users on business.uid=users.uid
left join salon_app.addresses on business.aid=addresses.aid
where users.uid = 5;"""

update_adress = """
UPDATE salon_app.addresses AS a
JOIN salon_app.business AS b ON a.aid = b.aid
JOIN salon_app.users AS u ON b.uid = u.uid
SET 
  a.street = %s,
  a.city = %s,
  a.state = %s,
  a.country = %s,
  a.zip_code = %s
WHERE u.uid = %s;
"""

update_user_info = """
update salon_app.users
set first_name=%s, last_name=%s, phone=%s
where uid=%s;
"""

update_business_name = """
update salon_app.business
join salon_app.users on business.uid=users.uid
set name = %s
where users.uid = %s
"""