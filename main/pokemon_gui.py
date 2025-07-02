from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QListWidget,
    QTextEdit,
    QProgressBar,
    QDialog,
    QGridLayout,
    QGraphicsOpacityEffect,
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
import sys
import os
import json
import poke_battle_sim as pb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import battle_simulator

# --- Load team config from JSON ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "teams_config.json")
STAGES_PATH = os.path.join(os.path.dirname(__file__), "pokemon_stages.json")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    TEAMS_CONFIG = json.load(f)
with open(STAGES_PATH, "r", encoding="utf-8") as f:
    POKEMON_STAGES = json.load(f)

TEAM_SIZE = len(TEAMS_CONFIG[0]["pokemon"])
NUM_TEAMS = len(TEAMS_CONFIG)

HP_BOOST = 10  # Set the HP boost factor here


class PokemonWrapper:
    def __init__(self, poke_dict):
        agg_name = poke_dict["name"]
        stage = str(poke_dict["stage"])
        level = poke_dict.get("level", 0)
        if level > 0:
            stage_info = POKEMON_STAGES[agg_name][stage]
            self.name = stage_info["name"]
            self.move = stage_info["move"]
            self.img = (
                os.path.join(os.path.dirname(__file__), stage_info["img"])
                if not os.path.isabs(stage_info["img"])
                else stage_info["img"]
            )
            self.gender = stage_info.get("gender", "male")
            self.level = level
            poke = pb.Pokemon(
                self.name,
                self.level,
                [self.move],
                self.gender,
                ivs=[15, 15, 15, 15, 15, 15],
                evs=[0, 0, 0, 0, 0, 0],
                nature="hardy",
            )
            self.max_hp = poke.max_hp * HP_BOOST
            self.cur_hp = self.max_hp
        else:
            self.max_hp = 0
            self.cur_hp = 0
            self.name = agg_name
            self.move = None
            self.img = None
            self.gender = None
            self.level = 0

    def is_alive(self):
        return self.level > 0 and self.cur_hp > 0

    def fresh_pokemon(self):
        # No longer needed, kept for compatibility
        return None


class TrainerTeam:
    def __init__(self, name, pokemon_wrappers):
        # Only include Pokémon with level > 0
        self.name = name
        self.pokemon_wrappers = [pw for pw in pokemon_wrappers if pw.level > 0]
        if self.pokemon_wrappers:
            self.active_idx = 0
        else:
            self.active_idx = None

    def get_active(self):
        if self.active_idx is None:
            return None
        return self.pokemon_wrappers[self.active_idx]

    def has_alive(self):
        return any(pw.is_alive() for pw in self.pokemon_wrappers)

    def next_alive_idx(self):
        for i, pw in enumerate(self.pokemon_wrappers):
            if pw.is_alive():
                return i
        return None


