const { app, BrowserWindow, ipcMain, shell } = require('electron');
const http = require('http');
const path = require('path');
const fs = require('fs');

const isDev = !app.isPackaged;
const webRoot = isDev
  ? path.resolve(__dirname, '..', '..')
  : path.join(process.resourcesPath, 'web');
const dataDir = path.join(app.getPath('userData'), 'data');
const localDb = path.join(dataDir, 'cindrela-local-db.json');
const agentScriptPath = path.join(__dirname, 'desktop-agent.js');
const PORT = 49321;
let localServer = null;

function emptyDb() {
  return { version: 2, storage: {}, leads: [], deals: [], notes: [], settings: {}, followUps: [], emailLog: [] };
}

function ensureDataStore() {
  fs.mkdirSync(dataDir, { recursive: true });
  if (!fs.existsSync(localDb)) fs.writeFileSync(localDb, JSON.stringify(emptyDb(), null, 2), 'utf8');
}

function readDb() {
  ensureDataStore();
  try { return { ...emptyDb(), ...JSON.parse(fs.readFileSync(localDb, 'utf8')) }; }
  catch { const fallback = emptyDb(); fs.writeFileSync(localDb, JSON.stringify(fallback, null, 2), 'utf8'); return fallback; }
}

function writeDb(value) {
  ensureDataStore();
  if (!value || typeof value !== 'object') throw new TypeError('Database payload must be an object');
  const current = readDb();
  const next = {
    ...current,
    ...value,
    version: 2,
    storage: value.storage && typeof value.storage === 'object' ? value.storage : current.storage,
    leads: Array.isArray(value.leads) ? value.leads : current.leads,
    deals: Array.isArray(value.deals) ? value.deals : current.deals,
    notes: Array.isArray(value.notes) ? value.notes : current.notes,
    settings: value.settings && typeof value.settings === 'object' ? value.settings : current.settings,
    followUps: Array.isArray(value.followUps) ? value.followUps : current.followUps,
    emailLog: Array.isArray(value.emailLog) ? value.emailLog : current.emailLog
  };
  const tmp = `${localDb}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(next, null, 2), 'utf8');
  fs.renameSync(tmp, localDb);
  return true;
}

function contentType(file) {
  const ext = path.extname(file).toLowerCase();
  return ({ '.html':'text/html; charset=utf-8', '.js':'text/javascript; charset=utf-8', '.css':'text/css; charset=utf-8', '.json':'application/json; charset=utf-8', '.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.svg':'image/svg+xml', '.ico':'image/x-icon' })[ext] || 'application/octet-stream';
}

function startLocalServer() {
  return new Promise((resolve, reject) => {
    localServer = http.createServer((req, res) => {
      try {
        const pathname = decodeURIComponent((req.url || '/').split('?')[0]);
        const relative = pathname === '/' ? 'index.html' : pathname.replace(/^\/+/, '');
        const root = path.resolve(webRoot);
        const file = path.resolve(root, relative);
        if (file !== root && !file.startsWith(`${root}${path.sep}`)) { res.writeHead(400); return res.end('Bad request'); }
        if (!fs.existsSync(file) || !fs.statSync(file).isFile()) { res.writeHead(404); return res.end('Not found'); }
        res.setHeader('Content-Type', contentType(file));
        res.setHeader('Cache-Control', 'no-store');
        fs.createReadStream(file).pipe(res);
      } catch (err) {
        console.error('Desktop local server error:', err);
        res.writeHead(500); res.end('Internal server error');
      }
    });
    localServer.once('error', reject);
    localServer.listen(PORT, '127.0.0.1', () => resolve(`http://127.0.0.1:${PORT}/`));
  });
}

async function createWindow() {
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

  if (fs.existsSync(agentScriptPath)) {
    const agentScript = fs.readFileSync(agentScriptPath, 'utf8');
    win.webContents.addScriptToExecuteOnNewDocument(agentScript);
  }

  const url = await startLocalServer();
  await win.loadURL(url);
  return win;
}

app.whenReady().then(async () => {
  ensureDataStore();
  const entry = path.join(webRoot, 'index.html');
  if (!fs.existsSync(entry)) throw new Error(`Cindrela Sales Radar web bundle missing: ${entry}`);

  ipcMain.handle('db:read', () => readDb());
  ipcMain.handle('db:write', (_event, value) => writeDb(value));
  ipcMain.handle('app:info', () => ({ isDev, version: app.getVersion(), userData: app.getPath('userData'), localOrigin: `http://127.0.0.1:${PORT}` }));
  ipcMain.handle('open:external', (_event, url) => {
    if (typeof url !== 'string' || !/^https?:\/\//i.test(url)) return false;
    shell.openExternal(url); return true;
  });

  await createWindow();
  app.on('activate', async () => { if (BrowserWindow.getAllWindows().length === 0) await createWindow(); });
}).catch((err) => {
  console.error('Cindrela Sales Radar startup failure:', err);
  app.quit();
});

app.on('window-all-closed', () => {
  if (localServer) localServer.close();
  if (process.platform !== 'darwin') app.quit();
});
