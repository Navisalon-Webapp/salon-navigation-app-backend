update_verify_salon = "UPDATE business JOIN users ON business.uid=users.uid SET status=1 WHERE users.uid=%s"
delete_reject_salon = "DELETE FROM business WHERE uid=%s"