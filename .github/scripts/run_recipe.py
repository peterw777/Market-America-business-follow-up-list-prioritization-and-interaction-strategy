#!/usr/bin/env python3
# File: .github/scripts/run_recipe.py

import os
import sys
import json
import requests
from datetime import datetime

def run_recipe():
    """Execute Composio Recipe via API"""

    # Get configuration from environment variables
    api_key = os.environ.get("COMPOSIO_API_KEY")
    recipe_id = os.environ.get("RECIPE_ID")

    if not api_key or not recipe_id:
        print("ERROR: Missing COMPOSIO_API_KEY or RECIPE_ID")
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

    print(f"[{datetime.now().isoformat()}] Starting recipe execution...")
    print(f"Recipe ID: {recipe_id}")
    print(f"Input data: {json.dumps(input_data, indent=2)}")

    # Call Composio API to execute recipe
    url = f"https://backend.composio.dev/api/v3/recipes/{recipe_id}/execute"

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    payload = {
        "input": input_data
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=600)
        response.raise_for_status()

        result = response.json()

        print(f"[{datetime.now().isoformat()}] Recipe execution completed!")
        print(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)}")

        # Save execution log
        log_data = {
            "execution_time": datetime.now().isoformat(),
            "recipe_id": recipe_id,
            "input": input_data,
            "result": result,
            "status": "success"
        }

        with open("execution_log.json", "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        # Check if execution was successful
        if result.get("success") or result.get("status") == "success":
            print("✅ Analysis completed successfully!")
            sys.exit(0)
        else:
            print("⚠️ Analysis completed with warnings")
            sys.exit(0)

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Failed to execute recipe: {e}")

        log_data = {
            "execution_time": datetime.now().isoformat(),
            "recipe_id": recipe_id,
            "input": input_data,
            "error": str(e),
            "status": "failed"
        }

        with open("execution_log.json", "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        sys.exit(1)

if __name__ == "__main__":
    run_recipe()

