# Alchemy RPG - 遊戲設計文檔

## 概述

Alchemy RPG 是一款結合煉金術與 Roguelike 元素的動作 RPG 遊戲。玩家通過探索程序生成的地牢、收集材料、合成技能與增益來挑戰敵人和 Boss。

---

## 核心系統

### 1. 屬性系統 (11 種元素)

遊戲採用 11 種元素屬性，構成複雜的相剋與合成系統：

| 元素 | 英文 | 對應 Buff | 效果 |
|------|------|-----------|------|
| 無屬性 | Untyped | - | 中性基礎 |
| 金 | Metal | Tear (撕裂) | 降低防禦 20% |
| 木 | Wood | Entangled (纏繞) | 無法移動 |
| 水 | Water | Humid (潮濕) | 降低雷/木抗性 20% |
| 火 | Fire | Burn (燃燒) | 每秒 5% 當前生命傷害 |
| 土 | Earth | Dist (塵土) | 降低移速與視野 10% |
| 風 | Wind | Disorder (紊亂) | 延長所有 Buff 持續時間 |
| 雷 | Electric | Paralysis (麻痺) | 無法移動與攻擊 |
| 冰 | Ice | Cold (寒冷) | 降低移速 40% |
| 光 | Light | Blind (致盲) | 降低視野 30% |
| 暗 | Dark | Erosion (侵蝕) | 每秒 5% 最大生命傷害 |

---

### 2. 元素相剋表

```
           弱點 (1.5x)
金 → 木 → 水 → 火 → 土 → 金
         ↓         ↓
        (木→風)   (火→冰)
         
土 → 雷 → 水
風 → 火
冰 → 木
光 ↔ 暗 (互相剋制)
```

**傷害倍率**：
- 剋制：1.5x 傷害
- 被剋制：0.5x 傷害
- 中性：1.0x 傷害

---

### 3. Buff 合成系統

當目標同時擁有兩種基礎 Buff 時，會觸發合成反應：

| 組合 | 合成結果 | 效果 |
|------|----------|------|
| Burn + Humid | Fog (霧) | 視野 -90% |
| Burn + Mud | Petrochemical (石化) | 無法動作，抗性 +90% |
| Burn + Freeze | Vulnerable (脆弱) | 全抗性 -50% |
| Burn + Entangled | Backdraft (回燃) | 即時 20% 最大生命傷害 |
| Humid + Cold | Freeze (冰凍) | 完全無法動作 |
| Humid + Paralysis | Taser (電擊) | 無法動作 + 每秒 10% 生命傷害 |
| Humid + Dist | Mud (泥濘) | 移速 -90% |
| Humid + Tear | Bleeding (流血) | 防禦 -20% + 已損生命 10% 傷害/秒 |
| Disorder + Dist | Sandstorm (沙暴) | 移速 -30%，視野 -50% |
| Blind + Erosion | Annihilation (湮滅) | 即時 20% 最大生命傷害 |

**抵銷組合** (產生 Empty Buff)：
- Mud + Humid
- Fog + Disorder
- Entangled + Disorder
- Tear + Dist / Entangled
- Paralysis + Dist

---

## 地牢生成算法

### BSP (Binary Space Partitioning) 演算法

地牢生成使用 BSP 樹遞歸分割空間：

```
1. 初始化：建立覆蓋整個地圖的根節點
2. 遞歸分割：
   - 若達到最大深度或空間太小，停止
   - 根據長寬比選擇分割方向（較長邊優先）
   - 在合法範圍內隨機選擇分割點
   - 建立左右子節點
3. 收集葉節點：所有葉節點成為房間的放置區域
4. 在每個葉節點內生成房間
5. 使用 MST 連接房間中心
6. 沿連線生成走廊
```

**配置參數**：
- `max_split_depth`: 最大分割深度 (預設 6)
- `min_split_size`: 最小分割尺寸
- `min_room_size`: 最小房間尺寸 (預設 15)
- `room_gap`: 房間間最小間距 (預設 2)

