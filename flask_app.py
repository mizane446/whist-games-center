import uuid
from flask import Flask, render_template, redirect, url_for, session
from flask_session import Session  # 服务端会话
from playcard import get_card_name
import blackjack, blackjack_eu, whist

SUPPORTED_GAMES = {'blackjack': blackjack, 'blackjack_eu': blackjack_eu, 'whist': whist}
app = Flask(__name__)

# 基础会话配置
app.secret_key = "blackjack_game_fixed_key_2026"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"
app.config['SESSION_COOKIE_SECURE'] = True

# 配置：会话存储在服务端文件（Vercel /tmp）
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = "/tmp/flask_sessions"
Session(app)

# 路由（全部沿用原始逻辑，无需修改读写）
@app.route('/')
def index():
    session.permanent = True
    return redirect(url_for('game'))

@app.route('/select')
def select():
    session.permanent = True
    session.setdefault('session_id', uuid.uuid4().hex)
    return render_template('select.html', cur_game=session.get('cur_game', ''))

@app.route('/new_game')
def new_game():
    session.permanent = True
    cur_game = session.get('cur_game', '')
    if cur_game in SUPPORTED_GAMES:
        SUPPORTED_GAMES[cur_game].new_game(session)
        session.modified = True
        return redirect(url_for('game'))
    return redirect(url_for('select'))

@app.route('/game')
def game():
    session.permanent = True
    session.setdefault('session_id', uuid.uuid4().hex)
    cur_game = session.get('cur_game', '')
    game_state = session.get('game_state', {})
    if cur_game in SUPPORTED_GAMES and game_state:
        return render_template(f'{cur_game}.html', game_state=game_state)
    return redirect(url_for('select'))

@app.route('/game_update/<path:action>')
def game_update(action):
    session.permanent = True
    cur_game = session.get('cur_game', '')
    if cur_game in SUPPORTED_GAMES:
        SUPPORTED_GAMES[cur_game].game_update(session, action)
        session.modified = True
        return redirect(url_for('game'))
    return redirect(url_for('select'))

@app.route('/select_game/<target_game>')
def select_game(target_game):
    session.permanent = True
    if target_game in SUPPORTED_GAMES:
        session['cur_game'] = target_game
        SUPPORTED_GAMES[target_game].new_game(session)
        session.modified = True
        return redirect(url_for('game'))
    return render_template('about.html', supported=False)

@app.route('/rules')
def rules():
    session.permanent = True
    return render_template('rules.html', cur_game=session.get('cur_game', ''))

@app.route('/log')
def log():
    session.permanent = True
    session.setdefault('session_id', uuid.uuid4().hex)
    return render_template('userlog.html', log="")

@app.route('/about')
def about():
    session.permanent = True
    return render_template('about.html', supported=True)

@app.context_processor
def utility_processor():
    return dict(enumerate=enumerate, get_card_name=get_card_name)

if __name__ == '__main__':
    app.run(port=80)
