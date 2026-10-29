DECISIONS.md

Why things are done the way they are. Append-only: never edit an old entry; add a new one that supersedes it.

Format: context, decision, alternatives considered, consequences. Status: Proposed / Accepted / Superseded by D-XXX.

D-001: uv for dependency management on the host

Status: Accepted

Context: The project needs a reproducible way to declare and lock dependencies.

Decision: Use uv on the host.

Alternatives:

Poetry: slower and heavier for a small project.
Plain venv + pip: less convenient; no built-in locking or project management.

Consequences: requirements.txt for the Pis is generated with uv export, never edited by hand.

D-002: Build wheels on the Pi 4, install them on the Pi Zero 2W

Status: Accepted

Context: Installing rgbmatrix on the Pi Zero 2W freezes midway: compiling it needs more RAM than the Zero has. The Pi 4 builds it successfully. The host has a different OS/architecture.

Decision: Compile wheels on the Pi 4 with pip wheel (build only, no install). Copy them to the Zero. Install offline with --no-index --find-links.

Alternatives:

Build on the Zero with a bigger swap file: might work, but very slow and wears the SD card. Kept as a fallback.
Cross-compile on the host: different architecture, much more complex to set up.
Build in an emulated container (Docker buildx/QEMU) on the host: possible, but complex and slow for a first iteration.

Consequences: Any new dependency or OS/Python upgrade means rebuilding wheels on the Pi 4.

D-003: Both Pis must share OS release, architecture and Python version

Status: Accepted

Context: Compiled wheels are tied to the CPU architecture (e.g. aarch64 vs armv7l), the Python version (e.g. cp311) and the system libraries of the OS.

Decision: Keep both Pis on the same OS image and use the system Python on both. Verify with cat /etc/os-release, uname -m, python3 --version before every build.

Alternatives: Managing separate Python versions with uv/pyenv on the Pis was rejected because it adds a way for the two Pis to drift apart.

Consequences: Upgrading one Pi means upgrading the other the same way.

D-004: GPIO mapping adafruit-hat

Status: Accepted

Context: The Adafruit HAT/Bonnet uses a different pinout from the library's default wiring.

Decision: Always use adafruit-hat.

Alternatives: adafruit-hat-pwm gives less flicker but requires soldering a wire between GPIO4 and GPIO18. That's postponed until after first light.

Consequences: Some flicker may remain until the hardware mod is done.

D-005: Disable on-board audio on the Pi Zero 2W

Status: Accepted

Context: The library and the on-board sound use the same hardware timing subsystem. The library exits if snd_bcm2835 is loaded.

Decision: Set dtparam=audio=off and blacklist snd_bcm2835.

Consequences: No on-board sound. A USB sound adapter can be used if sound is ever needed.

D-006: Build the rgbmatrix wheel from a git clone on the Pi 4, not from requirements.txt

Status: Accepted (2026-10-20)

Context: The pyproject.toml in this repo is the build file of the library itself (scikit-build-core + Cython + CMake), not a list of dependencies. Building it needs the whole source tree (lib/, include/, bindings/, CMakeLists.txt). The requirements.txt flow in CLAUDE.md is meant for an app that depends on rgbmatrix.

Decision: On the Pi 4, git clone https://github.com/hzeller/rpi-rgb-led-matrix.git and run pip wheel . -w ~/rgbmatrix-wheels/ from the clone, using a venv (~/build-venv) because Debian trixie blocks pip on the system Python (PEP 668). Wheels are stored outside /tmp so they survive a reboot.

Alternatives:

scp/rsync the host's working copy to the Pi 4: works, but slower and the host copy has only local doc changes, so a clone is equivalent.
requirements.txt containing rgbmatrix: pip would look for it on PyPI/piwheels rather than building this source.

Consequences: The requirements.txt flow is used later, once our own app exists. The clone sits in /tmp on the Pi 4 and is lost on reboot; re-clone if a rebuild is needed.

D-007: Reinstall the Zero after the SD card failure: Lite image, Imager 2, settings verified before boot

Status: Accepted (2026-10-22)

Context: The Zero's SD card died on 2026-10-20 after repeated power cuts without shutdown (see the shutdown rule in CLAUDE.md). All work stored on it (audio config, venv, installed wheel, samples) was lost. Two reflash attempts then produced a Zero that never joined Wi-Fi: the snap rpi-imager 1.9.6 left the cloud-init files user-data and network-config untouched on the 2026-10 trixie image, and the Desktop image (stage4) was chosen by mistake.

