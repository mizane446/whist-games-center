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
    """Determine which player wins a completed trick."""
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
            if is_trump and rank > best_rank:
                best_player = player
                best_rank = rank
                best_card = card
        else:
            if is_trump:
                best_player = player
                best_rank = rank
                best_card = card
                best_is_trump = True
            elif suit == lead_suit and rank > best_rank:
                best_player = player
                best_rank = rank
                best_card = card

    return best_player

# ====================== FULL-INFORMATION AI ======================

def card_value(card, trump_suit):
    """Return a numeric strength for a card (higher is better)."""
    suit = get_suit(card)
    rank = get_rank_ace_high(card)
    base = rank
    if suit == trump_suit:
        base += 20
    return base

def highest_card_of_suit(hand, suit):
    """Return the highest card of a given suit in hand, or None."""
    cards = [c for c in hand if get_suit(c) == suit]
    if not cards:
        return None
    return max(cards, key=lambda c: get_rank_ace_high(c))

def lowest_card_of_suit(hand, suit):
    """Return the lowest card of a given suit in hand, or None."""
    cards = [c for c in hand if get_suit(c) == suit]
    if not cards:
        return None
    return min(cards, key=lambda c: get_rank_ace_high(c))

def can_win_trick(current_trick, leader, trump_suit, player_hand, all_hands):
    """
    Determine if the player can potentially win the trick given all hands.
    Returns (can_win, best_card_to_win) where best_card_to_win is the minimal card that wins.
    """
    lead_suit = get_suit(current_trick[leader])
    # Determine current best card in trick
    best_player = leader
    best_card = current_trick[leader]
    best_rank = get_rank_ace_high(best_card)
    best_is_trump = (get_suit(best_card) == trump_suit)
    for p, card in current_trick.items():
        if p == leader:
            continue
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

    # If the current best is already partner's, no need to win
    partner = PARTNER[player_hand]  # but player_hand is not the player name, we need player param
    # We'll restructure function to accept player name instead of hand.
    # For simplicity, we'll just compute the minimal winning card for this player.
    # Better to rewrite.
    pass

# We'll implement separate helper functions that use the full hands.

def get_best_card_in_trick(trick, leader, trump_suit):
    """Return (best_player, best_card, best_rank, best_is_trump) for the current trick."""
    turn_order = get_turn_order(leader)
    lead_suit = get_suit(trick[leader])
    best_player = leader
    best_card = trick[leader]
    best_rank = get_rank_ace_high(best_card)
    best_is_trump = (get_suit(best_card) == trump_suit)
    for player in turn_order[1:]:
        if player not in trick:
            continue
        card = trick[player]
        rank = get_rank_ace_high(card)
        suit = get_suit(card)
        is_trump = (suit == trump_suit)
        if best_is_trump:
            if is_trump and rank > best_rank:
                best_player = player
                best_rank = rank
                best_card = card
        else:
            if is_trump:
                best_player = player
                best_rank = rank
                best_card = card
                best_is_trump = True
            elif suit == lead_suit and rank > best_rank:
                best_player = player
                best_rank = rank
                best_card = card
    return best_player, best_card, best_rank, best_is_trump

def get_legal_cards(hand, current_trick, leader):
    """Return cards that may legally be played now."""
    if not current_trick:
        return list(hand)

    lead_card = current_trick.get(leader)
    if not lead_card:
        return list(hand)

    lead_suit = get_suit(lead_card)
    same_suit_cards = [c for c in hand if get_suit(c) == lead_suit]
    return same_suit_cards if same_suit_cards else list(hand)

def card_beats_current(card, lead_suit, trump_suit, best_rank, best_is_trump):
    """Return True if card beats the current best card in a trick."""
    suit = get_suit(card)
    rank = get_rank_ace_high(card)

    if best_is_trump:
        return suit == trump_suit and rank > best_rank

    if suit == trump_suit and lead_suit != trump_suit:
        return True

    return suit == lead_suit and rank > best_rank

def lowest_card(cards):
    return min(cards, key=lambda c: get_rank_ace_high(c))

