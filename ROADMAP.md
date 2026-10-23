Living plan. Updated at the end of every work session. Status: [ ] to do, [~] in progress, [x] done.

Iteration 2: Our own app on the matrix

Goal: replace the library samples with our own Python code, kept in its own folder next to the library, deployed from the host to the Pi Zero 2W and running on the 64x64 panel.

In progress
 [ ] Decide where our code lives (open question, see "Decision needed" below). Record the choice as a new DECISIONS.md entry.

To do

Phase A: Project skeleton (host)
 [ ] Bring in the source from the other project (path to confirm) instead of starting from zero.
 [ ] Own folder with its own pyproject.toml managed by uv. Must not touch the library's root pyproject.toml / CMakeLists.txt.
 [ ] One config module for all matrix settings: rows=64, cols=64, hardware_mapping="adafruit-hat", gpio_slowdown=2, brightness (CLAUDE.md §5).
 [ ] Entry point that creates the RGBMatrix from that config, clears the matrix on exit and handles Ctrl+C cleanly.
 [ ] ruff check / ruff format pass.

Phase B: Deploy to the Zero
 [ ] Copy the app folder from the host to the Zero (scp/rsync; same path as the samples: host -> Zero).
 [ ] Run it with the existing ~/rgbmatrix/.venv (rgbmatrix already installed). No rebuild needed unless a new compiled dependency is added.
 [ ] If the app needs extra packages (e.g. Pillow for images): ask first, uv add, uv export requirements.txt, build wheels on the Pi 4, install offline on the Zero (D-002, D-003).

Phase C: First own content
 [ ] Minimal own script: fill the panel with one colour, then clear on exit (the old Phase 4 item from Iteration 1).
 [ ] Port the first real feature from the other project.

Decision needed: where does our code live?
 Option 1 (recommended): a folder inside this repo (e.g. app/) with its own pyproject.toml, on a separate git branch. The library stays untouched next to it.
 Option 2: keep the other project as its own repo and only install the rgbmatrix wheel into its environment.

Later (not planned yet)
 Shutdown push button on GPIO3 (pin 5) to GND with dtoverlay=gpio-shutdown, so the Zero never has to be unplugged hard. GPIO3 is not used by the adafruit-hat mapping (checked in lib/hardware-mapping.c).
 Read-only root file system (raspi-config overlay FS) once the app is stable, to protect the SD card from power cuts.
 Start the display automatically at boot (systemd service).
 Show text, images, animations.
 Flicker improvements: GPIO4-GPIO18 solder mod + adafruit-hat-pwm (D-004), isolating a CPU core, disabling unneeded services (README "Use minimal Raspbian distribution").
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
