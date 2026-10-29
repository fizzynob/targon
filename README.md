# targon — apple-style neural photo library & drive scanner

targon is an apple photos-inspired desktop application featuring generous white space, translucent frosted-glass surfaces, and a hierarchical neural network pipeline that scans images across your drives and folders.

![targon icon](icon.png)

## key capabilities

1. **three root systems**:
   - **root 1: semantic taxonomy & subject identity** (super type → category → individual identity, like animal → cat → blu).
   - **root 2: physical drive structure** (drive → folder → subfolder).
   - **root 3: camera hardware & capture timeline** (exif camera model → date → format).

2. **pet re-id & subject clustering**:
   - differentiates individual pets within the same category (e.g. your russian blue cat **blu** vs an orange tabby or neighbor's pet).
   - extracts salient subject bounding boxes with background-suppressed chromaticity and neural embedding vectors.
   - naming, renaming, and 1-click subject merging in the **people & pets** view.

3. **industry-grade curation & management**:
   - **star ratings (0–5)** with instant single-key shortcuts (`0`–`5`).
   - **lossless 90° rotation** (`r`).
   - **side-by-side compare view** (`c`) for comparing shots and picking the best photo.
   - **spotlight search** (`ctrl+k` / `cmd+k`) and **neural inspector** (`i` / `ctrl+i`).
   - **filters**: min rating, orientation (landscape, portrait, square), duplicate detector, game asset detection.
   - **xmp sidecar sync**: write and read industry-standard `.xmp` metadata sidecars.

4. **ultra-low spec optimization & speed**:
   - single-pass inference and shared feature representations.
   - batch sqlite transactions and in-memory settings cache.
   - low-spec mode switch, adjustable scan threads, fast tagging toggle, and text ocr pre-gating.
   - built-in 300 placeholder photo generator and stress-testing tool.

5. **strict aesthetic guidelines**:
   - strictly lowercase typography throughout the interface.
   - human-written, casual, and purposeful copy.
   - apple-inspired frosted glass design, fluid animations, and subtle sound feedback.

---

## keyboard shortcuts

| shortcut | action |
|---|---|
| `space` | quick look / lightbox preview |
| `0` – `5` | set star rating (applies to selected photos) |
| `r` | rotate photo 90° clockwise |
| `f` | toggle favorite |
| `c` | open side-by-side photo comparison |
| `ctrl+k` / `cmd+k` | open spotlight search |
| `i` / `ctrl+i` | toggle inspector slide-over panel |
| `ctrl+a` | select all photos in view |
| `delete` / `backspace` | remove photo(s) from library |
| `escape` | close lightbox / modal or clear selection |
| `?` | show keyboard shortcuts reference |

---

## building & running

### 1. download prebuilt binaries
grab `Targon Setup 1.0.0.exe` (installer) or `Targon 1.0.0.exe` (portable) from the [releases](https://github.com/fizzynob/targon/releases) page.

### 2. run with launcher script
```powershell
.\start_targon.bat
```

### 3. developer setup
```powershell
# terminal 1: run python backend (port 8420)
python backend/run_backend.py

# terminal 2: run electron desktop app
cd frontend
npm install
npm run electron
```

### 4. build desktop installer & portable binary
```powershell
cd frontend
npm run build
npx electron-builder
```
compiled executables will be output to `frontend/release/`.

### 5. run tests
```powershell
python -m pytest tests/ -v
```