Decision: Flash with Raspberry Pi Imager 2 (2.0.12), choose Raspberry Pi OS (other) -> Raspberry Pi OS Lite (64-bit), keep hostname rgbmatrix and user admin so all earlier commands stay valid. Before first boot, check user-data and network-config on the card from the host. Redo only the Zero-side phases (0 check, 1, 3, 4); keep the existing Pi 4 wheel because the new image is still trixie aarch64 with Python 3.13.

Alternatives:

Keep the Desktop image and switch it to console mode: works, but wastes RAM/CPU on a 512 MB Zero and the official README says never to run a GUI with the matrix.
Write cloud-init files by hand after flashing: reliable, but not needed once Imager 2 wrote them correctly.

Consequences: The snap rpi-imager 1.9.6 should be removed from the host (sudo snap remove rpi-imager). If the Zero's Python version ever differs from the Pi 4, the wheel must be rebuilt (D-003).

D-008: Claude never commits or pushes

Status: Accepted (2026-10-23)

Context: CLAUDE.md said "Do not push without asking". On 2026-10-23 Claude committed and pushed the Pillow dependency (b2dc33f on poc) after the user asked why Claude could not run the host commands itself. The user wants to keep full control over what goes into git history and to GitHub.

Decision: Claude never runs git commit or git push. Claude prepares the changes, says which files belong in the commit, and gives the commands labelled Host; the user runs them. Read-only git commands (status, log, diff) and branch creation stay allowed.

Alternatives:

Ask before each commit/push (the previous rule): left room for a quick "yes" or an ambiguous request to turn into a push.

Consequences: Every commit and push is done by the user. Claude's replies end with the exact git commands when files changed.

D-009: Display settings are tuned per kind of content

Status: Accepted (2026-10-24)

Context: Tests on the 64x64 panel (2026-10-22 to 2026-10-24) showed that pwm_bits and pwm_lsb_nanoseconds trade against each other. Fewer bitplanes allow longer pulses (less ghosting) at a high refresh rate, but cost grey levels. 11 bits at 130 ns ghosted; 11 bits at 300 ns removed the ghosting but dropped the refresh to about 50 Hz (CRT-like flicker); 4 bits gave sharp bands and a stroboscopic effect on the moving wave. No single setting is best for everything.

Decision: The PWM settings (pwm_bits, pwm_lsb_nanoseconds, possibly pwm_dither_bits) are chosen per kind of content, as named profiles in matrix_config.py, and found by testing on the panel. Rough starting points: cartoons, logos, pixel art and text with few colours: 4-5 bits with long pulses (500-1000 ns); photos and real-image GIFs: 9-11 bits around 300 ns. Before tuning or adding a display feature, Claude asks the user what kind of content will be shown (cartoon/flat colours, photo, real-image GIF, text, ...).

Alternatives:

One global setting for all content: simpler, but either ghosts or flickers on cartoons, or bands on photos.

Consequences: matrix_config.py holds several profiles instead of one PWM setting; each display script says which profile it uses. Profiles are re-tested after the GPIO4-GPIO18 mod (adafruit-hat-pwm), since glitches then no longer hide other effects.

D-010: GPIO4-GPIO18 wire soldered, mapping adafruit-hat-pwm

Status: Accepted (2026-10-25). Supersedes D-004.

Context: Without the mod, the Bonnet's OE pulses (LED on-time) are timed by the CPU. Linux interruptions and our own per-frame Python work stretched them, giving random brightness glitches, worst on dim colours and during animation; a static image showed only small glitches. The library README (Limitations, Improving flicker: hardware patch) recommends the mod.

Decision: A wire is soldered between GPIO4 (pin 7) and GPIO18 (pin 12) on 2026-10-25. Always use hardware_mapping = "adafruit-hat-pwm", so the OE pulses come from the Pi's PWM peripheral on GPIO18. Set once in rgb_led_matrix/matrix_config.py; library samples need --led-gpio-mapping=adafruit-hat-pwm.

Alternatives:

Keep adafruit-hat and hide the jitter with 4 PWM bits and long pulses: tested, gave sharp bands and a stroboscopic effect on motion.
Prepared canvases only: reduce per-frame CPU work, but cannot help content that never repeats (video).

Consequences: Never run anything with adafruit-hat while the wire is on. On-board audio must stay off (D-005): the PWM peripheral is shared with it. The same library and wheel are used; no rebuild. The PWM profiles of D-009 are re-tested with the wire.

D-011: Our code lives in this repo; the library is only an installed wheel

