from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

API_TOKEN = os.getenv('PIPEDRIVE_API_TOKEN')
print(API_TOKEN)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data.get('meta', {}).get('action') == 'added' and data.get('meta', {}).get('object') == 'organization':
        new_org = data.get('current', {})
        new_nip = new_org.get('NIP')
        if new_nip:
            duplicate_org = search_organization_by_nip(new_nip)
            if duplicate_org:
                # Duplicate found, delete the newly created organization
                delete_status = delete_organization(new_org.get('id'))
                if delete_status:
                    return jsonify({
                        'status': 'duplicate_found',
                        'message': f"Duplicate organization found with NIP: {new_nip}. Deleted the newly created organization.",
                        'duplicate_org': duplicate_org
                    }), 200
                else:
                    return jsonify({
                        'status': 'duplicate_found',
                        'message': f"Duplicate organization found with NIP: {new_nip}. Failed to delete the newly created organization.",
                        'duplicate_org': duplicate_org
                    }), 500
            else:
                return jsonify({
                    'status': 'no_duplicate',
                    'message': 'No duplicate organization found.'
                }), 200
    return jsonify({'status': 'ignored', 'message': 'Event ignored.'}), 200

def search_organization_by_nip(nip):
    url = f'https://api.pipedrive.com/v1/organizations/search'
    params = {
        'term': nip,
        'fields': 'NIP',
        'api_token': API_TOKEN
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        search_results = response.json().get('data', {}).get('items', [])
        if search_results:
            return search_results[0]['item']
    return None

def delete_organization(org_id):
    url = f'https://api.pipedrive.com/v1/organizations/{org_id}'
    params = {
        'api_token': API_TOKEN
    }
    response = requests.delete(url, params=params)
    return response.status_code == 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
