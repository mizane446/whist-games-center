import os
import uuid
from flask import Flask, render_template, redirect, url_for, session
from playcard import get_card_name
import blackjack, blackjack_eu, whist

SUPPORTED_GAMES = {'blackjack': blackjack, 'blackjack_eu': blackjack_eu, 'whist': whist}
app = Flask(__name__)

# ========= 这就是你当时修复 21 点的关键配置，必须全部加上 =========
app.secret_key = "blackjack_game_fixed_key_2026"  # 固定密钥，禁止修改
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 会话有效期1天
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"
app.config['SESSION_COOKIE_SECURE'] = True  # 适配Vercel HTTPS环境
app.config['SESSION_TYPE'] = 'cookie'  # 强制使用Cookie存储

# ========= 路由部分，和老师原版几乎一样，只加了session.permanent =========
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
    else:
        return redirect(url_for('select'))

@app.route('/game')
def game():
    session.permanent = True
    cur_game = session.get('cur_game', '')
    game_state = session.get('game_state', {})
    if cur_game in SUPPORTED_GAMES and game_state:
        return render_template(f'{cur_game}.html', game_state=game_state)
    else:
        return redirect(url_for('select'))

@app.route('/game_update/<path:action>')
def game_update(action):
    session.permanent = True
    cur_game = session.get('cur_game', '')
    if cur_game in SUPPORTED_GAMES:
        SUPPORTED_GAMES[cur_game].game_update(session, action)
        session.modified = True
        return redirect(url_for('game'))
    else:
        return redirect(url_for('select'))

@app.route('/select_game/<target_game>')
def select_game(target_game):
    session.permanent = True
    if target_game in SUPPORTED_GAMES:
        session['cur_game'] = target_game
        SUPPORTED_GAMES[target_game].new_game(session)
        session.modified = True
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
