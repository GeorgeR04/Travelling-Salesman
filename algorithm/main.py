import tkinter as tk
from tkinter import simpledialog
from gui import TSPApp

def main():

    root = tk.Tk()
    root.withdraw()


    root.destroy()


    app = TSPApp()
    app.mainloop()

if __name__ == "__main__":
    main()
