# Calculate uptime duration between start_time and updated_at for each record
uptime_duration = """
SELECT 
    id,
    start_time,
    updated_at,
    TIMESTAMPDIFF(SECOND, start_time, updated_at) as uptime_seconds,
    TIMESTAMPDIFF(MINUTE, start_time, updated_at) as uptime_minutes,
    TIMESTAMPDIFF(HOUR, start_time, updated_at) as uptime_hours
FROM service_time;
"""

# Calculate downtime between server sessions
downtime_duration = """
SELECT 
    curr.id as current_session,
    prev.id as previous_session,
    prev.updated_at as previous_down_time,
    curr.start_time as current_up_time,
    TIMESTAMPDIFF(SECOND, prev.updated_at, curr.start_time) as downtime_seconds
FROM service_time curr
JOIN service_time prev ON curr.id = prev.id + 1
ORDER BY curr.start_time;
"""

# uptime per day
daily_uptime = """
SELECT 
    DATE(start_time) as date,
    COUNT(*) as sessions,
    SUM(TIMESTAMPDIFF(SECOND, start_time, updated_at)) as total_uptime_seconds,
    SEC_TO_TIME(SUM(TIMESTAMPDIFF(SECOND, start_time, updated_at))) as total_uptime_formatted
FROM service_time
GROUP BY DATE(start_time)
ORDER BY date;
"""

# current server session uptime
current_session_uptime = """
SELECT
    start_time,
    updated_at,
    TIMESTAMPDIFF(SECOND, start_time, NOW()) as uptime_seconds
FROM service_time
ORDER BY start_time DESC
LIMIT 1;
"""

#Downtimes in the last 24 hours
downtime_24_hours = """
SELECT 
    prev.updated_at as outage_start,
    curr.start_time as recovery_time,
    TIMESTAMPDIFF(SECOND, prev.updated_at, curr.start_time) as downtime_seconds
FROM service_time curr
JOIN service_time prev ON curr.id = prev.id + 1
WHERE curr.start_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
   OR prev.updated_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY outage_start DESC;
"""