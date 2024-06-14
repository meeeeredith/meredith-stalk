from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

hypixel = "8202bf0d-d5a2-4bf8-b24c-ec8e7514b69b"

# ---------------------------------------------------- #
# STALK HELPER FUNCTIONS 
# ---------------------------------------------------- #

def uuidpull(username) -> str:
    url = f'https://api.mojang.com/users/profiles/minecraft/{username}'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            uuid = data.get('id')
            return uuid
        else:
            return "False"
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return "False"

def get_hypixel_rank(ign) -> str:
    uuid = uuidpull(ign)
    try:
        data = requests.get(
            f"https://api.hypixel.net/player?key={hypixel}&uuid={uuid}").json()
        if data["success"]:
            player_info = data["player"]
            if player_info is None:
                return "Player Not Found"
            elif "monthlyPackageRank" in player_info and player_info[
                    "monthlyPackageRank"] == "SUPERSTAR":
                return "MVP_PLUS_PLUS"
            elif "rank" in player_info:
                return player_info["rank"]
            elif "newPackageRank" in player_info:
                return player_info["newPackageRank"]
            else:
                return "NO_RANK"
        else:
            return "API Request Failed"
    except Exception as e:
        return str(e)

def getrank(rank) -> str:
    namedict = {
    "NO_RANK": "",
    "VIP": "[VIP]",
    "VIP_PLUS": "[VIP+]",
    "MVP": "[MVP]",
    "MVP_PLUS": "[MVP+]",
    "MVP_PLUS_PLUS": "[MVP++]"
    }
    if rank in namedict:
        format = namedict[rank]
        return format
    return ""

def time_difference_from_now(unix_timestamp):
    timestamp_datetime = datetime.utcfromtimestamp(unix_timestamp / 1000)  # Convert milliseconds to seconds
    current_datetime = datetime.utcnow()
    difference = current_datetime - timestamp_datetime
    days = difference.days
    hours, seconds = divmod(difference.seconds, 3600)
    minutes = seconds // 60

    if days > 0:
        return f"{days} days {hours} hours {minutes} minutes"
    else:
        return f"{hours} hours {minutes} minutes"

def get_quest_info(data):
    most_recent_timestamp = 0
    most_recent_category = None

    for category_name, category in data.items():
        if 'completions' in category:
            for completion in category["completions"]:
                timestamp = completion["time"]
                if timestamp > most_recent_timestamp:
                    most_recent_timestamp = timestamp
                    most_recent_category = category_name

    diff = time_difference_from_now(most_recent_timestamp)
    return [most_recent_category, diff]

def return_last_action(username: str) -> list:
    response = requests.get(f"https://api.hypixel.net/player?key={hypixel}&uuid={uuidpull(username)}")
    if response.status_code != 200:
        return None

    dog = response.json()
    cat = dog.get('player', {}).get('quests', {})
    
    return get_quest_info(cat)

def stalk(ign):
    # check if player is a mc account
    uuid = uuidpull(ign)
    if uuid == "False":
        return f"Username {ign} does not exist!"

    # check if player has logged onto hypixel
    try:
        data = requests.get(
            f"https://api.hypixel.net/player?key={hypixel}&uuid={uuid}").json()
        if not data["success"] or data["player"] is None:
            return f"Username {ign} has never logged onto Hypixel!"
    except KeyError:
        return f"Username {ign} has never logged onto Hypixel!"

    # now we know they exist on hypixel, now get their rank
    userrank = get_hypixel_rank(ign)
    
    # now lets grab their megawalls specific stuff
    classgrab = "n/a"
    skingrab = "No skin"
    
    try:
        classgrab = data['player']['stats']['Walls3']['chosen_class']
    except KeyError:
        pass
        
    try:
        skingrab = data['player']['stats']['Walls3'][f'chosen_skin_{classgrab}']
    except KeyError:
        skingrab = classgrab
        
    hypixel_rank = getrank(userrank)
    lastaction = return_last_action(ign)
    event = lastaction[0]
    time = lastaction[1]
    
    return {
        'class': classgrab,
        'skin': skingrab,
        'username': ign,
        'rank': hypixel_rank,
        'event': event,
        'time': time
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    username = request.args.get('username')
    if not username:
        return jsonify({'message': 'Username is required!'}), 400

    # Stalk the user
    result = stalk(username)
    if isinstance(result, str):
        return jsonify({'message': result}), 404

    return jsonify({
        'class': result['class'],
        'skin': result['skin'],
        'username': result['username'],
        'rank': result['rank'],
        'event': result['event'],
        'time': result['time']
    })

if __name__ == '__main__':
    app.run(debug=True)
