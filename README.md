# Roguelike Dungeon 遊戲專案

## 專案概述
本專案是一個基於 Pygame 的 Roguelike Dungeon 遊戲，包含隨機地牢生成、多種武器與技能、角色能力系統、多樣化敵人，以及多人連線功能。遊戲採用 Python 開發，結合現代軟體工程實踐，包括 CI/CD 流程、Flake8 程式碼檢查、Docker 容器化、網站部署，以及 GitHub Actions 自動化工作流程。遊戲支持在本機運行，並計畫提供網頁版以實現多人連線。

### 主要功能
- **隨機地牢生成**：使用演算法生成獨特的地牢地圖，每次遊戲體驗不同。
- **多種武器與技能**：玩家可選擇不同武器（如劍、弓、法杖）與技能（如火球、治療術），並升級角色能力。
- **多樣化敵人**：不同類型的敵人（如骷髏、哥布林、巨魔），各有獨特行為與屬性。
- **多人連線**：支持多人透過 WebSocket 或類似技術進行協作或對戰。
- **本地運行**：使用 Pygame 在本機運行遊戲，確保流暢體驗。
- **網站部署**：將遊戲封裝為網頁版，透過 Docker 部署到雲端。
- **開發工具**：
  - **CI/CD**：使用 GitHub Actions 自動化測試、程式碼檢查與部署。
  - **Flake8**：確保程式碼符合 PEP 8 規範。
  - **Docker**：容器化應用程式，簡化開發與部署流程。

## 技術棧
- **前端與遊戲邏輯**：Python, Pygame（本機版），Pyodide（網頁版）
- **後端與多人連線**：FastAPI（WebSocket 實現多人連線）
- **程式碼質量**：Flake8, Pytest
- **容器化**：Docker, Docker Compose
- **CI/CD**：GitHub Actions
- **版本控制**：Git, GitHub
- **部署**：網頁版部署至雲端（如 AWS、Heroku 或 Vercel）

## 環境設置
### 先決條件
- Python 3.10+
- Pygame
- Docker
- Git
- GitHub 帳戶

### 本機安裝步驟
1. 克隆專案：
   ```bash
   git clone https://github.com/your-username/roguelike-dungeon.git
   cd roguelike-dungeon
   ```
2. 安裝 Python 依賴：
   ```bash
   pip install -r requirements.txt
   ```
3. 運行遊戲：
   ```bash
   python main.py
   ```

### Docker 安裝
1. 構建 Docker 映像：
   ```bash
   docker-compose build
   ```
2. 啟動容器：
   ```bash
   docker-compose up
   ```

## 專案結構
```
roguelike-dungeon/
├── assets/                # 圖片、音效等資源
├── src/                   # 遊戲源碼
│   ├── dungeon/           # 地牢生成邏輯
│   ├── entities/          # 玩家、敵人、物品
│   ├── skills/            # 技能與能力系統
│   ├── multiplayer/       # 多人連線邏輯
│   └── main.py            # 遊戲主程式
├── tests/                 # 單元測試
├── Dockerfile             # Docker 配置文件
├── docker-compose.yml     # Docker Compose 配置文件
├── .github/workflows/     # GitHub Actions 工作流程
├── requirements.txt       # Python 依賴
├── flake8.ini             # Flake8 配置
└── README.md              # 本文件
```

## 接下來的工作步驟
1. **遊戲核心開發**：
   - 實現隨機地牢生成演算法（如 BSP 或醉漢漫步）。
   - 設計玩家角色系統，包括武器、技能與能力升級。
   - 創建多樣化敵人，包含 AI 行為（如巡邏、追擊）。
2. **多人連線功能**：
   - 使用 FastAPI 與 WebSocket 實現多人連線。
   - 設計同步機制，確保地牢狀態與玩家動作一致。
3. **網頁版實現**：
   - 使用 Pyodide 將 Pygame 遊戲轉換為網頁版。
   - 優化網頁版性能，確保多人連線穩定。
4. **CI/CD 流程設置**：
   - 配置 GitHub Actions，自動運行 Flake8 檢查與 Pytest 測試。
   - 實現自動部署至雲端平台。
5. **程式碼質量與測試**：
   - 使用 Flake8 檢查程式碼規範。
   - 編寫單元測試，覆蓋地牢生成、技能系統與敵人 AI。
6. **容器化與部署**：
   - 編寫 Dockerfile 與 docker-compose.yml，封裝遊戲與後端服務。
   - 部署網頁版至雲端（如 AWS ECS 或 Heroku）。
7. **文件與優化**：
   - 完善 README 與開發者文檔。
   - 優化遊戲性能，特別是多人連線與網頁版。

## 貢獻指南
1. Fork 本專案。
2. 創建功能分支：`git checkout -b feature/awesome-feature`。
3. 提交變更：`git commit -m "Add awesome feature"`。
4. 推送到遠端：`git push origin feature/awesome-feature`。
5. 提交 Pull Request。

## 許可證
本專案採用 MIT 許可證，詳見 LICENSE 文件。
