# poke-battle-sim-summer-camp
App designed for simulating poke battles in between 4 groups at summer camp.

# Pokemon Data
This section contains the data for the Pokémon used in the simulation. Each Pokémon has its type(s), signature move, and evolution details.

### table: pokemon_data
```markdown
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
```

### table: pokemon_type_effectiveness
```markdown
| Pokémon   | Type(s)        | Strong Against (Super Effective) | Weak Against (Vulnerable To) |
|-----------|----------------|----------------------------------|----------------------------------|
| Charmander| Fire           | Bulbasaur, Geodude, Gastly       |
|           |                |                                  | Squirtle, Geodude                |
| Squirtle  | Water          | Charmander, Geodude              | Bulbasaur, Pikachu               |
| Bulbasaur | Grass/Poison   | Squirtle, Geodude              | Charmander, Gastly              |
| Pikachu   | Electric       | Squirtle, (Gyarados if present) | Geodude (immune), Bulbasaur     |
| Abra      | Psychic        | Machop, Gastly                   | Geodude, Gastly (Ghost moves)   |
| Machop    | Fighting       | Geodude, Pikachu                 | Abra, Gastly, Bulbasaur     |
| Geodude   | Rock/Ground    | Charmander, Pikachu              | Squirtle, Bulbasaur, Machop      |
| Gastly    | Ghost/Poison   | Bulbasaur, Abra, Machop          | Geodude, Charmander              |