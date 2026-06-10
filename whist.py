import random
from playcard import make_deck, get_suit, get_rank_ace_high, SUITS, get_suit_name
#from userlog import add_log_entry

# ====================== CONSTANTS ======================

# 逆时针顺序: North -> West -> South -> East
TURN_ORDER = ['north', 'west', 'south', 'east']

PARTNER = {
    'north': 'south',
    'south': 'north',
    'east': 'west',
    'west': 'east'
}

TEAM = {
    'north': 'south_north',
    'south': 'south_north',
    'east': 'east_west',
    'west': 'east_west'
}

# ====================== HELPERS ======================

def get_next_player(player):
    """Return the next player in counter-clockwise order."""
    idx = TURN_ORDER.index(player)
    return TURN_ORDER[(idx + 1) % 4]


def get_turn_order(leader):
    """Return the full turn order starting from the leader (counter-clockwise)."""
    idx = TURN_ORDER.index(leader)
    return [TURN_ORDER[(idx + i) % 4] for i in range(4)]


def sort_hand(hand):
    """Sort a hand by suit (H/S/D/C), then rank descending (A high first)."""
    return sorted(hand, key=lambda c: (SUITS.index(get_suit(c)),
                                       -get_rank_ace_high(c)))


def determine_trick_winner(trick, leader, trump_suit):
    """Determine which player wins a completed trick.

    Args:
        trick: dict mapping player -> card, e.g. {'north': 'AS', 'east': '2H', ...}
        leader: the player who led the trick
        trump_suit: the trump suit for this round ('H', 'S', 'D', 'C')

    Returns:
        The winning player name (e.g. 'north')
    """
    turn_order = get_turn_order(leader)
    lead_suit = get_suit(trick[leader])

    best_player = leader
    best_card = trick[leader]
    best_rank = get_rank_ace_high(best_card)
    best_is_trump = (get_suit(best_card) == trump_suit)

    for player in turn_order[1:]:
        card = trick[player]
        rank = get_rank_ace_high(card)
        suit = get_suit(card)
        is_trump = (suit == trump_suit)

        if best_is_trump:
            # Both are trump: higher rank wins
            if is_trump and rank > best_rank:
                best_player = player
                best_rank = rank
                best_card = card
        else:
            if is_trump:
                # Trump beats any non-trump
                best_player = player
                best_rank = rank
                best_card = card
                best_is_trump = True
            elif suit == lead_suit and rank > best_rank:
                # Same suit, higher rank wins
                best_player = player
                best_rank = rank
                best_card = card

    return best_player


# ====================== AI STRATEGIES ======================

def ai_play(player, game_state):
    """AI chooses a card to play.

    Considers: current hand, who leads, what's already been played,
    trump suit, and partner/opponent relationships.
    """
    hand = game_state['hands'][player]
    current_trick = game_state['tricks'][-1] if game_state['tricks'] else {}
    leader = game_state['leader']
    trump_suit = game_state['trump_suit']

    # Leading a new trick
    if not current_trick:
        return ai_lead(player, hand, trump_suit)

    # Following to an existing trick
    return ai_follow(player, hand, current_trick, leader, trump_suit)


