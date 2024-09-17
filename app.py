from flask import Flask, request, jsonify
import requests
import os
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

ALERT_SERVER_URL = os.getenv('ALERT_SERVER_URL')  # The URL of your Node.js WebSocket server

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data.get('meta', {}).get('action') == 'added' and data.get('meta', {}).get('object') == 'organization':
        new_org = data.get('current', {})
        new_nip = new_org.get('eee088234e85a23e5fed084c858151291f1626a9')
        if new_nip:
            duplicate_org = search_organization_by_nip(new_nip)
            if duplicate_org:
                delete_status = delete_organization(new_org.get('id'))
                if delete_status:
                    notify_alert_server({
                        'message': f"Duplicate organization deleted: {duplicate_org['name']} (NIP: {new_nip})"
                    })
                    return jsonify({
                        'status': 'duplicate_found',
                        'message': f"Duplicate organization found with NIP: {new_nip}. Deleted the newly created organization.",
                        'duplicate_org': duplicate_org
                    }), 200
    return jsonify({'status': 'ignored', 'message': 'Event ignored.'}), 200

def search_organization_by_nip(nip):
    url = f'https://api.pipedrive.com/v1/organizations/search'
    params = {
        'term': nip,
        'custom_fields': 'eee088234e85a23e5fed084c858151291f1626a9',
        'api_token': os.getenv('PIPEDRIVE_API_TOKEN')
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
        'api_token': os.getenv('PIPEDRIVE_API_TOKEN')
    }
    response = requests.delete(url, params=params)
    return response.status_code == 200

def notify_alert_server(message):
    url = f'{ALERT_SERVER_URL}/notify'
    response = requests.post(url, json=message)
    print(f"Sent notification to alert server: {response.status_code}, message: {message}")


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