class TeamBattleManager:
    def __init__(self):
        self.teams = []
        for team_conf in TEAMS_CONFIG:
            team_pokes = [PokemonWrapper(poke) for poke in team_conf["pokemon"]]
            self.teams.append(TrainerTeam(team_conf["trainer"], team_pokes))
        self.scores = [0] * NUM_TEAMS
        self.battle_log = []
        self.reset_battle()

    def reset_battle(self):
        self.team_a_idx = 0
        self.team_b_idx = 1
        self.team_a = self.teams[self.team_a_idx]
        self.team_b = self.teams[self.team_b_idx]
        self.team_a.active_idx = self.team_a.next_alive_idx()
        self.team_b.active_idx = self.team_b.next_alive_idx()
        if self.team_a.get_active() is None or self.team_b.get_active() is None:
            raise ValueError(
                "Both teams must have at least one Pokémon with level > 0."
            )
        self.start_new_battle()

    def start_new_battle(self):
        poke_a = self.team_a.get_active()
        poke_b = self.team_b.get_active()
        self.battle_log.append(f"Battle: {poke_a.name} vs {poke_b.name}")
        self.battle_log.append(
            f"Starting HP: {poke_a.name}: {poke_a.cur_hp} HP, {poke_b.name}: {poke_b.cur_hp} HP"
        )

    def get_current_battlers(self):
        return self.team_a.get_active(), self.team_b.get_active()

    def get_battle_log(self):
        return "\n".join(self.battle_log[-20:])

    def do_battle_turn(self):
        t1 = self.team_a.get_active()
        t2 = self.team_b.get_active()
        # Simulate the battle multiple times and average the winner's HP
        NUM_SIMULATIONS = 100
        win_hp = []
        winner = None
        for _ in range(NUM_SIMULATIONS):
            result = battle_simulator.simulate_battle(
                poke_a_id=t1.name,
                poke_b_id=t2.name,
                poke_a_moves=[t1.move],
                poke_b_moves=[t2.move],
                poke_a_gender=t1.gender,
                poke_b_gender=t2.gender,
                poke_a_level=t1.level,
                poke_b_level=t2.level,
                poke_a_cur_hp=t1.cur_hp,
                poke_b_cur_hp=t2.cur_hp,
                hp_boost=HP_BOOST,
                verbose=False,
            )
            win_hp.append((result["winner"], result["winner_hp"]))
        # Determine most frequent winner
        from collections import Counter

        win_counts = Counter(w for w, _ in win_hp)
        if win_counts["A"] >= win_counts["B"]:
            winner = "A"
        else:
            winner = "B"
        avg_hp = (
            int(round(sum(hp for w, hp in win_hp if w == winner) / win_counts[winner]))
            if win_counts[winner]
            else 0
        )
        # Update HPs based on average result
        if winner == "A":
            t1.cur_hp = avg_hp
            t2.cur_hp = 0
        else:
            t1.cur_hp = 0
            t2.cur_hp = avg_hp
        self.battle_log.append(
            f"Simulated {NUM_SIMULATIONS} battles. Winner: {'A' if winner == 'A' else 'B'} (avg HP: {avg_hp})"
        )

    def is_battle_over(self):
        # This needs to be re-evaluated based on the local battle
        # For now, we can say a battle is over after one turn (one full simulation)
        return True

    def handle_faint(self, team_idx, new_idx):
        if team_idx == 0:
            self.team_a.active_idx = new_idx
        else:
            self.team_b.active_idx = new_idx
        self.start_new_battle()

    def get_team_status(self, team):
        return [
            f"{pw.name}{' (Fainted)' if not pw.is_alive() else ''}"
            for pw in team.pokemon_wrappers
        ]


