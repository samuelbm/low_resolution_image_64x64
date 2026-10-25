"""Cutter: pick a square crop of an image or GIF and preview it at 64x64 (host).

Usage (host, from the repository root): uv run cutter_project/cutter_app.py
See README.md, "Cutter" section, and ROADMAP.md Iteration 3 for the plan.
"""

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from media import (
    GIF_SUFFIXES,
    IMAGE_SUFFIXES,
    Media,
    Square,
    centered_square,
    crop_result,
    fit_size,
    list_files,
    load_media,
)
from PIL import Image, ImageTk

TITLE = "Cutter 64x64"
SOURCE_DIR = Path(__file__).resolve().parent.parent / "source_files"
# Each result pixel drawn as a 5x5 block, so the 64x64 preview is easy to judge.
PREVIEW_SCALE = 5
PREVIEW_SIZE = 64 * PREVIEW_SCALE
# Lets Python notice Ctrl+C in the terminal: tkinter's main loop otherwise
# blocks signal handling until the next window event.
SIGNAL_POLL_MS = 200
# While the window is being resized, wait for it to settle before rescaling
# every frame again.
RESIZE_DELAY_MS = 100
SQUARE_COLOR = "red"
SQUARE_WIDTH = 2


class CutterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title(TITLE)
        root.minsize(900, 500)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        self.media: Media | None = None
        # Tk only shows a PhotoImage while Python holds a reference to it.
        self.display_frames: list[ImageTk.PhotoImage] = []
        self.result_frames: list[ImageTk.PhotoImage] = []
        self.square: Square | None = None
        self.frame_index = 0
        self.animation_job: str | None = None
        self.resize_job: str | None = None

        self._build_file_pane()
        self._build_source_pane()
        self._build_result_pane()
        self._fill_file_lists()

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

        self.image_list.bind(
            "<<ListboxSelect>>", lambda _e: self._on_select(self.image_list)
        )
        self.gif_list.bind(
            "<<ListboxSelect>>", lambda _e: self._on_select(self.gif_list)
        )

    def _build_source_pane(self) -> None:
        pane = ttk.Frame(self.root, padding=8)
        pane.grid(row=0, column=1, sticky="nsew")
        pane.columnconfigure(0, weight=1)
        pane.rowconfigure(1, weight=1)

        self.source_label = ttk.Label(pane, text="Source")
        self.source_label.grid(row=0, column=0, sticky="w")
        self.source_canvas = tk.Canvas(pane, background="#202020", highlightthickness=0)
        self.source_canvas.grid(row=1, column=0, sticky="nsew")
        self.source_item = self.source_canvas.create_image(0, 0, anchor="nw")
        self.square_item = self.source_canvas.create_rectangle(
            0, 0, 0, 0, outline=SQUARE_COLOR, width=SQUARE_WIDTH, state="hidden"
        )
        self.source_canvas.bind("<Configure>", self._on_canvas_resize)

    def _build_result_pane(self) -> None:
        pane = ttk.Frame(self.root, padding=8)
        pane.grid(row=0, column=2, sticky="n")

        self.result_label = ttk.Label(pane, text="Result (64x64)")
        self.result_label.grid(row=0, column=0, sticky="w")
        self.result_canvas = tk.Canvas(
            pane,
            width=PREVIEW_SIZE,
            height=PREVIEW_SIZE,
            background="#000000",
            highlightthickness=0,
        )
        self.result_canvas.grid(row=1, column=0)
        self.result_item = self.result_canvas.create_image(0, 0, anchor="nw")

        # Disabled until saving exists (ROADMAP Iteration 3, step 6).
        self.save_button = ttk.Button(pane, text="Save", state="disabled")
        self.save_button.grid(row=2, column=0, sticky="ew", pady=(8, 0))

    def _fill_file_lists(self) -> None:
        self.image_paths = list_files(SOURCE_DIR / "images", IMAGE_SUFFIXES)
        self.gif_paths = list_files(SOURCE_DIR / "gifs", GIF_SUFFIXES)
        for path in self.image_paths:
            self.image_list.insert("end", path.name)
        for path in self.gif_paths:
            self.gif_list.insert("end", path.name)

    def _on_select(self, listbox: tk.Listbox) -> None:
        selection = listbox.curselection()
        if not selection:
            return
        # One file at a time: picking in one list clears the other.
        if listbox is self.image_list:
            self.gif_list.selection_clear(0, "end")
            path = self.image_paths[selection[0]]
        else:
            self.image_list.selection_clear(0, "end")
            path = self.gif_paths[selection[0]]
        self._show(path)

    def _show(self, path: Path) -> None:
        self._stop_animation()
        try:
            self.media = load_media(path)
        except (OSError, ValueError) as error:
            self.media = None
            self.square = None
            self.display_frames = []
            self.result_frames = []
            self.source_canvas.itemconfigure(self.source_item, image="")
            self.source_canvas.itemconfigure(self.square_item, state="hidden")
            self.result_canvas.itemconfigure(self.result_item, image="")
            self.source_label.configure(text=f"Cannot open {path.name}: {error}")
            self.result_label.configure(text="Result (64x64)")
            return

        w, h = self.media.size
        frames = len(self.media.frames)
        details = f"{w}x{h}" + (f", {frames} frames" if self.media.is_animated else "")
        self.source_label.configure(text=f"{path.name} ({details})")
        self.square = centered_square(self.media.size)
        self._update_result()
        self._rescale()

    def _update_result(self) -> None:
        """Recompute the 64x64 result of every frame for the current square."""
        if self.media is None or self.square is None:
            return
        self.result_frames = [
            # NEAREST: each result pixel becomes a sharp block, like an LED.
            ImageTk.PhotoImage(
                crop_result(frame, self.square).resize(
                    (PREVIEW_SIZE, PREVIEW_SIZE), Image.Resampling.NEAREST
                )
            )
            for frame in self.media.frames
        ]
        left, top, side = self.square
        self.result_label.configure(
            text=f"Result (64x64): {side}x{side} px at ({left}, {top})"
        )

    def _draw_square(self) -> None:
        """Place the red square over the displayed picture."""
        if self.media is None or self.square is None:
            return
        # Same factor on both axes, since the picture keeps its ratio.
        scale = self.display_size[0] / self.media.size[0]
        left, top, side = self.square
        x0 = self.display_offset[0] + left * scale
        y0 = self.display_offset[1] + top * scale
        self.source_canvas.coords(
            self.square_item, x0, y0, x0 + side * scale, y0 + side * scale
        )
        self.source_canvas.itemconfigure(self.square_item, state="normal")
        self.source_canvas.tag_raise(self.square_item)

    def _on_canvas_resize(self, _event: tk.Event) -> None:
        if self.resize_job is not None:
            self.root.after_cancel(self.resize_job)
        self.resize_job = self.root.after(RESIZE_DELAY_MS, self._rescale)

    def _rescale(self) -> None:
        """Fit the current file into the centre pane, keeping its ratio."""
        self.resize_job = None
        if self.media is None:
            return
        box = (self.source_canvas.winfo_width(), self.source_canvas.winfo_height())
        if box[0] < 2 or box[1] < 2:  # window not drawn yet
            return
        size = fit_size(self.media.size, box)
        # Shrinking: LANCZOS keeps detail. Enlarging a small file: NEAREST keeps
        # its pixels sharp instead of blurring them.
        shrinking = size[0] < self.media.size[0]
        resample = Image.Resampling.LANCZOS if shrinking else Image.Resampling.NEAREST
        self.display_frames = [
            ImageTk.PhotoImage(frame.resize(size, resample))
            for frame in self.media.frames
        ]
        # Centred in the pane; the red square is mapped through this offset.
        self.display_offset = ((box[0] - size[0]) // 2, (box[1] - size[1]) // 2)
        self.display_size = size
        self.source_canvas.coords(self.source_item, *self.display_offset)
        self._draw_square()

        self._stop_animation()
        self.frame_index = 0
        self._draw_frame()

    def _draw_frame(self) -> None:
        self.source_canvas.itemconfigure(
            self.source_item, image=self.display_frames[self.frame_index]
        )
        # Both panes show the same frame, so the result plays in step.
        if self.frame_index < len(self.result_frames):
            self.result_canvas.itemconfigure(
                self.result_item, image=self.result_frames[self.frame_index]
            )
        if self.media is not None and self.media.is_animated:
            delay = self.media.durations_ms[self.frame_index]
            self.animation_job = self.root.after(delay, self._next_frame)

    def _next_frame(self) -> None:
        self.frame_index = (self.frame_index + 1) % len(self.display_frames)
        self._draw_frame()

    def _stop_animation(self) -> None:
        if self.animation_job is not None:
            self.root.after_cancel(self.animation_job)
            self.animation_job = None


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
