# main.py

import tkinter as tk
from tkinter import simpledialog
from gui import TSPGUI

def main():
    root = tk.Tk()
    root.withdraw()  # On masque la fenêtre pendant la saisie

    num_cities = simpledialog.askinteger(
        "Configuration",
        "Combien de villes souhaitez-vous générer ?",
        minvalue=2
    )
    if num_cities is None:
        num_cities = 10  # par défaut si l'utilisateur annule

    root.deiconify()  # On ré-affiche la fenêtre

    app = TSPGUI(root, num_cities=num_cities)
    root.mainloop()

if __name__ == "__main__":
    main()
