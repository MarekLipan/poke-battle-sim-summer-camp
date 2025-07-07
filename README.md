# Pokémon Team Battle Simulator (Summer Camp Edition)

This application is a visually-rich Pokémon team battle simulator designed for summer camp tournaments. It allows four groups (trainers) to compete in a round-robin format, with each team fielding a roster of classic Pokémon. The simulator features a modern, accessible GUI, deterministic battle logic, and supports both English and Czech.

## Features

- **Team & Pokémon Configuration:**
  - Teams and Pokémon are defined in external JSON files for easy customization.
  - Each Pokémon has a type, level, evolution stage, and signature move.
  - Only Pokémon with level > 0 are available for battle.

- **Battle Engine:**
  - Deterministic outcome based on type, level, HP, and evolution stage.
  - Type effectiveness and evolution stage have a strong influence on results.
  - If both Pokémon would faint, one is randomly chosen to survive with 1 HP (no ties).

- **GUI Highlights:**
  - All trainers and teams are displayed with color theming and scores.
  - Large, visually consistent Pokémon icons with trainer-colored borders and white padding.
  - HP bars animate smoothly and change color based on health.
  - Fainted Pokémon are shown with a red cross overlay.
  - Stylish vertical separators between teams.
  - All user-facing text is available in Czech.
  - Trainers select their starting Pokémon at the beginning of each battle.
  - Winner popup after each battle.

- **Tournament Mode:**
  - Round-robin tournament between all teams.
  - Scores are tracked and displayed live.
  - Each battle is a single deterministic simulation.

## Data Files

- `teams_config.json`: Defines trainers, their team colors, and Pokémon rosters.
- `pokemon_stages.json`: Evolution lines, images, moves, and types for each Pokémon.
- `type_effectiveness.csv`: Type matchup chart.
- `images/`: Local images for all Pokémon.

## Pokémon Roster

| Pokémon   | Type(s)        | Signature Move | Evolves Into          |
|-----------|----------------|----------------|-----------------------|
| Charmander| Fire           | flamethrower   | Charmeleon/Charizard  |
| Squirtle  | Water          | hydro-pump     | Wartortle/Blastoise   |
| Bulbasaur | Grass/Poison   | solar-beam     | Ivysaur/Venusaur      |
| Pikachu   | Electric       | thunderbolt    | Raichu                |
| Abra      | Psychic        | psychic        | Kadabra/Alakazam      |
| Machop    | Fighting       | cross-chop     | Machoke/Machamp       |
| Geodude   | Rock/Ground    | earthquake     | Graveler/Golem        |
| Gastly    | Ghost/Poison   | shadow-ball    | Haunter/Gengar        |

## Type Effectiveness

Type matchups are based on the classic Pokémon chart. For example:
- Fire is strong against Grass, weak against Water and Rock.
- Electric is strong against Water and Flying, but does nothing to Ground.
- Psychic is strong against Fighting and Poison.

## How to Run

1. Install requirements (see `pyproject.toml`).
2. Run the main GUI:
   ```sh
   python main/pokemon_gui.py
   ```
3. Select starting Pokémon for each trainer and proceed through the tournament!

## Customization
- Edit `teams_config.json` to change trainers, team colors, or Pokémon rosters.
- Add or update Pokémon images in the `images/` folder.
- Adjust type matchups in `type_effectiveness.csv` if needed.

## Credits
- Pokémon images and names © Nintendo/Game Freak.

---
Enjoy your Pokémon tournament!