### 房間類型

| 類型 | 說明 |
|------|------|
| START | 玩家出生點 |
| END | 終點傳送門 |
| LOBBY | 大廳 (安全區) |
| MONSTER | 怪物房 (80%) |
| TRAP | 陷阱房 (10%) |
| REWARD | 獎勵房 (10%) |
| BOSS | Boss 房 |
| NPC | NPC 房 |

---

## ECS 架構

### 核心組件 (Components)

| 組件 | 用途 |
|------|------|
| Position | 世界座標 |
| Velocity | 移動向量與速度 |
| Health | 生命值、護盾、再生 |
| Combat | 攻擊力、元素、穿透 |
| Defense | 防禦、閃避、抗性 |
| Buffs | 活躍 Buff 列表 |
| AI | 行為樹、動作列表 |
| PlayerComponent | 技能鏈、能量 |
| Collider | 碰撞體積 |
| Renderable | 視覺表現 |

### 核心系統 (Systems)

| 系統 | 職責 |
|------|------|
| MovementSystem | 處理移動與碰撞 |
| CombatSystem | 傷害計算與碰撞檢測 |
| HealthSystem | 傷害處理、死亡邏輯 |
| BuffSystem | Buff 更新與合成 |
| AISystem | 執行敵人行為樹 |
| RenderSystem | 繪製所有實體 |

---

## AI 行為樹

### 節點類型

- **Selector**: 依序嘗試子節點直到成功
- **Sequence**: 依序執行子節點直到失敗
- **ConditionNode**: 條件判斷分支

### 動作類型

| 動作 | 說明 |
|------|------|
| ChaseAction | 追蹤目標 |
| AttackAction | 發射子彈 |
| WaitAction | 等待/硬直 |
| PatrolAction | 巡邏路徑點 |
| DodgeAction | 閃避子彈 |
| DashAction | 衝刺攻擊 |
| FanAttackAction | 扇形彈幕 |
| RadialBurstAction | 環形彈幕 |
| StrafeAction | 側向走位 |

---

## 技能系統

### 技能鏈

- 最多 9 條技能鏈
- 每條技能鏈最多 8 個技能槽
- 使用滑鼠滾輪/數字鍵切換技能鏈
- 技能依照順序自動循環施放

### 增幅器 (Amplifier)

可為技能附加額外效果：
- 元素屬性
- 傷害加成
- 範圍擴大
- 持續時間延長

---

## 傷害計算公式

```
最終傷害 = (基礎傷害 × 屬性倍率 × Buff倍率 - 防禦值) × (1 - 抗性)

其中：
- 屬性倍率 = 根據元素相剋表 (0.5 / 1.0 / 1.5)
- Buff倍率 = 來自攻擊者的 damage_multiplier
- 抗性 = 來自目標的 Defense.resistances[element]
```

**百分比傷害**：
- `max_hp_percentage_damage`: 最大生命百分比
- `current_hp_percentage_damage`: 當前生命百分比
- `lose_hp_percentage_damage`: 已損生命百分比

---

## 資源路徑

| 類型 | 路徑 |
|------|------|
| 圖片 | `assets/images/` |
| 音效 | `assets/audio/` |
| 字型 | `assets/fonts/` |
| 地牢配置 | `data/dungeon_flows/` |
| 預置資料 | `data/prefabs/` |
| 存檔 | `data/saves/` |

---

## 技術架構

```
src/alchemy_rpg/
├── core/           # 引擎核心 (Engine, EventBus, Input)
├── ecs/            # 實體組件系統
│   ├── components/ # 純資料組件
│   └── systems/    # 邏輯處理系統
├── dungeon/        # 地牢生成
│   └── algorithms/ # 生成算法
├── ui/             # 選單系統
└── utils/          # 工具函數
```
