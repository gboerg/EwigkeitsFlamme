import json
import requests
from datetime import datetime

# Lädt die Konfiguration (client_id, client_secret, access_token und watchlist) aus einer config.json
def load_config():
    try:
        with open("../../config.json") as config_file:
            return json.load(config_file)
    except Exception as e:
        print(f"Fehler beim Laden der config.json: {e}")
        return {}

# Funktion, um ein neues Zugangstoken zu erhalten
def get_app_access_token(config):
    """
    Holt ein neues Access-Token für die Anwendung, basierend auf den Client-Anmeldedaten.
    """
    params = {
        "client_id": config["client_id"],
        "client_secret": config["client_secret"],
        "grant_type": "client_credentials"
    }

    response = requests.post("https://id.twitch.tv/oauth2/token", params=params)
    if response.status_code == 200:
        access_token = response.json()["access_token"]
        config["access_token"] = access_token  # Access-Token in der Konfiguration speichern
        return access_token
    else:
        raise Exception(f"Fehler beim Abrufen des Tokens, Statuscode: {response.status_code}, Nachricht: {response.text}")

# Funktion, um Benutzer-IDs von Twitch zu erhalten
def get_users(login_names, config):
    """
    Holt die Benutzer-IDs für die angegebenen Login-Namen.
    """
    params = {
        "login": login_names
    }
    headers = {
        "Authorization": f"Bearer {config['access_token']}",
        "Client-ID": config["client_id"]
    }

    response = requests.get("https://api.twitch.tv/helix/users", params=params, headers=headers)
    if response.status_code == 200:
        return {entry["login"]: entry["id"] for entry in response.json()["data"]}
    else:
        raise Exception(f"Fehler beim Abrufen der Benutzerdaten, Statuscode: {response.status_code}, Nachricht: {response.text}")

# Funktion, um Streaming-Daten für die Benutzer abzurufen
def get_streams(user_ids, config):
    """
    Holt Stream-Daten für die angegebenen Benutzer-IDs.
    """
    params = {
        "user_id": user_ids
    }
    headers = {
        "Authorization": f"Bearer {config['access_token']}",
        "Client-ID": config["client_id"]
    }

    response = requests.get("https://api.twitch.tv/helix/streams", params=params, headers=headers)
    if response.status_code == 200:
        return {entry["user_id"]: entry for entry in response.json()["data"]}
    else:
        raise Exception(f"Fehler beim Abrufen der Streams, Statuscode: {response.status_code}, Nachricht: {response.text}")

# Benachrichtigungen generieren, wenn ein Benutzer live geht
def get_notifications(config, online_users):
    """
    Überprüft, welche Benutzer live sind und generiert Benachrichtigungen für die Benutzer in der Watchlist.
    """
    try:
        # Schritt 1: Benutzer-IDs für die Watchlist abrufen
        users = get_users(config["watchlist"], config)
        user_ids = list(users.values())

        # Schritt 2: Stream-Daten für diese Benutzer abrufen
        streams = get_streams(user_ids, config)

        notifications = []
        for user_name, user_id in users.items():
            stream_data = streams.get(user_id)
            if stream_data:
                # Stream-Startzeit analysieren
                started_at = datetime.strptime(stream_data["started_at"], "%Y-%m-%dT%H:%M:%SZ")

                # Wenn der Benutzer gerade live gegangen ist oder einen neuen Stream gestartet hat
                if online_users.get(user_name) is None or started_at > online_users[user_name]:
                    online_users[user_name] = started_at
                    notifications.append({
                        "user_name": stream_data["user_name"],
                        "url": f"https://twitch.tv/{stream_data['user_name']}"
                    })
            else:
                # Benutzer ist offline
                online_users[user_name] = None

        return notifications

    except Exception as e:
        print(f"Fehler in get_notifications: {e}")
        return []

# Funktion, um den Zeitplan eines bestimmten Kanals abzurufen
def get_schedule(user_ids, config):
    """
    Holt den Zeitplan für die angegebenen Benutzer-IDs (geplante Streams).
    """
    schedule_url = "https://api.twitch.tv/helix/schedule"

    params = {
        "broadcaster_id": user_ids
    }
    headers = {
        "Authorization": f"Bearer {config['access_token']}",
        "Client-ID": config["client_id"]
    }

    response = requests.get(schedule_url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()["data"]
    else:
        raise Exception(f"Fehler beim Abrufen des Zeitplans, Statuscode: {response.status_code}, Nachricht: {response.text}")

# Laden der Konfiguration und Zugriff auf den Zeitplan
if __name__ == "__main__":
    # Laden der Konfiguration
    config = load_config()

    # Access-Token anfordern, falls es noch nicht vorhanden ist
    if "access_token" not in config:
        config["access_token"] = get_app_access_token(config)

    # Online-Benutzer verfolgen
    online_users = {}

    # Benachrichtigungen für geplante Streams und aktuell live gehende Streams abrufen
    notifications = get_notifications(config, online_users)

    # Benachrichtigungen ausgeben
    if notifications:
        for notification in notifications:
            print(f"{notification['user_name']} ist jetzt live: {notification['url']}")
    else:
        print("Keine neuen Benachrichtigungen.")
