from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from mysql.connector import Error
from helper.utils import *
from datetime import timedelta, datetime
from decimal import Decimal
TAX_RATE = Decimal("0.06125")

transaction = Blueprint('transaction', __name__,)

def get_db():

    try:
        db = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            port=int(os.getenv("DB_PORT")),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
            )
        return db
    except mysql.connector.Error as err:
        print(f"Error: Database could not connect. : {err}")
        return None

def serialize_row(row):
    new_row = {}
    for k, v in row.items():
        if isinstance(v, (datetime, timedelta)):
            new_row[k] = str(v)  # or v.total_seconds() for timedelta
        else:
            new_row[k] = v
    return new_row

@transaction.route('/transactions', methods=['GET'])
@login_required
def get_transactions():
    if(check_role() != "customer"):
        print(f"Logged in user not a customer")
    cid = get_curr_cid()

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query_transactions = """
            select 
                t.trans_id, 
                b.bid, 
                b.name, 
                a.aid, 
                s.name, 
                s.price as service_cost, 
                p.pid, 
                p.name, 
                p.price as product_cost,
                pay.id as payment_id,
                pay.payment_type,
                pay.card_number,
                t.amount as final_cost
            from transactions t
            join business b on t.bid=b.bid
            left join appointments a on t.aid=a.aid
            join services s on a.sid=s.sid
            left join products p on t.pid=p.pid
            left join payment_information pay on t.payment_method_id=pay.id 
            where t.cid=%s;
        """
        cursor.execute(query_transactions,[cid])
        results = cursor.fetchall()
        return jsonify({
            "status":"success",
            "message":"retrieved past transactions",
            "transactions": results
        })
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Error",
            "error": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@transaction.route('/transactions/checkout/', methods=["POST"])
