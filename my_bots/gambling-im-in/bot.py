"""Bot A: The "Gambling? I'm in!" — wins every time."""
import random

BOT_NAME = "Gambling? I'm in!"

four_six_score_bet_range = [0.26, 0.5]
percent_stack_before_fold = 0.8
russian_roulette = [0.05, 0.1, 0.2]
amount_to_call_threshold = 0.3
all_in_ratio_when_exess = 0.5
all_in_amount = [1]


opponent_all_ins = 0

RANK_MAP = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, 'T':10, 'J':11, 'Q':12, 'K':13, 'A':14}

TIERS = {
    1: "AA KK QQ JJ AKs",
    2: "TT AQs AJs KQs AKo",
    3: "99 ATs KJs QJs JTs AQo",
    4: "88 KTs QTs J9s T9s 98s AJo KQo",
    5: "77 A9s A8s A7s A6s A5s A4s A3s A2s Q9s T8s 97s 87s 76s KJo QJo JTo",
    6: "66 55 K9s J8s 86s 75s 54s ATo KTo QTo",
    7: "44 33 22 K8s K7s K6s K5s K4s K3s K2s Q8s T7s 64s 53s 43s J9o T9o 98o",
    8: "J7s 96s 85s 74s 42s 32s A9o K9o Q9o J8o T8o 87o 76o 65o 54o",
}

HAND_RANK = {}
for tier, hands in TIERS.items():
    for h in hands.split():
        s = h[2] if len(h) == 3 else "o"
        HAND_RANK[h[0] + h[1] + s] = HAND_RANK[h[1] + h[0] + s] = tier

def hand_rank(c1, c2):
    return HAND_RANK.get(c1[0] + c2[0] + ("s" if c1[1] == c2[1] else "o"), 9)

def seven_two(c1, c2):
    return {c1[0], c2[0]} == {"7", "2"}

def has_one_pair(c1, c2, community_cards=[]):
    board_ranks = [c[0] for c in community_cards]
    return c1[0] == c2[0] or c1[0] in board_ranks or c2[0] in board_ranks

def has_two_pair(c1, c2, community_cards=[]):
    board_ranks = [c[0] for c in community_cards]
    pairs = 0
    if c1[0] == c2[0]:
        pairs += 1
    if c1[0] in board_ranks:
        pairs += 1
    if c2[0] in board_ranks:
        pairs += 1
    return (pairs >= 2 and not has_three_of_a_kind(c1, c2, community_cards))

def has_three_of_a_kind(c1, c2, community_cards=[]):
    board_ranks = [c[0] for c in community_cards]
    if c1[0] == c2[0]:
        return c1[0] in board_ranks
    return board_ranks.count(c1[0]) >= 2 or board_ranks.count(c2[0]) >= 2

def near_straight(c1, c2, community_cards = []):
    ranks = set([RANK_MAP[c1[0]], RANK_MAP[c2[0]]] + [RANK_MAP[c[0]] for c in community_cards])
    if len(set(ranks)) < 4:
        return False
    for rank in ranks:
        if sum((rank + i) in ranks for i in range(1, 5)) >= 3:
            return True
    if 14 in ranks and sum(i in ranks for i in range(2, 5)) >= 3:
        return True
    return False
    

def near_flush(c1, c2, community_cards = []):
    if (c1[1]!=c2[1]):
        return False
    matching = 2
    for card in community_cards:
        if (card[1] == c1[1]):
            matching += 1
    return matching >= 4
    
def is_straight(c1, c2, community_cards = []):
    ranks = set([RANK_MAP[c1[0]], RANK_MAP[c2[0]]] + [RANK_MAP[c[0]] for c in community_cards])
    if len(set(ranks)) < 5:
        return False
    for rank in ranks:
        if all((rank + i) in ranks for i in range(1, 5)):
            return True
    if 14 in ranks and all(i in ranks for i in range(2, 5)):
        return True
    return False


def is_flush(c1, c2, community_cards=[]):
    all_suits = [c1[1], c2[1]] + [c[1] for c in community_cards]
    flush = any(all_suits.count(s) >= 5 for s in {c1[1], c2[1]})
    if flush and is_straight(c1, c2, community_cards=community_cards) and ('K' in [c1[0], c2[0]] + [c[0] for c in community_cards]):
        print("Royal Flush! - ", c1, c2, community_cards)
    return flush


def how_good_hand(c1, c2, community_cards = []):
    if(has_three_of_a_kind(c1, c2, community_cards) or is_straight(c1, c2, community_cards) or is_flush(c1, c2, community_cards) or has_two_pair(c1, c2, community_cards)):
        return "really good"
    elif(has_one_pair(c1, c2, community_cards) or near_straight(c1, c2, community_cards) or near_flush(c1, c2, community_cards)):
        return "good"
    else:
        return "average"

