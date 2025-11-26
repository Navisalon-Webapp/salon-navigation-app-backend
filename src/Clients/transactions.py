from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from mysql.connector import Error
from helper.utils import *

transaction = Blueprint('transaction', __name__,)

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