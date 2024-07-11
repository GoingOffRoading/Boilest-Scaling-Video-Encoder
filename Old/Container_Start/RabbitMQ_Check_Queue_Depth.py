import requests
from requests.exceptions import RequestException

def check_and_purge_queue(queue_name, vhost, admin_user, admin_password, server_url):
    # Define the headers for the request
    headers = {'content-type': 'application/json'}

    # Define the URL for the queue
    queue_url = f"{server_url}/api/queues/{vhost}/{queue_name}"

    try:
        # Try to get the queue
        response = requests.get(queue_url, headers=headers, auth=(admin_user, admin_password))

        # If the queue exists and its depth is greater than 0, purge it
        if response.status_code == 200:
            if response.json()['messages'] > 0:
                purge_url = f"{server_url}/api/queues/{vhost}/{queue_name}/contents"
                response = requests.delete(purge_url, headers=headers, auth=(admin_user, admin_password))

                # If the queue could not be purged, raise an exception
                if response.status_code != 204:
                    raise Exception(f"Could not purge queue: {response.content}")

        elif response.status_code != 404:
            raise Exception(f"Unexpected response when checking queue: {response.content}")

    except RequestException as e:
        raise Exception(f"API is unreachable. Error: {str(e)}")

    except Exception as e:
        raise Exception(f"An error occurred: {str(e)}")

    return True

# Usage
check_and_purge_queue('my_queue', '/', 'admin_user', 'admin_password', 'http://localhost:15672')