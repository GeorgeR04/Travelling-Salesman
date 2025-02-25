# main.py

import tkinter as tk
from tkinter import simpledialog
from gui import TSPGUI

def main():
    root = tk.Tk()
    root.withdraw()  # On cache la fenêtre pendant la saisie

    # Boîte de dialogue pour demander le nombre de villes
    num_cities = simpledialog.askinteger(
        "Configuration",
        "Combien de villes souhaitez-vous générer ?",
        minvalue=1,
        maxvalue=999
    )
    if num_cities is None:
        num_cities = 10  # par défaut si l'utilisateur annule

    root.deiconify()  # Ré-affiche la fenêtre

    app = TSPGUI(root, num_cities=num_cities)
    root.mainloop()


if __name__ == "__main__":
    main()
