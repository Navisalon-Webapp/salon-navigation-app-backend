from flask import Blueprint, request, jsonify
from .admin_func import *
from .queries import *
from helper.utils import *
from flask_login import current_user, login_required
from mysql.connector import Error
from datetime import datetime

metrics = Blueprint("metrics",__name__,url_prefix='/admin')

@metrics.route('/retention', methods=['GET'])
@login_required
def get_retention_metrics():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    data = request.get_json()
    uid = data['uid']
    bid = get_bid_from_uid(uid)

    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_business_retention,[bid])
        retention = cursor.fetchall()
        max = retention[len(retention)-1]['x']
        retention_list = [0] * (max+1)
        for x in retention:
            retention_list[x['x']] = x['y']

        return jsonify(retention_list)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/retention-rate', methods=['GET'])
@login_required
def retention_rate():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    data = request.get_json()
    uid:int = data['uid'] if data['uid'] else None
    month:int = data['month'] if data['month'] else None
    year:int = data['year'] if data['month'] else None
    if not uid or not month or not year:
        return jsonify({
            "status":"failure",
            "message":"missing parameters"
        }), 400
    
    bid = get_bid_from_uid(uid)

    param = [bid, month, year]
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query_new_customers,param)
        result = cursor.fetchone()
        countNew = result[0]
        cursor.execute(query_old_customers,param)
        result = cursor.fetchone()
        countOld = result[0]
        cursor.execute(query_end_period,param)
        result = cursor.fetchone()
        countEnd = result[0]
        retention_rate = (countEnd-countNew)/countOld
        return jsonify({
            "status":"success",
            "message":"retrieved customer metrics",
            "start of period customers":countOld,
            "new customers":countNew,
            "end of period customers":countEnd,
            "retention-rate":retention_rate
        }), 200
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Database Error {e}")
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

@metrics.route('/customer-satisfaction', methods=['GET'])
def customer_satisfaction():
    data = request.get_json()
    uid:int = data['uid'] if data['uid'] else None
    if not uid:
        return jsonify({
            "status":"failure",
            "message":"missing parameters"
        }), 400
    bid = get_bid_from_uid(uid)

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query_customer_satisfaction,[bid])
        result = cursor.fetchone()
        return jsonify({
            "status":"success",
            "message":"retrieved business average rating",
            "customer satisfaction": result[0]
        }), 200
    except mysql.connector.Error as e:
        print(f"Database Error {e}")
        return jsonify({
            "status":"failure",
            "message":"Database Error",
            "error": str(e)
        }), 500
    except Exception as e:
        print(f"Database Error {e}")
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

@metrics.route('/total-active-users',methods=['GET'])
@login_required
def get_total_active_users():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_tot_active_users)

        tot_active = cursor.fetchone()
        tot_active_val = tot_active['total_active_users']

        return jsonify({"status":"success", "tot_active":tot_active_val})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/salons-explored',methods=['GET'])
@login_required
def get_salons_explored():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_avg_salons_expl)
        explored = cursor.fetchone()
        avg_salons_expl = explored['avg_salons_explored']

        return jsonify({"status":"success", "avg_salons_explored":avg_salons_expl})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/salon-views',methods=['GET'])
@login_required
def get_salon_views():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_avg_salon_views)
        salon_views = cursor.fetchone()
        avg_salon_views = salon_views['avg_salon_views']

        return jsonify({"status":"success", "avg_salon_views":avg_salon_views})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/product-views',methods=['GET'])
@login_required
def get_product_views():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_prod_views)
        prod_views = cursor.fetchone()
        avg_product_views = prod_views['avg_product_views']

        return jsonify({"status":"success", "avg_product_views":avg_product_views})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/new-user-trend',methods=['GET'])
@login_required
def get_new_user_trend():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_new_user_trend)
        new_user_rows = cursor.fetchall()
        new_user_labels = [row["month"] for row in new_user_rows]
        new_user_data = [row["new_users_count"] for row in new_user_rows]
        return jsonify({"status":"success", "new_user_labels":new_user_labels, "new_user_data":new_user_data})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/active-user-roles',methods=['GET'])
@login_required
def get_active_user_roles():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_active_user_roles)
        active_user_rows = cursor.fetchall()
        active_user_labels = [row["role"] for row in active_user_rows]
        active_user_data = [row["active_users"] for row in active_user_rows]
        return jsonify({"status":"success", "active_user_labels":active_user_labels, "active_user_data":active_user_data})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/active-user-trend',methods=['GET'])
@login_required
def get_active_user_trend():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_active_user_trend)
        active_users_rows = cursor.fetchall()
        active_user_labels = [row["month"] for row in active_users_rows]
        active_user_data = [row["active_count"] for row in active_users_rows]
        return jsonify({"status":"success", "active_user_labels":active_user_labels, "active_user_data":active_user_data})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/total-programs',methods=['GET'])
