const { app, BrowserWindow, ipcMain, dialog, Tray, Menu, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const http = require('http');

if (process.platform === 'win32') {
  app.setAppUserModelId('com.targon.photos');
}

let mainWindow = null;
let tray = null;
let pythonProcess = null;

function checkBackendReady() {
  return new Promise((resolve) => {
    const req = http.get('http://127.0.0.1:8420/api/health', (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(800, () => {
      req.destroy();
      resolve(false);
    });
  });
}

function waitForBackend(retries = 35) {
  return new Promise((resolve) => {
    let count = 0;
    const poll = () => {
      count++;
      const req = http.get('http://127.0.0.1:8420/api/health', (res) => {
        if (res.statusCode === 200) {
          resolve(true);
        } else if (count < retries) {
          setTimeout(poll, 250);
        } else {
          resolve(false);
        }
      });
      req.on('error', () => {
        if (count < retries) {
          setTimeout(poll, 250);
        } else {
          resolve(false);
        }
      });
      req.setTimeout(800, () => {
        req.destroy();
        if (count < retries) {
          setTimeout(poll, 250);
        } else {
          resolve(false);
        }
      });
    };
    poll();
  });
}

async function ensureBackendRunning() {
  const alreadyUp = await checkBackendReady();
  if (alreadyUp) return;

  const possibleBackendExes = [
    path.join(process.resourcesPath || '', 'backend', 'targon-backend.exe'),
    path.join(process.resourcesPath || '', 'backend', 'targon-backend', 'targon-backend.exe'),
    path.join(path.dirname(process.execPath), 'backend', 'targon-backend.exe'),
    path.join(path.dirname(process.execPath), 'resources', 'backend', 'targon-backend.exe'),
    path.join(__dirname, '..', '..', 'dist', 'targon-backend', 'targon-backend.exe'),
    path.join(__dirname, '..', 'dist', 'targon-backend', 'targon-backend.exe'),
  ];

  for (const exePath of possibleBackendExes) {
    if (fs.existsSync(exePath)) {
      console.log(`[Targon] Launching bundled backend executable: ${exePath}`);
      pythonProcess = spawn(exePath, [], {
        cwd: path.dirname(exePath),
        stdio: 'ignore',
        windowsHide: true,
      });
      return;
    }
  }

  const possibleScripts = [
    path.join(process.resourcesPath || '', 'backend', 'run_backend.py'),
    path.join(__dirname, '..', '..', 'backend', 'run_backend.py'),
    path.join(path.dirname(process.execPath), 'backend', 'run_backend.py'),
  ];
  for (const scriptPath of possibleScripts) {
    if (fs.existsSync(scriptPath)) {
      console.log(`[Targon] Launching python backend script: ${scriptPath}`);
      pythonProcess = spawn('python', [scriptPath], {
        cwd: path.dirname(path.dirname(scriptPath)),
        stdio: 'ignore',
        windowsHide: true,
      });
      return;
    }
  }
}

function createTray() {
  try {
    const icoPath = path.join(__dirname, 'icon.ico');
    const pngPath = path.join(__dirname, 'tray.png');
    const trayPath = process.platform === 'win32' && fs.existsSync(icoPath) ? icoPath : pngPath;
    let icon;
    if (fs.existsSync(trayPath)) {
      icon = nativeImage.createFromPath(trayPath);
    } else {
      const iconDataUrl =
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAA2SURBVDhPY2RgYPgPxFQBjAwM/8nUQA0waMGgBYMWDFowaAHlGhgZGP6TqYEqYGBkYGAEAJ+uD8V1M1tWAAAAAElFTkSuQmCC';
      icon = nativeImage.createFromDataURL(iconDataUrl);
    }
    if (icon && !icon.isEmpty()) {
      icon = icon.resize({ width: 16, height: 16 });
    }
    tray = new Tray(icon);
    const contextMenu = Menu.buildFromTemplate([
      {
        label: 'Open Targon Library',
        click: () => {
          if (mainWindow) {
            mainWindow.show();
            mainWindow.focus();
          }
        },
      },
      { type: 'separator' },
      {
        label: 'Quit Targon',
        click: () => {
          app.isQuiting = true;
          app.quit();
        },
      },
    ]);
    tray.setToolTip('Targon — AI Drive Photo Library');
    tray.setContextMenu(contextMenu);
    tray.on('double-click', () => {
      if (mainWindow) {
        mainWindow.show();
        mainWindow.focus();
      }
    });
  } catch (e) {
    // Ignore tray errors in headless environments
  }
}

async function createWindow() {
  await ensureBackendRunning();
  await waitForBackend(40);

  const appIconIco = path.join(__dirname, 'icon.ico');
  const appIconPng = path.join(__dirname, 'icon.png');
  const appIconPath = process.platform === 'win32' && fs.existsSync(appIconIco) ? appIconIco : appIconPng;
  const appIcon = fs.existsSync(appIconPath) ? nativeImage.createFromPath(appIconPath) : undefined;

  mainWindow = new BrowserWindow({
    width: 1460,
    height: 920,
    minWidth: 1024,
    minHeight: 680,
    frame: false,
    backgroundColor: '#FBFBFD',
    titleBarStyle: 'hidden',
    icon: appIcon,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  if (appIcon && !appIcon.isEmpty()) {
    mainWindow.setIcon(appIcon);
  }

  const devUrl = process.env.VITE_DEV_SERVER_URL;
  const distIndex = path.join(__dirname, '..', 'dist', 'index.html');

  mainWindow.webContents.on('console-message', (event, level, message, line, sourceId) => {
    console.log(`[Renderer] [${level}] ${message} (${sourceId}:${line})`);
  });

  mainWindow.webContents.on('render-process-gone', (event, details) => {
    console.error('[Renderer Gone]', details);
  });

  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    console.error('[did-fail-load]', errorCode, errorDescription);
    setTimeout(() => {
      if (!mainWindow) return;
      if (devUrl) {
        mainWindow.loadURL(devUrl);
      } else if (fs.existsSync(distIndex)) {
        mainWindow.loadFile(distIndex);
      } else {
        mainWindow.loadURL('http://127.0.0.1:8420/');
      }
    }, 800);
  });

  mainWindow.webContents.on('did-finish-load', () => {
    console.log('[did-finish-load] Loaded window successfully');
  });

  mainWindow.webContents.on('before-input-event', (event, input) => {
    if (input.key === 'F12' || (input.control && input.shift && input.key.toLowerCase() === 'i')) {
      mainWindow.webContents.toggleDevTools();
    }
  });

  if (process.env.DEBUG || process.env.VITE_DEV_SERVER_URL) {
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }

  if (devUrl) {
    mainWindow.loadURL(devUrl);
  } else if (fs.existsSync(distIndex)) {
    mainWindow.loadFile(distIndex);
  } else {
    mainWindow.loadURL('http://127.0.0.1:8420/');
  }
}

ipcMain.handle('window:minimize', () => {
  if (mainWindow) mainWindow.minimize();
});

ipcMain.handle('window:maximize', () => {
  if (!mainWindow) return false;
  if (mainWindow.isMaximized()) {
    mainWindow.unmaximize();
    return false;
  } else {
    mainWindow.maximize();
    return true;
  }
});

ipcMain.handle('window:close', () => {
  if (mainWindow) mainWindow.close();
});

ipcMain.handle('dialog:selectFolder', async () => {
  if (!mainWindow) return null;
  const result = await dialog.showOpenDialog(mainWindow, {
    title: 'Select Drive or Folder to Scan',
    properties: ['openDirectory'],
  });
  if (result.canceled || !result.filePaths.length) return null;
  return result.filePaths[0];
});

app.whenReady().then(() => {
  createTray();
  createWindow();
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    try {
      pythonProcess.kill();
    } catch (e) {}
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
