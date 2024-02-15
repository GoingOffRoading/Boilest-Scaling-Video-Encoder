import requests
from requests.exceptions import RequestException

def check_and_create_vhost(vhost_name, username, password, server_url):
    # Define the headers for the request
    headers = {'content-type': 'application/json'}

    # Define the URL for the vhost
    vhost_url = f"{server_url}/api/vhosts/{vhost_name}"

    try:
        # Try to get the vhost
        response = requests.get(vhost_url, headers=headers, auth=(username, password))

        # If the vhost does not exist, create it
        if response.status_code == 404:
            response = requests.put(vhost_url, headers=headers, auth=(username, password))

            # If the vhost could not be created, raise an exception
            if response.status_code != 204:
                raise Exception(f"Could not create vhost: {response.content}")

        elif response.status_code != 200:
            raise Exception(f"Unexpected response when checking vhost: {response.content}")

    except RequestException as e:
        print(f"API is unreachable. Error: {str(e)}")
        return False

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False

    return True

# Usage
check_and_create_vhost('my_vhost', 'my_username', 'my_password', 'http://localhost:15672')