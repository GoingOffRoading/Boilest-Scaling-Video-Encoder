import requests
from requests.exceptions import RequestException

def check_and_create_queue(queue_name, vhost, admin_user, admin_password, server_url):
    # Define the headers for the request
    headers = {'content-type': 'application/json'}

    # Define the URL for the queue
    queue_url = f"{server_url}/api/queues/{vhost}/{queue_name}"

    try:
        # Try to get the queue
        response = requests.get(queue_url, headers=headers, auth=(admin_user, admin_password))

        # If the queue does not exist or does not have the required arguments, create it
        if response.status_code == 404 or 'arguments' not in response.json() or \
           'x-max-priority' not in response.json()['arguments'] or 'default_priority' not in response.json()['arguments']:
            queue_data = {"arguments": {"x-max-priority": 10, "default_priority": 0}}
            response = requests.put(queue_url, headers=headers, auth=(admin_user, admin_password), json=queue_data)

            # If the queue could not be created, raise an exception
            if response.status_code != 204:
                raise Exception(f"Could not create queue: {response.content}")

        elif response.status_code != 200:
            raise Exception(f"Unexpected response when checking queue: {response.content}")

    except RequestException as e:
        raise Exception(f"API is unreachable. Error: {str(e)}")

    except Exception as e:
        raise Exception(f"An error occurred: {str(e)}")

    return True

# Usage
check_and_create_queue('my_queue', '/', 'admin_user', 'admin_password', 'http://localhost:15672')