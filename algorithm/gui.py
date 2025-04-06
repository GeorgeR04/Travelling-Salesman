import tkinter as tk
from tkinter import ttk
import random, math, threading
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ga import GeneticAlgorithm
from aco import AntColony
from algorithm.stats_logger import StatsLogger

class TSPApp(tk.Tk):
    HOVER_RADIUS = 10

    # ==============
    # FR: Initialise l'application TSP avec interface et variables.
    #
    # EN: Initializes the TSP application with interface and variables.
    # =========
    def __init__(self):
        super().__init__()
        self.title("TSP Synthwave - GA & ACO")
        self.state('zoomed')
        self.num_cities = 10
        self.cities = []
        self.best_distance = float('inf')
        self.best_path = []
        self.best_solution_saved = None
        self.current_path = []
        self.current_segment_index = 0
        self.is_animating = False
        self.auto_running = False
        self.stored_paths = []
        self.bg_image = None
        self.bg_image_resized = None
        self._load_background_image("IMG.png")
        self.stats_logger = StatsLogger()
        self.ga_instance = None
        self.ga_generator = None
        self._setup_ui()
        self._generate_cities()

    # ==============
    # FR: Charge une image de fond à partir d’un fichier.
    #
    # EN: Loads a background image from a file.
    # =========
    def _load_background_image(self, filename):
        try:
            img = Image.open(filename)
            self.bg_image = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Erreur de chargement de l'image: {e}")
            self.bg_image = None

    # ==============
    # FR: Applique les styles graphiques à l'interface utilisateur.
    #
    # EN: Applies UI styling to the application interface.
    # =========
    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        main_bg = "#282c34"
        text_fg = "#abb2bf"
        button_bg = "#3b4048"
        button_active_bg = "#4b515c"
        combo_bg = "#3b4048"
        labelframe_bg = "#2f2f2f"
        self.configure(bg=main_bg)
        style.configure("TFrame", background=main_bg)
        style.configure("TLabel", background=main_bg, foreground=text_fg, font=("Helvetica", 11))
        style.configure("TButton", background=button_bg, foreground=text_fg, font=("Helvetica", 10, "bold"), borderwidth=0)
        style.map("TButton", background=[("active", button_active_bg)], foreground=[("active", text_fg)])
        style.configure("TCombobox", fieldbackground=combo_bg, background=combo_bg, foreground=text_fg)
        style.map("TCombobox", fieldbackground=[("readonly", combo_bg)], foreground=[("readonly", text_fg)], background=[("readonly", combo_bg)])
        style.configure("TLabelframe", background=labelframe_bg, borderwidth=1)
        style.configure("TLabelframe.Label", background=labelframe_bg, foreground=text_fg, font=("Helvetica", 10, "bold"))

    # ==============
    # FR: Initialise l’interface graphique complète et ses composants.
    #
    # EN: Initializes the full user interface and its components.
    # =========
    def _setup_ui(self):
        self._setup_style()
        self.topbar = ttk.Frame(self, style="TFrame", height=50)
        self.topbar.pack(side=tk.TOP, fill="x")
        self.topbar.pack_propagate(False)
        ttk.Label(self.topbar, text="Mode Auto: ", style="TLabel").pack(side=tk.LEFT, padx=10, pady=5)
        self.auto_status_label = ttk.Label(self.topbar, text="OFF", foreground="#F00", style="TLabel")
        self.auto_status_label.pack(side=tk.LEFT, padx=10, pady=5)
        self.generation_label = ttk.Label(self.topbar, text="Génération: 0", style="TLabel")
        self.generation_label.pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Label(self.topbar, text="Max Générations:", style="TLabel").pack(side=tk.LEFT, padx=10, pady=5)
        self.max_gen_var = tk.IntVar(value=50)
        max_gen_slider = ttk.Scale(self.topbar, from_=10, to=500, orient=tk.HORIZONTAL, variable=self.max_gen_var)
        max_gen_slider.pack(side=tk.LEFT, padx=5, pady=5)
        self.max_gen_label = ttk.Label(self.topbar, text=str(self.max_gen_var.get()), style="TLabel")
        self.max_gen_label.pack(side=tk.LEFT, padx=5, pady=5)
        self.max_gen_var.trace_add("write", lambda *args: self.max_gen_label.config(text=str(self.max_gen_var.get())))
        ttk.Button(self.topbar, text="Visualisation", command=self._show_canvas_page).pack(side=tk.RIGHT, padx=5,                                                                                           pady=5)
        ttk.Button(self.topbar, text="Statistiques", command=self._show_stats_page).pack(side=tk.RIGHT, padx=5, pady=5)
        self.container = ttk.Frame(self, style="TFrame")
        self.container.pack(fill="both", expand=True)
        self.pages = {}
        self._create_canvas_page()
        self._create_stats_page()
        self._show_canvas_page()

    # ==============
    # FR: Crée la page principale de visualisation avec canvas et contrôles.
    #
    # EN: Creates the main visualization page with canvas and controls.
    # =========
    def _create_canvas_page(self):
        canvas_frame = ttk.Frame(self.container, style="TFrame")
        self.pages['canvas'] = canvas_frame
        main_frame = ttk.Frame(canvas_frame)
        main_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(main_frame, highlightthickness=0, background="#21252b")
        self.canvas.pack(side=tk.LEFT, fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<Motion>", self._on_mouse_move)
        controls = ttk.Frame(main_frame, width=250)
        controls.pack(side=tk.RIGHT, fill="y", padx=10, pady=10)
        ville_frame = ttk.Labelframe(controls, text="Gestion Villes")
        ville_frame.pack(fill="x", pady=10)
        ttk.Label(ville_frame, text="Nombre de villes", style="TLabel").pack(pady=5)
        self.num_cities_var = tk.IntVar(value=self.num_cities)
        num_cities_entry = ttk.Entry(ville_frame, textvariable=self.num_cities_var, width=10)
        num_cities_entry.pack(pady=5)
        ttk.Button(ville_frame, text="Générer Villes", command=self._generate_cities).pack(fill="x", pady=5)
        self.info_label = ttk.Label(ville_frame, text="Meilleure distance: -", style="TLabel")
        self.info_label.pack(pady=5)
        ttk.Label(controls, text="Choisir Algorithme:", style="TLabel").pack(pady=2)
        self.algo_var = tk.StringVar(value="GA")
        algo_menu = ttk.Combobox(controls, textvariable=self.algo_var, values=["GA", "ACO", "Hybride"], state="readonly")
        algo_menu.pack(fill="x", pady=5)
        ttk.Label(controls, text="Vitesse d'animation (ms):", style="TLabel").pack(pady=2)
        self.anim_speed_var = tk.IntVar(value=200)
        anim_speed_scale = ttk.Scale(controls, from_=50, to=500, variable=self.anim_speed_var)
        anim_speed_scale.pack(fill="x", pady=5)
        ttk.Button(controls, text="Lancer (animation)", command=self._run_once_thread).pack(fill="x", pady=5)
        ttk.Button(controls, text="Lancer Rapide", command=self._run_once_no_animation_thread).pack(fill="x", pady=5)
        auto_frame = ttk.Labelframe(controls, text="Mode Automatique")
        auto_frame.pack(fill="x", pady=10)
        ttk.Button(auto_frame, text="Démarrer", command=self._start_auto).pack(fill="x", pady=5)
        ttk.Button(auto_frame, text="Stop", command=self._stop_auto).pack(fill="x", pady=5)
        saved_frame = ttk.Labelframe(controls, text="Solution Enregistrée")
        saved_frame.pack(fill="x", pady=10)
        ttk.Button(saved_frame, text="Dessiner Best (Overlay)", command=lambda: self._draw_saved_solution(overlay=True)).pack(fill="x", pady=5)
        ttk.Button(saved_frame, text="Dessiner Best (Alone)", command=lambda: self._draw_saved_solution(overlay=False)).pack(fill="x", pady=5)
        self.hover_label = ttk.Label(controls, text="Survol: (x, y)", width=30, style="TLabel")
        self.hover_label.pack(pady=5)
        self.segment_label = ttk.Label(controls, text="Segment: -", width=30, style="TLabel")
        self.segment_label.pack(pady=5)

    # ==============
    # FR: Crée la page de visualisation des statistiques avec des graphiques.
    #
    # EN: Creates the statistics page with charts.
    # =========
    def _create_stats_page(self):
        stats_frame = ttk.Frame(self.container, style="TFrame")
        self.pages['stats'] = stats_frame
        algo_frame = ttk.Labelframe(stats_frame, text="Choix de l'algorithme")
        algo_frame.pack(pady=10, padx=10, fill="x")
        self.stats_algo_var = tk.StringVar(value="GA")
        selector = ttk.Combobox(algo_frame, textvariable=self.stats_algo_var, values=["GA", "ACO", "Hybride"], state="readonly")
        selector.pack(padx=10, pady=5)
        selector.bind("<<ComboboxSelected>>", lambda e: self._update_stats_graphs())
        self.stats_fig = plt.Figure(figsize=(12, 5), dpi=100, facecolor="#282c34")
        self.stats_ax1 = self.stats_fig.add_subplot(131, facecolor="#282c34")
        self.stats_ax2 = self.stats_fig.add_subplot(132, facecolor="#282c34")
        self.stats_ax3 = self.stats_fig.add_subplot(133, facecolor="#282c34")
        for ax in [self.stats_ax1, self.stats_ax2, self.stats_ax3]:
            ax.title.set_color("#abb2bf")
            ax.xaxis.label.set_color("#abb2bf")
            ax.yaxis.label.set_color("#abb2bf")
            ax.tick_params(axis='x', colors="#abb2bf")
            ax.tick_params(axis='y', colors="#abb2bf")
            for spine in ax.spines.values():
                spine.set_color("#abb2bf")
        self.canvas_stats = FigureCanvasTkAgg(self.stats_fig, master=stats_frame)
        self.canvas_stats.draw()
        self.canvas_stats.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    # ==============
    # FR: Affiche la page de visualisation (canvas).
    #
    # EN: Displays the visualization (canvas) page.
    # =========
    def _show_canvas_page(self):
        for page in self.pages.values():
            page.pack_forget()
        if 'canvas' in self.pages:
            self.pages['canvas'].pack(fill="both", expand=True)

    # ==============
    # FR: Affiche la page des statistiques et démarre la mise à jour.
    #
    # EN: Displays the statistics page and starts the update loop.
    # =========
    def _show_stats_page(self):
        if self.auto_running:
            self._stop_auto()
        for page in self.pages.values():
            page.pack_forget()
        if 'stats' in self.pages:
            self.pages['stats'].pack(fill="both", expand=True)
            self._start_stats_live_update()

    # ==============
    # FR: Lance la mise à jour continue des statistiques.
    #
    # EN: Starts live updating of statistics.
    # =========
    def _start_stats_live_update(self):
        self._update_stats_graphs()
        if self.pages['stats'].winfo_ismapped():
            self.after(1000, self._start_stats_live_update)

    # ==============
    # FR: Met à jour les graphiques de statistiques avec les dernières données.
    #
    # EN: Updates the statistics plots with the latest data.
    # =========
    def _update_stats_graphs(self):
        if not self.pages['stats'].winfo_ismapped():
            return
        algo = self.stats_algo_var.get()
        stats = self.stats_logger.get(algo)
        dists = stats.get("distances", [])
        times = stats.get("times", [])
        self.stats_ax1.clear()
        self.stats_ax1.set_title(f"{algo} - Distance par génération", color="#abb2bf")
        self.stats_ax1.set_xlabel("Génération", color="#abb2bf")
        self.stats_ax1.set_ylabel("Distance", color="#abb2bf")
        if dists:
            x_vals = list(range(1, len(dists) + 1))
            self.stats_ax1.plot(x_vals, dists, marker="o", color="#f72585")
        else:
            self.stats_ax1.text(0.5, 0.5, "Pas de données", horizontalalignment='center', color="#abb2bf")
        self.stats_ax2.clear()
        self.stats_ax2.set_title(f"{algo} - Temps par génération", color="#abb2bf")
        self.stats_ax2.set_xlabel("Génération", color="#abb2bf")
        self.stats_ax2.set_ylabel("Temps (s)", color="#abb2bf")
        if times:
            x_vals = list(range(1, len(times) + 1))
            self.stats_ax2.plot(x_vals, times, marker="x", color="#4cc9f0")
        else:
            self.stats_ax2.text(0.5, 0.5, "Pas de données", horizontalalignment='center', color="#abb2bf")
        all_stats = self.stats_logger.get_all()
        self.stats_ax3.clear()
        self.stats_ax3.set_title("Distribution des distances", color="#abb2bf")
        self.stats_ax3.set_xlabel("Distance", color="#abb2bf")
        self.stats_ax3.set_ylabel("Fréquence", color="#abb2bf")
        colors = {"GA": "#f72585", "ACO": "#4cc9f0", "Hybride": "#3a0ca3"}
        for algo_name, data in all_stats.items():
            if data["distances"]:
                self.stats_ax3.hist(data["distances"], bins=10, alpha=0.5, label=algo_name, color=colors.get(algo_name, "#abb2bf"))
        self.stats_ax3.legend(facecolor="#282c34", labelcolor="#abb2bf")
        self.canvas_stats.draw()

    # ==============
    # FR: Gère le redimensionnement du canvas.
    #
    # EN: Handles canvas resizing.
    # =========
    def _on_canvas_resize(self, event):
        self._refresh_canvas()

    # ==============
    # FR: Génère un nouvel ensemble de villes sur le canvas.
    #
    # EN: Generates a new set of cities on the canvas.
    # =========
    def _generate_cities(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        margin = 50
        if w < 100:
            w = 1200
        if h < 100:
            h = 800
        num = self.num_cities_var.get()
        self.cities = [(random.randint(margin, w - margin), random.randint(margin, h - margin))
                       for _ in range(num)]
        self.best_distance = float('inf')
        self.best_path = []
        self.best_solution_saved = None
        self.current_path = []
        self.current_segment_index = 0
        self.is_animating = False
        self.stored_paths.clear()
        self.ga_generator = None
        self.ga_instance = None
        self.stats_logger.reset()
        self.canvas.delete("all")
        self._refresh_canvas()
        self._update_info_label("Nouvelles villes générées.")

    # ==============
    # FR: Dessine les villes sur le canvas.
    #
    # EN: Draws the cities on the canvas.
    # =========
    def _draw_cities(self):
        for i, (x, y) in enumerate(self.cities):
            r = 5
            self.canvas.create_oval(x - r, y - r, x + r, y + r,fill="#ffffff", outline="#000000", width=1)
            self.canvas.create_text(x, y - 12, text=str(i + 1),fill="#ffffff", font=("Helvetica", 9, "bold"))

    # ==============
    # FR: Rafraîchit complètement le canvas.
    #
    # EN: Fully refreshes the canvas.
    # =========
    def _refresh_canvas(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        margin = 50
        self._draw_bg_image(margin, margin, w - margin, h - margin)
        self._draw_axes_with_grads(w, h, margin)
        self._draw_cities()
        for (path, color, width) in self.stored_paths:
            self._draw_path(path, color=color, width=width, clear_first=False, store_in_list=False)

    # ==============
    # FR: Dessine l'image de fond dans une zone spécifiée.
    #
    # EN: Draws the background image in a specified area.
    # =========
    def _draw_bg_image(self, x1, y1, x2, y2):
        if self.bg_image:
            zone_width = x2 - x1
            zone_height = y2 - y1
            try:
                img_pil = ImageTk.getimage(self.bg_image)
                resized = img_pil.resize((zone_width, zone_height), Image.Resampling.LANCZOS)
                self.bg_image_resized = ImageTk.PhotoImage(resized)
                self.canvas.create_image(x1, y1, anchor="nw", image=self.bg_image_resized)
            except Exception as e:
                print(f"Erreur lors du redimensionnement de l'image: {e}")
                self.canvas.create_image(x1, y1, anchor="nw", image=self.bg_image)

    # ==============
    # FR: Dessine les axes et les graduations sur le canvas.
    #
    # EN: Draws axes and ticks on the canvas.
    # =========
    def _draw_axes_with_grads(self, w, h, margin, step=50):
        x_start, x_end = margin, w - margin
        y_start, y_end = h - margin, margin
        for x_pos in range(x_start, x_end + 1, step):
            self.canvas.create_line(x_pos, y_end, x_pos, y_start,fill="white", width=1, stipple="gray75")
        for y_pos in range(y_end, y_start + 1, step):
            self.canvas.create_line(x_start, y_pos, x_end, y_pos,fill="white", width=1, stipple="gray75")
        self.canvas.create_line(x_start, y_start, x_end, y_start,fill="white", width=2)
        self.canvas.create_line(x_start, y_start, x_start, y_end,fill="white", width=2)
        for x_pos in range(x_start, x_end + 1, step):
            self.canvas.create_line(x_pos, y_start - 5, x_pos, y_start + 5,fill="white", width=2)
            label_val = x_pos - x_start
            self.canvas.create_text(x_pos, y_start + 12, text=str(label_val),fill="white", font=("Helvetica", 8))
        for y_pos in range(y_end, y_start + 1, step):
            self.canvas.create_line(x_start - 5, y_pos, x_start + 5, y_pos,fill="white", width=2)
            label_val = y_start - y_pos
            self.canvas.create_text(x_start - 8, y_pos, text=str(label_val),fill="white", font=("Helvetica", 8), anchor="e")
        self.canvas.create_text(x_end + 15, y_start, text="X",fill="white", font=("Helvetica", 9), anchor="nw")
        self.canvas.create_text(x_start, y_end - 15, text="Y",fill="white", font=("Helvetica", 9), anchor="sw")

    # ==============
    # FR: Calcule la distance totale d'un chemin donné.
    #
    # EN: Calculates the total distance of a given path.
    # =========
    def _compute_distance(self, path):
        dist = 0
        for i in range(-1, len(path) - 1):
            x1, y1 = self.cities[path[i]]
            x2, y2 = self.cities[path[i + 1]]
            dist += math.dist((x1, y1), (x2, y2))
        return dist

    # ==============
    # FR: Met à jour l'étiquette d'information avec la meilleure distance.
    #
    # EN: Updates the info label with the best distance.
    # =========
    def _update_info_label(self, msg=None):
        dist_txt = f"Meilleure distance: {self.best_distance:.2f}" if self.best_distance < float('inf') else "Meilleure distance: -"
        text = dist_txt if not msg else f"{dist_txt}\n{msg}"
        self.info_label.config(text=text)

    # ==============
    # FR: Lance un algorithme (avec animation) dans un thread.
    #
    # EN: Starts an algorithm (with animation) in a thread.
    # =========
    def _run_once_thread(self):
        self.stored_paths.clear()
        self._refresh_canvas()
        if not self.cities or self.is_animating:
            return
        if self.algo_var.get() == "GA":
            self.next_ga_generation(skip_animation=False, is_auto=False)
        else:
            thread = threading.Thread(target=self._run_algorithm_background, args=(self.algo_var.get(), False))
            thread.start()

    # ==============
    # FR: Lance un algorithme rapidement sans animation.
    #
    # EN: Starts an algorithm quickly without animation.
    # =========
    def _run_once_no_animation_thread(self):
        self.stored_paths.clear()
        self._refresh_canvas()
        if not self.cities:
            return
        if self.algo_var.get() == "GA":
            self.next_ga_generation(skip_animation=True, is_auto=False)
        else:
            thread = threading.Thread(target=self._run_algorithm_background, args=(self.algo_var.get(), False, True))
            thread.start()

    # ==============
    # FR: Exécute un algorithme en arrière-plan.
    #
    # EN: Runs an algorithm in the background.
    # =========
    def _run_algorithm_background(self, algo_name, is_auto, skip_animation=False):
        new_path = self._run_algorithm(algo_name)
        self.after(0, lambda: self._check_and_update_best(new_path, is_auto=is_auto, skip_animation=skip_animation))

    # ==============
    # FR: Exécute un algorithme (GA, ACO ou Hybride) et retourne le meilleur chemin.
    #
    # EN: Runs an algorithm (GA, ACO or Hybrid) and returns the best path.
    # =========
    def _run_algorithm(self, algo_name):
        if algo_name == "GA":
            ga = GeneticAlgorithm(self.cities, logger=self.stats_logger)
            best_path, _ = ga.run()
            return best_path
        elif algo_name == "ACO":
            aco = AntColony(self.cities, logger=self.stats_logger)
            best_path, _ = aco.run()
            return best_path
        else:
            ga = GeneticAlgorithm(self.cities, logger=self.stats_logger)
            ga_path, _ = ga.run()
            aco = AntColony(self.cities, initial_path=ga_path, logger=self.stats_logger)
            aco_path, _ = aco.run()
            return aco_path

    # ==============
    # FR: Exécute une génération de l’algorithme génétique (GA).
    #
    # EN: Executes one generation of the genetic algorithm (GA).
    # =========
    def next_ga_generation(self, skip_animation=False, is_auto=False):
        if self.is_animating:
            self.after(500, lambda: self.next_ga_generation(skip_animation=skip_animation, is_auto=is_auto))
            return
        if not self.ga_generator:
            max_gen = self.max_gen_var.get()
            self.ga_instance = GeneticAlgorithm(
                self.cities, pop_size=50, max_gen=max_gen, mutation_rate=0.05, elitism_count=10,
                logger=self.stats_logger
            )
            self.ga_generator = self.ga_instance.run_step_by_step()
        try:
            result = next(self.ga_generator)
            self.generation_label.config(text=f"Génération: {result['generation']}")
            self._update_info_label(
                f"Génération {result['generation']}: Meilleure distance = {result['best_distance']:.2f} (durée {result['duration']:.2f}s)"
            )
            self._update_stats_graphs()
            self._check_and_update_best(result["best_path"], is_auto=is_auto, skip_animation=skip_animation)
            max_gen = self.max_gen_var.get()
            if result['generation'] >= max_gen - 1:
                self.generation_label.config(text="Fin des générations GA.")
                self.after(1000, self._stop_auto)
                self.ga_generator = None
                self.ga_instance = None
            else:
                if is_auto and self.auto_running and skip_animation:
                    self.after(1000, self._clear_and_next_ga, skip_animation, is_auto)
        except StopIteration:
            self.generation_label.config(text="Fin des générations GA.")
            self.after(1000, self._stop_auto)
            self.ga_generator = None
            self.ga_instance = None

    # ==============
    # FR: Vide le canvas et lance une nouvelle génération GA.
    #
    # EN: Clears the canvas and launches a new GA generation.
    # =========
    def _clear_and_next_ga(self, skip_animation, is_auto):
        self.stored_paths.clear()
        self.canvas.delete("all")
        self._refresh_canvas()
        if self.auto_running:
            self.next_ga_generation(skip_animation=skip_animation, is_auto=is_auto)

    # ==============
    # FR: Vérifie et met à jour la meilleure solution trouvée.
    #
    # EN: Checks and updates the best found solution.
    # =========
    def _check_and_update_best(self, path, is_auto=False, skip_animation=False):
        dist = self._compute_distance(path)

        self._refresh_canvas()
        self.current_path = path
        self.current_segment_index = 0

        if not skip_animation:
            self.is_animating = True
            self._update_info_label(f"Chemin de génération (dist={dist:.2f})")
            self._animate_path(is_auto=is_auto)
        else:
            self.is_animating = False
            self._draw_path(path, color="#f72585", width=3, clear_first=False, store_in_list=True)
            self._update_info_label(f"Chemin de génération (Rapide) (dist={dist:.2f})")
            if is_auto and self.auto_running:
                self.after(5000, self._auto_loop)

        if dist < self.best_distance:
            self.best_distance = dist
            self.best_path = path
            self.best_solution_saved = (path[:], dist)

    # ==============
    # FR: Anime le tracé d’un chemin étape par étape.
    #
    # EN: Animates the step-by-step drawing of a path.
    # =========
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
                # Attendre 1 seconde après le tracé complet avant de passer à la prochaine génération
                self.after(1000, self._clear_and_next_ga, False, True)
            return
        if seg_idx > 0:
            self._draw_synthwave_line(path[seg_idx - 1], path[seg_idx], seg_idx - 1)
        self.current_segment_index += 1
        speed = self.anim_speed_var.get()
        self.after(speed, lambda: self._animate_path(is_auto=is_auto))

    # ==============
    # FR: Dessine un segment de type synthwave entre deux villes.
    #
    # EN: Draws a synthwave-style segment between two cities.
    # =========
    def _draw_synthwave_line(self, i1, i2, seg_idx):
        palette = ["#f72585", "#b5179e", "#7209b7", "#3a0ca3", "#4361ee", "#4cc9f0"]
        color = palette[seg_idx % len(palette)]
        x1, y1 = self.cities[i1]
        x2, y2 = self.cities[i2]
        line_id = self.canvas.create_line(x1, y1, x2, y2, fill=color, width=3)
        dist_val = math.dist((x1, y1), (x2, y2))
        self.canvas.tag_bind(line_id, "<Enter>", lambda e, d=dist_val: self._show_segment_distance(d))
        self.canvas.tag_bind(line_id, "<Leave>", lambda e: self._show_segment_distance(None))

    # ==============
    # FR: Ajoute un chemin à la liste des chemins affichés.
    #
    # EN: Adds a path to the list of displayed paths.
    # =========
    def _add_path_to_stored_paths(self, path, color="#ffa600", width=2):
        self.stored_paths.append((path[:], color, width))

    # ==============
    # FR: Démarre le mode automatique d'exécution de l'algorithme.
    #
    # EN: Starts the automatic execution mode of the algorithm.
    # =========
    def _start_auto(self):
        if self.auto_running:
            return
        self.auto_running = True
        self.best_distance = float('inf')
        self.best_path = []
        self.best_solution_saved = None
        self.stored_paths.clear()
        self._refresh_canvas()
        self.auto_status_label.config(text="ON", foreground="#0F0")
        if self.algo_var.get() == "GA":
            self.next_ga_generation(skip_animation=False, is_auto=True)
        else:
            self._auto_loop()

    # ==============
    # FR: Boucle interne du mode automatique.
    #
    # EN: Internal loop of automatic mode.
    # =========
    def _auto_loop(self):
        if not self.auto_running:
            return
        self._run_auto_iteration()

    # ==============
    # FR: Exécute une itération automatique de l'algorithme.
    #
    # EN: Executes one automatic iteration of the algorithm.
    # =========
    def _run_auto_iteration(self):
        if not self.cities or self.is_animating:
            return
        self.stored_paths.clear()
        self._refresh_canvas()
        if self.algo_var.get() == "GA":
            self.next_ga_generation(skip_animation=True, is_auto=True)
        else:
            thread = threading.Thread(target=self._run_algorithm_background, args=(self.algo_var.get(), True, True))
            thread.start()

    # ==============
    # FR: Stoppe l’exécution automatique de l’algorithme.
    #
    # EN: Stops the automatic execution of the algorithm.
    # =========
    def _stop_auto(self):
        self.auto_running = False
        self.auto_status_label.config(text="OFF", foreground="#F00")
        self.ga_generator = None
        self.ga_instance = None

    # ==============
    # FR: Dessine la meilleure solution enregistrée.
    #
    # EN: Draws the saved best solution.
    # =========
    def _draw_saved_solution(self, overlay=True):
        if not self.best_solution_saved:
            self._update_info_label("Aucune solution enregistrée à dessiner.")
            return
        path, dist = self.best_solution_saved
        if not overlay:
            self.stored_paths.clear()
            self._refresh_canvas()
        self._draw_path(path, color="#00FF00", width=3, clear_first=False, store_in_list=True)
        self._update_info_label(f"Solution enregistrée dessinée (dist={dist:.2f}).")

    # ==============
    # FR: Dessine un chemin complet rapidement avec survol interactif.
    #
    # EN: Quickly draws a full path with interactive hover effects.
    # =========
    def _draw_path(self, path, color="#ffa600", width=2, clear_first=True, store_in_list=False):
        if clear_first:
            self._refresh_canvas()
        for i in range(len(path) - 1):
            idx1 = path[i]
            idx2 = path[i + 1]
            x1, y1 = self.cities[idx1]
            x2, y2 = self.cities[idx2]
            dist_val = math.dist((x1, y1), (x2, y2))
            line_id = self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
            self.canvas.tag_bind(line_id, "<Enter>", lambda e, d=dist_val: self._show_segment_distance(d))
            self.canvas.tag_bind(line_id, "<Leave>", lambda e: self._show_segment_distance(None))
        if len(path) > 1:
            x_last, y_last = self.cities[path[-1]]
            x_first, y_first = self.cities[path[0]]
            dist_val = math.dist((x_last, y_last), (x_first, y_first))
            line_id = self.canvas.create_line(x_last, y_last, x_first, y_first, fill=color, width=width)
            self.canvas.tag_bind(line_id, "<Enter>", lambda e, d=dist_val: self._show_segment_distance(d))
            self.canvas.tag_bind(line_id, "<Leave>", lambda e: self._show_segment_distance(None))
        if store_in_list:
            self.stored_paths.append((path[:], color, width))

    # ==============
    # FR: Gère l’événement de survol de la souris sur le canvas.
    #
    # EN: Handles mouse hover events over the canvas.
    # =========
    def _on_mouse_move(self, event):
        found_city = False
        for i, (cx, cy) in enumerate(self.cities):
            if (event.x - cx) ** 2 + (event.y - cy) ** 2 <= self.HOVER_RADIUS ** 2:
                self.hover_label.config(text=f"Survol: Ville {i + 1} (X={cx}, Y={cy})")
                found_city = True
                break
        if not found_city:
            self.hover_label.config(text=f"Survol: ({event.x}, {event.y})")

    # ==============
    # FR: Affiche la distance du segment survolé.
    #
    # EN: Displays the hovered segment's distance.
    # =========
    def _show_segment_distance(self, dist_val):
        if dist_val is None:
            self.segment_label.config(text="Segment: -")
        else:
            self.segment_label.config(text=f"Segment: {dist_val:.2f}")
