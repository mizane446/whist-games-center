import os
import uuid
import json
import tempfile  # 必须加上，适配Vercel临时目录
from flask import Flask, render_template, redirect, url_for, session
from playcard import get_card_name
import blackjack, blackjack_eu, whist

SUPPORTED_GAMES = {'blackjack': blackjack, 'blackjack_eu': blackjack_eu, 'whist': whist}
app = Flask(__name__)

# ========= 沿用之前 Blackjack 的会话加固配置（必保留） =========
app.secret_key = "blackjack_game_fixed_key_2026"  # 固定密钥，必须有！
app.config['PERMANENT_SESSION_LIFETIME'] = 86400
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"
app.config['SESSION_COOKIE_SECURE'] = True

# ========= 适配Vercel：使用系统临时目录（可读写） =========
STATE_DIR = tempfile.gettempdir()  # 自动获取Vercel可读写的临时目录

# ========= 工具函数：读写游戏状态JSON文件 =========
def get_state_path(sid):
    return os.path.join(STATE_DIR, f"{sid}.json")

def save_game_state(sid, state):
    with open(get_state_path(sid), "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def load_game_state(sid):
    path = get_state_path(sid)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def clear_game_state(sid):
    path = get_state_path(sid)
    if os.path.exists(path):
        os.remove(path)

# ========= 路由部分 =========
@app.route('/')
def index():
    session.permanent = True
    return redirect(url_for('game'))

@app.route('/select')
def select():
    sid = session.setdefault('session_id', uuid.uuid4().hex)
    session.permanent = True
    clear_game_state(sid)
    return render_template('select.html', cur_game=session.get('cur_game', ''))

@app.route('/new_game')
def new_game():
    session.permanent = True
    cur_game = session.get('cur_game', '')
    sid = session.get('session_id', '')
    if cur_game in SUPPORTED_GAMES and sid:
        SUPPORTED_GAMES[cur_game].new_game(session)
        game_state = session.pop('game_state', {})
        save_game_state(sid, game_state)
        session.modified = True
        return redirect(url_for('game'))
    else:
        return redirect(url_for('select'))

@app.route('/game')
def game():
    session.permanent = True
    sid = session.setdefault('session_id', uuid.uuid4().hex)
    cur_game = session.get('cur_game', '')
    game_state = load_game_state(sid)
    if cur_game in SUPPORTED_GAMES and game_state:
        return render_template(f'{cur_game}.html', game_state=game_state)
    else:
        return redirect(url_for('select'))

@app.route('/game_update/<path:action>')
def game_update(action):
    session.permanent = True
    cur_game = session.get('cur_game', '')
    sid = session.get('session_id', '')
    if cur_game in SUPPORTED_GAMES and sid:
        game_state = load_game_state(sid) or {}
        session['game_state'] = game_state
        SUPPORTED_GAMES[cur_game].game_update(session, action)
        new_state = session.pop('game_state', {})
        save_game_state(sid, new_state)
        session.modified = True
        return redirect(url_for('game'))
    else:
        return redirect(url_for('select'))

@app.route('/select_game/<target_game>')
def select_game(target_game):
    session.permanent = True
    if target_game in SUPPORTED_GAMES:
        session['cur_game'] = target_game
        sid = session.get('session_id', '')
        if sid:
            clear_game_state(sid)
        SUPPORTED_GAMES[target_game].new_game(session)
        game_state = session.pop('game_state', {})
        save_game_state(sid, game_state)
        return redirect(url_for('game'))
    else:
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
