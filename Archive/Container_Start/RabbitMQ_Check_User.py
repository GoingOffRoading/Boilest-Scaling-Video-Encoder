import requests
from requests.exceptions import RequestException

def check_and_create_user(user_name, password, admin_user, admin_password, server_url):
    # Define the headers for the request
    headers = {'content-type': 'application/json'}

    # Define the URL for the user
    user_url = f"{server_url}/api/users/{user_name}"

    try:
        # Try to get the user
        response = requests.get(user_url, headers=headers, auth=(admin_user, admin_password))

        # If the user does not exist, create them
        if response.status_code == 404:
            user_data = {"password": password, "tags": ""}
            response = requests.put(user_url, headers=headers, auth=(admin_user, admin_password), json=user_data)

            # If the user could not be created, raise an exception
            if response.status_code != 204:
                raise Exception(f"Could not create user: {response.content}")

        elif response.status_code != 200:
            raise Exception(f"Unexpected response when checking user: {response.content}")

    except RequestException as e:
        raise Exception(f"API is unreachable. Error: {str(e)}")

    except Exception as e:
        raise Exception(f"An error occurred: {str(e)}")

    return True

# Usage
check_and_create_user('my_user', 'my_password', 'admin_user', 'admin_password', 'http://localhost:15672')