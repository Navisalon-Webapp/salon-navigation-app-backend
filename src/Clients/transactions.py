from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from mysql.connector import Error
from helper.utils import *
from src.LoyaltyProgram.loyalty_service import DISCOUNT_PER_POINT, redeem_points
from datetime import timedelta, datetime
from decimal import Decimal, ROUND_HALF_UP
TAX_RATE = Decimal("0.06125")

transaction = Blueprint('transaction', __name__,)


def _percentage_multiplier(raw: Decimal) -> Decimal:
    """Interpret a stored percentage that may be persisted as either 0-1 or 0-100."""
    if raw is None:
        return Decimal("0")
    if raw <= Decimal("0"):
        return Decimal("0")
    if raw <= Decimal("1"):
        return raw
    return raw / Decimal("100")

@transaction.route('/transactions/checkout/', methods=["POST"])
@login_required
def process_checkout():
    data = request.get_json() or {}
    cid = get_cid()
    bid = data.get("bid")
    payment_method_id = data.get("payment_method_id")
    is_product_purchase = bool(data.get("is_product_purchase", False))
    aid = data.get("aid")
    raw_points = data.get("loyalty_points_to_redeem", 0)

    try:
        payment_method_id = int(payment_method_id)
    except (TypeError, ValueError):
        payment_method_id = None

    try:
        loyalty_points_to_redeem = max(int(raw_points or 0), 0)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid loyalty points value"}), 400

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
        manual_loyalty_discount = Decimal("0")
        redemption_result = None
        skip_points_bonus = False

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

        cursor.execute(
            """
            INSERT INTO customer_loyalty_points (cid, bid, pts_balance, prod_purchased, appt_complete, amount_spent)
            VALUES (%s, %s, 0, 0, 0, 0)
            ON DUPLICATE KEY UPDATE cid = cid
            """,
            (cid, bid),
        )

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
                percent_multiplier = _percentage_multiplier(reward_val)
                promo_discount += percent_multiplier * original_amount
                applied_promo_lprog = p["lprog_id"]

        appointment_increment = Decimal("0")
        product_increment = Decimal("0")
        if is_product_purchase:
            product_increment = sum(Decimal(str(max(int(item.get("amount", 0)), 0))) for item in cart_items)
        else:
            appointment_increment = Decimal("1")
        amount_increment = original_amount

        cursor.execute("""
            SELECT lp.lprog_id, lp.description, c.pts_balance, c.appt_complete, c.prod_purchased, c.amount_spent,
                   lp.appts_thresh, lp.pdct_thresh, lp.price_thresh, lp.points_thresh, lp.threshold,
                   r.rwd_id, r.is_appt, r.is_product, r.is_price, r.is_points, r.is_discount, r.rwd_value, l.pts_value
            FROM customer_loyalty_points c
            JOIN loyalty_programs lp ON lp.bid = c.bid
            JOIN rewards r ON r.lprog_id = lp.lprog_id
            JOIN loyalty_points l on l.bid = lp.bid
            WHERE c.cid = %s AND c.bid = %s
        """, (cid, bid))
        reward_rows = cursor.fetchall()

        points_balance_val = Decimal("0")
        if bid:
            cursor.execute(
                "SELECT pts_balance FROM customer_loyalty_points WHERE cid = %s AND bid = %s",
                (cid, bid),
            )
            balance_row = cursor.fetchone()
            if balance_row is not None:
                if isinstance(balance_row, dict):
                    points_balance_val = to_decimal(balance_row.get("pts_balance"))
                else:
                    points_balance_val = to_decimal(balance_row[0])

        if loyalty_points_to_redeem > 0:
            try:
                redemption_result = redeem_points(
                    conn,
                    cid=cid,
                    bid=bid,
                    points=loyalty_points_to_redeem,
                    auto_commit=False,
                )
            except ValueError as exc:
                conn.rollback()
                return jsonify({"error": str(exc)}), 400

            manual_loyalty_discount = to_decimal(
                (redemption_result or {}).get("discount", 0)
            )
            points_balance_val = to_decimal((redemption_result or {}).get("balance", points_balance_val))
            skip_points_bonus = True

        loyalty_discount = Decimal("0")
        loyalty_redeemed_lprog = None
        thresh_met = []
        points_bonus = Decimal("0")

        def decrement_progress(progress_trigger: str, amount: Decimal) -> None:
            if amount <= Decimal("0"):
                return
            print(f"[checkout] decrementing {progress_trigger} by {amount}")
            if progress_trigger == "appts":
                cursor.execute(
                    """
                    UPDATE customer_loyalty_points
                    SET appt_complete = appt_complete - %s
                    WHERE cid=%s AND bid=%s
                    """,
                    (float(amount), cid, bid),
                )
            elif progress_trigger == "products":
                cursor.execute(
                    """
                    UPDATE customer_loyalty_points
                    SET prod_purchased = prod_purchased - %s
                    WHERE cid=%s AND bid=%s
                    """,
                    (float(amount), cid, bid),
                )
            elif progress_trigger == "price":
                cursor.execute(
                    """
                    UPDATE customer_loyalty_points
                    SET amount_spent = amount_spent - %s
                    WHERE cid=%s AND bid=%s
                    """,
                    (float(amount), cid, bid),
                )
            elif progress_trigger == "points":
                cursor.execute(
                    """
                    UPDATE customer_loyalty_points
                    SET pts_balance = pts_balance - %s
                    WHERE cid=%s AND bid=%s
                    """,
                    (float(amount), cid, bid),
                )

        print("[checkout] rewards fetched:", reward_rows)
        print("[preview] rewards fetched:", reward_rows)
        for r in reward_rows:
            base_threshold = to_decimal(r.get("threshold")) if r.get("threshold") is not None else Decimal("0")

            if r["appts_thresh"]:
                required = base_threshold if base_threshold > Decimal("0") else Decimal("1")
                appt_progress = to_decimal(r.get("appt_complete", 0)) + appointment_increment
                completions = int(appt_progress // required) if required > Decimal("0") else 0
                if completions > 0:
                    thresh_met.append((r, "appts", required, completions))

            if r["pdct_thresh"]:
                required = base_threshold if base_threshold > Decimal("0") else Decimal("1")
                product_progress = to_decimal(r.get("prod_purchased", 0)) + product_increment
                completions = int(product_progress // required) if required > Decimal("0") else 0
                if completions > 0:
                    thresh_met.append((r, "products", required, completions))

            if r["price_thresh"]:
                required = base_threshold if base_threshold > Decimal("0") else Decimal("0")
                amount_progress = to_decimal(r.get("amount_spent", 0)) + amount_increment
                completions = int(amount_progress // required) if required > Decimal("0") else 0
                if completions > 0:
                    thresh_met.append((r, "price", required, completions))

            if r["points_thresh"]:
                required = base_threshold if base_threshold > Decimal("0") else Decimal("0")
                points_progress = to_decimal(r.get("pts_balance", 0))
                completions = int(points_progress // required) if required > Decimal("0") else 0
                if completions > 0:
                    thresh_met.append((r, "points", required, completions))
        print("[checkout] thresholds met:", thresh_met)
        print("[preview] thresholds met:", thresh_met)
        for r, trigger, threshold_value_dec, completions in thresh_met:
            if completions <= 0:
                continue
            reward_val = to_decimal(r["rwd_value"])
            if threshold_value_dec <= Decimal("0"):
                threshold_value_dec = Decimal("1")
            consume_amount = threshold_value_dec * completions
            print("[checkout] applying reward", r["rwd_id"], "type", trigger, "threshold", threshold_value_dec, "completions", completions)

            if r["is_points"]:
                if skip_points_bonus and trigger == "points":
                    # Redemption already consumed the point-based progress; avoid double-deducting.
                    continue
                bonus_increment = (reward_val * completions).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                points_bonus += bonus_increment
                loyalty_redeemed_lprog = r["lprog_id"]
                decrement_progress(trigger, consume_amount)
                continue

            if not is_product_purchase and r["is_appt"]:
                unit_reward = (reward_val * sing_disc).quantize(Decimal("0.01"))
                loyalty_discount += unit_reward * completions
                loyalty_redeemed_lprog = r["lprog_id"]
                decrement_progress(trigger, consume_amount)
            elif is_product_purchase and r["is_product"]:
                unit_reward = (reward_val * sing_disc).quantize(Decimal("0.01"))
                loyalty_discount += unit_reward * completions
                loyalty_redeemed_lprog = r["lprog_id"]
                decrement_progress(trigger, consume_amount)
            elif r["is_price"]:
                unit_reward = reward_val.quantize(Decimal("0.01"))
                loyalty_discount += unit_reward * completions
                loyalty_redeemed_lprog = r["lprog_id"]
                decrement_progress(trigger, consume_amount)
            elif r["is_discount"]:
                percent_multiplier = _percentage_multiplier(reward_val)
                unit_reward = (percent_multiplier * original_amount).quantize(Decimal("0.01"))
                loyalty_discount += unit_reward * completions
                loyalty_redeemed_lprog = r["lprog_id"]
                decrement_progress(trigger, consume_amount)
            # points rewards handled earlier
        tax = (original_amount * TAX_RATE).quantize(Decimal("0.01"))
        combined_loyalty_discount = (loyalty_discount + manual_loyalty_discount).quantize(Decimal("0.01"))
        total_discount = (promo_discount + combined_loyalty_discount).quantize(Decimal("0.01"))
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
        print("[checkout] points earned:", points_earned, "bonus:", points_bonus)
        points_to_add = points_earned + points_bonus

        cursor.execute("""
            UPDATE customer_loyalty_points
            SET pts_balance = pts_balance + %s,
                prod_purchased = prod_purchased + %s,
                appt_complete = appt_complete + %s,
                amount_spent = amount_spent + %s
            WHERE cid=%s AND bid=%s
        """, (
            float(points_to_add),
            int(product_increment) if is_product_purchase else 0,
            0 if is_product_purchase else 1,
            float(final_amount),
            cid,
            bid
        ))
        points_balance_val = points_balance_val + points_to_add

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
            "trans_id": trans_id,
            "loyalty_discount": float(combined_loyalty_discount),
            "loyalty_points_discount": float(manual_loyalty_discount),
            "points_redeemed": loyalty_points_to_redeem,
            "loyalty_balance": float(redemption_result.get("balance")) if redemption_result else float(points_balance_val)
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

        cursor.execute(
            """
            INSERT INTO customer_loyalty_points (cid, bid, pts_balance, prod_purchased, appt_complete, amount_spent)
            VALUES (%s, %s, 0, 0, 0, 0)
            ON DUPLICATE KEY UPDATE cid = cid
            """,
            (cid, bid),
        )

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
                promo_discount += reward

            if p["is_product"]:
                reward = (reward_val * sing_disc).quantize(Decimal("0.01"))
                promos.append({"promo_id": p["promo_id"], "title": p["title"], "description": p["description"], "reward_type": "product", "threshold": 0, "reward": float(p["rwd_value"]), "rwd_value": float(reward)})
                promo_discount += reward

            if p["is_price"]:
                reward = reward_val.quantize(Decimal("0.01"))
                promos.append({"promo_id": p["promo_id"], "title": p["title"], "description": p["description"], "reward_type": "price", "threshold": 0, "reward": float(p["rwd_value"]), "rwd_value": float(reward)})
                promo_discount += reward

            if p["is_points"]:
                reward = (reward_val * to_decimal(p["pts_value"])).quantize(Decimal("0.01"))
                promos.append({"promo_id": p["promo_id"], "title": p["title"], "description": p["description"], "reward_type": "points", "threshold": 0, "reward": float(p["rwd_value"]), "rwd_value": float(reward)})
                promo_discount += reward

            if p["is_discount"]:
                percent_multiplier = _percentage_multiplier(reward_val)
                reward = (percent_multiplier * original_amount).quantize(Decimal("0.01"))
                promos.append({
                    "promo_id": p["promo_id"],
                    "title": p["title"],
                    "description": p["description"],
                    "reward_type": "discount",
                    "threshold": 0,
                    "reward": float((percent_multiplier * Decimal("100")).quantize(Decimal("0.01"))),
                    "rwd_value": float(reward)
                })
                promo_discount += reward

        appointment_increment = Decimal("0")
        product_increment = Decimal("0")
        if is_product_purchase:
            product_increment = sum(to_decimal(item.get("amount", 0)) for item in cart_items)
        else:
            appointment_increment = Decimal("1")
        amount_increment = original_amount

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

        points_balance_val = Decimal("0")
        if bid:
            cursor.execute(
                "SELECT pts_balance FROM customer_loyalty_points WHERE cid = %s AND bid = %s",
                (cid, bid),
            )
            balance_row = cursor.fetchone()
            if balance_row is not None:
                if isinstance(balance_row, dict):
                    points_balance_val = to_decimal(balance_row.get("pts_balance"))
                else:
                    points_balance_val = to_decimal(balance_row[0])

        loyalty_discount = Decimal("0")
        progs = []
        thresh_met = []
        points_bonus = Decimal("0")

        for r in reward_rows:
            base_threshold = to_decimal(r.get("threshold")) if r.get("threshold") is not None else Decimal("0")

            if r["appts_thresh"]:
                required = base_threshold if base_threshold > Decimal("0") else Decimal("1")
                appt_progress = to_decimal(r.get("appt_complete", 0)) + appointment_increment
                completions = int(appt_progress // required) if required > Decimal("0") else 0
                if completions > 0:
                    thresh_met.append((r, "appts", required, completions))

            if r["pdct_thresh"]:
                required = base_threshold if base_threshold > Decimal("0") else Decimal("1")
                product_progress = to_decimal(r.get("prod_purchased", 0)) + product_increment
                completions = int(product_progress // required) if required > Decimal("0") else 0
                if completions > 0:
                    thresh_met.append((r, "products", required, completions))

            if r["price_thresh"]:
                required = base_threshold if base_threshold > Decimal("0") else Decimal("0")
                amount_progress = to_decimal(r.get("amount_spent", 0)) + amount_increment
                completions = int(amount_progress // required) if required > Decimal("0") else 0
                if completions > 0:
                    thresh_met.append((r, "price", required, completions))

            if r["points_thresh"]:
                required = base_threshold if base_threshold > Decimal("0") else Decimal("0")
                points_progress = to_decimal(r.get("pts_balance", 0))
                completions = int(points_progress // required) if required > Decimal("0") else 0
                if completions > 0:
                    thresh_met.append((r, "points", required, completions))

        for r, trigger, threshold_value_dec, completions in thresh_met:
            if completions <= 0:
                continue
            reward_val = to_decimal(r["rwd_value"])
            if threshold_value_dec <= Decimal("0"):
                threshold_value_dec = Decimal("1")
            print("[preview] applying reward", r["rwd_id"], "type", trigger, "threshold", threshold_value_dec, "completions", completions)

            if r["is_points"]:
                bonus_increment = (reward_val * completions).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                points_bonus += bonus_increment
                progs.append({
                    "rwd_id": r["rwd_id"],
                    "description": r["description"],
                    "threshold": float(threshold_value_dec),
                    "reward_type": "points",
                    "reward": float(bonus_increment),
                    "rwd_value": 0.0
                })
                continue

            if not is_product_purchase and r["is_appt"]:
                reward = (reward_val * sing_disc).quantize(Decimal("0.01"))
                total_reward = reward * completions
                progs.append({
                    "rwd_id": r["rwd_id"],
                    "description": r["description"],
                    "threshold": float(threshold_value_dec),
                    "reward_type": "appointment",
                    "reward": float(r["rwd_value"] * completions),
                    "rwd_value": float(total_reward)
                })
                loyalty_discount += total_reward
            elif is_product_purchase and r["is_product"]:
                reward = (reward_val * sing_disc).quantize(Decimal("0.01"))
                total_reward = reward * completions
                progs.append({
                    "rwd_id": r["rwd_id"],
                    "description": r["description"],
                    "threshold": float(threshold_value_dec),
                    "reward_type": "product",
                    "reward": float(r["rwd_value"] * completions),
                    "rwd_value": float(total_reward)
                })
                loyalty_discount += total_reward
            elif r["is_price"]:
                reward = reward_val.quantize(Decimal("0.01"))
                total_reward = reward * completions
                progs.append({
                    "rwd_id": r["rwd_id"],
                    "description": r["description"],
                    "threshold": float(threshold_value_dec),
                    "reward_type": "price",
                    "reward": float(r["rwd_value"] * completions),
                    "rwd_value": float(total_reward)
                })
                loyalty_discount += total_reward
            elif r["is_discount"]:
                percent_multiplier = _percentage_multiplier(reward_val)
                reward = (percent_multiplier * original_amount).quantize(Decimal("0.01"))
                total_reward = reward * completions
                progs.append({
                    "rwd_id": r["rwd_id"],
                    "description": r["description"],
                    "threshold": float(threshold_value_dec),
                    "reward_type": "discount",
                    "reward": float((percent_multiplier * Decimal("100")).quantize(Decimal("0.01")) * completions),
                    "rwd_value": float(total_reward)
                })
                loyalty_discount += total_reward
            # points rewards handled earlier

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
            "loyalty_progs": progs,
            "loyalty_balance": float(points_balance_val),
            "loyalty_point_value": float(DISCOUNT_PER_POINT),
            "bonus_points": float(points_bonus)
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

    db = get_db_connection()
    if db is None:
        print("Error: Could not establish connection to the database.")
        return None

    cursor = db.cursor(buffered=True)
    try:
        query = "select cid from customers where uid = %s;"
        cursor.execute(query, (uid,))
        result = cursor.fetchone()
        if result:
            customer_id = result[0] if not isinstance(result, dict) else result.get("cid")
            return customer_id
        else:
            print("Error: No customer found for the given UID.")
            return None
    except Error as err:
        print(f"Error: Database query failed. : {err}")
        return None
    finally:
        cursor.close()
        db.close()