class MainWindow(QMainWindow):
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.setWindowTitle("Pokémon Team Battle Visualizer")
        self.init_ui()
        self.update_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        team_layout = QHBoxLayout()
        log_layout = QVBoxLayout()

        # Restore original background color (remove forced white)
        self.setStyleSheet("")
        button_style = (
            "QPushButton { background-color: #1976d2; color: white; font-weight: bold; border-radius: 6px; padding: 6px 16px; }"
            "QPushButton:disabled { background-color: #cccccc; color: #888888; }"
        )

        # Battle area
        battle_area_layout = QHBoxLayout()

        poke1_layout = QVBoxLayout()
        self.trainer1_name = QLabel()
        self.trainer1_name.setAlignment(Qt.AlignCenter)
        self.poke1_info = QLabel()
        self.poke1_info.setAlignment(Qt.AlignCenter)
        self.poke1_img = QLabel()
        self.poke1_img.setAlignment(Qt.AlignCenter)
        self.poke1_hp = QProgressBar()
        self.poke1_hp.setMaximum(100)
        self.poke1_hp.setTextVisible(True)
        self.poke1_hp.setFixedWidth(120)  # Make HP bar shorter
        poke1_layout.addWidget(self.trainer1_name)
        poke1_layout.addWidget(self.poke1_info)
        poke1_layout.addWidget(self.poke1_img, alignment=Qt.AlignCenter)
        poke1_layout.addWidget(self.poke1_hp, alignment=Qt.AlignCenter)

        poke2_layout = QVBoxLayout()
        self.trainer2_name = QLabel()
        self.trainer2_name.setAlignment(Qt.AlignCenter)
        self.poke2_info = QLabel()
        self.poke2_info.setAlignment(Qt.AlignCenter)
        self.poke2_img = QLabel()
        self.poke2_img.setAlignment(Qt.AlignCenter)
        self.poke2_hp = QProgressBar()
        self.poke2_hp.setMaximum(100)
        self.poke2_hp.setTextVisible(True)
        self.poke2_hp.setFixedWidth(120)  # Make HP bar shorter
        poke2_layout.addWidget(self.trainer2_name)
        poke2_layout.addWidget(self.poke2_info)
        poke2_layout.addWidget(self.poke2_img, alignment=Qt.AlignCenter)
        poke2_layout.addWidget(self.poke2_hp, alignment=Qt.AlignCenter)

        battle_area_layout.addLayout(poke1_layout)
        battle_area_layout.addWidget(QLabel("VS"))
        battle_area_layout.addLayout(poke2_layout)

        # Team rosters
        self.team_layouts = []
        self.team_containers = []
        for i in range(NUM_TEAMS):
            team_container = QWidget()
            team_v_layout = QVBoxLayout()
            team_container.setLayout(team_v_layout)

            trainer_name = QLabel()
            trainer_name.setAlignment(Qt.AlignCenter)
            team_v_layout.addWidget(trainer_name)

            roster_grid_widget = QWidget()
            roster_grid_layout = QGridLayout()
            roster_grid_widget.setLayout(roster_grid_layout)
            team_v_layout.addWidget(roster_grid_widget)

            team_layout.addWidget(team_container)
            self.team_layouts.append({"name": trainer_name, "grid": roster_grid_layout})
            self.team_containers.append(team_container)

        # Battle log
        self.battle_log = QTextEdit()
        self.battle_log.setReadOnly(True)
        log_layout.addWidget(self.battle_log)

        # Substitution buttons
        self.sub_buttons = []
        for i in range(2):
            btn = QPushButton(f"Substitute for Trainer {i+1}")
            btn.setStyleSheet(button_style)
            btn.clicked.connect(lambda _, idx=i: self.prompt_substitute(idx))
            self.sub_buttons.append(btn)
            log_layout.addWidget(btn)

        # Next turn button
        self.next_turn_btn = QPushButton("Battle")
        self.next_turn_btn.setStyleSheet(button_style)
        self.next_turn_btn.clicked.connect(self.next_turn)
        log_layout.addWidget(self.next_turn_btn)

        # Main layout
        main_layout.addLayout(battle_area_layout)
        main_layout.addLayout(team_layout)
        main_layout.addLayout(log_layout)

        central = QWidget()
        central.setLayout(main_layout)
        self.setCentralWidget(central)

    def update_ui(self):
        poke1, poke2 = self.manager.get_current_battlers()
        self.trainer1_name.setText(self.manager.team_a.name)
        self.trainer2_name.setText(self.manager.team_b.name)
        self.poke1_info.setText(f"Lv. {poke1.level} {poke1.name}")
        self.poke2_info.setText(f"Lv. {poke2.level} {poke2.name}")
        self.poke1_img.setPixmap(
            QPixmap(poke1.img).scaled(120, 120, Qt.KeepAspectRatio)
        )
        self.poke2_img.setPixmap(
            QPixmap(poke2.img).scaled(120, 120, Qt.KeepAspectRatio)
        )
        self.poke1_hp.setMaximum(poke1.max_hp)
        self.poke2_hp.setMaximum(poke2.max_hp)
        self.poke1_hp.setValue(poke1.cur_hp)
        self.poke2_hp.setValue(poke2.cur_hp)
        self.poke1_hp.setFormat(f"{poke1.cur_hp}/{poke1.max_hp} HP")
        self.poke2_hp.setFormat(f"{poke2.cur_hp}/{poke2.max_hp} HP")

        # Set health bar color (classic thresholds)
        def hp_color(cur, max_):
            ratio = cur / max_ if max_ else 0
            if ratio > 0.5:
                return "QProgressBar::chunk {background-color: #4caf50;}"
            elif ratio > 0.2:
                return "QProgressBar::chunk {background-color: #ffb300;}"
            else:
                return "QProgressBar::chunk {background-color: #e53935;}"

        self.poke1_hp.setStyleSheet(hp_color(poke1.cur_hp, poke1.max_hp))
        self.poke2_hp.setStyleSheet(hp_color(poke2.cur_hp, poke2.max_hp))

        # Show only the two currently fighting trainers' teams
        for i, container in enumerate(self.team_containers):
            if i == self.manager.team_a_idx or i == self.manager.team_b_idx:
                container.show()
            else:
                container.hide()

        for i, team in enumerate(self.manager.teams):
            # Clear previous widgets from grid
            for j in reversed(range(self.team_layouts[i]["grid"].count())):
                widget_to_remove = self.team_layouts[i]["grid"].itemAt(j).widget()
                widget_to_remove.setParent(None)

            self.team_layouts[i]["name"].setText(team.name)

            row, col = 0, 0
            for pw in team.pokemon_wrappers:
                icon = QLabel()
                pixmap = QPixmap(pw.img).scaled(40, 40, Qt.KeepAspectRatio)
                icon.setPixmap(pixmap)

                name = QLabel(pw.name)
                level = QLabel(f"Lv. {pw.level}")
                level.setAlignment(Qt.AlignCenter)

                poke_widget = QWidget()
                poke_layout = QVBoxLayout()
                poke_widget.setLayout(poke_layout)
                poke_layout.addWidget(icon)
                poke_layout.addWidget(name)
                poke_layout.addWidget(level)

                if not pw.is_alive():
                    opacity_effect = QGraphicsOpacityEffect()
                    opacity_effect.setOpacity(0.3)
                    poke_widget.setGraphicsEffect(opacity_effect)

                self.team_layouts[i]["grid"].addWidget(poke_widget, row, col)
                col += 1
                if col > 3:  # 4 pokemon per row
                    col = 0
                    row += 1

        self.battle_log.setText(self.manager.get_battle_log())

    def next_turn(self):
        self.manager.do_battle_turn()
        self.update_ui()

        # Handle fainted Pokémon
        for idx, team in enumerate([self.manager.team_a, self.manager.team_b]):
            if not team.get_active().is_alive():
                # Prompt for substitution
                self.prompt_substitute(idx)
        self.update_ui()

    def prompt_substitute(self, team_idx):
        team = self.manager.team_a if team_idx == 0 else self.manager.team_b
        alive_pokemon = [
            (i, pw)
            for i, pw in enumerate(team.pokemon_wrappers)
            if pw.is_alive() and i != team.active_idx
        ]
        if not alive_pokemon:
            self.battle_log.append(
                f"No available Pokémon to substitute for {team.name}!"
            )
            # Check for game over
            if (
                not self.manager.team_a.has_alive()
                or not self.manager.team_b.has_alive()
            ):
                winner = (
                    self.manager.team_a.name
                    if self.manager.team_a.has_alive()
                    else self.manager.team_b.name
                )
                self.battle_log.append(f"Game Over! {winner} wins!")
                self.next_turn_btn.setDisabled(True)
            return

        dialog = SubstitutionDialog(team.name, alive_pokemon, self)
        if dialog.exec_() == QDialog.Accepted:
            new_idx = dialog.selected_pokemon_index
            self.manager.handle_faint(team_idx, new_idx)
            self.update_ui()


