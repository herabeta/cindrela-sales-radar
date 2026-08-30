const { app, BrowserWindow, ipcMain, shell } = require('electron');
const path = require('path');
const fs = require('fs');

const isDev = !app.isPackaged;
const webRoot = path.resolve(__dirname, '..', '..');
const dataDir = path.join(app.getPath('userData'), 'data');
const localDb = path.join(dataDir, 'cindrela-local-db.json');

function ensureDataStore() {
  fs.mkdirSync(dataDir, { recursive: true });
  if (!fs.existsSync(localDb)) {
    fs.writeFileSync(
      localDb,
      JSON.stringify({ version: 1, leads: [], deals: [], notes: [], settings: {} }, null, 2),
      'utf8'
    );
  }
}

function readDb() {
  ensureDataStore();
  try {
    return JSON.parse(fs.readFileSync(localDb, 'utf8'));
  } catch {
    return { version: 1, leads: [], deals: [], notes: [], settings: {} };
  }
}

function writeDb(value) {
  ensureDataStore();
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
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  const entry = path.join(webRoot, 'index.html');
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
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
