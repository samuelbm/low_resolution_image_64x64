Stable working rules for this project. Read at the start of every session. Do NOT put plans, progress or temporary notes here. Those go in ROADMAP.md.

1. Project context
Goal: drive an RGB LED matrix from a Raspberry Pi Zero 2W, using the rpi-rgb-led-matrix library (Python package rgbmatrix, by hzeller).
What the project is and how to run it: see README.md.
Current plan and progress: see ROADMAP.md.
Why things are the way they are: see DECISIONS.md.
Reference documentation is the official repository README only: https://github.com/hzeller/rpi-rgb-led-matrix Many online tutorials describe an old version of the library. Do not rely on them.
2. Hardware and machines

There are three machines. Always say which one a command runs on.

Machine	Role	Notes
Host	Editing code, git	Different OS/architecture from the Pis
Pi 4	Build machine: compiles wheels	Same OS and architecture as the Zero
Pi Zero 2W	Target: runs the matrix	Too little RAM to build the library
Display: Adafruit RGB Matrix HAT/Bonnet on the Pi Zero 2W.
Panel: 64x64, HUB75 (needs the E address line jumper set on the HAT/Bonnet).
OS on both Pis: Debian GNU/Linux 13 (trixie), aarch64, 64-bit userland (confirmed 2026-10-20).
Python on both Pis: 3.13.5 (system Python). Note: CMakeLists.txt requires Python 3.13 exactly.

Hard rules:

Never build or pip install the rgbmatrix library from source on the Pi Zero 2W. It freezes from lack of RAM. Build wheels on the Pi 4, install them on the Zero.
Wheels only work if both Pis have the same OS release, CPU architecture and Python version. If any of these change, rebuild all wheels.
Always use --led-gpio-mapping=adafruit-hat (Python: options.hardware_mapping = "adafruit-hat"). Use adafruit-hat-pwm only if the GPIO4–GPIO18 solder mod has been done.
On-board audio must stay disabled on the Zero (the library refuses to run otherwise).
Always shut a Pi down before removing power: sudo shutdown -h now, then wait until the green LED stops flickering (on the Zero 2W it goes off). Pulling the plug while the OS writes can corrupt or kill the SD card (happened 2026-10-20).
3. Session workflow (memory between sessions)
At the start of a session: read ROADMAP.md and the recent entries of DECISIONS.md.
Before starting a task: confirm which ROADMAP item it belongs to.
At the end of a task: update ROADMAP.md (move items to Done, note what is In progress).
When a significant choice is made: add an entry to DECISIONS.md. Never rewrite old entries. Add a new one that supersedes it.
4. Change policy
Claude cannot access the Pis directly. Give the user commands to run, labelled with the machine, and ask for the output before moving on.
One step at a time on hardware: change one thing, test, then continue. When something fails, first ask whether the problem is hardware, OS config, or software.
Explain any command that uses sudo, edits files in /boot/firmware/, or removes packages before asking the user to run it.
Keep changes small and focused. Ask when requirements are unclear.
5. Coding standards
Python, formatted and linted with ruff.
Type hints on public functions. Comments explain why, not what.
Matrix settings (rows, cols, mapping, slowdown, brightness) live in one config place, never hard-coded across several files.
Always clear the matrix on exit (handle Ctrl+C cleanly).
6. Dependency management
On the host: uv manages the project (uv add <package>).
requirements.txt is generated, never edited by hand: uv export --format requirements-txt --no-hashes > requirements.txt
On the Pis: system Python plus a venv; wheels built on the Pi 4 with pip wheel.
Ask before adding a dependency. Every new dependency means rebuilding wheels.
7. Commands

Host:

Export requirements: uv export --format requirements-txt --no-hashes > requirements.txt
Lint / format: uv run ruff check . / uv run ruff format .

Pi 4 (build):

Build wheels: python3 -m pip wheel -r requirements.txt -w wheels/

Transfer (from the Pi 4):

rsync -av wheels/ requirements.txt <user>@<zero-host>:~/[project]/

Pi Zero 2W (target):

Install (no internet build): .venv/bin/pip install --no-index --find-links wheels/ -r requirements.txt
Run (root needed for hardware access; the library drops privileges afterwards): sudo .venv/bin/python [script].py
8. Git
Small commits: <type>: <summary> (e.g. fix: correct gpio mapping).
Never commit wheels/, .venv/, secrets or .env files.
Claude never commits or pushes, even when asked to run git commands for the user. Claude gives the commands (labelled Host) and the user runs them (D-008).
