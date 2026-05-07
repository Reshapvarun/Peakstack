const { app, BrowserWindow } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let backendProcess;

async function checkBackend(url) {
  try {
    const res = await new Promise((resolve) => {
      const http = require('http');
      http.get(url, (res) => resolve(res.statusCode === 200)).on('error', () => resolve(false));
    });
    return res;
  } catch (e) {
    return false;
  }
}

function startBackend() {
  console.log('[Electron] Starting FastAPI Backend...');
  
  // In dev, we use the relative path to the app module
  // In production, we'd point to the bundled executable or script
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  const backendPath = path.join(__dirname, '..', 'app', 'api', 'main.py');
  
  backendProcess = spawn(pythonCmd, ['-m', 'app.api.main'], {
    cwd: path.join(__dirname, '..'),
    env: { 
      ...process.env, 
      PORT: '8000', 
      PEAKSTACK_MODE: 'desktop' 
    }
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`[Backend] ${data}`);
  });

  backendProcess.stderr.on('data', (data) => {
    console.error(`[Backend Error] ${data}`);
  });

  backendProcess.on('close', (code) => {
    console.log(`[Backend] Process exited with code ${code}`);
  });
}

async function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1920,
    height: 1080,
    backgroundColor: '#0f172a',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
      devTools: false // Disable devtools in production
    },
    icon: path.join(__dirname, 'assets', 'icon.png')
  });

  // Start backend and wait for health check
  startBackend();

  let ready = false;
  let retries = 0;
  while (!ready && retries < 20) {
    console.log(`[Electron] Checking backend health... (${retries + 1}/20)`);
    ready = await checkBackend('http://127.0.0.1:8000/docs'); // FastAPI docs or any endpoint
    if (!ready) {
      await new Promise(r => setTimeout(r, 1000));
      retries++;
    }
  }

  if (ready) {
    console.log('[Electron] Backend ready. Loading UI...');
    mainWindow.loadURL('http://127.0.0.1:8000');
  } else {
    console.error('[Electron] Backend failed to start.');
    mainWindow.loadFile(path.join(__dirname, 'error.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('will-quit', () => {
  if (backendProcess) {
    console.log('[Electron] Killing backend process...');
    backendProcess.kill();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});
