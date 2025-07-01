import poke_battle_sim as pb


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
    if poke_a.is_alive:
        winner = "A"
        winner_name = poke_a_id
        winner_hp = poke_a.cur_hp
        loser_name = poke_b_id
        loser_hp = poke_b.cur_hp
    else:
        winner = "B"
        winner_name = poke_b_id
        winner_hp = poke_b.cur_hp
        loser_name = poke_a_id
        loser_hp = poke_a.cur_hp
    return {
        "winner": winner,
        "winner_name": winner_name,
        "winner_hp": winner_hp,
        "loser_name": loser_name,
        "loser_hp": loser_hp,
        "battle_log": battle_log,
    }
