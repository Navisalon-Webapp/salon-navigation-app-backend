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
    explicit_points: Optional[int] = None,
    source: str = "visit",
) -> Dict[str, object]:
    _ensure_tables(conn)
    awarded_points = calculate_points(amount, explicit_points)
    if awarded_points <= 0:
        balance = get_balance(conn, cid, bid)
        return {"awarded": False, "points": 0, "balance": float(balance)}

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO loyalty_point_events (aid, cid, bid, points, source)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (aid, cid, bid, awarded_points, source),
        )
        cursor.execute(
            """
            INSERT INTO customer_loyalty_points (cid, bid, pts_balance)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE pts_balance = pts_balance + VALUES(pts_balance)
            """,
            (cid, bid, awarded_points),
        )
        conn.commit()
    except mysql.connector.IntegrityError:
        conn.rollback()
        balance = get_balance(conn, cid, bid)
        cursor.close()
        return {"awarded": False, "points": 0, "balance": float(balance)}
    except Exception:
        conn.rollback()
        cursor.close()
        raise
    else:
        balance = get_balance(conn, cid, bid)
        cursor.close()
        return {"awarded": True, "points": awarded_points, "balance": float(balance)}


def redeem_points(
    conn: mysql.connector.MySQLConnection,
    *,
    cid: int,
    bid: int,
    points: int,
) -> Dict[str, object]:
    if points <= 0:
        raise ValueError("points to redeem must be positive")

    _ensure_tables(conn)
    cursor = conn.cursor()
    try:
        conn.start_transaction()
        cursor.execute(
            "SELECT pts_balance FROM customer_loyalty_points WHERE cid = %s AND bid = %s FOR UPDATE",
            (cid, bid),
        )
        row = cursor.fetchone()
        if not row:
            conn.rollback()
            raise ValueError("no loyalty balance for this salon")

        balance = _as_decimal(row[0])
        if balance < points:
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
        conn.commit()
        return {"balance": float(new_balance), "discount": float(discount_value)}
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
