# Alchemy RPG Game

## 專案概述
本專案是一個基於 Pygame 的屬性交互煉金 RPG 遊戲，結合隨機生成的副本、屬性覺醒、煉金合成系統、即時戰鬥以及多人連線功能。遊戲採用 Python 開發，融入物件導向設計與現代軟體工程實踐，包括 CI/CD 流程、Flake8 程式碼檢查、Docker 容器化、網站部署，以及 GitHub Actions 自動化工作流程。遊戲支持本機運行，並計畫提供網頁版以實現多人連線。

### 主要功能
- **隨機副本生成**：使用 BSP 演算法生成獨特的副本地圖，提供類肉鴿的遊戲體驗。
- **屬性交互與煉金系統**：玩家可透過煉金鍋合成技能與增幅詞條（如傷害、穿透、減傷、閃避率），結合屬性覺醒（魔法飛彈、魔法盾、魔法布）。
- **多樣化敵人與 NPC**：包含不同敵人（如敵人1）與 NPC（如魔法水晶、煉金鍋、交易者），各具獨特行為與互動。
- **多人連線**：透過 WebSocket 或類似技術實現協作或對戰。
- **本地運行**：使用 Pygame 提供流暢的本機遊戲體驗。
- **網站部署**：將遊戲封裝為網頁版，透過 Docker 部署至雲端。
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
- **資料儲存**：JSON（技能庫、組合與儲存檔，如 skill_library.json, skill_combo.json, storage.json）

## 環境設置
### 先決條件
- Python 3.12+
- Pygame
- Docker
- Git
- GitHub 帳戶

### 本機安裝步驟
1. 克隆專案：
   ```bash
   git clone https://github.com/your-username/alchemy-rpg-game.git
   cd alchemy-rpg-game
   ```
2. 安裝 Python 依賴：
   ```bash
   pip install -r requirements.txt
   ```
3. 運行遊戲：
   ```bash
   python src/main.py
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
alchemy-rpg-game/
├── assets/                # 圖片、音效等資源
├── src/                   # 遊戲源碼
│   ├── dungeon/           # 副本生成邏輯 (dungeon.py, bsp_node.py, room.py, bridge.py)
│   ├── entities/          # 玩家、敵人、NPC (player.py, enemy/, npc/, bullet/, buff/)
│   ├── skill/             # 技能與煉金系統 (skill.py, skill_combo.py, skill_library.json)
│   ├── menus/             # 選單邏輯 (main_menu.py, crystal_menu.py, stat_menu.py, etc.)
│   ├── utils/             # 輔助模組 (helpers.py, events.py, storage.json)
│   ├── environment/       # 環境模組
│   ├── audio_manager.py   # 音效管理
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
   - 實現隨機副本生成演算法（基於 BSP，包含房間與橋樑生成）。
   - 設計玩家能力系統（攻擊、防禦、移動、血量）與煉金合成（主材、副材、屬性、增幅劑）。
   - 創建敵人 AI（巡邏、追擊）與 NPC 互動（魔法水晶、煉金鍋）。
2. **多人連線功能**：
   - 使用 FastAPI 與 WebSocket 實現多人連線，同步玩家動作與副本狀態。
   - 設計事件處理（events.py）以支持多人互動。
3. **網頁版實現**：
   - 使用 Pyodide 將 Pygame 遊戲轉換為網頁版，支援多人連線。
   - 優化網頁版性能，特別是即時戰鬥與屬性交互。
4. **CI/CD 流程設置**：
   - 配置 GitHub Actions，自動運行 Flake8 檢查與 Pytest 測試。
   - 實現自動部署至雲端平台（如 AWS ECS 或 Heroku）。
5. **程式碼質量與測試**：
   - 使用 Flake8 確保程式碼符合 PEP 8 規範。
   - 編寫單元測試，覆蓋副本生成、技能合成、敵人 AI 與屬性交互。
6. **容器化與部署**：
   - 編寫 Dockerfile 與 docker-compose.yml，封裝遊戲與後端服務。
   - 部署網頁版至雲端，確保多人連線穩定。
7. **文件與優化**：
   - 完善 README 與開發者文檔，涵蓋類別設計與屬性交互邏輯。
   - 優化遊戲性能，特別是多人連線、即時戰鬥與網頁版渲染。

## 貢獻指南
1. Fork 本專案。
2. 創建功能分支：`git checkout -b feature/awesome-feature`。
3. 提交變更：`git commit -m "Add awesome feature"`。
4. 推送到遠端：`git push origin feature/awesome-feature`。
5. 提交 Pull Request。

## 許可證
本專案採用 MIT 許可證，詳見 LICENSE 文件。
