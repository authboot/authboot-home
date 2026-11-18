import os
import shutil
import zipfile

ROOT = os.path.abspath("electron-react-paypal")
ZIP_PATH = os.path.abspath("electron-react-paypal.zip")

if os.path.exists(ROOT):
    shutil.rmtree(ROOT)

if os.path.exists(ZIP_PATH):
    os.remove(ZIP_PATH)


files = {
    "package.json": r'''
{
  "name": "electron-react-paypal",
  "version": "1.0.0",
  "private": true,
  "main": "dist-electron/main.js",
  "scripts": {
    "dev": "concurrently -k \"vite --host 127.0.0.1\" \"wait-on http://127.0.0.1:5173 && cross-env ELECTRON_RENDERER_URL=http://127.0.0.1:5173 electron .\"",
    "build": "tsc -b && vite build && tsc -p tsconfig.electron.json",
    "start": "electron ."
  },
  "dependencies": {
    "@paypal/react-paypal-js": "^8.8.3",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/node": "^22.10.2",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "concurrently": "^9.1.2",
    "cross-env": "^7.0.3",
    "electron": "^34.0.0",
    "typescript": "^5.7.2",
    "vite": "^6.0.5",
    "wait-on": "^8.0.1"
  }
}
''',

    "index.html": r'''
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />

    <meta
      http-equiv="Content-Security-Policy"
      content="
        default-src 'self';
        script-src 'self' https://*.paypal.com https://*.paypalobjects.com;
        connect-src 'self' https://*.paypal.com https://*.paypalobjects.com http://127.0.0.1:8080;
        frame-src 'self' https://*.paypal.com https://*.paypalobjects.com;
        child-src 'self' https://*.paypal.com https://*.paypalobjects.com;
        img-src 'self' data: https://*.paypal.com https://*.paypalobjects.com;
        style-src 'self' 'unsafe-inline' https://*.paypal.com https://*.paypalobjects.com;
      "
    />

    <meta
      name="viewport"
      content="width=device-width, initial-scale=1.0"
    />

    <title>Electron PayPal Demo</title>
  </head>

  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
''',

    "vite.config.ts": r'''
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173
  },
  build: {
    outDir: "dist"
  }
});
''',

    "tsconfig.json": r'''
{
  "files": [],
  "references": [
    {
      "path": "./tsconfig.app.json"
    },
    {
      "path": "./tsconfig.electron.json"
    }
  ]
}
''',

    "tsconfig.app.json": r'''
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": [
      "ES2020",
      "DOM",
      "DOM.Iterable"
    ],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": [
    "src"
  ]
}
''',

    "tsconfig.electron.json": r'''
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "CommonJS",
    "moduleResolution": "Node",
    "outDir": "dist-electron",
    "rootDir": "electron",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "types": [
      "node"
    ]
  },
  "include": [
    "electron/**/*.ts"
  ]
}
''',

    "electron/main.ts": r'''
import {
  app,
  BrowserWindow,
  shell
} from "electron";

import path from "node:path";

const isDev = Boolean(
  process.env.ELECTRON_RENDERER_URL
);

function createWindow() {
  const win = new BrowserWindow({
    width: 1100,
    height: 800,
    minWidth: 900,
    minHeight: 650,

    webPreferences: {
      preload: path.join(
        __dirname,
        "preload.js"
      ),

      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true
    }
  });

  /*
   * PayPal Checkout 可能会使用 window.open。
   *
   * PayPal 域允许在 Electron 中打开子窗口。
   * 其他外部 URL 使用系统默认浏览器打开。
   */
  win.webContents.setWindowOpenHandler(
    ({ url }) => {
      if (
        url.startsWith(
          "https://www.paypal.com/"
        ) ||
        url.startsWith(
          "https://www.paypalobjects.com/"
        )
      ) {
        return {
          action: "allow",

          overrideBrowserWindowOptions: {
            width: 500,
            height: 700,

            webPreferences: {
              nodeIntegration: false,
              contextIsolation: true,
              sandbox: true,
              webSecurity: true
            }
          }
        };
      }

      void shell.openExternal(url);

      return {
        action: "deny"
      };
    }
  );

  if (isDev) {
    void win.loadURL(
      process.env.ELECTRON_RENDERER_URL!
    );

    win.webContents.openDevTools();
  } else {
    void win.loadFile(
      path.join(
        app.getAppPath(),
        "dist",
        "index.html"
      )
    );
  }
}

app.whenReady().then(() => {
  createWindow();

  app.on(
    "activate",
    () => {
      if (
        BrowserWindow.getAllWindows()
          .length === 0
      ) {
        createWindow();
      }
    }
  );
});

app.on(
  "window-all-closed",
  () => {
    if (process.platform !== "darwin") {
      app.quit();
    }
  }
);
''',

    "electron/preload.ts": r'''
import { contextBridge } from "electron";

contextBridge.exposeInMainWorld(
  "electronAPI",
  {
    platform: process.platform
  }
);
''',

    "src/vite-env.d.ts": r'''
/// <reference types="vite/client" />

interface Window {
  electronAPI?: {
    platform: string;
  };
}
''',

    "src/main.tsx": r'''
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./styles.css";

ReactDOM.createRoot(
  document.getElementById("root")!
).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
''',

    "src/App.tsx": r'''
import { useState } from "react";

import {
  PayPalButtons,
  PayPalScriptProvider
} from "@paypal/react-paypal-js";


const PAYPAL_CLIENT_ID =
  import.meta.env.VITE_PAYPAL_CLIENT_ID ||
  "YOUR_CLIENT_ID";


const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8080";


export default function App() {
  const [message, setMessage] =
    useState("等待支付");

  const [orderId, setOrderId] =
    useState("");


  /*
   * 创建 PayPal Order
   *
   * 注意：
   *
   * Electron
   *   ↓
   * Go Backend
   *   ↓
   * PayPal CreateOrder
   *
   * PayPal Client Secret 绝对不要放在 Electron。
   */
  async function createOrder() {
    setMessage(
      "正在创建 PayPal Order..."
    );

    const response = await fetch(
      `${API_BASE_URL}/api/paypal/orders`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json"
        },

        body: JSON.stringify({
          skuCode: "vip_monthly"
        })
      }
    );


    if (!response.ok) {
      throw new Error(
        `create order failed: ${response.status}`
      );
    }


    const data =
      await response.json();


    if (!data.orderId) {
      throw new Error(
        "Backend did not return orderId"
      );
    }


    setOrderId(
      data.orderId
    );


    return data.orderId;
  }


  /*
   * Capture PayPal Order
   */
  async function captureOrder(
    paypalOrderId: string
  ) {
    setMessage(
      "正在确认支付..."
    );


    const response = await fetch(
      `${API_BASE_URL}/api/paypal/orders/${paypalOrderId}/capture`,
      {
        method: "POST",

        headers: {
          "Content-Type":
            "application/json"
        }
      }
    );


    if (!response.ok) {
      throw new Error(
        `capture failed: ${response.status}`
      );
    }


    const data =
      await response.json();


    if (
      data.status ===
      "COMPLETED"
    ) {
      setMessage(
        "支付成功"
      );
    } else {
      setMessage(
        `支付状态：${
          data.status ||
          "UNKNOWN"
        }`
      );
    }
  }


  return (
    <main className="page">
      <section className="card">

        <div className="badge">
          Electron + React + PayPal
        </div>


        <h1>
          PayPal 支付 Demo
        </h1>


        <p className="description">
          Electron Renderer 中使用
          PayPal JavaScript SDK。
          Order 创建和 Capture
          均由 Go 后端完成。
        </p>


        <div className="payment-box">

          <PayPalScriptProvider
            options={{
              clientId:
                PAYPAL_CLIENT_ID,

              currency: "USD",

              intent: "capture"
            }}
          >

            <PayPalButtons
              style={{
                layout:
                  "vertical",

                shape:
                  "rect",

                label:
                  "paypal"
              }}


              createOrder={
                createOrder
              }


              onApprove={
                async (data) => {
                  try {
                    await captureOrder(
                      data.orderID
                    );
                  } catch (error) {
                    console.error(
                      error
                    );

                    setMessage(
                      "支付确认失败，请检查后端日志"
                    );
                  }
                }
              }


              onCancel={() => {
                setMessage(
                  "用户取消支付"
                );
              }}


              onError={(error) => {
                console.error(
                  "PayPal error:",
                  error
                );

                setMessage(
                  "PayPal 支付发生错误"
                );
              }}
            />

          </PayPalScriptProvider>

        </div>


        <div className="status">
          <strong>
            状态：
          </strong>

          {message}
        </div>


        {orderId && (
          <div className="order">

            PayPal Order ID：

            <code>
              {orderId}
            </code>

          </div>
        )}

      </section>
    </main>
  );
}
''',

    "src/styles.css": r'''
* {
  box-sizing: border-box;
}


body {
  margin: 0;

  min-width: 900px;

  min-height: 100vh;

  font-family:
    Inter,
    -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    "PingFang SC",
    "Microsoft YaHei",
    sans-serif;

  background: #f5f7fb;

  color: #111827;
}


.page {
  min-height: 100vh;

  display: flex;

  justify-content: center;

  align-items: center;

  padding: 40px;
}


.card {
  width: 480px;

  padding: 36px;

  border-radius: 20px;

  background: white;

  box-shadow:
    0 16px 50px
    rgba(15, 23, 42, 0.10);
}


.badge {
  display: inline-block;

  padding: 6px 10px;

  border-radius: 999px;

  background: #f1f5f9;

  color: #475569;

  font-size: 12px;

  font-weight: 600;
}


h1 {
  margin: 18px 0 10px;

  font-size: 30px;
}


.description {
  color: #64748b;

  line-height: 1.7;

  font-size: 14px;
}


.payment-box {
  margin-top: 28px;

  padding: 20px;

  border: 1px solid #e5e7eb;

  border-radius: 14px;

  background: #fafafa;
}


.status {
  margin-top: 20px;

  padding: 12px 14px;

  border-radius: 10px;

  background: #f8fafc;

  font-size: 14px;
}


.order {
  margin-top: 12px;

  color: #64748b;

  font-size: 12px;

  word-break: break-all;
}


code {
  color: #334155;
}
''',

    ".env.example": r'''
VITE_PAYPAL_CLIENT_ID=YOUR_CLIENT_ID
VITE_API_BASE_URL=http://127.0.0.1:8080
''',

    ".gitignore": r'''
node_modules
dist
dist-electron
.env
.DS_Store
''',

    "README.md": r'''
# Electron + React + PayPal

Electron + React + TypeScript + Vite + PayPal JS SDK Demo。

## 安装

```bash
npm install