Status: Accepted (2026-10-25). Answers the open question of ROADMAP Iteration 2.

Context: The four .md files came from the earlier project that got rgbmatrix working on the Zero. That project kept the library source next to our code. This repo (low_resolution_image_64x64) is about producing images for the panel.

Decision: All our code lives in this repo: rgb_led_matrix/ runs on the Zero, cutter_project/ runs on the host. The library is not part of the repo; the Zero uses the wheel already installed in ~/rgbmatrix/.venv (D-006). The Zero gets the code with git clone/pull (read-only deploy key). Pure-Python or ready-made-wheel dependencies such as Pillow are installed on the Zero with pip --only-binary=:all: -r requirements.txt, which never compiles; anything that would need compiling still goes through the Pi 4 (D-002).

Alternatives:

A folder inside the library repo on a separate branch: mixes our history with the library's, and the library build files (pyproject.toml, CMakeLists.txt) would sit next to ours.

Consequences: Images and GIFs are git-ignored and copied to the Zero with scp. The library's own README is kept below our section in README.md as reference.

D-012: tkinter for the cutter app

Status: Proposed (2026-10-25)

Context: The cutter (ROADMAP Iteration 3) is a small desktop app on the host: file lists, an image/GIF view with a draggable square, a 64x64 preview, a Save button.

Decision: Use tkinter (Python standard library) with Pillow for image work.

Alternatives:

PySide6/PyQt6: nicer widgets, but a large new dependency; it would also land in requirements.txt and the Pis would have to skip it.
A web page (local server + browser): more moving parts for a one-person tool.

Consequences: No new dependency (tkinter is included in the uv-managed Python 3.13 on the host, checked: Tk 9.0). GIF playback is done by hand (Pillow frames + tkinter timer).

D-013: Start the display at boot with a systemd service, not Docker

Status: Accepted (2026-10-25)

Context: The Zero should show a chosen image or GIF as soon as it powers on, also away from home, and restart the player if it crashes unless it was stopped on purpose. Docker was considered for this.

Decision: A systemd service (systemd/rgbmatrix-display.service in the repo, installed in /etc/systemd/system/) runs rgb_led_matrix/play_selection.py with the existing ~/rgbmatrix/.venv at boot, as root, with Restart=always. systemctl stop stops it until the next start or boot; systemctl disable keeps it from starting at boot.

Alternatives:

Docker with --restart unless-stopped: same behaviour, but adds the Docker daemon (disk and RAM on a 512 MB Zero), needs --privileged for GPIO and /dev/mem, and an image built on the Pi 4 and copied over. Worth it only to rebuild the whole setup with one command or to isolate several services.
Cron @reboot: no restart after a crash, no stop/status commands.

Consequences: No new software on the Zero. While the service runs the panel is taken: stop it before running other display scripts by hand.

D-014: The selection is a plain text file on the Zero only

Status: Accepted (2026-10-25)

Context: The player needs to know what to show, and the user wants to change it remotely over SSH/Wi-Fi.

Decision: ~/low_resolution_image_64x64/object_files/selection.txt, plain text. The first line that is not empty or a # comment is the path to show, relative to the repo root, the same path typed with show_image.py / show_gif.py (e.g. object_files/gifs/floating_eye_64x64bits.gif). It lives only on the Zero: git-ignored, skipped by scripts/sync_to_zero.sh (also with --delete), edited over SSH. The player refuses paths outside the repo.

Alternatives:

A .sh file: it would be executed as root, so anything written in it would run; a text file is data that the player checks.
Path relative to object_files/ (gifs/...): shorter, but differs from the paths typed on the command line.
Editing on the host and syncing: the host copy would overwrite edits made on the Zero.

Consequences: The selection is not backed up by git. Later it can grow into a playlist (one path per line) or take options without changing the file name.

D-015: Control the panel from the phone through a web page served by the Zero

Status: Proposed (2026-10-26)

Context: The user wants more control than one fixed selection: choose what plays from the phone, and shut the Zero down safely without pulling the plug (SD card died on 2026-10-20). A home server on the Pi 4 exists, reachable on the local network only.

