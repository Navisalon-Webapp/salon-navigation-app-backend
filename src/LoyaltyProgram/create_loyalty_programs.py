from flask import request, jsonify, Blueprint
from flask_login import login_required
import mysql.connector
from dotenv import load_dotenv
import os

from helper.utils import check_role, get_curr_bid

load_dotenv()

loyalty_prog = Blueprint('loyalty_prog', __name__)





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




#Salon Owner can create loyalty programs
@loyalty_prog.route("/api/owner/create-loyalty-programs", methods=["POST"])
@login_required
def create_lprogs():
    if check_role() != "owner":
        return jsonify({"message": "Only salon owners can configure loyalty programs."}), 403
    data = request.get_json()

    try:
        business_id = get_curr_bid()
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400
    threshold = data.get("threshold")
    prog_type = data.get("prog_type")
    reward_type = data.get("reward_type")
    reward_value = data.get("rwd_value")

    allowed_prog_types = ["appts_thresh", "pdct_thresh","points_thresh", "price_thresh"]
    if prog_type not in allowed_prog_types:
        return jsonify({"message": "Invalid program type. Must literally use the terms in quotes: 'appts_thresh', 'pdct_thresh','points_thresh', 'price_thresh'. "}), 400
    
    allowed_reward_types = ["is_appt","is_product","is_price", "is_points", "is_discount"]
    if reward_type not in allowed_reward_types:
        return jsonify({"message": "Invalid reward type. "
        "Must literally use the terms in quotes: 'is_appt','is_product','is_price', 'is_points', 'is_discount'. "}), 400
    
    db = None
    cursor = None
    try:
        db = get_db()

        if db is None:
            print("Error: Could not establish connection to the database.")
            return jsonify({"message": "Could not connect to database."}), 500
    
        cursor = db.cursor(buffered=True)

        #f string: cleanly insert prog_type into query
        query_lprog = f"""
        insert into loyalty_programs(bid, {prog_type}, threshold)
        values(%s, %s, %s);
         """
        cursor.execute(query_lprog, (business_id, True, threshold))
        lprog_id = cursor.lastrowid
        query_rwd = f"""
        insert into rewards(bid, lprog_id, {reward_type}, rwd_value)
        values(%s,%s, %s, %s);
         """
        cursor.execute(query_rwd, (business_id, lprog_id, True, reward_value))
        db.commit()
        return jsonify({"message": "Loyalty program created successfully.", "lprog_id": lprog_id }), 201
    except mysql.connector.Error as err:
        print(f"Error: Loyalty program creation unsuccessful. : {err}")
        if db:
            db.rollback() 
        return jsonify({"message": "Failed to create loyalty program."}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@loyalty_prog.route("/api/owner/loyalty-programs", methods=["GET"])
@login_required
def list_loyalty_programs():
    if check_role() != "owner":
        return jsonify({"message": "Only salon owners can view loyalty programs."}), 403

    try:
        bid = get_curr_bid()
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400

    db = None
    cursor = None
    rewards_cursor = None
    try:
        db = get_db()
        if db is None:
            return jsonify({"message": "Could not connect to database."}), 500

        cursor = db.cursor(dictionary=True, buffered=True)
        cursor.execute(
            """
            SELECT lprog_id, threshold, appts_thresh, pdct_thresh, points_thresh, price_thresh
            FROM loyalty_programs
            WHERE bid = %s
            ORDER BY lprog_id DESC
            """,
            (bid,),
        )
        programs = cursor.fetchall()

        rewards_cursor = db.cursor(dictionary=True, buffered=True)
        payload = []
        reward_flags = ["is_appt", "is_product", "is_price", "is_points", "is_discount"]
        for program in programs:
            rewards_cursor.execute(
                "SELECT * FROM rewards WHERE bid = %s AND lprog_id = %s LIMIT 1",
                (bid, program["lprog_id"]),
            )
            reward_row = rewards_cursor.fetchone() or {}
            active_reward = next((flag for flag in reward_flags if reward_row.get(flag)), None)
            reward_value = reward_row.get("rwd_value")
            payload.append(
                {
                    "lprog_id": program["lprog_id"],
                    "threshold": float(program.get("threshold") or 0),
                    "program_type": next(
                        (
                            flag
                            for flag, active in (
                                ("appts_thresh", program.get("appts_thresh")),
                                ("pdct_thresh", program.get("pdct_thresh")),
                                ("points_thresh", program.get("points_thresh")),
                                ("price_thresh", program.get("price_thresh")),
                            )
                            if active
                        ),
                        None,
                    ),
                    "reward_type": active_reward,
                    "reward_value": float(reward_value) if reward_value is not None else None,
                }
            )

        return jsonify({"status": "success", "programs": payload}), 200
    except mysql.connector.Error as err:
        return jsonify({"message": f"Database error: {err}"}), 500
    finally:
        if rewards_cursor:
            rewards_cursor.close()
        if cursor:
            cursor.close()
        if db:
            db.close()


@loyalty_prog.route("/api/owner/loyalty-programs/<int:lprog_id>", methods=["PUT"])
@login_required
def update_loyalty_program(lprog_id: int):
    if check_role() != "owner":
        return jsonify({"message": "Only salon owners can update loyalty programs."}), 403

    data = request.get_json() or {}
    threshold = data.get("threshold")
    reward_type = data.get("reward_type")
    reward_value = data.get("rwd_value")

    allowed_program_types = ["appts_thresh", "pdct_thresh", "points_thresh", "price_thresh"]
    allowed_reward_types = ["is_appt", "is_product", "is_price", "is_points", "is_discount"]

    if reward_type and reward_type not in allowed_reward_types:
        return jsonify({"message": "Invalid reward type provided."}), 400

    prog_type = data.get("prog_type")
    if prog_type and prog_type not in allowed_program_types:
        return jsonify({"message": "Invalid program type provided."}), 400

    if threshold is not None:
        try:
            threshold = float(threshold)
        except (TypeError, ValueError):
            return jsonify({"message": "Threshold must be a number."}), 400

    if reward_value is not None:
        try:
            reward_value = float(reward_value)
        except (TypeError, ValueError):
            return jsonify({"message": "Reward value must be a number."}), 400

    try:
        bid = get_curr_bid()
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400

    db = None
    cursor = None
    try:
        db = get_db()
        if db is None:
            return jsonify({"message": "Could not connect to database."}), 500

        cursor = db.cursor()
        updates = []
        params = []
        if threshold is not None:
            updates.append("threshold = %s")
            params.append(threshold)

        if prog_type:
            for prog in allowed_program_types:
                updates.append(f"{prog} = %s")
                params.append(1 if prog == prog_type else 0)

        if updates:
            params.extend([lprog_id, bid])
            cursor.execute(
                f"UPDATE loyalty_programs SET {', '.join(updates)} WHERE lprog_id = %s AND bid = %s",
                params,
            )

        if reward_type or reward_value is not None:
            reward_updates = []
            reward_params = []
            if reward_type:
                for flag in allowed_reward_types:
                    reward_updates.append(f"{flag} = %s")
                    reward_params.append(1 if flag == reward_type else 0)
            if reward_value is not None:
                reward_updates.append("rwd_value = %s")
                reward_params.append(reward_value)

            if reward_updates:
                reward_params.extend([lprog_id, bid])
                cursor.execute(
                    f"UPDATE rewards SET {', '.join(reward_updates)} WHERE lprog_id = %s AND bid = %s",
                    reward_params,
                )

        db.commit()
        return jsonify({"message": "Loyalty program updated."}), 200
    except mysql.connector.Error as err:
        if db:
            db.rollback()
        return jsonify({"message": f"Failed to update loyalty program: {err}"}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()


@loyalty_prog.route("/api/owner/loyalty-programs/<int:lprog_id>", methods=["DELETE"])
@login_required
def delete_loyalty_program(lprog_id: int):
    if check_role() != "owner":
        return jsonify({"message": "Only salon owners can delete loyalty programs."}), 403

    try:
        bid = get_curr_bid()
    except ValueError as exc:
        return jsonify({"message": str(exc)}), 400

    db = None
    cursor = None
    try:
        db = get_db()
        if db is None:
            return jsonify({"message": "Could not connect to database."}), 500

        cursor = db.cursor()
        cursor.execute("DELETE FROM rewards WHERE lprog_id = %s AND bid = %s", (lprog_id, bid))
        cursor.execute("DELETE FROM loyalty_programs WHERE lprog_id = %s AND bid = %s", (lprog_id, bid))
        db.commit()
        return jsonify({"message": "Loyalty program removed."}), 200
    except mysql.connector.Error as err:
        if db:
            db.rollback()
        return jsonify({"message": f"Failed to delete loyalty program: {err}"}), 500
    finally:
        if cursor:
            cursor.close()
        if db:
            db.close()






