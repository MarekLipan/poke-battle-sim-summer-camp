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
            self.max_hp = 100 * 10  # Arbitrary default, can be adjusted
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
        # Use simulate_battle from battle_simulator
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
            hp_boost=1,  # Already boosted in wrapper
            verbose=False,
        )
        # Update HPs based on result
        if result["winner"] == "A":
            t1.cur_hp = result["winner_hp"]
            t2.cur_hp = 0
        else:
            t1.cur_hp = 0
            t2.cur_hp = result["winner_hp"]
        self.battle_log.extend(result["battle_log"])
        self.battle_log.append(
            f"Battle result: {t1.name} HP: {t1.cur_hp}, {t2.name} HP: {t2.cur_hp}"
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
                # Green
                return "QProgressBar::chunk {background-color: #4caf50;}"
            elif ratio > 0.2:
                # Yellow/Orange
                return "QProgressBar::chunk {background-color: #ffb300;}"
            else:
                # Red
                return "QProgressBar::chunk {background-color: #e53935;}"

        self.poke1_hp.setStyleSheet(hp_color(poke1.cur_hp, poke1.max_hp))
        self.poke2_hp.setStyleSheet(hp_color(poke2.cur_hp, poke2.max_hp))

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    manager = TeamBattleManager()
    window = MainWindow(manager)
    window.show()
    sys.exit(app.exec_())
