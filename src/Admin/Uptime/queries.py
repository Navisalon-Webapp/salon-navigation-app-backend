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

# Monthly uptime percentage
monthly_uptime = """
SELECT 
    YEAR(start_time) as year,
    MONTH(start_time) as month,
    COUNT(*) as total_sessions,
    SUM(TIMESTAMPDIFF(SECOND, start_time, updated_at)) as total_uptime_seconds,
    -- Calculate uptime percentage (assuming month has 30 days for simplicity)
    ROUND(
        (SUM(TIMESTAMPDIFF(SECOND, start_time, updated_at)) / (30 * 24 * 60 * 60)) * 100, 
        2
    ) as uptime_percentage
FROM service_time
GROUP BY YEAR(start_time), MONTH(start_time)
ORDER BY year, month;
"""

# current server session uptime
current_session_uptime = """
SELECT 
    id,
    start_time,
    updated_at,
    TIMESTAMPDIFF(SECOND, start_time, NOW()) as current_uptime_seconds,
    SEC_TO_TIME(TIMESTAMPDIFF(SECOND, start_time, NOW())) as current_uptime_formatted
FROM service_time
ORDER BY start_time DESC
LIMIT 1;
"""

# Comprehensive uptime analysis
uptime_report = """
WITH uptime_stats AS (
    SELECT 
        MIN(start_time) as first_record,
        MAX(updated_at) as last_record,
        COUNT(*) as total_sessions,
        SUM(TIMESTAMPDIFF(SECOND, start_time, updated_at)) as total_uptime_seconds
    FROM service_time
),
downtime_stats AS (
    SELECT 
        SUM(TIMESTAMPDIFF(SECOND, prev.updated_at, curr.start_time)) as total_downtime_seconds,
        COUNT(*) as downtime_events
    FROM service_time curr
    JOIN service_time prev ON curr.id = prev.id + 1
)
SELECT 
    u.first_record,
    u.last_record,
    u.total_sessions,
    SEC_TO_TIME(u.total_uptime_seconds) as total_uptime,
    SEC_TO_TIME(COALESCE(d.total_downtime_seconds, 0)) as total_downtime,
    ROUND(
        (u.total_uptime_seconds / 
         (TIMESTAMPDIFF(SECOND, u.first_record, u.last_record))) * 100, 
        2
    ) as overall_uptime_percentage,
    COALESCE(d.downtime_events, 0) as number_of_outages
FROM uptime_stats u
LEFT JOIN downtime_stats d ON 1=1;
"""

# Recent outages and recovery times
monthly_outage_analysis = """
SELECT 
    curr.id,
    prev.updated_at as outage_start,
    curr.start_time as recovery_time,
    TIMESTAMPDIFF(MINUTE, prev.updated_at, curr.start_time) as outage_duration_minutes
FROM service_time curr
JOIN service_time prev ON curr.id = prev.id + 1
WHERE curr.start_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)
ORDER BY curr.start_time DESC;
"""