"""Cutter: pick a square crop of an image or GIF and preview it at 64x64 (host).

Usage (host, from the repository root): uv run cutter_project/cutter_app.py
See README.md, "Cutter" section, and ROADMAP.md Iteration 3 for the plan.
"""

import tkinter as tk
from tkinter import ttk

TITLE = "Cutter 64x64"
# Each result pixel drawn as a 5x5 block, so the 64x64 preview is easy to judge.
PREVIEW_SCALE = 5
PREVIEW_SIZE = 64 * PREVIEW_SCALE
# Lets Python notice Ctrl+C in the terminal: tkinter's main loop otherwise
# blocks signal handling until the next window event.
SIGNAL_POLL_MS = 200


class CutterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title(TITLE)
        root.minsize(900, 500)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        self._build_file_pane()
        self._build_source_pane()
        self._build_result_pane()

    def _build_file_pane(self) -> None:
        pane = ttk.Frame(self.root, padding=8)
        pane.grid(row=0, column=0, sticky="ns")
        pane.rowconfigure(1, weight=1)
        pane.rowconfigure(3, weight=1)

        ttk.Label(pane, text="Images").grid(row=0, column=0, sticky="w")
        self.image_list = tk.Listbox(pane, width=30, exportselection=False)
        self.image_list.grid(row=1, column=0, sticky="nsew", pady=(0, 8))

        ttk.Label(pane, text="GIFs").grid(row=2, column=0, sticky="w")
        self.gif_list = tk.Listbox(pane, width=30, exportselection=False)
        self.gif_list.grid(row=3, column=0, sticky="nsew")

    def _build_source_pane(self) -> None:
        pane = ttk.Frame(self.root, padding=8)
        pane.grid(row=0, column=1, sticky="nsew")
        pane.columnconfigure(0, weight=1)
        pane.rowconfigure(1, weight=1)

        ttk.Label(pane, text="Source").grid(row=0, column=0, sticky="w")
        self.source_canvas = tk.Canvas(pane, background="#202020", highlightthickness=0)
        self.source_canvas.grid(row=1, column=0, sticky="nsew")

    def _build_result_pane(self) -> None:
        pane = ttk.Frame(self.root, padding=8)
        pane.grid(row=0, column=2, sticky="n")

        ttk.Label(pane, text="Result (64x64)").grid(row=0, column=0, sticky="w")
        self.result_canvas = tk.Canvas(
            pane,
            width=PREVIEW_SIZE,
            height=PREVIEW_SIZE,
            background="#000000",
            highlightthickness=0,
        )
        self.result_canvas.grid(row=1, column=0)

        # Disabled until saving exists (ROADMAP Iteration 3, step 6).
        self.save_button = ttk.Button(pane, text="Save", state="disabled")
        self.save_button.grid(row=2, column=0, sticky="ew", pady=(8, 0))


def main() -> None:
    root = tk.Tk()
    CutterApp(root)

    def keep_signals_alive() -> None:
        root.after(SIGNAL_POLL_MS, keep_signals_alive)

    keep_signals_alive()
    try:
        root.mainloop()
    except KeyboardInterrupt:
        root.destroy()


if __name__ == "__main__":
    main()
