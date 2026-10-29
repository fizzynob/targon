const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('targonDesktop', {
  isElectron: true,
  minimize: () => ipcRenderer.invoke('window:minimize'),
  maximize: () => ipcRenderer.invoke('window:maximize'),
  close: () => ipcRenderer.invoke('window:close'),
  selectFolder: () => ipcRenderer.invoke('dialog:selectFolder'),
});