@login_required
def get_total_programs():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_tot_loyalty_progs)
        
        active_loyalty_programs = cursor.fetchone()
        total_programs = active_loyalty_programs['active_loyalty_programs']
        return jsonify({"status":"success", "total_programs":total_programs})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/client-participation',methods=['GET'])
@login_required
def get_client_participation():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_client_prog_percent)
        client_part = cursor.fetchone()
        client_part_val = f"{round(client_part['percent_participating'], 2)}%"
        return jsonify({"status":"success", "client_participation":client_part_val})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/average-saved',methods=['GET'])
@login_required
def get_average_saved():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_average_saved)
        avg_saved = cursor.fetchone()
        avg_saved_val = f"${round(avg_saved['avg_amount_saved_per_customer'], 2)}"
        return jsonify({"status":"success", "avg_saved":avg_saved_val})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/total-saved',methods=['GET'])
@login_required
def get_total_saved():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_tot_saved)
        tot_savings = cursor.fetchone()
        tot_savings_val = f"${round(tot_savings['total_savings'], 2)}"
        return jsonify({"status":"success", "total_savings":tot_savings_val})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/prog-salon',methods=['GET'])
@login_required
def get_programs_by_salon():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_progs_by_salon)
        prog_rows = cursor.fetchall()
        prog_salon_labels = [row["num_programs"] for row in prog_rows]
        prog_salon_data = [row["num_salons"] for row in prog_rows]
        return jsonify({"status":"success", "prog_salon_labels":prog_salon_labels, "prog_salon_data":prog_salon_data})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/prog-types',methods=['GET'])
@login_required
def get_program_types():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_prog_types)
        prog_row = cursor.fetchone()
        prog_labels = ["Points", "Price", "Appointments", "Products"]
        prog_data = [prog_row["points"], prog_row["price"], prog_row["appointments"], prog_row["products"]]

        return jsonify({"status":"success", "labels":prog_labels, "data":prog_data})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/savings-trend',methods=['GET'])
@login_required
def get_savings_trend():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_savings_trend)
        savings_rows = cursor.fetchall()
        savings_labels = [row["month"] for row in savings_rows]
        savings_data = [row["total_redeemed"] for row in savings_rows]
        return jsonify({"status":"success", "savings_labels":savings_labels, "savings_data":savings_data})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/total-revenue',methods=['GET'])
@login_required
def get_total_revenue():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_tot_rev)
        tot_rev = cursor.fetchone()
        tot_rev_val = f"${round(tot_rev['total_revenue'], 2)}"
        return jsonify({"status":"success", "total_revenue":tot_rev_val})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/revenue-month',methods=['GET'])
@login_required
def get_revenue_month():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_month_rev_change)
        rev = cursor.fetchone()
        rev_month = round(rev['percent_change'], 2)
        return jsonify({"status":"success", "revenue_month_change":rev_month})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/revenue-year',methods=['GET'])
@login_required
def get_revenue_year():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_year_rev_change)
        rev = cursor.fetchone()
        rev_year = round(rev['percent_change'], 2)
        return jsonify({"status":"success", "revenue_year_change":rev_year})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/average-revenue',methods=['GET'])
@login_required
def get_average_revenue():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_avg_salon_rev)
        avg_rev = cursor.fetchone()
        avg_rev_val = f"${round(avg_rev['avg_monthly_salon_revenue'], 2)}"
        return jsonify({"status":"success", "average_revenue":avg_rev_val})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/revenue-trend',methods=['GET'])
@login_required
def get_revenue_trend():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_rev_trend)
        revenue_rows = cursor.fetchall()
        revenue_labels = [row["month"] for row in revenue_rows]
        revenue_data = [row["revenue"] for row in revenue_rows]
        return jsonify({"status":"success", "revenue_labels":revenue_labels, "revenue_data":revenue_data})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/revenue-source',methods=['GET'])
@login_required
def get_revenue_source():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_rev_by_src)
        revenue_rows = cursor.fetchall()
        revenue_labels = [row["source"] for row in revenue_rows]
        revenue_data = [row["revenue"] for row in revenue_rows]
        return jsonify({"status":"success", "revenue_labels":revenue_labels, "revenue_data":revenue_data})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/top-services',methods=['GET'])
@login_required
def get_top_services():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_top_services)
        service_rows = cursor.fetchall()
        top_service_labels = [row["name"] for row in service_rows]
        top_service_data = [row["revenue"] for row in service_rows]
        return jsonify({"status":"success", "top_service_labels":top_service_labels, "top_service_data":top_service_data})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/reschedule',methods=['GET'])
