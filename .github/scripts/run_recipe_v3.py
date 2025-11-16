#!/usr/bin/env python3
# File: .github/scripts/run_recipe.py
# Updated to use Composio v3 API / Rube execution endpoint

import os
import sys
import json
import requests
import time
from datetime import datetime

# API Configuration
API_BASE_URL = "https://backend.composio.dev/api/v1/rube"

def log(message):
    """Print timestamped log message"""
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] {message}")

def run_recipe():
    """Execute Composio Recipe via Rube API"""

    log("=== Starting Market America Prospect Analysis ===")

    # Get configuration from environment variables
    api_key = os.environ.get("COMPOSIO_API_KEY")
    recipe_id = os.environ.get("RECIPE_ID")

    if not api_key:
        log("ERROR: COMPOSIO_API_KEY not set")
        sys.exit(1)

    if not recipe_id:
        log("ERROR: RECIPE_ID not set")
        sys.exit(1)

    # Prepare input data
    input_data = {
        "prospect_spreadsheet_id": os.environ.get("PROSPECT_SPREADSHEET_ID", ""),
        "line_log_spreadsheet_id": os.environ.get("LINE_LOG_SPREADSHEET_ID", ""),
        "email_recipient": os.environ.get("EMAIL_RECIPIENT", ""),
        "calendar_id": os.environ.get("CALENDAR_ID", "primary"),
        "days_ahead": os.environ.get("DAYS_AHEAD", "21"),
        "top_n_prospects": os.environ.get("TOP_N_PROSPECTS", "10")
    }

    # Validate required inputs
    if not input_data["prospect_spreadsheet_id"]:
        log("ERROR: PROSPECT_SPREADSHEET_ID not set")
        sys.exit(1)
    if not input_data["line_log_spreadsheet_id"]:
        log("ERROR: LINE_LOG_SPREADSHEET_ID not set")
        sys.exit(1)
    if not input_data["email_recipient"]:
        log("ERROR: EMAIL_RECIPIENT not set")
        sys.exit(1)

    log(f"Recipe ID: {recipe_id}")
    log(f"Input data: {json.dumps(input_data, indent=2, ensure_ascii=False)}")

    # Call Composio Rube API to execute recipe
    url = f"{API_BASE_URL}/recipe/execute"

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "recipe_id": recipe_id,
        "params": input_data
    }

    log(f"Calling Rube API: {url}")

    try:
        # Execute recipe
        response = requests.post(
            url, 
            headers=headers, 
            json=payload, 
            timeout=600
        )

        log(f"Response status code: {response.status_code}")

        if response.status_code not in [200, 201]:
            error_msg = f"API request failed with status {response.status_code}"
            log(f"ERROR: {error_msg}")
            log(f"Response: {response.text}")

            # Save error log
            save_log({
                "status": "failed",
                "error": error_msg,
                "response": response.text,
                "status_code": response.status_code
            })

            sys.exit(1)

        result = response.json()

        log("Recipe execution initiated successfully!")
        log(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)}")

        # Check if execution is async
        execution_id = result.get("execution_id")

        if execution_id:
            log(f"Recipe executing asynchronously with execution_id: {execution_id}")
            log("Results will be available in spreadsheet and email when complete")

            # Save success log
            save_log({
                "status": "started",
                "execution_id": execution_id,
                "recipe_id": recipe_id,
                "input": input_data,
                "message": "Recipe execution started successfully",
                "note": "Results will be updated to spreadsheet and sent via email"
            })

            log("✅ Analysis started successfully!")
            log("📊 Results will be available in 3-5 minutes")
            log("📧 You will receive an email notification when complete")

        else:
            # Sync execution
            log("Recipe executed synchronously")

            # Extract results
            data = result.get("data", result)

            save_log({
                "status": "success",
                "recipe_id": recipe_id,
                "input": input_data,
                "result": data,
                "total_prospects": data.get("total_prospects_analyzed"),
                "top_prospects": data.get("top_prospects_count"),
                "events": data.get("relevant_events_count")
            })

            log("✅ Analysis completed successfully!")

            if data.get("spreadsheet_updated"):
                log("📊 Spreadsheet updated")
            if data.get("email_sent"):
                log("📧 Email report sent")

        sys.exit(0)

    except requests.exceptions.Timeout:
        error_msg = "Request timeout after 10 minutes"
        log(f"ERROR: {error_msg}")
        save_log({
            "status": "failed",
            "error": error_msg
        })
        sys.exit(1)

    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {str(e)}"
        log(f"ERROR: {error_msg}")
        save_log({
            "status": "failed",
            "error": error_msg
        })
        sys.exit(1)

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        log(f"ERROR: {error_msg}")
        save_log({
            "status": "failed",
            "error": error_msg
        })
        sys.exit(1)

def save_log(data):
    """Save execution log to file"""
    log_data = {
        "execution_time": datetime.now().isoformat(),
        "recipe_id": os.environ.get("RECIPE_ID"),
        **data
    }

    try:
        with open("execution_log.json", "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        log("Execution log saved to execution_log.json")
    except Exception as e:
        log(f"Warning: Failed to save log: {e}")

if __name__ == "__main__":
    run_recipe()
