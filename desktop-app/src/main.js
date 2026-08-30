const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const fs = require('fs');

const isDev = !app.isPackaged;
const webRoot = isDev
  ? path.resolve(__dirname, '..', '..')
  : path.join(process.resourcesPath, 'web');
const dataDir = path.join(app.getPath('userData'), 'data');
const localDb = path.join(dataDir, 'cindrela-local-db.json');

function emptyDb() {
  return { version: 1, leads: [], deals: [], notes: [], settings: {} };
}

function ensureDataStore() {
  fs.mkdirSync(dataDir, { recursive: true });
  if (!fs.existsSync(localDb)) {
    fs.writeFileSync(localDb, JSON.stringify(emptyDb(), null, 2), 'utf8');
  }
}

function readDb() {
  ensureDataStore();
  try {
    return JSON.parse(fs.readFileSync(localDb, 'utf8'));
  } catch {
    const fallback = emptyDb();
    fs.writeFileSync(localDb, JSON.stringify(fallback, null, 2), 'utf8');
    return fallback;
  }
}

function writeDb(value) {
  ensureDataStore();
  if (!value || typeof value !== 'object') throw new TypeError('Database payload must be an object');
  const tmp = `${localDb}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(value, null, 2), 'utf8');
  fs.renameSync(tmp, localDb);
  return true;
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1000,
    minHeight: 700,
    title: 'Cindrela Sales Radar',
    backgroundColor: '#f4f7fb',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });

  const entry = path.join(webRoot, 'index.html');
  if (!fs.existsSync(entry)) {
    throw new Error(`Cindrela Sales Radar web bundle missing: ${entry}`);
  }

  win.loadFile(entry);
}

app.whenReady().then(() => {
  ensureDataStore();

  ipcMain.handle('db:read', () => readDb());
  ipcMain.handle('db:write', (_event, value) => writeDb(value));
  ipcMain.handle('app:info', () => ({
    isDev,
    version: app.getVersion(),
    userData: app.getPath('userData')
  }));
  ipcMain.handle('open:external', (_event, url) => {
    if (typeof url !== 'string' || !/^https?:\/\//i.test(url)) return false;
    shell.openExternal(url);
    return true;
  });

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
}).catch((err) => {
  console.error('Cindrela Sales Radar startup failure:', err);
  app.quit();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