def decide(state, money_ratio_to_all_in = 0.8, ratio_of_all_in = 0.5):
    street  = state["street"]
    owed    = state["amount_owed"]
    pot     = state["pot"]
    stack   = state["your_stack"]
    hand    = state["your_cards"]
    seat    = state["seat_to_act"]
    bet_this_street = state["your_bet_this_street"]
    min_bet = state["min_raise_to"]
    total_bet_this_hand = owed + bet_this_street
    n       = len(state["players"])
    players = state["players"]
    player_stacks = [p["stack"] for p in players]
    an_opponent = list(state["players"].values())[0]
    all_in_occured = any(a["action"] == "all_in" and a["bot_id"] == state["your_bot_id"] for a in state["action_log"])
    


    if (any(a["action"] == "all_in" and a["bot_id"] == an_opponent for a in state["action_log"])):
         opponent_all_ins += 1

    # if (hand == 100) and (opponent_all_ins > 15):

    if street == "preflop":

        if stack < 500:
             return {"action": "all_in"}

        if not state["can_check"]:
            if hand_rank(hand[0], hand[1]) > 3:
                if total_bet_this_hand > stack * max(percent_stack_before_fold - hand_rank(hand[0], hand[1]) * .1, .05):
                    return {"action": "fold"}
                else:
                    return {"action": "call"}


        if hand_rank(hand[0], hand[1]) <= 3:
            if(any(stack > player_stack * money_ratio_to_all_in for player_stack in [p["stack"] for p in players if p["seat"] != seat])):
                return {"action": "raise", "amount": max(player_stacks)*ratio_of_all_in}
            else:
                return {"action": "raise", "amount": stack * all_in_ratio_when_exess}

        elif hand_rank(hand[0], hand[1]) <= 6:
            return {"action": "raise", "amount": max(player_stacks) * random.uniform(*four_six_score_bet_range)}
        else:
            if min_bet < stack * .1:
                return {"action": "raise", "amount": min_bet}

        if state["can_check"]:
            return {"action": "check"}
        else:
            return {"action": "fold"}


    elif street == "flop":
        hand_good = how_good_hand(hand[0], hand[1], state["community_cards"]) 

        if hand_good == "really good":
                return {"action": "raise", "amount": stack * random.choice(all_in_amount)}
        
        if state["can_check"]:
            if hand_good == "good":
                return {"action": "raise", "amount": max(player_stacks) * random.uniform(*four_six_score_bet_range)}
            elif seven_two(hand[0], hand[1]):
                return {"action": "raise", "amount": max(player_stacks) * russian_roulette[0]}
            else:
                return {"action": "check"}
            
        elif not state['can_check']:
            if total_bet_this_hand < stack * amount_to_call_threshold and hand_good == "good" or all_in_occured: # can tweak this
                return {"action": "call"}
        
        return {"action": "fold"}

    elif street == "turn":
        hand_good = how_good_hand(hand[0], hand[1], state["community_cards"]) 
        if hand_good == "really good":
                return {"action": "raise", "amount": stack * random.choice(all_in_amount)}
        
        if state["can_check"]:
                if hand_good == "good":
                                return {"action": "raise", "amount": max(player_stacks) * random.uniform(*four_six_score_bet_range)}
                elif seven_two(hand[0], hand[1]):
                                return {"action": "raise", "amount": max(player_stacks) * russian_roulette[1]}
                return {"action": "check"}
        
        elif not state['can_check']:
                if total_bet_this_hand < stack * amount_to_call_threshold and hand_good == "good" or all_in_occured: # can tweak this
                    return {"action": "call"}

        return {"action": "fold"}


    elif street == "river":
        hand_good = how_good_hand(hand[0], hand[1], state["community_cards"]) 
        if hand_good == "really good":
                return {"action": "raise", "amount": stack * random.choice(all_in_amount)}

        if state["can_check"]:
                        if hand_good == "good":
                                        return {"action": "raise", "amount": max(player_stacks) * random.uniform(*four_six_score_bet_range)}
                        elif seven_two(hand[0], hand[1]):
                                        return {"action": "raise", "amount": max(player_stacks) * russian_roulette[1]}
                        return {"action": "check"}
        
        elif not state['can_check']:
                if total_bet_this_hand < stack * amount_to_call_threshold and hand_good == "good" or all_in_occured: # can tweak this currently .2
                    return {"action": "call"}
                else:
                    return {"action": "fold"}

        return {"action": "check"}

    elif street == "showdown":
        all_in_occured = False

        if not state['can_check']:
                if total_bet_this_hand < stack * amount_to_call_threshold and hand_good == "good" or all_in_occured: # can tweak this currnetly .2
                    return {"action": "call"}
                else:
                    return {"action": "fold"}
                
        return {"action": "check"}

    