def ai_lead(player, hand, trump_suit):
    """AI chooses a card when leading a trick.

    Strategy:
    - If we have 4+ trump cards, lead a medium trump to draw out opponents' trump.
    - Otherwise, lead the highest card of our strongest non-trump suit.
    - If only trump left, lead the lowest trump.
    """
    # Group cards by suit
    suits = {}
    for card in hand:
        suit = get_suit(card)
        suits.setdefault(suit, []).append(card)

    # Sort each suit by rank descending
    for suit in suits:
        suits[suit].sort(key=get_rank_ace_high, reverse=True)

    trump_cards = suits.get(trump_suit, [])

    # If we have many trump cards, lead a medium one
    if len(trump_cards) >= 4:
        trump_cards.sort(key=get_rank_ace_high)
        # Play a medium trump (around the middle of our trump holding)
        return trump_cards[len(trump_cards) // 2]

    # Find the strongest non-trump suit
    best_card = None
    best_rank = -1

    for suit, cards in suits.items():
        if suit == trump_suit:
            continue
        # Lead the highest card in this suit
        card = cards[0]
        rank = get_rank_ace_high(card)
        if rank > best_rank:
            best_rank = rank
            best_card = card

    if best_card is not None:
        return best_card

    # Only trump cards left — lead the lowest
    trump_cards.sort(key=get_rank_ace_high)
    return trump_cards[0]


def ai_follow(player, hand, current_trick, leader, trump_suit):
    """AI chooses a card when following to a trick.

    Strategy:
    - Must follow suit if possible (enforced by rules, but AI self-enforces).
    - If partner is currently winning: play our lowest card in the lead suit
      (or discard low if we can't follow suit).
    - If opponent is winning: try to win with a higher card in the lead suit,
      or trump if we can't.
    """
    lead_suit = get_suit(current_trick[leader])
    partner = PARTNER[player]

    # Cards we can play that follow suit
    same_suit_cards = [c for c in hand if get_suit(c) == lead_suit]

    # Determine who is currently winning the trick (excluding our own card)
    turn_order = get_turn_order(leader)
    best_player = leader
    best_card = current_trick[leader]
    best_rank = get_rank_ace_high(best_card)
    best_is_trump = (get_suit(best_card) == trump_suit)

    for p in turn_order:
        if p == player or p not in current_trick:
            continue
        card = current_trick[p]
        rank = get_rank_ace_high(card)
        suit = get_suit(card)
        is_trump = (suit == trump_suit)

        if best_is_trump:
            if is_trump and rank > best_rank:
                best_player = p
                best_rank = rank
                best_card = card
        else:
            if is_trump:
                best_player = p
                best_rank = rank
                best_card = card
                best_is_trump = True
            elif suit == lead_suit and rank > best_rank:
                best_player = p
                best_rank = rank
                best_card = card

    # CASE 1: Partner is winning — play low
    if best_player == partner:
        if same_suit_cards:
            # Play the lowest card of the lead suit
            same_suit_cards.sort(key=get_rank_ace_high)
            return same_suit_cards[0]
        else:
            # Can't follow suit — discard lowest non-trump (or lowest overall)
            return _discard_lowest(hand, trump_suit)

    # CASE 2: Opponent is winning — try to win
    if same_suit_cards:
        # If opponent is already winning with trump, we cannot beat with same suit
        if not best_is_trump:
            # Try to beat with a higher card of the same suit
            beaters = [c for c in same_suit_cards
                       if get_rank_ace_high(c) > best_rank]
            if beaters:
                beaters.sort(key=get_rank_ace_high)
                return beaters[0]  # Lowest winning card
        # Can't beat (or opponent has trump) — play lowest of that suit
        same_suit_cards.sort(key=get_rank_ace_high)
        return same_suit_cards[0]

    else:
        # Can't follow suit — consider trumping
        if lead_suit != trump_suit:
            trump_cards = [c for c in hand if get_suit(c) == trump_suit]
            if trump_cards and not best_is_trump:
                # Trump it with the lowest trump
                trump_cards.sort(key=get_rank_ace_high)
                return trump_cards[0]
            elif trump_cards and best_is_trump:
                # Opponent already trumped — can we overtrump?
                overtrump = [c for c in trump_cards
                             if get_rank_ace_high(c) > best_rank]
                if overtrump:
                    overtrump.sort(key=get_rank_ace_high)
                    return overtrump[0]

        # Discard lowest non-trump (or lowest overall)
        return _discard_lowest(hand, trump_suit)


def _discard_lowest(hand, trump_suit):
    """Discard the lowest-value card, preferring to keep trump cards."""
    non_trump = [c for c in hand if get_suit(c) != trump_suit]
    if non_trump:
        non_trump.sort(key=get_rank_ace_high)
        return non_trump[0]
    # All trump — play lowest trump
    hand.sort(key=get_rank_ace_high)
    return hand[0]


# ====================== GAME FLOW ======================

def finish_trick(game_state, session_id):
    """Determine the trick winner, update scores, and prepare for next trick."""
    current_trick = game_state['tricks'][-1]
    leader = game_state['leader']
    trump_suit = game_state['trump_suit']

    winner = determine_trick_winner(current_trick, leader, trump_suit)

    # Update score
    winner_team = TEAM[winner]
    game_state['scores'][winner_team] += 1

    total_tricks = (game_state['scores']['south_north'] +
                    game_state['scores']['east_west'])

    if total_tricks >= 13:
        # Game over
        sn = game_state['scores']['south_north']
        ew = game_state['scores']['east_west']
        if sn >= 7:
            game_state['message'] = f"Game Over! South-North wins ({sn}-{ew})!"
            game_state['message_class'] = "win-message"
        else:
            game_state['message'] = f"Game Over! East-West wins ({ew}-{sn})!"
            game_state['message_class'] = "lose-message"
        game_state['stop_type'] = 'game_over'
        # add_log_entry(session_id, f"Game over. South-North: {sn}, East-West: {ew}")
    else:
        team_name = "South-North" if winner_team == 'south_north' else "East-West"
        game_state['message'] = f"{team_name} wins the trick!"
        game_state['message_class'] = "info-message"
        game_state['leader'] = winner
        game_state['stop_type'] = 'new_trick'
        # add_log_entry(session_id, f"Trick won by {winner} ({team_name}).")


def handle_new_trick(game_state, session_id):
    """Set up a new trick and process AI plays until it's South's turn."""
    # Do not start a new trick if the game is already over
    if game_state.get('stop_type') == 'game_over':
        return

    current_trick = {}
    game_state['tricks'].append(current_trick)
    game_state['message'] = None

    leader = game_state['leader']
    turn_order = get_turn_order(leader)

    # AI players play until it's South's turn
    for player in turn_order:
        if player == 'south':
            # Human's turn
            if not current_trick:
                # South is leading
                game_state['stop_type'] = 'lead_card'
            else:
                # South must follow
                game_state['stop_type'] = 'follow_card'
            return

        # AI plays
        card = ai_play(player, game_state)
        current_trick[player] = card
        game_state['hands'][player].remove(card)

    # All four played (shouldn't happen normally since South is human)
    finish_trick(game_state, session_id)


def handle_human_play(game_state, card, session_id):
    """Process the card played by the human player (South)."""
    # Validate the card
    if card not in game_state['hands']['south']:
        return

    # Validate that South is allowed to play this card
    if game_state['stop_type'] == 'follow_card':
        # South must follow suit if possible
        current_trick = game_state['tricks'][-1]
        leader = game_state['leader']
        lead_suit = get_suit(current_trick[leader])
        if get_suit(card) != lead_suit:
            # Check if South has any card of the lead suit
            has_lead_suit = any(get_suit(c) == lead_suit
                                for c in game_state['hands']['south'])
            if has_lead_suit:
                # Illegal play — can't discard when you have the suit
                return

    # Remove card from hand and add to trick
    game_state['hands']['south'].remove(card)
    current_trick = game_state['tricks'][-1]
    current_trick['south'] = card

    # Remaining AI players play after South
    leader = game_state['leader']
    turn_order = get_turn_order(leader)
    south_idx = turn_order.index('south')
    remaining_players = turn_order[south_idx + 1:]

    for player in remaining_players:
        if player not in current_trick:
            card = ai_play(player, game_state)
            current_trick[player] = card
            game_state['hands'][player].remove(card)

    # Trick is now complete — determine winner
    finish_trick(game_state, session_id)


# ====================== PUBLIC API ======================

def new_game(session):
    """Initialize a new Whist game."""
    session_id = session.get('session_id', '')

    # Create and shuffle the deck
    deck = make_deck()
    random.shuffle(deck)

    players = {
        'north': 'North (AI)',
        'east': 'East (AI)',
        'south': 'You',
        'west': 'West (AI)',
    }

    # Deal 13 cards to each player.
    # Use an order that gives the last card (deck[51]) to East, as specified.
    # 51 % 4 = 3, so East must be at index 3 in the deal sequence.
    deal_order = ['west', 'north', 'south', 'east']
    hands = {'north': [], 'east': [], 'south': [], 'west': []}
    for i, card in enumerate(deck):
        hands[deal_order[i % 4]].append(card)

    # The last card goes to East — its suit is the trump suit
    trump_card = deck[51]
    trump_suit = get_suit(trump_card)

    # Sort each hand for display
    for p in hands:
        hands[p] = sort_hand(hands[p])

    session['game_state'] = {
        'players': players,
        'hands': hands,
        'trump_suit': trump_suit,
        'trump_suit_name': get_suit_name(trump_suit),
        'stop_type': 'new_trick',
        'leader': 'north',  # North leads the first trick
        'tricks': [],       # list of dicts, one per trick
        'scores': {'south_north': 0, 'east_west': 0},
        'message': None,
        'message_class': "info-message",
    }

    # add_log_entry(session_id,
    #               f"New Whist game started. Trump is {get_suit_name(trump_suit)} ({trump_suit}).")


def game_update(session, action):
    """Process a game action (new_trick or play/<card>)."""
    game_state = session.get('game_state')
    if not game_state:
        return new_game(session)

    session_id = session.get('session_id', '')

    if action == 'new_trick':
        handle_new_trick(game_state, session_id)
    elif action.startswith('play/'):
        card = action[5:]  # e.g. 'AS' for Ace of Spades
        handle_human_play(game_state, card, session_id)
    # Ignore unknown actions