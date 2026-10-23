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