Decision: The Zero serves a small web page (opened in the phone's browser, no app to install). The page does not drive the panel itself: it writes what to play (selection.txt, later a playlist) and the player shows it (D-014). A Shut down button runs only the shutdown command, through a sudo rule; the web server does not run as root. The Pi 4 may later give it a name or host the image library, but the Zero must keep working without it. MVP first: rgb_led_matrix/loop.py plays a folder in turn from the command line.

Alternatives:

A native phone app: much more work, an app store or sideloading, for the same result.
Control through the Pi 4 server only: the panel would stop being controllable whenever the Pi 4 is off.

Consequences: The web server must stay light (the panel refresh uses a full core on the Zero). Any library it needs must have a ready-made wheel or go through the Pi 4 (D-002). Where the panel is used away from home is still open: it decides how the phone reaches the Zero (home Wi-Fi, phone hotspot, or the Zero as its own access point).

D-016: The boot service runs loop.py, settings in loop.env

Status: Accepted (2026-10-26). Changes D-013 (the service runs loop.py, not play_selection.py, for now).

Context: The user wants the Zero to play a folder at power-up, e.g. object_files/gifs/halloween at 0.2 minutes per file, and asked whether a .sh script could hold that command.

Decision: systemd/rgbmatrix-display.service runs loop.py directly with ${LOOP_FOLDER} and ${LOOP_MINUTES}. Defaults are in the unit; ~/low_resolution_image_64x64/loop.env (git-ignored, Zero only) overrides them. KillSignal=SIGINT so a stop acts like Ctrl+C and the panel is cleared.

Alternatives:

A .sh script started by the unit: one more file, and it runs as root, so anything written in it would run as root (same reason as D-014). loop.env is read by systemd as plain KEY=value data, never executed.
Arguments written only in the unit: every change needs sudo, cp and daemon-reload.

Consequences: Changing the folder or time = edit loop.env + restart the service. When the phone control comes (D-015) it can write loop.env (or a selection) and restart the service. play_selection.py (Iteration 4) is not needed for now.

D-017: Shutdown push button on GPIO3, normally closed, active_low=0

Status: Accepted (2026-10-27)

Context: The Zero now starts the display at boot (D-016) and will often be unplugged without SSH. Pulling the power while the OS writes killed an SD card (2026-10-20). A shutdown button was in the Later list.

Decision: A push button is soldered between pin 5 (GPIO3) and pin 6 (GND) on the underside of the Zero. GPIO3 is free with adafruit-hat-pwm (checked in lib/hardware-mapping.c: the mapping uses GPIO 5, 6, 12, 13, 16, 17, 18, 20-24, 26, 27, plus GPIO4 through the D-010 wire). The button is normally closed, so /boot/firmware/config.txt has dtoverlay=gpio-shutdown,active_low=0 (shutdown when the pin goes high, i.e. when pushed). Backup before the change: /boot/firmware/config.txt.bak-shutdown.

Alternatives:

Normally open button with plain dtoverlay=gpio-shutdown: the standard setup, and the same button then also powers the halted Zero back up. Not what was soldered; still the fix if the NC button causes trouble.
Shutdown only over SSH: needs a laptop or phone every time, so the plug gets pulled instead.

Consequences: Wait until the green LED is off before unplugging. With an NC button GPIO3 is held low at rest, which is also the Pi's power-up signal, so a halted Zero may start again by itself; if so, hold the button until the LED is off, or swap to a normally open button. I2C (GPIO2/3) cannot be used while the button is there.

D-018: loop.py plays each GIF a number of times; the service passes LOOP_ARGS

Status: Accepted (2026-10-28). Supersedes D-016 on how the service gets its settings.

Context: With many GIFs of different lengths, one fixed time per file (duration_minutes) cuts long GIFs and repeats short ones many times. The user wants each animation to play twice, then the next one, and wants code updates to work with git pull + reboot.

Decision: loop.py folder_path [--plays N] [--image-seconds S]: each GIF plays N times (default 2), each still image (or one-frame GIF) stays S seconds (default 10). The unit runs loop.py $LOOP_ARGS: one setting holds all arguments, default LOOP_ARGS=object_files/gifs/halloween, and ~/low_resolution_image_64x64/loop.env can override it. systemd splits $VAR (without braces) into separate arguments.

Alternatives:

One variable per option in the unit (LOOP_FOLDER, LOOP_PLAYS, ...): every new loop.py option would change the unit, and a unit change needs scripts/install_on_zero.sh, not only a pull.
Keep duration_minutes next to --plays: two ways to say how long a file stays; not needed now.

Consequences: Defaults live in loop.py, so a git pull + reboot picks up new behaviour. Only changes to files in systemd/ need scripts/install_on_zero.sh. A loop.env with the old LOOP_FOLDER/LOOP_MINUTES lines is ignored. Folder paths in LOOP_ARGS cannot contain spaces.
