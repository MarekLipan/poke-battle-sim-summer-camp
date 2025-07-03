import poke_battle_sim as pb
import csv
import os

# --- Load type effectiveness chart from CSV ---
TYPE_EFFECTIVENESS = {}
type_chart_path = os.path.join(os.path.dirname(__file__), "type_effectiveness.csv")
with open(type_chart_path, newline="", encoding="utf-8") as csvfile:
    reader = csv.reader(csvfile)
    header = next(reader)[1:]  # skip first empty cell
    for row in reader:
        atk_type = row[0].lower()
        TYPE_EFFECTIVENESS[atk_type] = {
            def_type.lower(): float(mult) for def_type, mult in zip(header, row[1:])
        }


def simulate_battle(
    poke_a_id,
    poke_b_id,
    poke_a_moves,
    poke_b_moves,
    poke_a_gender,
    poke_b_gender,
    poke_a_level,
    poke_b_level,
    poke_a_cur_hp,
    poke_b_cur_hp,
    hp_boost=10,
    verbose=False,
):
    # Create Pokémon with calculated stats, then boost only HP
    poke_a = pb.Pokemon(
        poke_a_id,
        poke_a_level,
        poke_a_moves,
        poke_a_gender,
        ivs=[15, 15, 15, 15, 15, 15],
        evs=[0, 0, 0, 0, 0, 0],
        nature="hardy",
    )
    poke_a.cur_hp = poke_a.max_hp * hp_boost if poke_a_cur_hp is None else poke_a_cur_hp
    poke_a.max_hp = poke_a.max_hp * hp_boost

    poke_b = pb.Pokemon(
        poke_b_id,
        poke_b_level,
        poke_b_moves,
        poke_b_gender,
        ivs=[15, 15, 15, 15, 15, 15],
        evs=[0, 0, 0, 0, 0, 0],
        nature="hardy",
    )
    poke_b.cur_hp = poke_b.max_hp * hp_boost if poke_b_cur_hp is None else poke_b_cur_hp
    poke_b.max_hp = poke_b.max_hp * hp_boost

    trainer_a = pb.Trainer("A", [poke_a])
    trainer_b = pb.Trainer("B", [poke_b])
    battle = pb.Battle(trainer_a, trainer_b)
    battle.start()
    turn_num = 1
    battle_log = []
    if verbose:
        battle_log.append(f"{poke_a_id} (Lv {poke_a_level}) HP: {poke_a.max_hp}")
        battle_log.append(f"{poke_b_id} (Lv {poke_b_level}) HP: {poke_b.max_hp}")
        battle_log.append("--- Battle Start ---")
        battle_log.append(
            f"Turn 0: {poke_a_id} HP: {poke_a.cur_hp}, {poke_b_id} HP: {poke_b.cur_hp}"
        )
    while not battle.is_finished():
        t1_action = ["move", poke_a_moves[0]]
        t2_action = ["move", poke_b_moves[0]]
        battle.turn(t1_action, t2_action)
        if verbose:
            battle_log.append(
                f"Turn {turn_num}: {poke_a_id} HP: {poke_a.cur_hp}, {poke_b_id} HP: {poke_b.cur_hp}"
            )
            for line in battle.get_cur_text():
                battle_log.append(line)
        turn_num += 1
    if verbose:
        battle_log.append("--- Battle End ---")
        battle_log.append(
            f"Final: {poke_a_id} HP: {poke_a.cur_hp}, {poke_b_id} HP: {poke_b.cur_hp}"
        )
    # Determine winner and HP left
    if poke_a.cur_hp <= 0 and poke_b.cur_hp <= 0:
        # Both fainted: randomly pick one to survive with 1 HP
        import random

        if random.choice([True, False]):
            poke_a.cur_hp = 1
            poke_b.cur_hp = 0
            winner = "A"
            winner_name = poke_a_id
            winner_hp = 1
            loser_name = poke_b_id
            loser_hp = 0
        else:
            poke_a.cur_hp = 0
            poke_b.cur_hp = 1
            winner = "B"
            winner_name = poke_b_id
            winner_hp = 1
            loser_name = poke_a_id
            loser_hp = 0
    elif poke_a.cur_hp > 0 and poke_b.cur_hp <= 0:
        winner = "A"
        winner_name = poke_a_id
        winner_hp = poke_a.cur_hp
        loser_name = poke_b_id
        loser_hp = poke_b.cur_hp
    elif poke_b.cur_hp > 0 and poke_a.cur_hp <= 0:
        winner = "B"
        winner_name = poke_b_id
        winner_hp = poke_b.cur_hp
        loser_name = poke_a_id
        loser_hp = poke_a.cur_hp
    else:
        # Both are alive (should not happen, but fallback)
        winner = "A"
        winner_name = poke_a_id
        winner_hp = poke_a.cur_hp
        loser_name = poke_b_id
        loser_hp = poke_b.cur_hp
    return {
        "winner": winner,
        "winner_name": winner_name,
        "winner_hp": winner_hp,
        "loser_name": loser_name,
        "loser_hp": loser_hp,
        "battle_log": battle_log,
    }