def highest_card(cards):
    return max(cards, key=lambda c: get_rank_ace_high(c))

def lowest_discard(cards, trump_suit):
    """Prefer throwing a low non-trump; keep trump when possible."""
    non_trump = [c for c in cards if get_suit(c) != trump_suit]
    return lowest_card(non_trump if non_trump else cards)

def minimal_winning_card(legal_cards, lead_suit, trump_suit, best_rank, best_is_trump):
    """
    Returns the smallest legal card that would win the trick given the current best.
    If cannot win, returns None.
    """
    winners = [
        c for c in legal_cards
        if card_beats_current(c, lead_suit, trump_suit, best_rank, best_is_trump)
    ]
    return lowest_card(winners) if winners else None

def winning_legal_cards(legal_cards, lead_suit, trump_suit, best_rank, best_is_trump):
    return [
        c for c in legal_cards
        if card_beats_current(c, lead_suit, trump_suit, best_rank, best_is_trump)
    ]

def players_after(player, leader, current_trick):
    """Return players still to act after player in the current trick."""
    turn_order = get_turn_order(leader)
    idx = turn_order.index(player)
    return [p for p in turn_order[idx + 1:] if p not in current_trick]

def later_opponent_can_beat(player, card, current_trick, leader, trump_suit, game_state):
    """Use full information to see if a later opponent can overtake this card."""
    simulated_trick = dict(current_trick)
    simulated_trick[player] = card
    best_player, best_card, best_rank, best_is_trump = get_best_card_in_trick(
        simulated_trick, leader, trump_suit
    )

    if best_player != player:
        return False

    lead_suit = get_suit(simulated_trick[leader])
    for future_player in players_after(player, leader, simulated_trick):
        if TEAM[future_player] == TEAM[player]:
            continue

        legal_cards = get_legal_cards(
            game_state['hands'][future_player],
            simulated_trick,
            leader
        )
        if any(card_beats_current(c, lead_suit, trump_suit, best_rank, best_is_trump)
               for c in legal_cards):
            return True

    return False

def partner_can_still_win(player, current_trick, leader, trump_suit, game_state):
    """Return True if partner has not played yet and owns a legal winning card."""
    partner = PARTNER[player]
    if partner in current_trick or partner not in players_after(player, leader, current_trick):
        return False

    best_player, best_card, best_rank, best_is_trump = get_best_card_in_trick(
        current_trick, leader, trump_suit
    )
    if TEAM[best_player] == TEAM[player]:
        return False

    lead_suit = get_suit(current_trick[leader])
    legal_cards = get_legal_cards(game_state['hands'][partner], current_trick, leader)
    return any(card_beats_current(c, lead_suit, trump_suit, best_rank, best_is_trump)
               for c in legal_cards)

def opponent_void_in_suit(opponent, suit, game_state):
    """Return True if opponent has no cards of given suit (based on perfect information)."""
    return not any(get_suit(c) == suit for c in game_state['hands'][opponent])

def count_cards_in_suit(player_hand, suit):
    return sum(1 for c in player_hand if get_suit(c) == suit)

def strongest_non_trump_suit(hand, trump_suit):
    """Return the suit (string) with the highest top card (excluding trump)."""
    best_suit = None
    best_top_rank = -1
    for suit in SUITS:
        if suit == trump_suit:
            continue
        top = highest_card_of_suit(hand, suit)
        if top and get_rank_ace_high(top) > best_top_rank:
            best_top_rank = get_rank_ace_high(top)
            best_suit = suit
    return best_suit

def expected_winner_if_play(player, card, game_state):
    """Simulate the outcome of playing a specific card in the current trick."""
    # This is a simplified simulation: assume all other players will play optimally?
    # For performance, we just do a static analysis.
    # We'll implement a deterministic evaluation: given all cards, who would win if we play this card?
    # Since we don't know future plays, we can't simulate fully. Instead we'll use heuristics.
    pass

# ====================== MAIN AI FUNCTIONS (with full information) ======================

