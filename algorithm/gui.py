# gui.py

import tkinter as tk
from tkinter import ttk
import random
import math

from ga import run_genetic_algorithm
from aco import run_ant_colony

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800


class TSPGUI:
    def __init__(self, root, num_cities=10):
        self.root = root
        self.root.title("TSP Synthwave - GA & ACO")

        self.num_cities = num_cities
        self.cities = []

        # Meilleure solution trouvée
        self.best_distance = float("inf")
        self.best_path = []

        # Animation en cours
        self.current_path = []
        self.current_segment_index = 0
        self.is_animating = False

        # Mode automatique
        self.auto_running = False

        # ==========================================================
        # 1) Configuration du style pour un look plus "moderne"
        # ==========================================================
        style = ttk.Style()
        style.theme_use("clam")
        # Couleur de fond du Frame principal (contrôles)
        style.configure("TFrame", background="#2c2c2c")
        # Label
        style.configure("TLabel", background="#2c2c2c", foreground="white", font=("Helvetica", 11))
        # Boutons
        style.configure("TButton", background="#3a3a3a", foreground="white", font=("Helvetica", 10, "bold"))

        # ---- Canevas principal (fond dégradé)
        self.canvas = tk.Canvas(self.root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT)
        self.canvas.pack(side=tk.LEFT, fill="both", expand=True)

        # Dessin initial du dégradé
        self.draw_canvas_bg_gradient()

        # ---- Cadre de contrôles (à droite)
        self.control_frame = ttk.Frame(self.root, style="TFrame")
        self.control_frame.pack(side=tk.RIGHT, fill="y", padx=10, pady=10)

        # Bouton "Générer Villes"
        self.btn_generate = ttk.Button(
            self.control_frame,
            text="Générer Villes",
            command=self.generate_cities
        )
        self.btn_generate.pack(pady=5, fill="x")

        # Choix d'algorithme
        self.algo_var = tk.StringVar(value="GA")
        ttk.Label(self.control_frame, text="Choisir Algorithme:", style="TLabel").pack(pady=2)
        self.algo_menu = ttk.Combobox(self.control_frame, textvariable=self.algo_var, values=["GA", "ACO", "Hybride"])
        self.algo_menu.pack(pady=5, fill="x")
        self.algo_menu.current(0)

        # Bouton "Lancer" (une fois)
        self.btn_run_once = ttk.Button(
            self.control_frame,
            text="Lancer",
            command=self.run_once
        )
        self.btn_run_once.pack(pady=5, fill="x")

        # Bouton "Automatique"
        self.btn_auto = ttk.Button(
            self.control_frame,
            text="Automatique",
            command=self.start_auto
        )
        self.btn_auto.pack(pady=5, fill="x")

        # Bouton "Stop"
        self.btn_stop = ttk.Button(
            self.control_frame,
            text="Stop",
            command=self.stop_auto
        )
        self.btn_stop.pack(pady=5, fill="x")

        # Label info
        self.info_label = ttk.Label(self.control_frame, text="Meilleure distance: -", style="TLabel")
        self.info_label.pack(pady=10)

        # Générer les villes initiales
        self.generate_cities()

    # =======================================================
    # 1) FOND EN DÉGRADÉ DE GRIS
    # =======================================================
    def draw_canvas_bg_gradient(self):
        """
        Dessine un dégradé vertical du gris foncé au gris moyen
        sur tout le canevas.
        """
        self.canvas.delete("gradient_bg")

        start_color = (0x2D, 0x2D, 0x2D)  # #2d2d2d
        end_color = (0x4D, 0x4D, 0x4D)  # #4d4d4d
        steps = 60

        for i in range(steps):
            f = i / (steps - 1)
            r = int(start_color[0] + f * (end_color[0] - start_color[0]))
            g = int(start_color[1] + f * (end_color[1] - start_color[1]))
            b = int(start_color[2] + f * (end_color[2] - start_color[2]))
            color_hex = f"#{r:02x}{g:02x}{b:02x}"

            y_start = int(WINDOW_HEIGHT * i / steps)
            y_end = int(WINDOW_HEIGHT * (i + 1) / steps)

            self.canvas.create_rectangle(
                0, y_start,
                WINDOW_WIDTH, y_end,
                fill=color_hex,
                outline=color_hex,
                tags="gradient_bg"
            )

    # =======================================================
    # 2) GÉNÉRATION ET AFFICHAGE DES VILLES
    # =======================================================
    def generate_cities(self):
        """Génère des villes aléatoirement et réinitialise la meilleure distance."""
        self.cities.clear()
        self.best_distance = float("inf")
        self.best_path = []
        self.current_path = []
        self.is_animating = False

        self.canvas.delete("all")
        self.draw_canvas_bg_gradient()

        for _ in range(self.num_cities):
            x = random.randint(50, WINDOW_WIDTH - 50)
            y = random.randint(50, WINDOW_HEIGHT - 50)
            self.cities.append((x, y))

        self.draw_cities()
        self.update_info_label("Nouvelles villes générées.")

    def draw_cities(self):
        """Dessine les points (villes) sur le canevas."""
        for i, (x, y) in enumerate(self.cities):
            r = 6
            self.canvas.create_oval(
                x - r, y - r, x + r, y + r,
                fill="#f1f1f1", outline="#888888", width=1
            )
            self.canvas.create_text(
                x, y - 12,
                text=str(i),
                fill="#ffffff",
                font=("Helvetica", 9, "bold")
            )

    # =======================================================
    # 3) CALCUL DE DISTANCE
    # =======================================================
    def compute_distance(self, path):
        """Calcule la distance totale (avec boucle) d'une permutation."""
        if len(path) < 2:
            return 0.0
        dist = 0.0
        for i in range(len(path) - 1):
            x1, y1 = self.cities[path[i]]
            x2, y2 = self.cities[path[i + 1]]
            dist += math.dist((x1, y1), (x2, y2))

        # boucler
        x1, y1 = self.cities[path[-1]]
        x2, y2 = self.cities[path[0]]
        dist += math.dist((x1, y1), (x2, y2))

        return dist

    def update_info_label(self, msg=None):
        """Met à jour l'affichage sur le label info (distance, message)."""
        if self.best_distance < float("inf"):
            dist_txt = f"Meilleure distance: {self.best_distance:.2f}"
        else:
            dist_txt = "Meilleure distance: -"
        if msg:
            self.info_label.config(text=f"{dist_txt}\n{msg}")
        else:
            self.info_label.config(text=dist_txt)

    # =======================================================
    # 4) LANCEMENT DES ALGORITHMES : GA / ACO / Hybride
    # =======================================================
    def run_once(self):
        """
        Lance l'algorithme (GA, ACO ou Hybride) UNE SEULE FOIS,
        compare avec la meilleure solution, et éventuellement anime.
        """
        if not self.cities or self.is_animating:
            # si on est en pleine animation, on évite d'en lancer une autre
            return

        algo = self.algo_var.get()
        if algo == "GA":
            new_path = run_genetic_algorithm(self.cities)
        elif algo == "ACO":
            new_path = run_ant_colony(self.cities)
        else:
            # Hybride = GA puis ACO
            path_ga = run_genetic_algorithm(self.cities)
            new_path = run_ant_colony(self.cities, initial_path=path_ga)

        self.check_and_update_best(new_path, is_auto=False)

    def check_and_update_best(self, path, is_auto=False):
        """
        Compare la solution 'path' avec la meilleure distance.
        Si c'est meilleur, animation; sinon, on trace vite fait en orange.

        is_auto : pour savoir si on est en mode automatique,
                  afin de relancer la prochaine itération à la fin.
        """
        dist = self.compute_distance(path)
        if dist < self.best_distance:
            self.best_distance = dist
            self.best_path = path

            # On redessine le fond + villes
            self.canvas.delete("all")
            self.draw_canvas_bg_gradient()
            self.draw_cities()

            # Animation
            self.current_path = path
            self.current_segment_index = 0
            self.is_animating = True
            self.update_info_label(f"Nouvelle meilleure solution ! (dist={dist:.2f})")

            self.animate_path(is_auto=is_auto)

        else:
            # Chemin non meilleur => on dessine en orange rapidement
            self.draw_quick_path(path, color="#ffa600")
            self.update_info_label(f"Solution non meilleure (dist={dist:.2f})")

            # Si on est en auto => on planifie la suite après 5 secondes
            if is_auto and self.auto_running:
                self.root.after(5000, self.auto_loop)

    # =======================================================
    # 5) ANIMATION « SYNTHWAVE »
    # =======================================================
    def animate_path(self, is_auto=False):
        """
        Dessine progressivement le chemin self.current_path
        (200 ms par segment).
        """
        # Si on a stoppé entre-temps
        if not self.is_animating:
            return

        path = self.current_path
        seg_idx = self.current_segment_index
        n = len(path)

        if seg_idx >= n:
            # on ferme la boucle
            self.draw_synthwave_line(path[-1], path[0], seg_idx)
            self.is_animating = False
            self.update_info_label("Animation terminée.")

            # Si on est en mode auto => on attend 5 secondes puis on relance
            if is_auto and self.auto_running:
                self.root.after(5000, self.auto_loop)

            return

        # On dessine le segment
        if seg_idx > 0:
            self.draw_synthwave_line(path[seg_idx - 1], path[seg_idx], seg_idx - 1)

        self.current_segment_index += 1

        self.root.after(200, lambda: self.animate_path(is_auto=is_auto))

    def draw_synthwave_line(self, i1, i2, seg_idx):
        """Trace un segment coloré selon une palette néon."""
        palette = [
            "#f72585",  # rose
            "#b5179e",  # rose violet
            "#7209b7",  # violet
            "#3a0ca3",  # bleu foncé
            "#4361ee",  # bleu
            "#4cc9f0"  # turquoise
        ]
        color = palette[seg_idx % len(palette)]

        x1, y1 = self.cities[i1]
        x2, y2 = self.cities[i2]
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=3)

    def draw_quick_path(self, path, color="#ff7f00"):
        """Trace instantanément un chemin dans la couleur donnée."""
        self.canvas.delete("all")
        self.draw_canvas_bg_gradient()
        self.draw_cities()

        n = len(path)
        for i in range(n - 1):
            x1, y1 = self.cities[path[i]]
            x2, y2 = self.cities[path[i + 1]]
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)

        # fermer la boucle
        if n > 1:
            x1, y1 = self.cities[path[-1]]
            x2, y2 = self.cities[path[0]]
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)

    # =======================================================
    # 6) MODE AUTOMATIQUE
    # =======================================================
    def start_auto(self):
        """Démarre le mode automatique (si pas déjà en cours)."""
        if not self.auto_running:
            self.auto_running = True
            self.auto_loop()

    def auto_loop(self):
        """Exécute l'algo choisi, puis animation; attend 5s, recommence..."""
        if not self.auto_running:
            return

        # On appelle une version "auto" du run pour savoir qu'il faut enchaîner
        self.run_auto_iteration()

    def run_auto_iteration(self):
        """Comme run_once(), mais on signale is_auto=True pour relancer après animation."""
        if not self.cities or self.is_animating:
            return  # attend la fin de l'animation en cours

        algo = self.algo_var.get()
        if algo == "GA":
            new_path = run_genetic_algorithm(self.cities)
        elif algo == "ACO":
            new_path = run_ant_colony(self.cities)
        else:
            path_ga = run_genetic_algorithm(self.cities)
            new_path = run_ant_colony(self.cities, initial_path=path_ga)

        # On vérifie si c'est meilleur, etc.
        # on passe is_auto=True, ainsi on enchaînera un after(5000) après la fin
        self.check_and_update_best(new_path, is_auto=True)

    def stop_auto(self):
        """Arrête le mode automatique."""
        self.auto_running = False
