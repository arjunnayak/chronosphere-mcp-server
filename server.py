# server.py
from datetime import datetime, timedelta, timezone
from mcp.server.fastmcp import FastMCP
import requests
import os
import time
from typing import Dict, Any, Tuple
import re
import logging

logger = logging.getLogger(__name__)

mcp = FastMCP("chronosphere-mcp")

def parse_simple_time_range(simple_time_range: str) -> Tuple[str, str]:
    """Parse the simple time range and return formatted start and end times."""
    match = re.match(r"(\d+)([mhdwy])", simple_time_range.strip())
    if not match:
        raise ValueError("Invalid simple_time_range format. Use formats like 30m, 1h, 7d, 2w.")
    value, unit = int(match.group(1)), match.group(2)
    now = datetime.now(timezone.utc)
    if unit == 'm':
        start_time = now - timedelta(minutes=value)
    elif unit == 'h':
        start_time = now - timedelta(hours=value)
    elif unit == 'd':
        start_time = now - timedelta(days=value)
    elif unit == 'w':
        start_time = now - timedelta(weeks=value)
    else:
        raise ValueError("Unsupported time unit in simple_time_range.")
    end_time = now
    # Format as required by Chronosphere
    start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_time = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return start_time, end_time

def make_chronosphere_logs_request(query: str, start_time: str, end_time: str, page_token: str = None) -> Dict[str, Any]:
    """Handles the Chronosphere logs API request and polling."""
    api_token = os.getenv("CHRONOSPHERE_API_TOKEN")
    if not api_token:
        raise ValueError("CHRONOSPHERE_API_TOKEN environment variable not set")
    domain = "affirm.chronosphere.io"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    start_url = f"https://{domain}/api/unstable/data/logs:get-range-query-start"
    start_params = {
        "query": query,
        "timestamp_filter.happened_after": start_time,
        "timestamp_filter.happened_before": end_time,
        "timestamp_sort": "DESC",
    }
    if page_token:
        start_params["page.token"] = page_token
    start_response = requests.get(start_url, headers=headers, params=start_params)
    start_response.raise_for_status()
    start_json = start_response.json()
    query_id = start_json.get("query_id")
    poll_interval = start_json.get("refresh_interval_ms", 1000) / 1000.0
    if not query_id:
        raise ValueError("Failed to get query_id from start response")
    poll_url = f"https://{domain}/api/unstable/data/logs:get-range-query-poll"
    max_poll_attempts = 10
    for attempt in range(max_poll_attempts):
        poll_params = {"query_id": query_id}
        poll_response = requests.get(poll_url, headers=headers, params=poll_params)
        poll_response.raise_for_status()
        result = poll_response.json()
        logger.info(f"polling result result: status {result.get('is_finished')} {len(result.get('logs', []))}")
        if result.get("is_finished") == True:
            return result
        time.sleep(poll_interval)
    raise TimeoutError("Logs query did not complete within the maximum polling time")

@mcp.tool()
def query_logs(query: str, start_time: str, end_time: str, simple_time_range: str, page_token: str = None) -> Dict[str, Any]:
    """
    Query logs from Chronosphere using the logs API. 
    
    Args:
        query: The log query string
        start_time: Start time for the query range e.g. 2025-05-08T18:08:35.000Z
        end_time: End time for the query range e.g. 2025-05-08T18:20:35.000Z
        page_token: Next page token for the query. If provided, the query will continue from the next page.
        simple_time_range: Simple time range for the query range e.g. 1h, 1d, 1w, 1m, 1y. This takes precedence over start_time and end_time, if provided.
    Returns:
        Dict containing the query results
    """
    if simple_time_range:
        start_time, end_time = parse_simple_time_range(simple_time_range)
    else:
        # Parse and format provided timestamps
        start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%fZ")

    return make_chronosphere_logs_request(query, start_time, end_time, page_token)

# @mcp.tool()
# def query_dt_error_logs(dt_name: str, environment: str, simple_time_range: str = "10m", next_page_token: str = None) -> Dict[str, Any]:
#     """
#     Query error logs for a given DT/service and environment in the last N minutes/hours/days. 
#     This is the preferred tool to query error logs for a DT.
#     Args:
#         dt_name: The name of the DT/service
#         environment: The environment of the DT/service
#         simple_time_range: Simple time range for the query range e.g. 1h, 1d, 1w, 1m, 1y. This takes precedence over start_time and end_time, if provided.
#         next_page_token: Next page token for the query. If provided, the query will continue from the next page.
#     Returns:
#         Dict containing the query results
#     """
#     query = f'service = "{dt_name}" and event.dataset="application-logs" and environment.name = "{environment}" and severity = "ERROR" | project @timestamp, message, payload'
#     start_time, end_time = parse_simple_time_range(simple_time_range)
#     return make_chronosphere_logs_request(query, start_time, end_time, next_page_token)

if __name__ == "__main__":
    # Start the server
    mcp.run()

