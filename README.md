# Setup

This project displays low-resolution images on a 64x64 RGB LED matrix driven by a
Raspberry Pi 4 with the **Adafruit RGB Matrix Bonnet**. It uses
[hzeller/rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix)
(imported as `rgbmatrix`) and Pillow, managed with [uv](https://docs.astral.sh/uv/).

## Hardware

- Raspberry Pi 4 (hostname `pi4server`, user `admin`)
- Adafruit RGB Matrix Bonnet, plugged onto the Pi's GPIO header
- 64x64 HUB75 RGB LED matrix, connected with the ribbon cable to the Bonnet
  (plug into the matrix's **INPUT** side)
- A separate **5V 4A (or larger)** power supply plugged into the Bonnet.
  The Pi cannot power the matrix.

> **64x64 panels only:** the Bonnet's "E" address jumper on the underside must be
> soldered so the middle pad connects to the pad marked **8**. Without it, the
> image shows up only half drawn or garbled.

## Development workflow

Code lives on the Pi. The computer only edits it through an SSHFS mount.

| Where | What |
|---|---|
| Computer (`samuelbm@ubuntu`) | Edit files in PyCharm through the mount |
| Pi (`admin@pi4server`) over SSH | `uv`, `git`, installers, running the code |

> Rule of thumb: anything that **installs, builds or runs** must happen on the Pi.
> Running `uv` on the computer inside the mount builds an x86 `.venv` the Pi can't use.

### Mount the Pi's projects folder on the computer

```bash
# on the computer, from the home folder
cd ~
sudo apt install sshfs          # first time only
mkdir -p ~/pi4server            # first time only
sshfs admin@pi4server.local:/home/admin/Projects ~/pi4server -o reconnect,ServerAliveInterval=15
```

Open `~/pi4server/low_resolution_image_64x64` in PyCharm (not the whole `~/pi4server`),
and mark `.venv` as **Excluded**.

- Check the mount: `findmnt ~/pi4server`
- Unmount: `cd ~ && fusermount -u ~/pi4server`
- If a terminal was already inside `~/pi4server` before mounting, `cd ~` and back in,
  or it will look empty.
- The mount does not survive reboots of either machine. Remount when needed.
- PyCharm doesn't detect changes on the mount automatically: use
  **File → Reload All from Disk** if files or git status look out of date.

## Pi setup (run everything below over SSH on the Pi)

```bash
ssh admin@pi4server.local
cd ~/Projects/low_resolution_image_64x64
```

### 1. Match the Python version to the Pi's system Python

```bash
python3 --version               # e.g. Python 3.13.5
echo "3.13" > .python-version   # use the version printed above
```

`requires-python` in `pyproject.toml` must also allow that version (currently `>=3.11`).
If `.python-version` doesn't match, `uv sync` silently replaces the venv with a
uv-managed Python that lacks pip and system packages, and the installer below fails.

### 2. Create the virtual environment

```bash
sudo rm -rf .venv   # only if an old .venv exists (sudo needed: the installer leaves root-owned files)
uv venv --seed --system-site-packages --python /usr/bin/python3
uv sync --inexact
```

- `--seed` adds pip, which the matrix installer needs.
- `--system-site-packages` lets the venv see system-wide packages.
- `--python /usr/bin/python3` uses the Pi's own Python.
- `uv sync --inexact` installs Pillow without removing packages uv didn't install.
  If it prints "Removed virtual environment", the Python version in step 1 is wrong.

### 3. Install the RGB matrix library

```bash
cd ~
wget https://github.com/adafruit/Raspberry-Pi-Installer-Scripts/raw/main/rgb-matrix.py
cd ~/Projects/low_resolution_image_64x64

source .venv/bin/activate
pip install adafruit-python-shell          # helper the installer requires
sudo -E env PATH=$PATH python3 ~/rgb-matrix.py
```

The installer has to run inside the activated venv so it installs the `rgbmatrix`
bindings there. `sudo -E env PATH=$PATH` keeps the venv active under sudo.
Keep `rgb-matrix.py` outside the project folder so it doesn't get committed.

Installer answers used:

| Question | Answer | Why |
|---|---|---|
| Interface board | Adafruit RGB Matrix Bonnet | The hardware in use |
| Quality or Convenience | **Convenience** | No GPIO4–GPIO18 wire soldered; Pi audio stays on |
| Reserve a CPU core | **Yes** | Less flicker; adds `isolcpus=3` to the boot config |
| Reboot | Yes | Needed for the boot settings |

To switch to Quality later: solder a wire between GPIO4 and GPIO18 on the Bonnet,
rerun the installer, and use `hardware_mapping = "adafruit-hat-pwm"` in the code.

### 4. Verify

After the reboot, reconnect and check:

```bash
cd ~/Projects/low_resolution_image_64x64
.venv/bin/python -c "import PIL; print(PIL.__version__)"
sudo .venv/bin/python -c "import rgbmatrix; print('ok')"
```

## Running

The matrix library needs root for precise GPIO timing:

```bash
sudo .venv/bin/python main.py
```

Matrix options for this hardware:

```python
from rgbmatrix import RGBMatrix, RGBMatrixOptions

options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.hardware_mapping = "adafruit-hat"   # "adafruit-hat-pwm" if using Quality mode
matrix = RGBMatrix(options=options)
```

## Important notes

- **Always use `uv sync --inexact`.** `rgbmatrix` was installed by the Adafruit script,
  not by uv, so it isn't in `pyproject.toml` or `uv.lock`. A plain `uv sync` deletes it.
  If that happens, rerun step 3.
- Deleting `.venv` or setting up on another Pi means redoing steps 1–4.
- The CPU core reservation and other boot settings are system-level. They don't appear
  in the project files or in git.
- `uv add <package>` works normally for other dependencies. Run it on the Pi.