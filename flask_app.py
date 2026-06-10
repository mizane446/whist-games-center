import os
import uuid
import json
from flask import Flask, render_template, redirect, url_for, session
from playcard import get_card_name
import blackjack, blackjack_eu, whist

SUPPORTED_GAMES = {'blackjack': blackjack, 'blackjack_eu': blackjack_eu, 'whist': whist}
app = Flask(__name__)

# ========= 沿用之前 Blackjack 的会话加固配置（必保留） =========
app.secret_key = "blackjack_game_fixed_key_2026"
app.config['PERMANENT_SESSION_LIFETIME'] = 86400
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"
app.config['SESSION_COOKIE_SECURE'] = True

# ========= 新增：游戏状态文件存储目录 =========
STATE_DIR = "game_states"
# 自动创建文件夹（不存在则新建）
if not os.path.exists(STATE_DIR):
    os.mkdir(STATE_DIR)

# ========= 工具函数：读写游戏状态JSON文件 =========
def get_state_path(sid):
    """根据 session_id 生成文件路径"""
    return os.path.join(STATE_DIR, f"{sid}.json")

def save_game_state(sid, state):
    """保存游戏状态到JSON文件"""
    file_path = get_state_path(sid)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def load_game_state(sid):
    """从JSON文件读取游戏状态，不存在返回空"""
    file_path = get_state_path(sid)
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def clear_game_state(sid):
    """清空游戏状态（新游戏/切换游戏时调用）"""
    file_path = get_state_path(sid)
    if os.path.exists(file_path):
        os.remove(file_path)

# ========= 路由部分：仅修改 game_state 读写逻辑，其余不动 =========
@app.route('/')
def index():
    session.permanent = True
    return redirect(url_for('game'))

@app.route('/select')
def select():
    # 生成唯一会话ID，只存在Cookie中（体积极小）
    sid = session.setdefault('session_id', uuid.uuid4().hex)
    session.permanent = True
    # 切换游戏页，清空旧游戏状态
    clear_game_state(sid)
    return render_template('select.html', cur_game=session.get('cur_game', ''))

@app.route('/new_game')
def new_game():
    session.permanent = True
    cur_game = session.get('cur_game', '')
    sid = session.get('session_id', '')
    if cur_game in SUPPORTED_GAMES and sid:
        # 调用游戏模块初始化对局
        SUPPORTED_GAMES[cur_game].new_game(session)
        # 从session取出状态，写入本地文件，不再依赖session存大数据
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
    # 从文件读取游戏状态，不再读session
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
        # 1. 从文件读取最新状态，临时写入session供游戏逻辑使用
        game_state = load_game_state(sid) or {}
        session['game_state'] = game_state
        # 2. 执行游戏更新逻辑
        SUPPORTED_GAMES[cur_game].game_update(session, action)
        # 3. 把更新后的状态重新存回文件，清空session里的大数据
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
        # 切换游戏，清空旧状态
        if sid:
            clear_game_state(sid)
        SUPPORTED_GAMES[target_game].new_game(session)
        # 状态落地到文件
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
    session_id = session.setdefault('session_id', uuid.uuid4().hex)
    # 若有日志功能，沿用原有逻辑即可
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