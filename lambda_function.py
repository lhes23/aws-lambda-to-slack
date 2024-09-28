import os
import boto3
import json
import urllib3
from datetime import datetime

# Set Slack webhook URL
SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')

# Initialize Cost Explorer client
ce = boto3.client('ce')

def get_aws_bill(start_date,end_date):
    # Get cost and usage report from Cost Explorer
    response = ce.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost']
    )

    total_cost = response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']
    rounded_total_cost = round(float(total_cost), 2)
    return rounded_total_cost
    
    
def send_message_to_slack(message):
     # Send message to Slack using urllib3
    http = urllib3.PoolManager()
    slack_data = {'text': message}
    encoded_data = json.dumps(slack_data).encode('utf-8')
    
    response = http.request(
        'POST',
        SLACK_WEBHOOK_URL,
        body=encoded_data,
        headers={'Content-Type': 'application/json'}
    )
    
    return response
    

def lambda_handler(event, context):
    today = datetime.today()
    start_date = today.replace(day=1).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    rounded_total_cost = get_aws_bill(start_date,end_date)
    billing_dashboard_url = "https://console.aws.amazon.com/billing/home#/bills"
    cost_explorer_url = "https://console.aws.amazon.com/cost-management/home?#/cost-explorer"

    message = (
        f"AWS Billing Report:\n" 
        f"from: {start_date}\n"
        f"to: {end_date}:\n"
        f"Estimated total cost: ${rounded_total_cost}\n"
        f"<{billing_dashboard_url}|View Billing Dashboard>\n"
        f"<{cost_explorer_url}|View Cost Explorer>"
    )
    
    response = send_message_to_slack(message)
    
    if response.status != 200:
        raise ValueError(f"Request to Slack returned error {response.status}, "
                         f"the response is:\n{response.data.decode('utf-8')}")
    
    return {
        'statusCode': 200,
        'body': f"Sent report to Slack: {message}"
    }