def ai_play(player, game_state):
    """AI chooses a card using full information of all hands."""
    hand = game_state['hands'][player]
    current_trick = game_state['tricks'][-1] if game_state['tricks'] else {}
    leader = game_state['leader']
    trump_suit = game_state['trump_suit']

    if not current_trick:
        card = ai_lead_fullinfo(player, hand, trump_suit, game_state)
    else:
        card = ai_follow_fullinfo(player, hand, current_trick, leader, trump_suit, game_state)

    legal_cards = get_legal_cards(hand, current_trick, leader)
    if card in legal_cards:
        return card
    return lowest_discard(legal_cards, trump_suit)

def ai_lead_fullinfo(player, hand, trump_suit, game_state):
    """
    Leading strategy with complete knowledge of all hands.
    """
    # Count trump in each hand
    trump_counts = {p: count_cards_in_suit(game_state['hands'][p], trump_suit) for p in TURN_ORDER}
    my_trump = trump_counts[player]
    partner = PARTNER[player]
    partner_trump = trump_counts[partner]
    opponents = [p for p in TURN_ORDER if p not in (player, partner)]
    
    # 1. If we have a long solid suit (5+ cards with top honors), lead its highest.
    for suit in SUITS:
        if suit == trump_suit:
            continue
        suit_cards = [c for c in hand if get_suit(c) == suit]
        if len(suit_cards) >= 5:
            # Check if we have the Ace or King
            ranks = [get_rank_ace_high(c) for c in suit_cards]
            if max(ranks) >= 11:  # King or Ace
                return max(suit_cards, key=lambda c: get_rank_ace_high(c))
    
    # 2. If opponent has many trump, lead a low trump to force them to waste high trump.
    opp_trump_total = sum(trump_counts[o] for o in opponents)
    if opp_trump_total >= 6 and my_trump >= 3:
        low_trump = lowest_card_of_suit(hand, trump_suit)
        if low_trump:
            return low_trump
    
    # 3. If partner has strong trump and we have a singleton, lead that singleton.
    if partner_trump >= 4 and my_trump == 1:
        singleton = [c for c in hand if count_cards_in_suit(hand, get_suit(c)) == 1]
        if singleton:
            return singleton[0]
    
    # 4. Otherwise, lead the highest card of our strongest non-trump suit.
    best_suit = strongest_non_trump_suit(hand, trump_suit)
    if best_suit:
        return highest_card_of_suit(hand, best_suit)
    
    # 5. Only trump left – lead the lowest.
    trump_cards = [c for c in hand if get_suit(c) == trump_suit]
    if trump_cards:
        return min(trump_cards, key=lambda c: get_rank_ace_high(c))
    
    # Fallback
    return hand[0]

def ai_follow_fullinfo(player, hand, current_trick, leader, trump_suit, game_state):
    """
    Following strategy with complete knowledge.
    """
    lead_suit = get_suit(current_trick[leader])
    partner = PARTNER[player]

    legal_cards = get_legal_cards(hand, current_trick, leader)
    best_player, best_card, best_rank, best_is_trump = get_best_card_in_trick(
        current_trick, leader, trump_suit
    )

    if best_player == partner:
        return lowest_discard(legal_cards, trump_suit)

    if partner_can_still_win(player, current_trick, leader, trump_suit, game_state):
        return lowest_discard(legal_cards, trump_suit)

    winning_card = minimal_winning_card(
        legal_cards, lead_suit, trump_suit, best_rank, best_is_trump
    )

    if winning_card is None:
        return lowest_discard(legal_cards, trump_suit)

    if not players_after(player, leader, current_trick):
        return winning_card

    if later_opponent_can_beat(player, winning_card, current_trick, leader, trump_suit, game_state):
        stronger_winners = sorted(
            winning_legal_cards(legal_cards, lead_suit, trump_suit, best_rank, best_is_trump),
            key=lambda c: get_rank_ace_high(c)
        )
        for candidate in stronger_winners:
            if not later_opponent_can_beat(player, candidate, current_trick, leader, trump_suit, game_state):
                return candidate
        return lowest_discard(legal_cards, trump_suit)

    return winning_card

# ====================== GAME FLOW (unchanged) ======================

