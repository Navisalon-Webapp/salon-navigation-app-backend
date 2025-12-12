"""Utility helpers for loyalty point accrual and redemption."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Optional

import mysql.connector

POINTS_PER_DOLLAR = Decimal("1.0")
MIN_POINTS_PER_VISIT = Decimal("5")
DISCOUNT_PER_POINT = Decimal("0.10")


def _as_decimal(value: Optional[object]) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _ensure_tables(conn: mysql.connector.MySQLConnection) -> None:
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS customer_loyalty_points (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cid INT NOT NULL,
                bid INT NOT NULL,
                pts_balance DECIMAL(12, 2) NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uniq_customer_business (cid, bid)
            ) ENGINE=InnoDB
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS loyalty_point_events (
                event_id INT AUTO_INCREMENT PRIMARY KEY,
                aid INT NULL,
                cid INT NOT NULL,
                bid INT NOT NULL,
                points INT NOT NULL,
                source VARCHAR(32) NOT NULL DEFAULT 'visit',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uniq_aid (aid)
            ) ENGINE=InnoDB
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS loyalty_redemptions (
                redemption_id INT AUTO_INCREMENT PRIMARY KEY,
                cid INT NOT NULL,
                bid INT NOT NULL,
                points INT NOT NULL,
                discount DECIMAL(12, 2) NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
            """
        )
        conn.commit()
    finally:
        cursor.close()


def _fetch_program_details(conn: mysql.connector.MySQLConnection, bid: int) -> Optional[Dict[str, object]]:
    """Fetch the active loyalty configuration for a business."""

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT lp.threshold, lp.appts_thresh, lp.pdct_thresh, lp.points_thresh, lp.price_thresh,
                   r.is_appt, r.is_product, r.is_price, r.is_points, r.is_discount, r.rwd_value
            FROM loyalty_programs lp
            LEFT JOIN rewards r ON r.lprog_id = lp.lprog_id AND r.bid = lp.bid
            WHERE lp.bid = %s
            ORDER BY lp.lprog_id DESC
            LIMIT 1
            """,
            (bid,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()

    if not row:
        return None

    program_type = None
    if row.get("appts_thresh"):
        program_type = "appts_thresh"
    elif row.get("pdct_thresh"):
        program_type = "pdct_thresh"
    elif row.get("points_thresh"):
        program_type = "points_thresh"
    elif row.get("price_thresh"):
        program_type = "price_thresh"

    reward_type = None
    for key, label in (
        ("is_appt", "is_appt"),
        ("is_product", "is_product"),
        ("is_price", "is_price"),
        ("is_points", "is_points"),
        ("is_discount", "is_discount"),
    ):
        if row.get(key):
            reward_type = label
            break

    return {
        "program_type": program_type,
        "threshold": row.get("threshold"),
        "reward_type": reward_type,
        "reward_value": row.get("rwd_value"),
    }


def calculate_points(amount: Optional[object], override: Optional[int] = None) -> int:
    if override is not None:
        return max(int(override), 0)

    amount_dec = _as_decimal(amount)
    raw_points = (amount_dec * POINTS_PER_DOLLAR).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    points = int(raw_points)
    minimum = int(MIN_POINTS_PER_VISIT)
    if amount_dec > 0:
        points = max(points, minimum)
    if points <= 0:
        points = minimum
    return max(points, 0)


def get_balance(conn: mysql.connector.MySQLConnection, cid: int, bid: int) -> Decimal:
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT pts_balance FROM customer_loyalty_points WHERE cid = %s AND bid = %s",
            (cid, bid),
        )
        row = cursor.fetchone()
        return _as_decimal(row[0]) if row else Decimal("0")
    finally:
        cursor.close()


def award_points_for_visit(
    conn: mysql.connector.MySQLConnection,
    *,
    aid: Optional[int],
    cid: int,
    bid: int,
    amount: Optional[object] = None,
    quantity: Optional[int] = None,
    explicit_points: Optional[int] = None,
    source: str = "visit",
) -> Dict[str, object]:
    _ensure_tables(conn)
    program_details = _fetch_program_details(conn, bid) or {}
    program_type = program_details.get("program_type")
    reward_type = program_details.get("reward_type")
    reward_value = _as_decimal(program_details.get("reward_value")) if program_details.get("reward_value") is not None else Decimal("0")
    threshold = _as_decimal(program_details.get("threshold")) if program_details.get("threshold") is not None else Decimal("0")
    print("[award] program_details:", program_details)

    if explicit_points is not None:
        base_points = max(int(explicit_points), 0)
    elif program_type == "pdct_thresh":
        units = 1
        if quantity is not None:
            try:
                units = int(quantity)
            except (TypeError, ValueError):
                units = 1
        if units <= 0:
            units = 1
        base_points = units
    elif amount is not None:
        base_points = calculate_points(amount, None)
    else:
        base_points = 1

    if reward_type == "is_points" and program_type in {"appts_thresh", "pdct_thresh", "price_thresh"}:
        base_points = 0

    if base_points < 0:
        base_points = 0

    appt_increment = Decimal("1") if aid is not None else Decimal("0")
    prod_increment = Decimal("0")
    if quantity is not None:
        try:
            prod_increment = Decimal(str(max(int(quantity), 0)))
        except (TypeError, ValueError):
            prod_increment = Decimal("0")
    amount_increment = _as_decimal(amount) if amount is not None else Decimal("0")

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            """
            SELECT pts_balance, appt_complete, prod_purchased, amount_spent
            FROM customer_loyalty_points
            WHERE cid = %s AND bid = %s
            FOR UPDATE
            """,
            (cid, bid),
        )
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                """
                INSERT INTO customer_loyalty_points (cid, bid, pts_balance, prod_purchased, appt_complete, amount_spent)
                VALUES (%s, %s, 0, 0, 0, 0)
                """,
                (cid, bid),
            )
            row = {"pts_balance": Decimal("0"), "appt_complete": Decimal("0"), "prod_purchased": Decimal("0"), "amount_spent": Decimal("0")}

        current_appts = _as_decimal(row.get("appt_complete"))
        current_products = _as_decimal(row.get("prod_purchased"))
        current_amount = _as_decimal(row.get("amount_spent"))

        new_appts = current_appts + appt_increment
        new_products = current_products + prod_increment
        new_amount = current_amount + amount_increment

        bonus_points = Decimal("0")
        completions = 0

        if program_type == "appts_thresh" and threshold > Decimal("0"):
            completions = int(new_appts // threshold)
            if completions > 0:
                new_appts = new_appts - (threshold * completions)
        elif program_type == "pdct_thresh" and threshold > Decimal("0"):
            completions = int(new_products // threshold)
            if completions > 0:
                new_products = new_products - (threshold * completions)
        elif program_type == "price_thresh" and threshold > Decimal("0"):
            completions = int(new_amount // threshold)
            if completions > 0:
                new_amount = new_amount - (threshold * completions)

        if completions > 0 and reward_type == "is_points" and reward_value > Decimal("0"):
            bonus_points = (reward_value * completions).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

        total_points = Decimal(str(base_points)) + bonus_points
        print("[award] base:", base_points, "bonus:", bonus_points)
        if total_points <= Decimal("0"):
            cursor.close()
            balance = get_balance(conn, cid, bid)
            return {"awarded": False, "points": 0, "balance": float(balance)}

        cursor.execute(
            """
            UPDATE customer_loyalty_points
            SET pts_balance = pts_balance + %s,
                appt_complete = %s,
                prod_purchased = %s,
                amount_spent = %s
            WHERE cid = %s AND bid = %s
            """,
            (
                float(total_points),
                float(new_appts),
                float(new_products),
                float(new_amount),
                cid,
                bid,
            ),
        )

        event_cursor = conn.cursor()
        event_cursor.execute(
            """
            INSERT INTO loyalty_point_events (aid, cid, bid, points, source)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (aid, cid, bid, int(total_points), source),
        )
        event_cursor.close()
        conn.commit()
        balance = get_balance(conn, cid, bid)
        cursor.close()
        return {"awarded": True, "points": int(total_points), "balance": float(balance)}
    except mysql.connector.IntegrityError:
        conn.rollback()
        cursor.close()
        balance = get_balance(conn, cid, bid)
        return {"awarded": False, "points": 0, "balance": float(balance)}
    except Exception:
        conn.rollback()
        cursor.close()
        raise


