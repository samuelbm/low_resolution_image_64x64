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
