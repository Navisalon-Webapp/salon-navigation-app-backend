from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from mysql.connector import Error
from helper.utils import *
from datetime import timedelta, datetime
from decimal import Decimal
TAX_RATE = Decimal("0.06125")

transaction = Blueprint('transaction', __name__,)

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
    data = request.get_json()
    cid = current_user.id
    bid = data.get("bid")
    payment_method_id = data.get("payment_method_id")
    is_product_purchase = data.get("is_product_purchase", False)

    if not (cid and bid and payment_method_id):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Checkout subtotal from products
        if is_product_purchase:
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

            original_amount = sum(item["amount"] * item["price"] for item in cart_items)
            sing_disc = cart_items[0]["price"]
            appointment_id = None

        else:
            # Checkout subtotal from appointments
            cursor.execute("""
                SELECT a.aid, s.price
                FROM appointments a
                JOIN services s ON s.sid=a.sid
                WHERE a.cid = %s AND a.bid = %s AND a.status = 'pending_payment'
                ORDER BY a.created_at DESC LIMIT 1
            """, (cid, bid))
            appt = cursor.fetchone()

            if not appt:
                return jsonify({"error": "No appointment found"}), 400

            original_amount = appt["price"]
            sing_disc = appt["price"]
            appointment_id = appt["aid"]

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

        promo_discount = 0
        applied_promo_lprog = None

        for p in promotions:
            if p["is_appt"]:
                promo_discount += Decimal(p["rwd_value"]) * Decimal(sing_disc)
                applied_promo_lprog = p["lprog_id"]
            if p["is_product"]:
                promo_discount += Decimal(p["rwd_value"]) * Decimal(sing_disc)
                applied_promo_lprog = p["lprog_id"]
            if p["is_price"]:
                promo_discount += Decimal(p["rwd_value"])
                applied_promo_lprog = p["lprog_id"]
            if p["is_points"]:
                promo_discount += Decimal(p["rwd_value"]) * Decimal(p["pts_value"])
                applied_promo_lprog = p["lprog_id"]
            if p["is_discount"]:
                promo_discount += Decimal(p["rwd_value"]) * Decimal(.01) * Decimal(original_amount)
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

        loyalty_discount = 0
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
            # appointment reward
            if not is_product_purchase and r["is_appt"] and (r["threshold"] > 0):
                loyalty_discount += Decimal(r["rwd_value"]) * Decimal(sing_disc)
                loyalty_redeemed_lprog = r["lprog_id"]

                # deduct appointments completed from balance
                cursor.execute("""
                    UPDATE customer_loyalty_points
                    SET appt_complete = appt_complete - %s
                    WHERE cid=%s AND bid=%s
                """, (loyalty_discount, cid, bid))

            # product reward
            if is_product_purchase and r["is_product"] and (r["threshold"] > 0):
                loyalty_discount += Decimal(r["rwd_value"]) * Decimal(sing_disc)
                loyalty_redeemed_lprog = r["lprog_id"]
                
                # deduct products purchased from balance
                cursor.execute("""
                    UPDATE customer_loyalty_points
                    SET prod_purchased = prod_purchased - %s
                    WHERE cid=%s AND bid=%s
                """, (loyalty_discount, cid, bid))

            # price reward
            if r["is_price"] and (r["threshold"] > 0):
                loyalty_discount += Decimal(r["rwd_value"])
                loyalty_redeemed_lprog = r["lprog_id"]

                # deduct amount spent from balance
                cursor.execute("""
                    UPDATE customer_loyalty_points
                    SET amount_spent = amount_spent - %s
                    WHERE cid=%s AND bid=%s
                """, (loyalty_discount, cid, bid))
            
            # discount reward
            if r["is_discount"] and (r["threshold"] > 0):
                loyalty_discount += Decimal(r["rwd_value"]) * Decimal(.01) * Decimal(original_amount)
                loyalty_redeemed_lprog = r["lprog_id"]

            # points redemption
            if r["is_points"] and (r["threshold"] > 0):
                loyalty_discount += Decimal(r["rwd_value"]) * Decimal(p["pts_value"])
                loyalty_redeemed_lprog = r["lprog_id"]

                # deduct points from balance
                cursor.execute("""
                    UPDATE customer_loyalty_points
                    SET pts_balance = pts_balance - %s
                    WHERE cid=%s AND bid=%s
                """, (loyalty_discount, cid, bid))

        tax = original_amount * TAX_RATE
        total_discount = promo_discount + loyalty_discount
        final_amount = max(0, round(original_amount + tax - total_discount, 2))

        cursor.execute("""
            INSERT INTO transactions (cid, bid, aid, amount, payment_method_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (cid, bid, appointment_id, final_amount, payment_method_id))
        trans_id = cursor.lastrowid

        if is_product_purchase:
            for item in cart_items:
                cursor.execute("""
                    INSERT INTO transactions_products (trans_id, pid, amount)
                    VALUES (%s, %s, %s)
                """, (trans_id, item["pid"], item["amount"]))

                cursor.execute("""
                    SELECT name, stock
                    FROM products
                    WHERE pid=%s
                """, (item["pid"],))
                product_stock = cursor.fetchall()

                for product in product_stock:
                    if product["stock"] < item["amount"]:
                        return jsonify({"error": "Not enough stock to complete purchase"}), 400
                
                cursor.execute("""
                    UPDATE products
                    SET stock = stock - %s
                    WHERE pid=%s
                """, (item["amount"], item["pid"]))

        cursor.execute("""
            SELECT pts_value FROM loyalty_points WHERE bid=%s
        """, (bid,),)
        pts_row = cursor.fetchone()
        pts_value = Decimal(pts_row["pts_value"]) if pts_row else 1.0

        points_earned = final_amount * pts_value

        cursor.execute("""
            UPDATE customer_loyalty_points
            SET pts_balance = pts_balance + %s,
                prod_purchased = prod_purchased + %s,
                appt_complete = appt_complete + %s,
                amount_spent = amount_spent + %s
            WHERE cid=%s AND bid=%s
        """, (
            points_earned,
            len(cart_items) if is_product_purchase else 0,
            0 if is_product_purchase else 1,
            final_amount,
            cid,
            bid
        ))

        if applied_promo_lprog:
            cursor.execute("""
                INSERT INTO loyalty_transactions (cid, trans_id, lprog_id, val_earned, val_redeemed)
                VALUES (%s, %s, %s, %s, %s)
            """, (cid, trans_id, applied_promo_lprog, total_discount, promo_discount))

        if loyalty_redeemed_lprog:
            cursor.execute("""
                INSERT INTO loyalty_transactions (cid, trans_id, lprog_id, val_earned, val_redeemed)
                VALUES (%s, %s, %s, %s, %s)
            """, (cid, trans_id, loyalty_redeemed_lprog, total_discount, loyalty_discount))

        cursor.execute("""
            INSERT INTO monthly_revenue (bid, year, month, revenue)
            VALUES (%s, YEAR(NOW()), MONTH(NOW()), %s)
            ON DUPLICATE KEY UPDATE revenue = revenue + %s
        """, (bid, final_amount, final_amount))

        if is_product_purchase:
            cursor.execute("DELETE FROM cart WHERE cid=%s AND bid=%s", (cid, bid))

        conn.commit()

        return jsonify({
            "success": True,
            "original_amount": Decimal(original_amount),
            "discount": Decimal(total_discount),
            "final_amount": Decimal(final_amount),
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
    cid = current_user.id
    bid = request.args.get("bid")
    is_product_purchase = request.args.get("is_product_purchase", False)

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Checkout subtotal from products
        if is_product_purchase:
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

            original_amount = sum(item["amount"] * item["price"] for item in cart_items)
            sing_disc = cart_items[0]["price"]

        else:
            # Checkout subtotal from appointments
            cursor.execute("""
                SELECT a.aid, s.price
                FROM appointments a
                JOIN services s ON s.sid=a.sid
                WHERE a.cid = %s AND a.bid = %s AND a.status = 'pending_payment'
                ORDER BY a.created_at DESC LIMIT 1
            """, (cid, bid))
            appt = cursor.fetchone()

            if not appt:
                return jsonify({"error": "No appointment found"}), 400

            original_amount = appt["price"]
            sing_disc = appt["price"]

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

        promo_discount = 0
        promos = []

        for p in promotions:
            if p["is_appt"]:
                reward = round(Decimal(p["rwd_value"]) * Decimal(sing_disc), 2)
                promos.append({"promo_id": p["promo_id"], "title": p["title"], "description": p["description"], "reward_type": "appointment", "threshold": 0, "reward": p["rwd_value"], "rwd_value": reward})

            if p["is_product"]:
                reward = round(Decimal(p["rwd_value"]) * Decimal(sing_disc), 2)
                promos.append({"promo_id": p["promo_id"], "title": p["title"], "description": p["description"], "reward_type": "product", "threshold": 0, "reward": p["rwd_value"], "rwd_value": reward})

            if p["is_price"]:
                reward = round(Decimal(p["rwd_value"]), 2)
                promos.append({"promo_id": p["promo_id"], "title": p["title"], "description": p["description"], "reward_type": "price", "threshold": 0, "reward": p["rwd_value"], "rwd_value": reward})

            if p["is_points"]:
                reward = round(Decimal(p["rwd_value"]) * Decimal(p["pts_value"]), 2)
                promos.append({"promo_id": p["promo_id"], "title": p["title"], "description": p["description"], "reward_type": "points", "threshold": 0, "reward": p["rwd_value"], "rwd_value": reward})

            if p["is_discount"]:
                reward = round(Decimal(p["rwd_value"]) * Decimal(.01) * Decimal(original_amount), 2)
                promos.append({"promo_id": p["promo_id"], "title": p["title"], "description": p["description"], "reward_type": "discount", "threshold": 0, "reward": p["rwd_value"], "rwd_value": reward})

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

        loyalty_discount = 0
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
            # appointment reward
            if not is_product_purchase and r["is_appt"] and (r["threshold"] > 0):
                reward = round(Decimal(r["rwd_value"]) * Decimal(sing_disc), 2)
                progs.append({"rwd_id": r["rwd_id"], "description": r["description"], "threshold": r["threshold"], "reward_type": "appointment", "rwd_value": r["rwd_value"], "rwd_value": reward})

            # product reward
            if is_product_purchase and r["is_product"] and (r["threshold"] > 0):
                reward = round(Decimal(r["rwd_value"]) * Decimal(sing_disc), 2)
                progs.append({"rwd_id": r["rwd_id"], "description": r["description"], "threshold": r["threshold"], "reward_type": "product", "rwd_value": r["rwd_value"], "rwd_value": reward})

            # price reward
            if r["is_price"] and (r["threshold"] > 0):
                reward = round(Decimal(r["rwd_value"]), 2)
                progs.append({"rwd_id": r["rwd_id"], "description": r["description"], "threshold": r["threshold"], "reward_type": "price", "rwd_value": r["rwd_value"], "rwd_value": reward})

            # discount reward
            if r["is_discount"] and (r["threshold"] > 0):
                reward = round(Decimal(r["rwd_value"]) * Decimal(.01) * Decimal(original_amount), 2)
                progs.append({"rwd_id": r["rwd_id"], "description": r["description"], "threshold": r["threshold"], "reward_type": "discount", "rwd_value": r["rwd_value"], "rwd_value": reward})
            
            # points reward
            if r["is_points"] and (r["threshold"] > 0):
                reward = round(Decimal(r["rwd_value"]) * Decimal(p["pts_value"]), 2)
                progs.append({"rwd_id": r["rwd_id"], "description": r["description"], "threshold": r["threshold"], "reward_type": "points", "rwd_value": r["rwd_value"], "rwd_value": reward})
            
            loyalty_discount += reward

        tax = round(original_amount * TAX_RATE, 2)
        total_discount = promo_discount + loyalty_discount
        final_amount = max(0, round(original_amount + tax - total_discount, 2))

        return jsonify({
            "status": "success",
            "subtotal": original_amount,
            "tax": tax,
            "discount": total_discount,
            "total": final_amount,
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