@login_required
def get_reschedule_rate():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_resched_rate)
        resched_rate = cursor.fetchone()
        resched_rate_val = f"{round(resched_rate['reschedule_rate'], 2)}%"

        return jsonify({"status":"success", "resched_rate":resched_rate_val})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/cancel',methods=['GET'])
@login_required
def get_cancel_rate():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_cancel_rate)

        cancel_rate = cursor.fetchone()
        cancel_rate_val = f"{round(cancel_rate['cancellation_rate'], 2)}%"        

        return jsonify({"status":"success", "cancel_rate":cancel_rate_val})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/no-show',methods=['GET'])
@login_required
def get_no_show_rate():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_no_show_rate)
        
        no_show_rate = cursor.fetchone()
        no_show_rate_val = f"{round(no_show_rate['no_show_rate'], 2)}%"

        return jsonify({"status":"success", "no_show_rate":no_show_rate_val})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/appt-service',methods=['GET'])
@login_required
def get_appt_by_service():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_appt_by_service)
        service_rows = cursor.fetchall()

        appt_cat_labels = [row["name"] for row in service_rows]
        appt_cat_data = [row["appt_count"] for row in service_rows]

        return jsonify({"status":"success", "appt_cat_labels":appt_cat_labels, "appt_cat_data":appt_cat_data})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/appt-day',methods=['GET'])
@login_required
def get_appt_by_day():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_appt_by_day)
        day_rows = cursor.fetchall()

        appt_day_labels = [row["day"] for row in day_rows]
        appt_day_data = [row["appt_count"] for row in day_rows]

        return jsonify({"status":"success", "appt_day_labels":appt_day_labels, "appt_day_data":appt_day_data})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/appt-time',methods=['GET'])
@login_required
def get_appt_by_time():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_appt_by_time)
        time_rows = cursor.fetchall()

        appt_time_labels = [row["time_block"] for row in time_rows]
        appt_time_data = [row["appt_count"] for row in time_rows]

        return jsonify({"status":"success", "appt_time_labels":appt_time_labels, "appt_time_data":appt_time_data})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/appt-trend',methods=['GET'])
@login_required
def get_appt_trend():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_appt_trend)
        year_rows = cursor.fetchall()

        appt_trend_labels = [row["month"] for row in year_rows]
        appt_trend_data = [row["completed_appointments"] for row in year_rows]

        return jsonify({"status":"success", "appt_trend_labels":appt_trend_labels, "appt_trend_data":appt_trend_data})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/income',methods=['GET'])
@login_required
def get_average_income():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_avg_income)
        avg_income = cursor.fetchone()
        avg_income_val = f"${round(avg_income['avg_income'], 2)}"
        return jsonify({"status":"success", "avg_income":avg_income_val})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/salon-age',methods=['GET'])
@login_required
def get_average_salon_age():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_avg_salon_age)
        salon_age = cursor.fetchone()
        salon_age_val = f"{round(salon_age['avg_salon_age'], 2)} years"
        return jsonify({"status":"success", "avg_salon_age":salon_age_val})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/experience',methods=['GET'])
@login_required
def get_average_worker_experiences():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_avg_worker_exp)
        worker_experience = cursor.fetchone()
        worker_experience_val = f"{round(worker_experience['avg_worker_experience'], 2)} years"
        return jsonify({"status":"success", "avg_worker_experience":worker_experience_val})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/gender',methods=['GET'])
@login_required
def get_gender_distribution():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_gender_dist)
        gender_rows = cursor.fetchall()
        gender_labels = [row["gender"] for row in gender_rows]
        gender_data = [row["count"] for row in gender_rows]
        return jsonify({"status":"success", "gender_labels":gender_labels, "gender_data":gender_data})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/age',methods=['GET'])
@login_required
def get_age_distribution():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_age_dist)
        age_rows = cursor.fetchall()
        age_labels = [row["age_range"] for row in age_rows]
        age_data = [row["count"] for row in age_rows]
        return jsonify({"status":"success", "age_labels":age_labels, "age_data":age_data})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@metrics.route('/industry',methods=['GET'])
@login_required
def get_industry_distribution():
    if not check_role() == 'admin':
        return jsonify({
            "status":"failure",
            "message":"unauthorized",
        }), 403
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_industry_dist)
        industry_rows = cursor.fetchall()
        industry_labels = [row["name"] for row in industry_rows]
        industry_data = [row["client_count"] for row in industry_rows]
        return jsonify({"status":"success", "industry_labels":industry_labels, "industry_data":industry_data})
    except Exception as e:
        return jsonify({
            "status": "failure",
            "message": str(e)
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()