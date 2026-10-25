Living plan. Updated at the end of every work session. Status: [ ] to do, [~] in progress, [x] done.

Iteration 4: Show the selection at boot (Pi Zero 2W)

Goal: when the Zero powers on, the panel shows what object_files/selection.txt names, with no SSH needed. Changing the selection over SSH switches the panel within about a second. A systemd service starts the player at boot and restarts it after a crash, unless stopped (D-013, D-014). Built one step at a time; after each step Claude stops, the user reviews and commits (D-008).

In progress
 [ ] Step 1 (next).

To do
 [ ] Step 1: rgb_led_matrix/play_selection.py reads object_files/selection.txt (first line that is not empty or a # comment; path relative to the repo root, e.g. object_files/gifs/floating_eye_64x64bits.gif) and shows a PNG statically or plays a GIF, reusing show_image.py / show_gif.py. Missing, empty or bad selection (not 64x64, unknown type, outside the repo): clear the panel, print why, keep waiting; never crash.
 [ ] Step 2: Switch on change. About once a second the player checks selection.txt; when it changes it loads the new file and switches without restarting. Decide here how it keeps reading files after the library drops root (drop_privileges = False for this player, or readable content folder).
 [ ] Step 3: Test by hand on the Zero: sudo ~/rgbmatrix/.venv/bin/python rgb_led_matrix/play_selection.py, edit selection.txt over SSH, watch the panel switch.
 [ ] Step 4: systemd service. systemd/rgbmatrix-display.service in the repo (runs as root, Restart=always, no network needed, Python cache kept out of the repo). Install with sudo cp + systemctl daemon-reload + systemctl enable --now. README section "Display service" with the everyday commands (status, journalctl, stop/start, disable). Note: while the service runs the panel is taken; stop it before running other scripts by hand.
 [ ] Step 5: Protect the SD card against power cuts, since the device will be unplugged without shutdown. Options: read-only overlay (but then selection.txt and new images are lost at reboot unless object_files/ sits on a separate writable partition), or a shutdown button on GPIO3 (recheck it is free with adafruit-hat-pwm). Decide, then record a DECISIONS entry.

Notes
 selection.txt lives only on the Zero (git-ignored, skipped by scripts/sync_to_zero.sh). Edit it over SSH, e.g. nano ~/low_resolution_image_64x64/object_files/selection.txt.
 On another Wi-Fi network the Zero still plays the selection, but SSH needs that network configured on the Zero.

Iteration 3: Cutter app (host): crop and preview images/GIFs for 64x64

Goal: a desktop app in cutter_project/ to pick a source image or GIF, choose a square crop with a red square, preview the 64x64 result and save it to object_files/ (see README, "Cutter" section). Built one step at a time; after each step Claude stops, the user reviews and commits (D-008).

Technical frame: tkinter (stdlib, already in the uv-managed Python 3.13) + Pillow, no new dependency. Host only, nothing goes to the Pis. Entry point: uv run cutter_project/cutter_app.py. Crop and resize code shared with cutter_project/resize_to_64x64.py (LANCZOS, same _64x64bits suffix).

In progress
 [~] Step 7: written (cutter_app.py + media.py), waiting for user review and commit.

To do
 [x] Step 1: Empty app. A window opens with three panes (left: file lists, centre: source, right: result) and a Save button; nothing works yet. Closes cleanly.
 [x] Step 2: Browse and view. The left pane lists source_files/images/ and source_files/gifs/ in two separate lists. Clicking a name shows the file in the centre pane, scaled to fit; GIFs play with their own frame timing.
 [x] Step 3: Fixed square and result. A red square of 64x64 source pixels sits in the centre of the image/GIF (smaller if the image is smaller). The right pane shows the crop scaled to 64x64 and enlarged with visible pixels (GIFs play). The square cannot be moved yet.
 [x] Step 4: Drag. Click inside the square and drag to move it; it stays 64x64 source pixels and cannot leave the image. The right pane follows live.
 [x] Step 5: Resize. Drag a corner to make the square bigger or smaller; it always stays a square, the opposite corner stays fixed, it cannot leave the image, minimum size 8 source pixels. The right pane follows live.
 [x] Step 6: Save. The Save button writes <name>_64x64bits.png to object_files/images/ or <name>_64x64bits.gif to object_files/gifs/ (all frames cropped the same way, frame durations and looping kept). Shows where it was saved.
 [~] Step 7: Save name and no overwrite. A text box above Save holds the name to save under, filled with the source file name when a file is selected. The _64x64bits suffix and the extension are added automatically, and the full target path is shown under the box. Several crops of one file can be saved by changing the name (e.g. pumpkin2). Save is blocked, with the reason shown, while the name is empty or invalid or the target file already exists: files are never overwritten (replaces step 6's overwrite question).

Notes
 scripts/sync_to_zero.sh (host): rsync of object_files/ to the Zero, keeping the folder structure.
 GIF results play on the panel with rgb_led_matrix/show_gif.py (Iteration 2).

Iteration 2: Our own code on the matrix (mostly DONE)

Goal: replace the library samples with our own Python code in this repo, deployed to the Pi Zero 2W and running on the 64x64 panel.

Done
 [x] Code lives in this repo; the library is only a wheel installed on the Zero (D-011). Branch poc.
 [x] uv project at the repo root (Python 3.13), Pillow added (pyproject.toml, uv.lock, requirements.txt).
 [x] rgb_led_matrix/matrix_config.py: the one place for matrix settings (rows, cols, mapping, slowdown, brightness, PWM).
 [x] Deploy by git: read-only GitHub deploy key on the Zero (~/.ssh/pizero2w_github, set in ~/.ssh/config), clone in ~/low_resolution_image_64x64, git pull to update. Images/GIFs are git-ignored and copied with scp.
 [x] Pillow 13.0.0 installed in ~/rgbmatrix/.venv on the Zero with pip --only-binary=:all: -r requirements.txt (ready-made aarch64 wheel, nothing compiled).
 [x] diagonal_wave.py (11 bits) and diagonal_wave_4bits.py, shared code in utils.py. Clear on Ctrl+C.
 [x] cutter_project/resize_to_64x64.py: centre-crop to square, LANCZOS to 64x64, _64x64bits suffix.
 [x] rgb_led_matrix/show_image.py: static 64x64 image until Ctrl+C.
 [~] rgb_led_matrix/show_gif.py: plays a 64x64 GIF from the cutter in a loop, one prepared canvas per frame (converted once at startup, the loop only swaps), GIF frame timing kept. Written 2026-10-25, to test on the panel.
 [x] Artefacts investigated: ghosting (pwm_lsb_nanoseconds), refresh flicker (pwm_bits x lsb), brightness glitches (software OE timing), strobe on motion (4 bits + jumping edges).
 [x] GPIO4-GPIO18 wire soldered, mapping adafruit-hat-pwm (D-010, 2026-10-25). Static image: clean.

To do
 [ ] Generated animations (e.g. the diagonal wave) with prepared canvases: either save them as GIFs for show_gif.py, or a raw RGB file format if GIF's 256 colours per frame are not enough.
 [ ] PWM profiles per kind of content in matrix_config.py, found by testing (D-009). Ask the user what content each time.
 [ ] Optional --pwm-bits / --pwm-lsb-ns arguments on show_image.py for those tests.
 [ ] Retest diagonal_wave.py with the wire; decide whether diagonal_wave_4bits.py is still needed.
 [ ] resize_to_64x64.py writes to cutter_project/images/ since it moved; point it to object_files/images/.
 [ ] Clean the two staged image_resolution_analyzer/ entries (files no longer exist).

Later (not planned yet)
 Shutdown push button on GPIO3 (pin 5) to GND with dtoverlay=gpio-shutdown, so the Zero never has to be unplugged hard. GPIO3 is not used by the adafruit-hat mapping (checked in lib/hardware-mapping.c); recheck for adafruit-hat-pwm.
 Read-only root file system (raspi-config overlay FS) once the app is stable, to protect the SD card from power cuts.
 Start the display automatically at boot (systemd service).
 Show text.
 Flicker improvements still open: isolating a CPU core, disabling unneeded services (README "Use minimal Raspbian distribution"), --led-limit-refresh.
 Remove the old snap rpi-imager 1.9.6 from the host (sudo snap remove rpi-imager) (D-007).

Iteration 1: First light (DONE 2026-10-22)

Goal: the matrix lights up with a solid colour, driven by Python on the Pi Zero 2W. Achieved: pulsing-colors.py sample fills the whole 64x64 panel.

Final working setup:
 Pi 4 builds the wheel from a git clone (D-006): rgbmatrix-0.0.1+20260125-cp313-cp313-linux_aarch64.whl, backup on the host in ~/rgbmatrix-wheels/.
 Zero: Raspberry Pi OS Lite 64-bit trixie, Python 3.13.5, hostname rgbmatrix, user admin, SSH key only (D-007). Wheel installed in ~/rgbmatrix/.venv, samples in ~/rgbmatrix/samples/.
 Zero config: dtparam=audio=off (backup /boot/firmware/config.txt.bak), /etc/modprobe.d/blacklist-rgb-matrix.conf, update-initramfs -u.
 Bonnet: bottom solder jumper E bridged to 8 (64x64 needs the E address line).
 Run command (Zero, in ~/rgbmatrix/samples): sudo ../.venv/bin/python pulsing-colors.py --led-rows=64 --led-cols=64 --led-gpio-mapping=adafruit-hat --led-slowdown-gpio=2

Done
 [x] Phase 0: both Pis trixie, aarch64, 64-bit, Python 3.13.5 (host: Ubuntu 24.04 x86_64, not used for builds). Panel 64x64. Panel powered by its own 5V supply into the Bonnet.
 [x] Phase 1: on-board audio disabled on the Zero (redone on the new SD card 2026-10-22).
 [x] Phase 2: build prerequisites on the Pi 4, clone, pip wheel in ~/build-venv (PEP 668).
 [x] Phase 3: wheel copied Pi 4 -> host -> Zero (Pi 4 has no SSH key for the Zero), venv, offline install, import test OK (redone 2026-10-22).
 [x] Phase 4: first light (2026-10-22). Earlier test without the E jumper showed only rows 0-15 and 32-47 = missing E line; fixed by the E-8 bridge.
 [x] Confirmed the Pi Zero 2W cannot build the library (freezes from lack of RAM); the Pi 4 can.

Incidents and lessons
 2026-10-20: Zero SD card died after repeated power cuts without shutdown (bootfs "not properly unmounted", card falls back to a bogus 32 MB device). Shutdown rule added to CLAUDE.md.
 2026-10-21: two reflashes gave a Zero that never joined Wi-Fi: snap rpi-imager 1.9.6 did not write the cloud-init files (user-data, network-config), and the Desktop image was chosen. Fixed with Imager 2.0.12 + Lite, settings checked on the card from the host before first boot.
 2026-10-22: the admin password set in Imager was not the one in KeePass; changed with passwd over SSH. After a reflash, the host needs ssh-keygen -R rgbmatrix.local (new host key).
