# server.py
from flask import Flask
from flask_socketio import SocketIO, join_room, send
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'galaxy_secret')
socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)

# Хранилище комнат: {game_id: {'host': sid, 'client': sid or None, 'state': {...}}}
games = {}

@socketio.on('create')
def handle_create():
    from uuid import uuid4
    game_id = str(uuid4())[:6].upper()
    games[game_id] = {'host': request.sid, 'client': None, 'state': None}
    join_room(game_id)
    print(f"Created game: {game_id}")
    send({'type': 'created', 'game_id': game_id}, to=request.sid)

@socketio.on('join')
def handle_join(data):
    game_id = data.get('game_id')
    if game_id in games and games[game_id]['client'] is None:
        games[game_id]['client'] = request.sid
        join_room(game_id)
        send({'type': 'joined'}, to=request.sid)
        send({'type': 'peer_joined'}, to=games[game_id]['host'])
        print(f"Player joined game: {game_id}")
    else:
        send({'type': 'error', 'msg': 'Game not found or full'}, to=request.sid)

@socketio.on('state')
def handle_state(data):
    game_id = data.get('game_id')
    if game_id in games:
        # Рассылаем состояние другому игроку
        target = None
        if request.sid == games[game_id]['host']:
            target = games[game_id]['client']
        elif request.sid == games[game_id]['client']:
            target = games[game_id]['host']
        if target:
            send({'type': 'state', 'data': data['data']}, to=target)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    for game_id, game in list(games.items()):
        if game['host'] == sid or game['client'] == sid:
            print(f"Game {game_id} closed due to disconnect")
            del games[game_id]
            break

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)