def redeem_points(
    conn: mysql.connector.MySQLConnection,
    *,
    cid: int,
    bid: int,
    points: int,
    auto_commit: bool = True,
) -> Dict[str, object]:
    if points <= 0:
        raise ValueError("points to redeem must be positive")

    _ensure_tables(conn)
    cursor = conn.cursor()
    try:
        if auto_commit:
            conn.start_transaction()
        cursor.execute(
            "SELECT pts_balance FROM customer_loyalty_points WHERE cid = %s AND bid = %s FOR UPDATE",
            (cid, bid),
        )
        row = cursor.fetchone()
        if not row:
            if auto_commit:
                conn.rollback()
            raise ValueError("no loyalty balance for this salon")

        balance = _as_decimal(row[0])
        if balance < points:
            if auto_commit:
                conn.rollback()
            raise ValueError("insufficient loyalty points")

        new_balance = balance - Decimal(points)
        cursor.execute(
            "UPDATE customer_loyalty_points SET pts_balance = %s WHERE cid = %s AND bid = %s",
            (float(new_balance), cid, bid),
        )
        discount_value = (Decimal(points) * DISCOUNT_PER_POINT).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        cursor.execute(
            """
            INSERT INTO loyalty_redemptions (cid, bid, points, discount)
            VALUES (%s, %s, %s, %s)
            """,
            (cid, bid, points, float(discount_value)),
        )
        if auto_commit:
            conn.commit()
        return {"balance": float(new_balance), "discount": float(discount_value)}
    except Exception:
        if auto_commit:
            conn.rollback()
        raise
    finally:
        cursor.close()
