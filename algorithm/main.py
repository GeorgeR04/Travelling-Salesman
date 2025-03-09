import tkinter as tk
from tkinter import simpledialog
from gui import TSPApp

def main():

    root = tk.Tk()
    root.withdraw()


    num_cities = simpledialog.askinteger(
        "Configuration",
        "Combien de villes souhaitez-vous générer ?",
        minvalue=2
    ) or 10


    root.destroy()


    app = TSPApp(num_cities=num_cities)
    app.mainloop()

if __name__ == "__main__":
    main()
