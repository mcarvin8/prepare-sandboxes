"""
    Query Stale Sandboxes with Tooling API.
"""
import argparse
import datetime
import logging
import sys

import get_salesforce_connection
import sandbox_functions


# Format logging message
logging.basicConfig(format='%(message)s', level=logging.DEBUG)


def parse_args():
    """
        Function to pass required arguments.
    """
    parser = argparse.ArgumentParser(description='A script to query sandboxes.')
    parser.add_argument('-a', '--alias', help='Production alias used for authentication', required=False)
    parser.add_argument('-u', '--url', help='Force Auth URL for your production org.', required=False)
    args = parser.parse_args()
    return args


def is_sandbox_eligible(start_date):
    """
        Determine if sandbox is stale
    """
    if not start_date:
        return False
    current_time = datetime.datetime.now()
    delta = current_time - start_date
    return delta.days >= 30


def log_sandbox_info(sandbox_name, start_date):
    """
        Log sandbox info such as name and start date.
    """
    sbx_info = f'SandboxName: {sandbox_name}, LastRefreshDate: {start_date}'
    logging.info(sbx_info)


def main(alias, url):
    """
        Main function
    """
    if alias:
        sf = get_salesforce_connection.get_salesforce_connection_alias(alias)
    elif url:
        sf = get_salesforce_connection.get_salesforce_connection_url(url)
    else:
        logging.error('ERROR: The Salesforce Production alias or URL was not provided for authentication.')
        logging.error('Please provide `--alias` or `--url` flag and try again.')
        sys.exit(1)

    query_data = sf.toolingexecute('query?q=SELECT+StartDate,SandboxName,Status+FROM+SandboxProcess','GET')
    records = query_data.get('records', [])

    unique_sandbox_info = {}

    for item in records:
        sandbox_name = item.get('SandboxName')
        start_date_str = item.get('StartDate')
        sandbox_status = item.get('Status')

        if sandbox_status in {'Deleted', 'Deleting'}:
            continue

        if sandbox_name not in unique_sandbox_info:
            start_date = sandbox_functions.parse_iso_datetime(start_date_str)
            if is_sandbox_eligible(start_date):
                unique_sandbox_info[sandbox_name] = (sandbox_name, start_date)

    sorted_sandbox_info = dict(sorted(unique_sandbox_info.values(), key=lambda x: x[0].lower()))

    for sandbox_name, start_date in sorted_sandbox_info.items():
        log_sandbox_info(sandbox_name, start_date)

    if not records:
        logging.error("No 'records' key found in the query response.")
        sys.exit(1)


if __name__ == '__main__':
    inputs = parse_args()
    main(inputs.alias, inputs.url)
