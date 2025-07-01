import poke_battle_sim as pb

pikachu = pb.Pokemon(...)
ash = pb.Trainer("Ash", [pikachu])

starmie = pb.Pokemon(...)
misty = pb.Trainer("Misty", [starmie])

battle = pb.Battle(ash, misty)
battle.start()
battle.turn()

print(battle.get_all_text())
