import tkinter as tk
from tkinter import ttk
import random
import math

from PIL import Image, ImageTk

# Import GA et ACO (inchangé)
from ga import GeneticAlgorithm
from aco import AntColony

class TSPApp(tk.Tk):
    HOVER_RADIUS = 10

    def __init__(self, num_cities=10):
        super().__init__()
        self.title("TSP Synthwave - GA & ACO")
        self.state('zoomed')

        self.num_cities = num_cities
        self.cities = []

        # Meilleur résultat
        self.best_distance = float('inf')
        self.best_path = []
        self.best_solution_saved = None

        # Animation
        self.current_path = []
        self.current_segment_index = 0
        self.is_animating = False

        # Mode auto
        self.auto_running = False

        # Liste de tous les chemins conservés
        self.stored_paths = []

        # Image de fond
        self.bg_image = None
        self.bg_image_resized = None
        self._load_background_image("IMG.png")

        # Style + UI
        self._setup_style()

        ### CHANGEMENT ###
        # On crée un topbar en haut pour le statut du mode auto
        self.topbar = ttk.Frame(self, style="TFrame")
        self.topbar.pack(side=tk.TOP, fill="x")

        # Label pour le statut du mode auto
        self.auto_status_label = ttk.Label(self.topbar, text="Mode Auto: OFF")
        self.auto_status_label.pack(side=tk.LEFT, padx=10, pady=5)

        # Frame principal (en-dessous du topbar)
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True)

        # Canvas à gauche
        self.canvas = tk.Canvas(main_frame, highlightthickness=0, background="#21252b")
        self.canvas.pack(side=tk.LEFT, fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Motion>", self._on_mouse_move)

        # Panneau de droite
        controls = ttk.Frame(main_frame)
        controls.config(width=250)
        controls.pack(side=tk.RIGHT, fill="y", padx=10, pady=10)

        # Suite de la config UI
        self._setup_ui(controls)

        # Génération initiale
        self._generate_cities()

    ################################################################
    # 1) Image de fond
    ################################################################
    def _load_background_image(self, filename):
        try:
            img = Image.open(filename)
            self.bg_image = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Impossible de charger l'image : {e}")
            self.bg_image = None

    ################################################################
    # 2) Style + UI
    ################################################################
    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Palette
        main_bg = "#282c34"
        text_fg = "#abb2bf"
        button_bg = "#3b4048"
        button_active_bg = "#4b515c"
        combo_bg = "#3b4048"
        labelframe_bg = "#2f2f2f"

        self.configure(bg=main_bg)

        style.configure("TFrame", background=main_bg)
        style.configure("TLabel", background=main_bg, foreground=text_fg, font=("Helvetica", 11))
        style.configure("TButton",
                        background=button_bg,
                        foreground=text_fg,
                        font=("Helvetica", 10, "bold"),
                        borderwidth=0)
        style.map("TButton",
                  background=[("active", button_active_bg)],
                  foreground=[("active", text_fg)])

        style.configure("TCombobox",
                        fieldbackground=combo_bg,
                        background=combo_bg,
                        foreground=text_fg)
        style.map("TCombobox",
                  fieldbackground=[("readonly", combo_bg)],
                  foreground=[("readonly", text_fg)],
                  background=[("readonly", combo_bg)])

        style.configure("TLabelframe", background=labelframe_bg, borderwidth=1)
        style.configure("TLabelframe.Label", background=labelframe_bg, foreground=text_fg)
        style.configure("TLabelframe.Label", font=("Helvetica", 10, "bold"))

    def _setup_ui(self, controls):
        # -- Labelframe: GESTION VILLES
        ville_frame = ttk.Labelframe(controls, text="Gestion Villes")
        ville_frame.pack(fill="x", pady=10)

        ttk.Button(ville_frame, text="Générer Villes",
                   command=self._generate_cities).pack(fill="x", pady=5)

        self.info_label = ttk.Label(ville_frame, text="Meilleure distance: -")
        self.info_label.pack(pady=5)

        # Choix Algorithme
        ttk.Label(controls, text="Choisir Algorithme:").pack(pady=2)
        self.algo_var = tk.StringVar(value="GA")
        algo_menu = ttk.Combobox(controls, textvariable=self.algo_var,
                                 values=["GA", "ACO", "Hybride"], state="readonly")
        algo_menu.pack(fill="x", pady=5)

        # Boutons Lancer
        ttk.Button(controls, text="Lancer", command=self._run_once).pack(fill="x", pady=5)
        ttk.Button(controls, text="Lancer Rapide", command=self._run_once_no_animation).pack(fill="x", pady=5)

        # -- Labelframe: MODE AUTOMATIQUE
        auto_frame = ttk.Labelframe(controls, text="Mode Automatique")
        auto_frame.pack(fill="x", pady=10)

        ttk.Button(auto_frame, text="Démarrer", command=self._start_auto).pack(fill="x", pady=5)
        ttk.Button(auto_frame, text="Stop", command=self._stop_auto).pack(fill="x", pady=5)

        # -- Labelframe: SOLUTION ENREGISTREE
        saved_frame = ttk.Labelframe(controls, text="Solution Enregistrée")
        saved_frame.pack(fill="x", pady=10)

        ttk.Button(saved_frame, text="Dessiner Best (Overlay)",
                   command=lambda: self._draw_saved_solution(overlay=True)).pack(fill="x", pady=5)
        ttk.Button(saved_frame, text="Dessiner Best (Alone)",
                   command=lambda: self._draw_saved_solution(overlay=False)).pack(fill="x", pady=5)

        # Survol
        self.hover_label = ttk.Label(controls, text="Survol: (x, y)", width=30)
        self.hover_label.pack(pady=5)

        self.segment_label = ttk.Label(controls, text="Segment: -", width=30)
        self.segment_label.pack(pady=5)

    ################################################################
    # 3) Redimensionnement
    ################################################################
    def _on_canvas_resize(self, event):
        self._refresh_canvas()

    ################################################################
    # 4) Génération de villes
    ################################################################
    def _generate_cities(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        margin = 50

        if w < 100: w = 1200
        if h < 100: h = 800

        self.cities = [
            (random.randint(margin, w - margin),
             random.randint(margin, h - margin))
            for _ in range(self.num_cities)
        ]

        self.best_distance = float('inf')
        self.best_path = []
        self.best_solution_saved = None
        self.current_path = []
        self.current_segment_index = 0
        self.is_animating = False

        # On vide la liste des chemins
        self.stored_paths.clear()

        self._refresh_canvas()
        self._update_info_label("Nouvelles villes générées.")

    def _draw_cities(self):
        for i, (x, y) in enumerate(self.cities):
            r = 5
            self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                    fill="#ffffff", outline="#000000", width=1)
            self.canvas.create_text(x, y - 12, text=str(i+1),
                                    fill="#ffffff", font=("Helvetica", 9, "bold"))

    ################################################################
    # 5) refresh_canvas (image, axes, villes + chemins)
    ################################################################
    def _refresh_canvas(self):
        self.canvas.delete("all")

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        margin = 50

        # Image => prend la taille (margin->w-margin, margin->h-margin)
        self._draw_bg_image(margin, margin, w - margin, h - margin)
        # Axes + grille
        self._draw_axes_with_grads(w, h, margin)
        # Villes
        self._draw_cities()

        # Redessine tous les chemins stockés
        for (path, color, width) in self.stored_paths:
            self._draw_path(path, color=color, width=width,
                            clear_first=False, store_in_list=False)

    def _draw_bg_image(self, x1, y1, x2, y2):
        if self.bg_image:
            zone_width = x2 - x1
            zone_height = y2 - y1
            try:
                img_pil = ImageTk.getimage(self.bg_image)
                resized = img_pil.resize((zone_width, zone_height), Image.Resampling.LANCZOS)
                self.bg_image_resized = ImageTk.PhotoImage(resized)
                self.canvas.create_image(x1, y1, anchor="nw", image=self.bg_image_resized)
            except:
                self.canvas.create_image(x1, y1, anchor="nw", image=self.bg_image)

    def _draw_axes_with_grads(self, w, h, margin, step=50):
        x_start, x_end = margin, w - margin
        y_start, y_end = h - margin, margin

        # Grille vertical/horizontal
        for x_pos in range(x_start, x_end+1, step):
            self.canvas.create_line(x_pos, y_end, x_pos, y_start,
                                    fill="white", width=1, stipple="gray75")
        for y_pos in range(y_end, y_start+1, step):
            self.canvas.create_line(x_start, y_pos, x_end, y_pos,
                                    fill="white", width=1, stipple="gray75")

        # Axe X
        self.canvas.create_line(x_start, y_start, x_end, y_start,
                                fill="white", width=2)
        # Axe Y
        self.canvas.create_line(x_start, y_start, x_start, y_end,
                                fill="white", width=2)

        # Graduations X
        for x_pos in range(x_start, x_end+1, step):
            self.canvas.create_line(x_pos, y_start-5, x_pos, y_start+5,
                                    fill="white", width=2)
            label_val = x_pos - x_start
            self.canvas.create_text(x_pos, y_start+12, text=str(label_val),
                                    fill="white", font=("Helvetica", 8))

        # Graduations Y
        for y_pos in range(y_end, y_start+1, step):
            self.canvas.create_line(x_start-5, y_pos, x_start+5, y_pos,
                                    fill="white", width=2)
            label_val = y_start - y_pos
            self.canvas.create_text(x_start-8, y_pos, text=str(label_val),
                                    fill="white", font=("Helvetica", 8),
                                    anchor="e")

        self.canvas.create_text(x_end+15, y_start, text="X",
                                fill="white", font=("Helvetica", 9), anchor="nw")
        self.canvas.create_text(x_start, y_end-15, text="Y",
                                fill="white", font=("Helvetica", 9), anchor="sw")

    ################################################################
    # 6) Distances + info
    ################################################################
    def _compute_distance(self, path):
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
    # 7) Lancer l'algo
    ################################################################
    def _run_once(self):
        # Effacer les chemins existants
        self.stored_paths.clear()
        self._refresh_canvas()

        if not self.cities or self.is_animating:
            return
        path = self._run_algorithm(self.algo_var.get())
        self._check_and_update_best(path, is_auto=False, skip_animation=False)

    def _run_once_no_animation(self):
        # On efface les anciens chemins
        self.stored_paths.clear()
        self._refresh_canvas()

        if not self.cities:
            return

        path = self._run_algorithm(self.algo_var.get())
        self._check_and_update_best(path, is_auto=False, skip_animation=True)

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
            ga = GeneticAlgorithm(self.cities)
            ga_path, _ = ga.run()
            aco = AntColony(self.cities, initial_path=ga_path)
            aco_path, _ = aco.run()
            return aco_path

    def _check_and_update_best(self, path, is_auto=False, skip_animation=False):
        dist = self._compute_distance(path)
        if dist < self.best_distance:
            self.best_distance = dist
            self.best_path = path

            self._refresh_canvas()
            self.current_path = path
            self.current_segment_index = 0

            self.best_solution_saved = (path[:], dist)

            if not skip_animation:
                self.is_animating = True
                self._update_info_label(f"Nouvelle meilleure solution ! (dist={dist:.2f})")
                self._animate_path(is_auto=is_auto)
            else:
                self.is_animating = False
                self._draw_path(path, color="#f72585", width=3,
                                clear_first=False, store_in_list=True)
                self._update_info_label(f"Nouvelle meilleure solution (Rapide) ! (dist={dist:.2f})")

                if is_auto and self.auto_running:
                    self.after(5000, self._auto_loop)
        else:
            # Chemin non meilleur => on dessine en orange
            self._draw_path(path, color="#ffa600", width=2,
                            clear_first=False, store_in_list=True)
            self._update_info_label(f"Solution non meilleure (dist={dist:.2f})")

            if is_auto and self.auto_running:
                self.after(5000, self._auto_loop)

    ################################################################
    # 8) Animation
    ################################################################
    def _animate_path(self, is_auto=False):
        if not self.is_animating:
            return

        path = self.current_path
        seg_idx = self.current_segment_index
        n = len(path)

        if seg_idx >= n:
            self._draw_synthwave_line(path[-1], path[0], seg_idx)
            self.is_animating = False
            self._update_info_label("Animation terminée.")
            self._add_path_to_stored_paths(path, color="#f72585", width=3)

            if is_auto and self.auto_running:
                self.after(5000, self._auto_loop)
            return

        if seg_idx > 0:
            self._draw_synthwave_line(path[seg_idx - 1], path[seg_idx], seg_idx - 1)

        self.current_segment_index += 1
        self.after(200, lambda: self._animate_path(is_auto=is_auto))

    def _draw_synthwave_line(self, i1, i2, seg_idx):
        palette = ["#f72585", "#b5179e", "#7209b7",
                   "#3a0ca3", "#4361ee", "#4cc9f0"]
        color = palette[seg_idx % len(palette)]
        x1, y1 = self.cities[i1]
        x2, y2 = self.cities[i2]

        line_id = self.canvas.create_line(x1, y1, x2, y2, fill=color, width=3)

        dist_val = math.dist((x1, y1), (x2, y2))
        self.canvas.tag_bind(line_id, "<Enter>",
                             lambda e, d=dist_val: self._show_segment_distance(d))
        self.canvas.tag_bind(line_id, "<Leave>",
                             lambda e: self._show_segment_distance(None))

    def _add_path_to_stored_paths(self, path, color="#ffa600", width=2):
        self.stored_paths.append((path[:], color, width))

    ################################################################
    # 9) Mode auto
    ################################################################
    def _start_auto(self):
        # S’il est déjà lancé, on ne relance pas.
        if self.auto_running:
            return

        self.auto_running = True

        ### CHANGEMENT : on efface l'état précédent ###
        self.best_distance = float('inf')
        self.best_path = []
        self.best_solution_saved = None
        self.stored_paths.clear()
        self._refresh_canvas()

        # On met à jour le label en haut
        self.auto_status_label.config(text="Mode Auto: ON")

        # On démarre la boucle automatique
        self._auto_loop()

    def _auto_loop(self):
        if not self.auto_running:
            return
        self._run_auto_iteration()

    def _run_auto_iteration(self):
        if not self.cities or self.is_animating:
            return

        # On vide les chemins stockés avant de tracer le nouveau
        self.stored_paths.clear()
        self._refresh_canvas()

        new_path = self._run_algorithm(self.algo_var.get())
        self._check_and_update_best(new_path, is_auto=True)

    def _stop_auto(self):
        self.auto_running = False
        # On met à jour le label
        self.auto_status_label.config(text="Mode Auto: OFF")

    ################################################################
    # 10) Dessiner la solution sauvegardée
    ################################################################
    def _draw_saved_solution(self, overlay=True):
        if not self.best_solution_saved:
            self._update_info_label("Aucune solution enregistrée à dessiner.")
            return
        path, dist = self.best_solution_saved

        if not overlay:
            self.stored_paths.clear()
            self._refresh_canvas()

        self._draw_path(path, color="#00FF00", width=3,
                        clear_first=False, store_in_list=True)
        self._update_info_label(f"Solution enregistrée dessinée (dist={dist:.2f}).")

    ################################################################
    # 11) DESSIN RAPIDE (avec survol segment)
    ################################################################
    def _draw_path(self, path, color="#ffa600", width=2,
                   clear_first=True, store_in_list=False):
        if clear_first:
            self._refresh_canvas()

        for i in range(len(path) - 1):
            idx1 = path[i]
            idx2 = path[i + 1]
            x1, y1 = self.cities[idx1]
            x2, y2 = self.cities[idx2]

            dist_val = math.dist((x1, y1), (x2, y2))
            line_id = self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
            self.canvas.tag_bind(line_id, "<Enter>",
                                 lambda e, d=dist_val: self._show_segment_distance(d))
            self.canvas.tag_bind(line_id, "<Leave>",
                                 lambda e: self._show_segment_distance(None))

        # Fermeture
        if len(path) > 1:
            x_last, y_last = self.cities[path[-1]]
            x_first, y_first = self.cities[path[0]]
            dist_val = math.dist((x_last, y_last), (x_first, y_first))
            line_id = self.canvas.create_line(x_last, y_last, x_first, y_first,
                                              fill=color, width=width)
            self.canvas.tag_bind(line_id, "<Enter>",
                                 lambda e, d=dist_val: self._show_segment_distance(d))
            self.canvas.tag_bind(line_id, "<Leave>",
                                 lambda e: self._show_segment_distance(None))

        if store_in_list:
            self.stored_paths.append((path[:], color, width))

    ################################################################
    # 12) Survol ville + distance segment
    ################################################################
    def _on_mouse_move(self, event):
        found_city = False
        for i, (cx, cy) in enumerate(self.cities):
            dx = event.x - cx
            dy = event.y - cy
            if dx*dx + dy*dy <= self.HOVER_RADIUS*self.HOVER_RADIUS:
                self.hover_label.config(
                    text=f"Survol: Ville {i+1} (X={cx}, Y={cy})"
                )
                found_city = True
                break

        if not found_city:
            self.hover_label.config(text=f"Survol: ({event.x}, {event.y})")

    def _show_segment_distance(self, dist_val):
        if dist_val is None:
            self.segment_label.config(text="Segment: -")
        else:
            self.segment_label.config(text=f"Segment: {dist_val:.2f}")