def finish_trick(game_state, session_id):
    """Determine the trick winner, update scores, and prepare for next trick."""
    current_trick = game_state['tricks'][-1]
    leader = game_state['leader']
    trump_suit = game_state['trump_suit']

    winner = determine_trick_winner(current_trick, leader, trump_suit)

    winner_team = TEAM[winner]
    game_state['scores'][winner_team] += 1

    total_tricks = (game_state['scores']['south_north'] +
                    game_state['scores']['east_west'])

    if total_tricks >= 13:
        sn = game_state['scores']['south_north']
        ew = game_state['scores']['east_west']
        if sn >= 7:
            game_state['message'] = f"Game Over! South-North wins ({sn}-{ew})!"
            game_state['message_class'] = "win-message"
        else:
            game_state['message'] = f"Game Over! East-West wins ({ew}-{sn})!"
            game_state['message_class'] = "lose-message"
        game_state['stop_type'] = 'game_over'
    else:
        team_name = "South-North" if winner_team == 'south_north' else "East-West"
        game_state['message'] = f"{team_name} wins the trick!"
        game_state['message_class'] = "info-message"
        game_state['leader'] = winner
        game_state['stop_type'] = 'new_trick'

def handle_new_trick(game_state, session_id):
    """Set up a new trick and process AI plays until it's South's turn."""
    if game_state.get('stop_type') == 'game_over':
        return

    current_trick = {}
    game_state['tricks'].append(current_trick)
    game_state['message'] = None

    leader = game_state['leader']
    turn_order = get_turn_order(leader)

    for player in turn_order:
        if player == 'south':
            if not current_trick:
                game_state['stop_type'] = 'lead_card'
            else:
                game_state['stop_type'] = 'follow_card'
            return

        card = ai_play(player, game_state)   # uses full-info AI
        current_trick[player] = card
        game_state['hands'][player].remove(card)

    finish_trick(game_state, session_id)

def handle_human_play(game_state, card, session_id):
    """Process the card played by the human player (South)."""
    if card not in game_state['hands']['south']:
        return

    current_trick = game_state['tricks'][-1]
    leader = game_state['leader']
    if card not in get_legal_cards(game_state['hands']['south'], current_trick, leader):
        return

    game_state['hands']['south'].remove(card)
    current_trick['south'] = card

    leader = game_state['leader']
    turn_order = get_turn_order(leader)
    south_idx = turn_order.index('south')
    remaining_players = turn_order[south_idx + 1:]

    for player in remaining_players:
        if player not in current_trick:
            card = ai_play(player, game_state)
            current_trick[player] = card
            game_state['hands'][player].remove(card)

    finish_trick(game_state, session_id)

# ====================== PUBLIC API ======================

def new_game(session):
    """Initialize a new Whist game."""
    session_id = session.get('session_id', '')

    deck = make_deck()
    random.shuffle(deck)

    players = {
        'north': 'North (AI)',
        'east': 'East (AI)',
        'south': 'You',
        'west': 'West (AI)',
    }

    deal_order = ['west', 'north', 'south', 'east']
    hands = {'north': [], 'east': [], 'south': [], 'west': []}
    for i, card in enumerate(deck):
        hands[deal_order[i % 4]].append(card)

    trump_card = deck[51]
    trump_suit = get_suit(trump_card)

    for p in hands:
        hands[p] = sort_hand(hands[p])

    session['game_state'] = {
        'players': players,
        'hands': hands,
        'trump_suit': trump_suit,
        'trump_suit_name': get_suit_name(trump_suit),
        'stop_type': 'new_trick',
        'leader': 'north',
        'tricks': [],
        'scores': {'south_north': 0, 'east_west': 0},
        'message': None,
        'message_class': "info-message",
    }

def game_update(session, action):
    """Process a game action (new_trick or play/<card>)."""
    game_state = session.get('game_state')
    if not game_state:
        return new_game(session)

    session_id = session.get('session_id', '')

    if action == 'new_trick':
        handle_new_trick(game_state, session_id)
    elif action.startswith('play/'):
        card = action[5:]
        handle_human_play(game_state, card, session_id)
