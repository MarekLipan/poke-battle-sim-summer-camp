import poke_battle_sim as pb

# Fair simulation: only species and level provided, average IVs, no EVs, neutral nature
NUM_SIMULATIONS = 100
pikachu_wins = 0
starmie_wins = 0


def simulate_battle(
    poke_a_id="Pikachu",
    poke_b_id="Starmie",
    poke_a_moves=None,
    poke_b_moves=None,
    poke_a_gender="male",
    poke_b_gender="genderless",
    poke_a_level=10,
    poke_b_level=10,
    verbose=False,
):
    if poke_a_moves is None:
        poke_a_moves = ["thunderbolt"]
    if poke_b_moves is None:
        poke_b_moves = ["water-gun"]
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
    poke_a.cur_hp *= 10

    poke_b = pb.Pokemon(
        poke_b_id,
        poke_b_level,
        poke_b_moves,
        poke_b_gender,
        ivs=[15, 15, 15, 15, 15, 15],
        evs=[0, 0, 0, 0, 0, 0],
        nature="hardy",
    )
    poke_b.cur_hp *= 10
    trainer_a = pb.Trainer("A", [poke_a])
    trainer_b = pb.Trainer("B", [poke_b])
    battle = pb.Battle(trainer_a, trainer_b)
    battle.start()
    if verbose:
        print(f"{poke_a_id} (Lv {poke_a_level}) HP: {poke_a.stats_actual[0]}")
        print(f"{poke_b_id} (Lv {poke_b_level}) HP: {poke_b.stats_actual[0]}")
        print("--- Battle Start ---")
        print(
            f"Turn 0: {poke_a_id} HP: {poke_a.cur_hp}, {poke_b_id} HP: {poke_b.cur_hp}"
        )
    turn_num = 1
    while not battle.is_finished():
        t1_action = ["move", poke_a_moves[0]]
        t2_action = ["move", poke_b_moves[0]]
        battle.turn(t1_action, t2_action)
        if verbose:
            print(
                f"Turn {turn_num}: {poke_a_id} HP: {poke_a.cur_hp}, {poke_b_id} HP: {poke_b.cur_hp}"
            )
            for line in battle.get_cur_text():
                print(line)
        turn_num += 1
    if verbose:
        print("--- Battle End ---")
        print(
            f"Final: {poke_a_id} HP: {poke_a.cur_hp}, {poke_b_id} HP: {poke_b.cur_hp}"
        )
    if trainer_a.current_poke.is_alive:
        return (poke_a_id, poke_a.cur_hp)
    else:
        return (poke_b_id, poke_b.cur_hp)


def run_many_battles(
    num_simulations=100,
    poke_a_id="Pikachu",
    poke_b_id="Starmie",
    poke_a_moves=None,
    poke_b_moves=None,
    poke_a_gender="genderless",
    poke_b_gender="genderless",
    poke_a_level=10,
    poke_b_level=10,
):
    if poke_a_moves is None:
        poke_a_moves = ["thunderbolt"]
    if poke_b_moves is None:
        poke_b_moves = ["water-gun"]
    a_win_hp = []
    b_win_hp = []
    for _ in range(num_simulations):
        result = simulate_battle(
            poke_a_id=poke_a_id,
            poke_b_id=poke_b_id,
            poke_a_moves=poke_a_moves,
            poke_b_moves=poke_b_moves,
            poke_a_gender=poke_a_gender,
            poke_b_gender=poke_b_gender,
            poke_a_level=poke_a_level,
            poke_b_level=poke_b_level,
            verbose=False,
        )
        if result[0] == poke_a_id:
            a_win_hp.append(result[1])
        else:
            b_win_hp.append(result[1])
    if len(a_win_hp) >= len(b_win_hp):
        avg = round(sum(a_win_hp) / len(a_win_hp)) if a_win_hp else 0
        print(f"{poke_a_id} is the most frequent winner. Avg HP left: {avg}")
    else:
        avg = round(sum(b_win_hp) / len(b_win_hp)) if b_win_hp else 0
        print(f"{poke_b_id} is the most frequent winner. Avg HP left: {avg}")


# Run many simulations and print average result
run_many_battles(
    num_simulations=1000,
    poke_a_id="Charmander",
    poke_b_id="Charizard",
    poke_a_moves=["flamethrower"],
    poke_b_moves=["flamethrower"],
    poke_a_gender="genderless",
    poke_b_gender="genderless",
    poke_a_level=30,
    poke_b_level=15,
)
