from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Pipedrive API settings (ensure to add these to Heroku config or .env file)
API_TOKEN = os.getenv('PIPEDRIVE_API_TOKEN')  # Store your Pipedrive API token as an env variable

# Webhook endpoint for Pipedrive
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    # Ensure this is an organization creation event
    if data.get('meta', {}).get('action') == 'added' and data.get('meta', {}).get('object') == 'organization':
        new_org = data.get('current', {})
        new_nip = new_org.get('NIP')  # Assuming 'NIP' is the custom field name

        if new_nip:
            # Check for duplicates by searching organizations with the same NIP
            duplicate_org = search_organization_by_nip(new_nip)

            if duplicate_org:
                # Duplicate found, handle accordingly (e.g., send alert or take action)
                return jsonify({
                    'status': 'duplicate_found',
                    'message': f"Duplicate organization found with NIP: {new_nip}",
                    'duplicate_org': duplicate_org
                }), 200

            else:
                # No duplicate found
                return jsonify({
                    'status': 'no_duplicate',
                    'message': 'No duplicate organization found.'
                }), 200

    # If not an organization creation event, ignore
    return jsonify({'status': 'ignored', 'message': 'Event ignored.'}), 200


def search_organization_by_nip(nip):
    """
    Search for an organization in Pipedrive with a matching custom NIP field.
    :param nip: The NIP value to search for.
    :return: Organization data if duplicate is found, else None.
    """
    url = f'https://api.pipedrive.com/v1/itemSearch'
    params = {
        'term': nip,  # Search term is the NIP
        'item_type': 'organization',  # Specify that we're searching for organizations
        'fields': 'NIP',  # Restrict the search to the 'NIP' custom field
        'api_token': API_TOKEN  # Use the API token for authentication
    }

    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        search_results = response.json().get('data', [])
        
        # If results are found, return the first matching organization
        if search_results:
            return search_results[0]  # Return first matching org

    return None


if __name__ == '__main__':
    app.run(debug=True)