def deterministic_battle(
    poke_a_id,
    poke_b_id,
    poke_a_moves,
    poke_b_moves,
    poke_a_gender,
    poke_b_gender,
    poke_a_level,
    poke_b_level,
    poke_a_cur_hp,
    poke_b_cur_hp,
    poke_a_type=None,
    poke_b_type=None,
    poke_a_stage=1,
    poke_b_stage=1,
    verbose=False,
):
    """
    Deterministic battle simulation based on level, HP, type, and evolution stage.
    poke_a_type and poke_b_type should be a string (e.g., 'Fire') or a list of types.
    poke_a_stage and poke_b_stage: 1=base, 2=stage1, 3=stage2, etc.
    """

    def get_type_multiplier(attacker, defender):
        # attacker, defender: string or list of strings (types)
        if not attacker or not defender:
            return 1.0
        if isinstance(attacker, str):
            attacker = [attacker]
        if isinstance(defender, str):
            defender = [defender]
        # For each attacker's type, calculate the best multiplier against all defender's types
        best = 1.0
        for atk in attacker:
            atk = atk.lower()
            mult = 1.0
            for dft in defender:
                dft = dft.lower()
                mult *= TYPE_EFFECTIVENESS.get(atk, {}).get(dft, 1.0)
            if mult > best:
                best = mult
        return best

    # Calculate scores
    a_type_mult = get_type_multiplier(poke_a_type, poke_b_type)
    b_type_mult = get_type_multiplier(poke_b_type, poke_a_type)
    # Make type advantage more pronounced by increasing its weight
    TYPE_WEIGHT = 60  # was 20
    STAGE_WEIGHT = 14  # was 10, slightly boost evolution effect
    a_score = (
        poke_a_level * 2 + poke_a_cur_hp * 1.5 + a_type_mult * TYPE_WEIGHT + poke_a_stage * STAGE_WEIGHT
    )
    b_score = (
        poke_b_level * 2 + poke_b_cur_hp * 1.5 + b_type_mult * TYPE_WEIGHT + poke_b_stage * STAGE_WEIGHT
    )
    battle_log = []
    if verbose:
        battle_log.append(
            f"{poke_a_id} (Lv {poke_a_level}, HP {poke_a_cur_hp}, Type {poke_a_type}, Stage {poke_a_stage}) vs {poke_b_id} (Lv {poke_b_level}, HP {poke_b_cur_hp}, Type {poke_b_type}, Stage {poke_b_stage})"
        )
        battle_log.append(f"A score: {a_score:.1f}, B score: {b_score:.1f}")
    if a_score > b_score:
        winner = "A"
        winner_name = poke_a_id
        loser_name = poke_b_id
        # Remaining HP: proportional to margin
        margin = a_score - b_score
        winner_hp = int(min(poke_a_cur_hp, margin * 0.7))
        loser_hp = 0
        if verbose:
            battle_log.append(f"Winner: {poke_a_id} (A) with {winner_hp} HP left.")
    else:
        winner = "B"
        winner_name = poke_b_id
        loser_name = poke_a_id
        margin = b_score - a_score
        winner_hp = int(min(poke_b_cur_hp, margin * 0.7))
        loser_hp = 0
        if verbose:
            battle_log.append(f"Winner: {poke_b_id} (B) with {winner_hp} HP left.")
    return {
        "winner": winner,
        "winner_name": winner_name,
        "winner_hp": winner_hp,
        "loser_name": loser_name,
        "loser_hp": loser_hp,
        "battle_log": battle_log,
    }
