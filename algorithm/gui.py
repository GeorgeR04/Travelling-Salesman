import tkinter as tk
from tkinter import ttk
import random
import math

# Importe la GA et l'ACO depuis leurs fichiers respectifs
from ga import GeneticAlgorithm
from aco import AntColony

class TSPApp(tk.Tk):
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800

    # Rayon de détection pour le survol de la souris
    HOVER_RADIUS = 10

    def __init__(self, num_cities=10):
        super().__init__()
        self.title("TSP Synthwave - GA & ACO")
        self.configure(bg="#2c2c2c")

        self.num_cities = num_cities
        self.cities = []

        # Suivi de la meilleure distance & chemin
        self.best_distance = float("inf")
        self.best_path = []
        self.best_solution_saved = None  # (path, dist)

        # Variables pour l'animation
        self.current_path = []
        self.current_segment_index = 0
        self.is_animating = False

        # Mode automatique
        self.auto_running = False

        # Configuration du style
        self._setup_style()

        # Configuration de l'interface
        self._setup_ui()

        # Génération initiale de villes
        self._generate_cities()

    ################################################################
    # 1) Configuration du style et interface
    ################################################################
    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TFrame", background="#2c2c2c")
        style.configure("TLabel", background="#2c2c2c", foreground="white", font=("Helvetica", 11))
        style.configure("TButton", background="#3a3a3a", foreground="white", font=("Helvetica", 10, "bold"))
        style.configure("TCombobox",
                        fieldbackground="#3a3a3a",
                        background="#3a3a3a",
                        foreground="white")
        style.map("TCombobox",
                  fieldbackground=[("readonly", "#3a3a3a")],
                  foreground=[("readonly", "white")],
                  background=[("readonly", "#3a3a3a")])

    def _setup_ui(self):
        # Canevas principal
        self.canvas = tk.Canvas(
            self, width=self.WINDOW_WIDTH, height=self.WINDOW_HEIGHT,
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, fill="both", expand=True)

        # Événement <Motion> pour détecter la souris et afficher (x,y)
        self.canvas.bind("<Motion>", self._on_mouse_move)

        self._draw_canvas_bg_gradient()

        # Cadre de commandes à droite
        controls = ttk.Frame(self)
        controls.pack(side=tk.RIGHT, fill="y", padx=10, pady=10)

        ttk.Button(controls, text="Générer Villes", command=self._generate_cities).pack(fill="x", pady=5)

        ttk.Label(controls, text="Choisir Algorithme:").pack(pady=2)
        self.algo_var = tk.StringVar(value="GA")
        algo_menu = ttk.Combobox(controls, textvariable=self.algo_var,
                                 values=["GA", "ACO", "Hybride"], state="readonly")
        algo_menu.pack(fill="x", pady=5)

        ttk.Button(controls, text="Lancer", command=self._run_once).pack(fill="x", pady=5)
        ttk.Button(controls, text="Mode Automatique", command=self._start_auto).pack(fill="x", pady=5)
        ttk.Button(controls, text="Stop Mode Automatic", command=self._stop_auto).pack(fill="x", pady=5)

        ttk.Button(controls, text="Dessiner Best (Overlay)",
                   command=lambda: self._draw_saved_solution(overlay=True)).pack(fill="x", pady=5)
        ttk.Button(controls, text="Dessiner Best (Alone)",
                   command=lambda: self._draw_saved_solution(overlay=False)).pack(fill="x", pady=5)

        self.info_label = ttk.Label(controls, text="Meilleure distance: -")
        self.info_label.pack(pady=10)

        # Label pour afficher la position de la ville survolée
        self.hover_label = ttk.Label(controls, text="Survol: (x, y)")
        self.hover_label.pack(pady=5)

    ################################################################
    # 2) Fond dégradé du canevas
    ################################################################
    def _draw_canvas_bg_gradient(self):
        """Dessine un dégradé vertical de gris sur tout le canevas."""
        self.canvas.delete("gradient_bg")
        steps = 60
        start_color = (0x2D, 0x2D, 0x2D)  # #2d2d2d
        end_color   = (0x4D, 0x4D, 0x4D)  # #4d4d4d

        for i in range(steps):
            f = i / (steps - 1)
            r = int(start_color[0] + f * (end_color[0] - start_color[0]))
            g = int(start_color[1] + f * (end_color[1] - start_color[1]))
            b = int(start_color[2] + f * (end_color[2] - start_color[2]))
            color_hex = f"#{r:02x}{g:02x}{b:02x}"

            y_start = int(self.WINDOW_HEIGHT * i / steps)
            y_end   = int(self.WINDOW_HEIGHT * (i + 1) / steps)

            self.canvas.create_rectangle(
                0, y_start,
                self.WINDOW_WIDTH, y_end,
                fill=color_hex,
                outline=color_hex,
                tags="gradient_bg"
            )

    def _draw_scale(self):
        """
        Dessine une grille (ou axes) avec des repères pour montrer
        les coordonnées (x, y). Ici, c’est une grille tous les 100 pixels.
        """
        step = 100
        line_color = "#444444"
        text_color = "#ffffff"

        # Lignes verticales + label X
        for x in range(0, self.WINDOW_WIDTH + 1, step):
            self.canvas.create_line(x, 0, x, self.WINDOW_HEIGHT, fill=line_color, dash=(2, 2))
            self.canvas.create_text(x + 15, 10, text=str(x), fill=text_color, font=("Helvetica", 9, "bold"))

        # Lignes horizontales + label Y
        for y in range(0, self.WINDOW_HEIGHT + 1, step):
            self.canvas.create_line(0, y, self.WINDOW_WIDTH, y, fill=line_color, dash=(2, 2))
            self.canvas.create_text(30, y + 10, text=str(y), fill=text_color, font=("Helvetica", 9, "bold"))

    ################################################################
    # 3) Génération des villes
    ################################################################
    def _generate_cities(self):
        """Génère des villes en position aléatoire et réinitialise le meilleur chemin."""
        margin = 50
        self.cities = [
            (
                random.randint(margin, self.WINDOW_WIDTH - margin),
                random.randint(margin, self.WINDOW_HEIGHT - margin)
            )
            for _ in range(self.num_cities)
        ]

        self.best_distance = float("inf")
        self.best_path = []
        self.current_path = []
        self.is_animating = False
        self.best_solution_saved = None

        self._refresh_canvas()
        self._update_info_label("Nouvelles villes générées.")

    def _draw_cities(self):
        for i, (x, y) in enumerate(self.cities):
            r = 6
            self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                    fill="#f1f1f1", outline="#888888", width=1)
            self.canvas.create_text(x, y - 12, text=str(i+1),
                                    fill="#ffffff", font=("Helvetica", 9, "bold"))

    def _refresh_canvas(self):
        self.canvas.delete("all")
        self._draw_canvas_bg_gradient()
        self._draw_scale()  # <-- DESSINE LA GRILLE / ÉCHELLE
        self._draw_cities()

    ################################################################
    # 4) Calcul distance et mise à jour des infos
    ################################################################
    def _compute_distance(self, path):
        """Calcule la distance totale d'une tournée fermée."""
        dist = 0
        for i in range(-1, len(path) - 1):
            x1, y1 = self.cities[path[i]]
            x2, y2 = self.cities[path[i+1]]
            dist += math.dist((x1, y1), (x2, y2))
        return dist

    def _update_info_label(self, msg=None):
        if self.best_distance < float('inf'):
            dist_txt = f"Meilleure distance: {self.best_distance:.2f}"
        else:
            dist_txt = "Meilleure distance: -"

        text = dist_txt if not msg else f"{dist_txt}\n{msg}"
        self.info_label.config(text=text)

    ################################################################
    # 5) Lancer l’algorithme (GA / ACO / Hybride)
    ################################################################
    def _run_once(self):
        """Exécute un algorithme choisi, une seule fois."""
        if not self.cities or self.is_animating:
            return
        new_path = self._run_algorithm(self.algo_var.get())
        self._check_and_update_best(new_path, is_auto=False)

    def _run_algorithm(self, algo_name):
        if algo_name == "GA":
            ga = GeneticAlgorithm(self.cities)
            best_path, _ = ga.run()
            return best_path
        elif algo_name == "ACO":
            aco = AntColony(self.cities)
            best_path, _ = aco.run()
            return best_path
        else:
            # Hybride: GA puis ACO avec la solution GA en "hint"
            ga = GeneticAlgorithm(self.cities)
            ga_path, _ = ga.run()
            aco = AntColony(self.cities, initial_path=ga_path)
            aco_path, _ = aco.run()
            return aco_path

    def _check_and_update_best(self, path, is_auto=False):
        """Vérifie si la solution courante est meilleure que la meilleure connue."""
        dist = self._compute_distance(path)
        if dist < self.best_distance:
            self.best_distance = dist
            self.best_path = path

            self._refresh_canvas()
            self.current_path = path
            self.current_segment_index = 0
            self.is_animating = True
            self._update_info_label(f"Nouvelle meilleure solution ! (dist={dist:.2f})")

            # Sauvegarde
            self.best_solution_saved = (path[:], dist)

            # Lance l’animation
            self._animate_path(is_auto=is_auto)
        else:
            # Chemin non meilleur, on l’affiche en orange brièvement
            self._draw_path(path, color="#ffa600", width=2, clear_first=True)
            self._update_info_label(f"Solution non meilleure (dist={dist:.2f})")

            # Si on est en auto, enchaîne
            if is_auto and self.auto_running:
                self.after(5000, self._auto_loop)

    ################################################################
    # 6) Animation synthwave
    ################################################################
    def _animate_path(self, is_auto=False):
        if not self.is_animating:
            return

        path = self.current_path
        seg_idx = self.current_segment_index
        n = len(path)

        # Quand on a tracé tous les segments, on ferme la boucle
        if seg_idx >= n:
            self._draw_synthwave_line(path[-1], path[0], seg_idx)
            self.is_animating = False
            self._update_info_label("Animation terminée.")
            if is_auto and self.auto_running:
                self.after(5000, self._auto_loop)
            return

        if seg_idx > 0:
            self._draw_synthwave_line(path[seg_idx - 1], path[seg_idx], seg_idx - 1)

        self.current_segment_index += 1
        self.after(200, lambda: self._animate_path(is_auto=is_auto))

    def _draw_synthwave_line(self, i1, i2, seg_idx):
        """Trace un segment coloré façon "néon synthwave"."""
        palette = [
            "#f72585", "#b5179e", "#7209b7",
            "#3a0ca3", "#4361ee", "#4cc9f0"
        ]
        color = palette[seg_idx % len(palette)]
        x1, y1 = self.cities[i1]
        x2, y2 = self.cities[i2]
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=3)

    ################################################################
    # 7) Mode automatique
    ################################################################
    def _start_auto(self):
        """Démarre un enchaînement infini d’exécutions."""
        if not self.auto_running:
            self.auto_running = True
            self._auto_loop()

    def _auto_loop(self):
        """Boucle d’exécution automatique tant que self.auto_running est True."""
        if not self.auto_running:
            return
        self._run_auto_iteration()

    def _run_auto_iteration(self):
        if not self.cities or self.is_animating:
            return
        new_path = self._run_algorithm(self.algo_var.get())
        self._check_and_update_best(new_path, is_auto=True)

    def _stop_auto(self):
        self.auto_running = False

    ################################################################
    # 8) Dessiner la solution sauvegardée
    ################################################################
    def _draw_saved_solution(self, overlay=True):
        if not self.best_solution_saved:
            self._update_info_label("Aucune solution enregistrée à dessiner.")
            return
        saved_path, saved_dist = self.best_solution_saved

        if not overlay:
            self._refresh_canvas()

        # On la dessine en vert
        self._draw_path(saved_path, color="#00FF00", width=3, clear_first=False)
        self._update_info_label(f"Solution enregistrée dessinée (dist={saved_dist:.2f}).")

    ################################################################
    # 9) DESSIN RAPIDE D’UN CHEMIN
    ################################################################
    def _draw_path(self, path, color="#ffa600", width=2, clear_first=True):
        if clear_first:
            self._refresh_canvas()

        for i in range(len(path) - 1):
            x1, y1 = self.cities[path[i]]
            x2, y2 = self.cities[path[i+1]]
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)

        # Boucle fermée
        if len(path) > 1:
            x1, y1 = self.cities[path[-1]]
            x2, y2 = self.cities[path[0]]
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)

    ################################################################
    # 10) DÉTECTION DE LA VILLE SURVOLÉE
    ################################################################
    def _on_mouse_move(self, event):
        """
        À chaque mouvement de souris dans le canevas, on regarde si
        le pointeur est proche d’une ville (à moins de HOVER_RADIUS).
        Si oui, on affiche (x,y) dans self.hover_label, sinon on remet un texte neutre.
        """
        found_city = False

        for i, (cx, cy) in enumerate(self.cities):
            dx = event.x - cx
            dy = event.y - cy
            # On compare la distance au carré pour éviter un sqrt()
            if dx*dx + dy*dy <= self.HOVER_RADIUS * self.HOVER_RADIUS:
                self.hover_label.config(
                    text=f"Survol: Ville {i+1} (X={cx}, Y={cy})"
                )
                found_city = True
                break

        if not found_city:
            self.hover_label.config(text="Survol: (x, y)")