@login_required
def process_checkout():
    data = request.get_json() or {}
    cid = get_cid()
    bid = data.get("bid")
    payment_method_id = data.get("payment_method_id")
    is_product_purchase = bool(data.get("is_product_purchase", False))
    aid = data.get("aid")

    if not cid or not payment_method_id:
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    def to_decimal(val) -> Decimal:
        return Decimal(str(val or 0))

    try:
        cart_items = []
        appointment_id = None
        original_amount = Decimal("0")
        sing_disc = Decimal("0")

        if is_product_purchase:
            if not bid:
                return jsonify({"error": "Missing business id"}), 400

            cursor.execute("""
                SELECT c.pid, c.amount, p.price
                FROM cart c
                JOIN products p ON p.pid = c.pid
                WHERE c.cid = %s AND c.bid = %s
                ORDER BY p.price ASC
            """, (cid, bid))
            cart_items = cursor.fetchall()

            if not cart_items:
                return jsonify({"error": "Cart is empty"}), 400

            original_amount = sum(to_decimal(item["amount"]) * to_decimal(item["price"]) for item in cart_items)
            sing_disc = to_decimal(cart_items[0]["price"])

        else:
            if aid:
                cursor.execute("""
                    SELECT a.aid, a.bid, s.price
                    FROM appointments a
                    JOIN services s ON s.sid = a.sid
                    WHERE a.cid = %s AND a.aid = %s
                """, (cid, aid))
            else:
                if not bid:
                    return jsonify({"error": "Missing business id"}), 400
                cursor.execute("""
                    SELECT a.aid, a.bid, s.price
                    FROM appointments a
                    JOIN services s ON s.sid=a.sid
                    WHERE a.cid = %s AND a.bid = %s
                    ORDER BY a.created_at DESC LIMIT 1
                """, (cid, bid))

            appt = cursor.fetchone()
            if not appt:
                return jsonify({"error": "No appointment found"}), 400

            appointment_id = appt["aid"]
            bid = bid or appt["bid"]
            appointment_price = to_decimal(appt["price"])

            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) AS paid_amount
                FROM transactions
                WHERE aid=%s AND payment_method_id IS NOT NULL
            """, (appointment_id,))
            paid_row = cursor.fetchone() or {}
            already_paid = to_decimal(paid_row.get("paid_amount", 0))

            original_amount = appointment_price - already_paid
            if original_amount <= Decimal("0"):
                return jsonify({"error": "Appointment already paid"}), 400

            sing_disc = original_amount

        cursor.execute("""
            SELECT p.lprog_id, p.title, p.description, l.pts_value,
                   r.is_appt, r.is_product, r.is_price, r.is_points, r.is_discount, r.rwd_value
            FROM promotions p
            JOIN loyalty_programs lp ON lp.lprog_id = p.lprog_id
            JOIN rewards r ON r.lprog_id = p.lprog_id
            JOIN loyalty_points l on l.bid = lp.bid
            WHERE lp.bid=%s
              AND start_date <= CURDATE()
              AND end_date >= CURDATE()
              AND (
                    is_recurring = 0
                    OR (
                        FIND_IN_SET(DAYOFWEEK(CURDATE()), recurr_days)
                        AND CURTIME() BETWEEN start_time AND end_time
                    )
                 )
        """, (bid,))
        promotions = cursor.fetchall()

        promo_discount = Decimal("0")
        applied_promo_lprog = None

        for p in promotions:
            reward_val = to_decimal(p["rwd_value"])
            if p["is_appt"] and not is_product_purchase:
                promo_discount += reward_val * sing_disc
                applied_promo_lprog = p["lprog_id"]
            if p["is_product"] and is_product_purchase:
                promo_discount += reward_val * sing_disc
                applied_promo_lprog = p["lprog_id"]
            if p["is_price"]:
                promo_discount += reward_val
                applied_promo_lprog = p["lprog_id"]
            if p["is_points"]:
                promo_discount += reward_val * to_decimal(p["pts_value"])
                applied_promo_lprog = p["lprog_id"]
            if p["is_discount"]:
                promo_discount += reward_val * Decimal("0.01") * original_amount
                applied_promo_lprog = p["lprog_id"]

        cursor.execute("""
            SELECT lp.lprog_id, lp.description, c.pts_balance, c.appt_complete, c.prod_purchased, c.amount_spent,
                   lp.appts_thresh, lp.pdct_thresh, lp.price_thresh, lp.points_thresh, lp.threshold,
                   r.is_appt, r.is_product, r.is_price, r.is_points, r.is_discount, r.rwd_value, l.pts_value
            FROM customer_loyalty_points c
            JOIN loyalty_programs lp ON lp.bid = c.bid
            JOIN rewards r ON r.lprog_id = lp.lprog_id
            JOIN loyalty_points l on l.bid = lp.bid
            WHERE c.cid = %s AND c.bid = %s
        """, (cid, bid))
        reward_rows = cursor.fetchall()

        loyalty_discount = Decimal("0")
        loyalty_redeemed_lprog = None
        thresh_met = []

        for r in reward_rows:
            if r["appts_thresh"] and r["appt_complete"] >= r["threshold"]:
                thresh_met.append(r)
            if r["pdct_thresh"] and r["prod_purchased"] >= r["threshold"]:
                thresh_met.append(r)
            if r["price_thresh"] and r["amount_spent"] >= r["threshold"]:
                thresh_met.append(r)
            if r["points_thresh"] and r["pts_balance"] >= r["threshold"]:
                thresh_met.append(r)

        for r in thresh_met:
            reward_val = to_decimal(r["rwd_value"])
            if not is_product_purchase and r["is_appt"] and r["threshold"] > 0:
                loyalty_discount += reward_val * sing_disc
                loyalty_redeemed_lprog = r["lprog_id"]
                cursor.execute("""
                    UPDATE customer_loyalty_points
                    SET appt_complete = appt_complete - %s
                    WHERE cid=%s AND bid=%s
                """, (float(r["threshold"]), cid, bid))

            if is_product_purchase and r["is_product"] and r["threshold"] > 0:
                loyalty_discount += reward_val * sing_disc
                loyalty_redeemed_lprog = r["lprog_id"]
                cursor.execute("""
                    UPDATE customer_loyalty_points
                    SET prod_purchased = prod_purchased - %s
                    WHERE cid=%s AND bid=%s
                """, (float(r["threshold"]), cid, bid))

            if r["is_price"] and r["threshold"] > 0:
                loyalty_discount += reward_val
                loyalty_redeemed_lprog = r["lprog_id"]
                cursor.execute("""
                    UPDATE customer_loyalty_points
                    SET amount_spent = amount_spent - %s
                    WHERE cid=%s AND bid=%s
                """, (float(reward_val), cid, bid))

            if r["is_discount"] and r["threshold"] > 0:
                loyalty_discount += reward_val * Decimal("0.01") * original_amount
                loyalty_redeemed_lprog = r["lprog_id"]

            if r["is_points"] and r["threshold"] > 0:
                loyalty_discount += reward_val * to_decimal(r["pts_value"])
                loyalty_redeemed_lprog = r["lprog_id"]
                cursor.execute("""
                    UPDATE customer_loyalty_points
                    SET pts_balance = pts_balance - %s
                    WHERE cid=%s AND bid=%s
                """, (float(reward_val * to_decimal(r["pts_value"])), cid, bid))

        tax = (original_amount * TAX_RATE).quantize(Decimal("0.01"))
        total_discount = (promo_discount + loyalty_discount).quantize(Decimal("0.01"))
        final_amount = (original_amount + tax - total_discount).quantize(Decimal("0.01"))
        if final_amount < Decimal("0"):
            final_amount = Decimal("0.00")

        cursor.execute("""
            INSERT INTO transactions (cid, bid, aid, amount, payment_method_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (cid, bid, appointment_id, float(final_amount), payment_method_id))
        trans_id = cursor.lastrowid

        if is_product_purchase:
            for item in cart_items:
                cursor.execute("""
                    INSERT INTO transactions_products (trans_id, pid, amount)
                    VALUES (%s, %s, %s)
                """, (trans_id, item["pid"], item["amount"]))

                cursor.execute("""
                    SELECT stock
                    FROM products
                    WHERE pid=%s
                """, (item["pid"],))
                product_stock = cursor.fetchone()

                if product_stock and product_stock["stock"] < item["amount"]:
                    conn.rollback()
                    return jsonify({"error": "Not enough stock to complete purchase"}), 400

                cursor.execute("""
                    UPDATE products
                    SET stock = stock - %s
                    WHERE pid=%s
                """, (item["amount"], item["pid"]))

        cursor.execute("""
            SELECT pts_value FROM loyalty_points WHERE bid=%s
        """, (bid,))
        pts_row = cursor.fetchone()
        pts_value = to_decimal(pts_row["pts_value"]) if pts_row else Decimal("1.0")

        points_earned = (final_amount * pts_value).quantize(Decimal("0.01"))

        cursor.execute("""
            UPDATE customer_loyalty_points
            SET pts_balance = pts_balance + %s,
                prod_purchased = prod_purchased + %s,
                appt_complete = appt_complete + %s,
                amount_spent = amount_spent + %s
            WHERE cid=%s AND bid=%s
        """, (
            float(points_earned),
            len(cart_items) if is_product_purchase else 0,
            0 if is_product_purchase else 1,
            float(final_amount),
            cid,
            bid
        ))

        if applied_promo_lprog:
            cursor.execute("""
                INSERT INTO loyalty_transactions (cid, trans_id, lprog_id, val_earned, val_redeemed)
                VALUES (%s, %s, %s, %s, %s)
            """, (cid, trans_id, applied_promo_lprog, float(total_discount), float(promo_discount)))

        if loyalty_redeemed_lprog:
            cursor.execute("""
                INSERT INTO loyalty_transactions (cid, trans_id, lprog_id, val_earned, val_redeemed)
                VALUES (%s, %s, %s, %s, %s)
            """, (cid, trans_id, loyalty_redeemed_lprog, float(total_discount), float(loyalty_discount)))

        cursor.execute("""
            INSERT INTO monthly_revenue (bid, year, month, revenue)
            VALUES (%s, YEAR(NOW()), MONTH(NOW()), %s)
            ON DUPLICATE KEY UPDATE revenue = revenue + %s
        """, (bid, float(final_amount), float(final_amount)))

        if is_product_purchase:
            cursor.execute("DELETE FROM cart WHERE cid=%s AND bid=%s", (cid, bid))

        if appointment_id:
            cursor.execute("""
                UPDATE appointments
                SET status = %s
                WHERE aid = %s
            """, ("paid", appointment_id))

        conn.commit()

        return jsonify({
            "success": True,
            "original_amount": float(original_amount),
            "discount": float(total_discount),
            "tax": float(tax),
            "final_amount": float(final_amount),
            "trans_id": trans_id
        }), 200

    except Error as e:
        conn.rollback()
        print("Checkout Error:", e)
        return jsonify({"error": "Checkout failed"}), 500

    finally:
        cursor.close()
        conn.close()