class SubstitutionDialog(QDialog):
    def __init__(self, trainer_name, alive_pokemon, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{trainer_name}, choose your next Pokémon!")
        self.selected_pokemon_index = -1

        layout = QGridLayout()
        self.setLayout(layout)

        for i, (idx, pw) in enumerate(alive_pokemon):
            icon = QLabel()
            pixmap = QPixmap(pw.img).scaled(60, 60, Qt.KeepAspectRatio)
            icon.setPixmap(pixmap)

            name = QLabel(pw.name)
            level = QLabel(f"Lv. {pw.level}")

            btn = QPushButton("Select")
            btn.clicked.connect(lambda _, index=idx: self.select_pokemon(index))

            layout.addWidget(icon, i, 0)
            layout.addWidget(name, i, 1)
            layout.addWidget(level, i, 2)
            layout.addWidget(btn, i, 3)

    def select_pokemon(self, index):
        self.selected_pokemon_index = index
        self.accept()


class TournamentWindow(QMainWindow):
    def __init__(self, teams_config, pokemon_stages):
        super().__init__()
        self.setWindowTitle("Pokémon Tournament")
        self.teams_config = teams_config
        self.pokemon_stages = pokemon_stages
        self.trainers = [team["trainer"] for team in teams_config]
        self.scores = {trainer: 0 for trainer in self.trainers}
        self.battle_pairs = self._generate_battle_pairs()
        self.current_battle_idx = 0
        self.battle_windows = []
        self.init_ui()
        self.update_ui()

    def _generate_battle_pairs(self):
        pairs = []
        n = len(self.trainers)
        for i in range(n):
            for j in range(i + 1, n):
                pairs.append((i, j))
        return pairs

    def init_ui(self):
        main_layout = QVBoxLayout()
        self.score_labels = []
        score_layout = QHBoxLayout()
        for trainer in self.trainers:
            vbox = QVBoxLayout()
            name_label = QLabel(trainer)
            name_label.setAlignment(Qt.AlignCenter)
            score_label = QLabel("Score: 0")
            score_label.setAlignment(Qt.AlignCenter)
            self.score_labels.append(score_label)
            vbox.addWidget(name_label)
            vbox.addWidget(score_label)
            # Team roster
            team = next(t for t in self.teams_config if t["trainer"] == trainer)
            grid = QGridLayout()
            for idx, poke in enumerate(team["pokemon"]):
                poke_name = self.pokemon_stages[poke["name"]][str(poke["stage"])]
                icon = QLabel()
                pixmap = QPixmap(
                    os.path.join(os.path.dirname(__file__), poke_name["img"])
                )
                icon.setPixmap(pixmap.scaled(40, 40, Qt.KeepAspectRatio))
                poke_label = QLabel(f"Lv.{poke['level']} {poke_name['name']}")
                poke_label.setAlignment(Qt.AlignCenter)
                poke_widget = QVBoxLayout()
                poke_widget.addWidget(icon)
                poke_widget.addWidget(poke_label)
                grid.addLayout(poke_widget, idx // 3, idx % 3)
            vbox.addLayout(grid)
            score_layout.addLayout(vbox)
        main_layout.addLayout(score_layout)
        # Next battle button
        self.next_battle_btn = QPushButton("Start Next Battle")
        self.next_battle_btn.clicked.connect(self.start_next_battle)
        main_layout.addWidget(self.next_battle_btn)
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)
        central = QWidget()
        central.setLayout(main_layout)
        self.setCentralWidget(central)

    def update_ui(self):
        for i, trainer in enumerate(self.trainers):
            self.score_labels[i].setText(f"Score: {self.scores[trainer]}")
        if self.current_battle_idx < len(self.battle_pairs):
            a, b = self.battle_pairs[self.current_battle_idx]
            self.status_label.setText(f"Next: {self.trainers[a]} vs {self.trainers[b]}")
            self.next_battle_btn.setEnabled(True)
        else:
            self.status_label.setText("Tournament finished!")
            self.next_battle_btn.setEnabled(False)

    def start_next_battle(self):
        if self.current_battle_idx >= len(self.battle_pairs):
            return
        a_idx, b_idx = self.battle_pairs[self.current_battle_idx]
        # Create a new TeamBattleManager for this battle
        teams = [self.teams_config[a_idx], self.teams_config[b_idx]]
        # Patch global config for TeamBattleManager
        global TEAMS_CONFIG
        TEAMS_CONFIG = teams
        battle_manager = TeamBattleManager()
        battle_window = MainWindow(battle_manager)
        battle_window.setWindowTitle(
            f"Battle: {self.trainers[a_idx]} vs {self.trainers[b_idx]}"
        )
        battle_window.show()
        self.battle_windows.append(battle_window)

        # Connect to battle end
        def on_battle_end():
            # Determine winner
            team_a_alive = any(
                pw.is_alive() for pw in battle_manager.team_a.pokemon_wrappers
            )
            team_b_alive = any(
                pw.is_alive() for pw in battle_manager.team_b.pokemon_wrappers
            )
            if team_a_alive and not team_b_alive:
                self.scores[self.trainers[a_idx]] += 1
            elif team_b_alive and not team_a_alive:
                self.scores[self.trainers[b_idx]] += 1
            # Close battle window and update
            battle_window.close()
            self.current_battle_idx += 1
            self.update_ui()

        # Patch MainWindow to call on_battle_end when battle is over
        orig_next_turn = battle_window.next_turn

        def patched_next_turn():
            orig_next_turn()
            if (
                not battle_manager.team_a.has_alive()
                or not battle_manager.team_b.has_alive()
            ):
                on_battle_end()

        battle_window.next_turn = patched_next_turn
        battle_window.next_turn_btn.clicked.disconnect()
        battle_window.next_turn_btn.clicked.connect(battle_window.next_turn)
        self.update_ui()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Tournament main window
    window = TournamentWindow(TEAMS_CONFIG, POKEMON_STAGES)
    window.show()
    sys.exit(app.exec_())
