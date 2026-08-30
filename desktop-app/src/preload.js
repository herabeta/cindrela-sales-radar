const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('cindrelaDesktop', {
  isDesktop: true,
  readDatabase: () => ipcRenderer.invoke('db:read'),
  writeDatabase: (value) => ipcRenderer.invoke('db:write', value),
  getAppInfo: () => ipcRenderer.invoke('app:info'),
  openExternal: (url) => ipcRenderer.invoke('open:external', url)
});