@transaction.route('/transactions/details', methods=["GET"])
@login_required
def get_discounts():
    cid = get_cid()
    bid = request.args.get("bid")
    is_product_purchase = request.args.get("is_product_purchase", "false").lower() == "true"
    aid = request.args.get("aid")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        def to_decimal(val) -> Decimal:
            return Decimal(str(val or 0))

        # Checkout subtotal from products
        if is_product_purchase:
            cursor.execute("""
                SELECT c.pid, c.amount, p.price
                FROM cart c
                JOIN products p ON p.pid = c.pid
                WHERE c.cid = %s
                ORDER BY p.price ASC
            """, (cid,))
            cart_items = cursor.fetchall()

            if not cart_items:
                return jsonify({"error": "Cart is empty"}), 400

            original_amount = sum(to_decimal(item["amount"]) * to_decimal(item["price"]) for item in cart_items)
            sing_disc = to_decimal(cart_items[0]["price"])

        else:
            # Checkout subtotal from appointments
            if aid:
                cursor.execute("""
                    SELECT a.aid, a.bid, s.price
                    FROM appointments a
                    JOIN services s ON s.sid = a.sid
                    WHERE a.cid = %s AND a.aid = %s
                """, (cid, aid))
            else:
                cursor.execute("""
                    SELECT a.aid, a.bid, s.price
                    FROM appointments a
                    JOIN services s ON s.sid=a.sid
                    WHERE a.cid = %s AND a.bid = %s
                    ORDER BY a.created_at DESC LIMIT 1
                """, (cid, bid))
            appt = cursor.fetchone()

            if not appt:
                return jsonify({"error": "No appointment found"}), 400

            bid = bid or appt["bid"]
            price = to_decimal(appt["price"])

            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) AS paid_amount
                FROM transactions
                WHERE aid=%s AND payment_method_id IS NOT NULL
            """, (appt["aid"],))
            paid_row = cursor.fetchone() or {}
            already_paid = to_decimal(paid_row.get("paid_amount", 0))

            original_amount = price - already_paid
            if original_amount <= Decimal("0"):
                return jsonify({
                    "status": "success",
                    "subtotal": 0,
                    "tax": 0,
                    "discount": 0,
                    "total": 0,
                    "promotions": [],
                    "loyalty_progs": []
                })

            sing_disc = original_amount

        cursor.execute("""
            SELECT p.promo_id, p.lprog_id, p.title, p.description, l.pts_value,
            r.is_appt, r.is_product, r.is_price, r.is_points, r.is_discount, r.rwd_value
            FROM promotions p
            JOIN loyalty_programs lp ON lp.lprog_id = p.lprog_id
            JOIN rewards r ON r.lprog_id = p.lprog_id
            JOIN loyalty_points l on l.bid = lp.bid
            WHERE lp.bid=%s
                AND start_date <= CURDATE()
                AND end_date >= CURDATE()
                AND (
                    is_recurring = 0
                    OR (
                        FIND_IN_SET(DAYOFWEEK(CURDATE()), recurr_days)
                        AND CURTIME() BETWEEN start_time AND end_time
                    )
                )
        """, (bid,))
        promotions = cursor.fetchall()

        promo_discount = Decimal("0")
        promos = []

        for p in promotions:
            reward_val = to_decimal(p["rwd_value"])
            if p["is_appt"]:
                reward = (reward_val * sing_disc).quantize(Decimal("0.01"))
                promos.append({"promo_id": p["promo_id"], "title": p["title"], "description": p["description"], "reward_type": "appointment", "threshold": 0, "reward": float(p["rwd_value"]), "rwd_value": float(reward)})

            if p["is_product"]:
                reward = (reward_val * sing_disc).quantize(Decimal("0.01"))
                promos.append({"promo_id": p["promo_id"], "title": p["title"], "description": p["description"], "reward_type": "product", "threshold": 0, "reward": float(p["rwd_value"]), "rwd_value": float(reward)})

            if p["is_price"]:
                reward = reward_val.quantize(Decimal("0.01"))
                promos.append({"promo_id": p["promo_id"], "title": p["title"], "description": p["description"], "reward_type": "price", "threshold": 0, "reward": float(p["rwd_value"]), "rwd_value": float(reward)})

            if p["is_points"]:
                reward = (reward_val * to_decimal(p["pts_value"])).quantize(Decimal("0.01"))
                promos.append({"promo_id": p["promo_id"], "title": p["title"], "description": p["description"], "reward_type": "points", "threshold": 0, "reward": float(p["rwd_value"]), "rwd_value": float(reward)})

            if p["is_discount"]:
                reward = (reward_val * Decimal("0.01") * original_amount).quantize(Decimal("0.01"))
                promos.append({"promo_id": p["promo_id"], "title": p["title"], "description": p["description"], "reward_type": "discount", "threshold": 0, "reward": float(p["rwd_value"]), "rwd_value": float(reward)})

            promo_discount += reward

        cursor.execute("""
            SELECT lp.description, c.pts_balance, c.appt_complete, c.prod_purchased, c.amount_spent,
            lp.appts_thresh, lp.pdct_thresh, lp.price_thresh, lp.points_thresh, lp.threshold,
            r.rwd_id, r.is_appt, r.is_product, r.is_price, r.is_points, r.is_discount, r.rwd_value, l.pts_value
            FROM customer_loyalty_points c
            JOIN loyalty_programs lp ON lp.bid = c.bid
            JOIN rewards r ON r.lprog_id = lp.lprog_id
            JOIN loyalty_points l on l.bid = lp.bid
            WHERE c.cid = %s AND c.bid = %s
        """, (cid, bid))
        reward_rows = cursor.fetchall()

        loyalty_discount = Decimal("0")
        progs = []
        thresh_met = []

        for r in reward_rows:
            if r["appts_thresh"] and r["appt_complete"] >= r["threshold"]:
                thresh_met.append(r)
            if r["pdct_thresh"] and r["prod_purchased"] >= r["threshold"]:
                thresh_met.append(r)
            if r["price_thresh"] and r["amount_spent"] >= r["threshold"]:
                thresh_met.append(r)
            if r["points_thresh"] and r["pts_balance"] >= r["threshold"]:
                thresh_met.append(r)

        reward = 0

        for r in thresh_met:
            reward_val = to_decimal(r["rwd_value"])
            # appointment reward
            if not is_product_purchase and r["is_appt"] and (r["threshold"] > 0):
                reward = (reward_val * sing_disc).quantize(Decimal("0.01"))
                progs.append({"rwd_id": r["rwd_id"], "description": r["description"], "threshold": r["threshold"], "reward_type": "appointment", "reward": float(r["rwd_value"]), "rwd_value": float(reward)})

            # product reward
            if is_product_purchase and r["is_product"] and (r["threshold"] > 0):
                reward = (reward_val * sing_disc).quantize(Decimal("0.01"))
                progs.append({"rwd_id": r["rwd_id"], "description": r["description"], "threshold": r["threshold"], "reward_type": "product", "reward": float(r["rwd_value"]), "rwd_value": float(reward)})

            # price reward
            if r["is_price"] and (r["threshold"] > 0):
                reward = reward_val.quantize(Decimal("0.01"))
                progs.append({"rwd_id": r["rwd_id"], "description": r["description"], "threshold": r["threshold"], "reward_type": "price", "reward": float(r["rwd_value"]), "rwd_value": float(reward)})

            # discount reward
            if r["is_discount"] and (r["threshold"] > 0):
                reward = (reward_val * Decimal("0.01") * original_amount).quantize(Decimal("0.01"))
                progs.append({"rwd_id": r["rwd_id"], "description": r["description"], "threshold": r["threshold"], "reward_type": "discount", "reward": float(r["rwd_value"]), "rwd_value": float(reward)})
            
            # points reward
            if r["is_points"] and (r["threshold"] > 0):
                reward = (reward_val * to_decimal(r["pts_value"])).quantize(Decimal("0.01"))
                progs.append({"rwd_id": r["rwd_id"], "description": r["description"], "threshold": r["threshold"], "reward_type": "points", "reward": float(r["rwd_value"]), "rwd_value": float(reward)})
            
            loyalty_discount += reward

        tax = (original_amount * TAX_RATE).quantize(Decimal("0.01"))
        total_discount = (promo_discount + loyalty_discount).quantize(Decimal("0.01"))
        final_amount = (original_amount + tax - total_discount).quantize(Decimal("0.01"))
        if final_amount < Decimal("0"):
            final_amount = Decimal("0.00")

        return jsonify({
            "status": "success",
            "subtotal": float(original_amount),
            "tax": float(tax),
            "discount": float(total_discount),
            "total": float(final_amount),
            "promotions": promos,
            "loyalty_progs": progs
        })

        conn.commit()

    except Error as e:
        conn.rollback()
        print("Transaction error:", e)
        return jsonify({"error": "Loading transaction details failed"}), 500

    finally:
        cursor.close()
        conn.close()

def get_cid():
    uid = getattr(current_user, 'id', None)
    if uid is None:
        print("Error: No UID found in request context.")
        return None
    
    db = get_db()
    if db is None:
        print("Error: Could not establish connection to the database.")
        return None
    cursor = db.cursor(buffered=True)
    try:
        query = "select cid from customers where uid = %s;"
        cursor.execute(query, (uid,))
        result = cursor.fetchone()
        if result:
            customer_id = result[0]
            return customer_id
        else:
            print("Error: No customer found for the given UID.")
            return None
    except mysql.connector.Error as err:
        print(f"Error: Database query failed. : {err}")
        return None
    finally:
        cursor.close()
        db.close()