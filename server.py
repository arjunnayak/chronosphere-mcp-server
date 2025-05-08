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


@mcp.tool()
def query_logs(query: str, start_time: str, end_time: str, simple_time_range: str) -> Dict[str, Any]:
    """Query logs from Chronosphere using the logs API.
    
    Args:
        query: The log query string
        start_time: Start time for the query range e.g. 2025-05-08T18:08:35.000Z
        end_time: End time for the query range e.g. 2025-05-08T18:20:35.000Z
        simple_time_range: Simple time range for the query range e.g. 1h, 1d, 1w, 1m, 1y. This takes precedence over start_time and end_time, if provided.
    Returns:
        Dict containing the query results
    """
    # Always use the helper to parse the time range if provided
    if simple_time_range:
        start_time, end_time = parse_simple_time_range(simple_time_range)
    else:
        # Parse and format provided timestamps
        start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S.%fZ")
        start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        end_time = end_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # Get API token from environment variable
    api_token = os.getenv("CHRONOSPHERE_API_TOKEN")
    if not api_token:
        raise ValueError("CHRONOSPHERE_API_TOKEN environment variable not set")
    
    domain = "affirm.chronosphere.io"
    
    # Prepare headers with authentication
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    # Step 1: Start the logs query
    start_url = f"https://{domain}/api/unstable/data/logs:list-start"
    start_params = {
        "log_filter.query": query,
        "log_filter.happened_after": start_time,
        "log_filter.happened_before": end_time,
        "timestamp_sort": "DESC"
    }
    
    start_response = requests.get(start_url, headers=headers, params=start_params)
    start_response.raise_for_status()
    query_id = start_response.json().get("query_id")
    poll_interval = start_response.json().get("refresh_interval_ms", 1000) / 1000.0
    
    if not query_id:
        raise ValueError("Failed to get query_id from start response")
    
    # Step 2: Poll for results
    poll_url = f"https://{domain}/api/unstable/data/logs:list-poll"
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

if __name__ == "__main__":
    # Start the server
    mcp.run()

