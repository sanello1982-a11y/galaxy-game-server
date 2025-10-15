from flask import Flask
from flask_socketio import SocketIO, send, emit
import os
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'galaxy_secret')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

games = {}

@socketio.on('create')
def handle_create():
    game_id = str(uuid.uuid4())[:6].upper()
    games[game_id] = {'host': request.sid, 'client': None, 'state': None}
    print(f"Created game: {game_id}")
    emit('created', {'game_id': game_id})

@socketio.on('join')
def handle_join(data):
    game_id = data.get('game_id')
    if game_id in games and games[game_id]['client'] is None:
        games[game_id]['client'] = request.sid
        emit('joined')
        emit('peer_joined', room=games[game_id]['host'])
        print(f"Player joined: {game_id}")
    else:
        emit('error', {'msg': 'Game not found or full'})

@socketio.on('state')
def handle_state(data):
    game_id = data.get('game_id')
    if game_id in games:
        target = None
        if request.sid == games[game_id]['host']:
            target = games[game_id]['client']
        elif request.sid == games[game_id]['client']:
            target = games[game_id]['host']
        if target:
            emit('state', data['data'], room=target)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    for gid, game in list(games.items()):
        if game['host'] == sid or game['client'] == sid:
            print(f"Game {gid} closed")
            del games[gid]
            break

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)