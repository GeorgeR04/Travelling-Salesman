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

        # -- Configuration de la fenêtre racine, pour ne plus avoir de fond blanc
        self.root.configure(bg="#2c2c2c")  # gris foncé

        self.num_cities = num_cities
        self.cities = []

        self.best_distance = float("inf")
        self.best_path = []

        # Contiendra la solution "best" qu'on veut sauvegarder
        # On la mettra à jour automatiquement dès qu'une meilleure solution est trouvée
        self.best_solution_saved = None  # (path, dist)

        # Animation
        self.current_path = []
        self.current_segment_index = 0
        self.is_animating = False

        # Mode automatique
        self.auto_running = False

        # ==========================================================
        # Configuration du style global (ttk) pour tout en gris
        # ==========================================================
        style = ttk.Style()
        style.theme_use("clam")

        # Couleur de fond générale pour cadres (Frame) et labels
        style.configure("TFrame", background="#2c2c2c")
        style.configure("TLabel", background="#2c2c2c", foreground="white", font=("Helvetica", 11))
        style.configure("TButton", background="#3a3a3a", foreground="white", font=("Helvetica", 10, "bold"))

        # Combobox : changer le fond (fieldbackground) et le texte (foreground)
        style.configure("TCombobox",
                        fieldbackground="#3a3a3a",
                        background="#3a3a3a",
                        foreground="white")
        # Pour que la liste déroulante soit aussi sombre, il faut parfois configurer map :
        style.map("TCombobox",
            fieldbackground=[("readonly", "#3a3a3a")],
            foreground=[("readonly", "white")],
            background=[("readonly", "#3a3a3a")]
        )

        # ---- Canevas principal (fond dégradé)
        self.canvas = tk.Canvas(self.root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, highlightthickness=0)
        # highlightthickness=0 pour enlever la bordure blanche
        self.canvas.pack(side=tk.LEFT, fill="both", expand=True)

        # Dessin initial du dégradé
        self.draw_canvas_bg_gradient()

        # ---- Cadre de contrôles
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

        self.algo_menu = ttk.Combobox(
            self.control_frame,
            textvariable=self.algo_var,
            values=["GA","ACO","Hybride"],
            state="readonly"  # pour l'apparence plus stable
        )
        self.algo_menu.pack(pady=5, fill="x")
        self.algo_menu.current(0)

        # Bouton "Lancer"
        self.btn_run_once = ttk.Button(
            self.control_frame,
            text="Lancer",
            command=self.run_once
        )
        self.btn_run_once.pack(pady=5, fill="x")

        # Bouton "Automatique"
        self.btn_auto = ttk.Button(
            self.control_frame,
            text="Mode Automatique",
            command=self.start_auto
        )
        self.btn_auto.pack(pady=5, fill="x")

        # Bouton "Stop"
        self.btn_stop = ttk.Button(
            self.control_frame,
            text="Stop Mode Automatic",
            command=self.stop_auto
        )
        self.btn_stop.pack(pady=5, fill="x")

        # -------------------------------------------------------
        # Nouveaux boutons : Dessiner la solution sauvegardée
        # -------------------------------------------------------
        self.btn_draw_saved_overlay = ttk.Button(
            self.control_frame,
            text="Dessiner Best (Overlay)",
            command=lambda: self.draw_saved_solution(overlay=True)
        )
        self.btn_draw_saved_overlay.pack(pady=5, fill="x")

        self.btn_draw_saved_alone = ttk.Button(
            self.control_frame,
            text="Dessiner Best (Alone)",
            command=lambda: self.draw_saved_solution(overlay=False)
        )
        self.btn_draw_saved_alone.pack(pady=5, fill="x")

        # Label info
        self.info_label = ttk.Label(self.control_frame, text="Meilleure distance: -", style="TLabel")
        self.info_label.pack(pady=10)

        # Générer les villes initiales
        self.generate_cities()

    # =======================================================
    # 1) FOND DÉGRADÉ DE GRIS DANS LE CANEVAS
    # =======================================================
    def draw_canvas_bg_gradient(self):
        """
        Dessine un dégradé vertical du gris foncé au gris moyen
        sur tout le canevas.
        """
        self.canvas.delete("gradient_bg")

        start_color = (0x2D, 0x2D, 0x2D)  # #2d2d2d
        end_color   = (0x4D, 0x4D, 0x4D)  # #4d4d4d
        steps = 60

        for i in range(steps):
            f = i / (steps - 1)
            r = int(start_color[0] + f*(end_color[0] - start_color[0]))
            g = int(start_color[1] + f*(end_color[1] - start_color[1]))
            b = int(start_color[2] + f*(end_color[2] - start_color[2]))
            color_hex = f"#{r:02x}{g:02x}{b:02x}"

            y_start = int(WINDOW_HEIGHT * i / steps)
            y_end   = int(WINDOW_HEIGHT * (i+1) / steps)

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
        """Génère des villes aléatoirement, réinitialise la meilleure distance."""
        self.cities.clear()
        self.best_distance = float("inf")
        self.best_path = []
        self.current_path = []
        self.is_animating = False

        self.best_solution_saved = None  # on efface aussi l'enregistrement

        self.canvas.delete("all")
        self.draw_canvas_bg_gradient()

        for _ in range(self.num_cities):
            x = random.randint(50, WINDOW_WIDTH - 50)
            y = random.randint(50, WINDOW_HEIGHT - 50)
            self.cities.append((x, y))

        self.draw_cities()
        self.update_info_label("Nouvelles villes générées.")

    def draw_cities(self):
        """Dessine les points (villes) sur le canevas (petits cercles)."""
        for i, (x, y) in enumerate(self.cities):
            r = 6
            self.canvas.create_oval(
                x - r, y - r, x + r, y + r,
                fill="#f1f1f1", outline="#888888", width=1
            )
            self.canvas.create_text(
                x, y - 12,
                text=str(i + 1),  # i + 1 => "ville #1" pour l'indice 0
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

        # boucler pour fermer la tournée
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

        On récupère (best_path, best_dist), mais on ne garde que best_path
        pour dessiner.
        """
        if not self.cities or self.is_animating:
            return

        algo = self.algo_var.get()
        if algo == "GA":
            best_path_ga, dist_ga = run_genetic_algorithm(self.cities)
            new_path = best_path_ga
        elif algo == "ACO":
            best_path_aco, dist_aco = run_ant_colony(self.cities)
            new_path = best_path_aco
        else:
            # Hybride => GA puis ACO (amorçage)
            ga_path, ga_dist = run_genetic_algorithm(self.cities)
            aco_path, aco_dist = run_ant_colony(self.cities, initial_path=ga_path)
            new_path = aco_path

        self.check_and_update_best(new_path, is_auto=False)

    def check_and_update_best(self, path, is_auto=False):
        """
        Compare la solution 'path' avec la meilleure distance.
        Si c'est meilleur, on anime; sinon, on trace vite fait en orange.

        Si c'est vraiment meilleur => on l'enregistre aussi dans best_solution_saved.
        """
        dist = self.compute_distance(path)
        if dist < self.best_distance:
            self.best_distance = dist
            self.best_path = path

            # On redessine
            self.canvas.delete("all")
            self.draw_canvas_bg_gradient()
            self.draw_cities()

            # Animation
            self.current_path = path
            self.current_segment_index = 0
            self.is_animating = True
            self.update_info_label(f"Nouvelle meilleure solution ! (dist={dist:.2f})")

            # On ENREGISTRE cette solution comme "best solution saved"
            self.best_solution_saved = (path[:], dist)

            self.animate_path(is_auto=is_auto)
        else:
            # Chemin non meilleur => on dessine en orange
            self.draw_quick_path(path, color="#ffa600")
            self.update_info_label(f"Solution non meilleure (dist={dist:.2f})")

            # Si on est en auto => planifier la suite après 5 s
            if is_auto and self.auto_running:
                self.root.after(5000, self.auto_loop)

    # =======================================================
    # 5) ANIMATION « SYNTHWAVE »
    # =======================================================
    def animate_path(self, is_auto=False):
        """Dessine progressivement la tournée self.current_path (200 ms par segment)."""
        if not self.is_animating:
            return

        path = self.current_path
        seg_idx = self.current_segment_index
        n = len(path)

        if seg_idx >= n:
            # fermer la boucle
            self.draw_synthwave_line(path[-1], path[0], seg_idx)
            self.is_animating = False
            self.update_info_label("Animation terminée.")

            if is_auto and self.auto_running:
                self.root.after(5000, self.auto_loop)
            return

        if seg_idx > 0:
            self.draw_synthwave_line(path[seg_idx - 1], path[seg_idx], seg_idx - 1)

        self.current_segment_index += 1
        self.root.after(200, lambda: self.animate_path(is_auto=is_auto))

    def draw_synthwave_line(self, i1, i2, seg_idx):
        """Trace un segment coloré selon une palette néon."""
        palette = [
            "#f72585",  # rose flashy
            "#b5179e",
            "#7209b7",
            "#3a0ca3",
            "#4361ee",
            "#4cc9f0"
        ]
        color = palette[seg_idx % len(palette)]
        x1, y1 = self.cities[i1]
        x2, y2 = self.cities[i2]
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=3)

    def draw_quick_path(self, path, color="#ff7f00"):
        """
        Trace instantanément un chemin dans la couleur donnée,
        en effaçant d'abord le canevas.
        """
        self.canvas.delete("all")
        self.draw_canvas_bg_gradient()
        self.draw_cities()

        n = len(path)
        for i in range(n - 1):
            x1, y1 = self.cities[path[i]]
            x2, y2 = self.cities[path[i+1]]
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)
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
        """Exécute l'algo choisi, attend la fin, relance après 5s..."""
        if not self.auto_running:
            return
        self.run_auto_iteration()

    def run_auto_iteration(self):
        """Lance l'algo (GA/ACO/Hybride), is_auto=True, pour enchaîner."""
        if not self.cities or self.is_animating:
            return
        algo = self.algo_var.get()
        if algo == "GA":
            (best_p, dist_p) = run_genetic_algorithm(self.cities)
            new_path = best_p
        elif algo == "ACO":
            (best_p, dist_p) = run_ant_colony(self.cities)
            new_path = best_p
        else:
            # Hybride
            (ga_path, ga_dist) = run_genetic_algorithm(self.cities)
            (aco_path, aco_dist) = run_ant_colony(self.cities, initial_path=ga_path)
            new_path = aco_path

        self.check_and_update_best(new_path, is_auto=True)

    def stop_auto(self):
        """Arrête le mode automatique."""
        self.auto_running = False

    # =======================================================
    # 7) AFFICHER LA SOLUTION SAUVEGARDÉE
    # =======================================================
    def draw_saved_solution(self, overlay=True):
        """
        Dessine la solution sauvegardée (self.best_solution_saved).
        - overlay=True => on la superpose sur le dessin actuel,
        - overlay=False => on efface tout d'abord puis on la dessine seule.
        """
        if not self.best_solution_saved:
            self.update_info_label("Aucune solution enregistrée à dessiner.")
            return

        saved_path, saved_dist = self.best_solution_saved

        if not overlay:
            # On efface tout
            self.canvas.delete("all")
            self.draw_canvas_bg_gradient()
            self.draw_cities()

        # On la dessine en vert
        self.draw_quick_path_custom(saved_path, color="#00FF00", width=3)
        self.update_info_label(f"Solution enregistrée dessinée (dist={saved_dist:.2f}).")

    def draw_quick_path_custom(self, path, color="#00FF00", width=3):
        """
        Trace un cycle path sur le canevas en color, SANS effacer ni redessiner avant.
        """
        n = len(path)
        for i in range(n - 1):
            x1, y1 = self.cities[path[i]]
            x2, y2 = self.cities[path[i+1]]
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)

        if n > 1:
            x1, y1 = self.cities[path[-1]]
            x2, y2 = self.cities[path[0]]
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
