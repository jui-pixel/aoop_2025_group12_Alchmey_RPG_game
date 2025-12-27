import pytest
import json
import os
from pathlib import Path
from src.dungeon.config.config_loader import LevelConfigLoader, create_default_level_config
from src.dungeon.config.level_config import LevelConfig

# --- Fixtures ---

@pytest.fixture
def temp_loader(tmp_path):
    """
    創建一個指向臨時目錄的 LevelConfigLoader 實例。
    tmp_path 是 pytest 內建的 fixture，測試結束後會自動清理。
    """
    return LevelConfigLoader(config_dir=str(tmp_path))

@pytest.fixture
def sample_level_config():
    """創建一個標準的測試用關卡配置物件"""
    return create_default_level_config(level_id=1)

# --- 測試案例 ---

def test_save_and_load_success(temp_loader, sample_level_config):
    """測試完整的保存與讀取流程 (Happy Path)"""
    # 1. 保存配置
    success = temp_loader.save_level(sample_level_config)
    assert success is True
    
    # 檢查文件是否真的建立
    expected_path = temp_loader.config_dir / "level_1.json"
    assert expected_path.exists()
    
    # 2. 讀取配置
    loaded_config = temp_loader.load_level(1)
    
    # 3. 驗證數據完整性
    assert loaded_config is not None
    assert isinstance(loaded_config, LevelConfig)
    assert loaded_config.level_id == 1
    assert loaded_config.grid_width == sample_level_config.grid_width
    # 驗證嵌套的怪物池配置是否正確加載
    assert len(loaded_config.monster_pool.monsters) == len(sample_level_config.monster_pool.monsters)

def test_load_non_existent_level(temp_loader):
    """測試讀取不存在的關卡"""
    result = temp_loader.load_level(999)
    assert result is None

def test_load_malformed_json(temp_loader):
    """測試讀取格式錯誤的 JSON 文件 (語法錯誤)"""
    # 手動創建一個損壞的 JSON 文件
    bad_file = temp_loader.config_dir / "level_99.json"
    bad_file.write_text("{ this is not valid json ", encoding='utf-8')
    
    result = temp_loader.load_level(99)
    assert result is None

def test_load_invalid_config_schema(temp_loader, sample_level_config):
    """
    測試讀取雖然 JSON 語法正確，但邏輯驗證失敗的配置
    (例如：grid_width 為負數)
    """
    # 先保存一個正常的
    temp_loader.save_level(sample_level_config, level_id=2)
    
    # 手動讀取、修改為非法數據、再寫回
    file_path = temp_loader.config_dir / "level_2.json"
    
    # [修正] 這裡必須顯式指定 encoding='utf-8'，否則 Windows 會用 cp950 報錯
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 破壞數據：設置負的網格寬度
    data["dungeon_config"]["grid_width"] = -50
    
    # [修正] 寫回時也要保持 utf-8
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
        
    # 嘗試載入
    result = temp_loader.load_level(2)
    
    # 預期 validate() 會失敗，所以返回 None
    assert result is None

def test_list_available_levels(temp_loader, sample_level_config):
    """測試列出目錄下所有可用的關卡 ID"""
    # 創建幾個不同的關卡文件
    temp_loader.save_level(sample_level_config, level_id=1)
    temp_loader.save_level(sample_level_config, level_id=5)
    temp_loader.save_level(sample_level_config, level_id=10)
    
    # 創建一個不相關的文件干擾測試
    (temp_loader.config_dir / "other_config.json").touch()
    
    levels = temp_loader.list_available_levels()
    
    assert len(levels) == 3
    assert levels == [1, 5, 10]  # 確保有排序

def test_create_default_config_logic():
    """測試預設配置生成器的邏輯"""
    # Level 1
    config_lv1 = create_default_level_config(1)
    assert config_lv1.level_id == 1
    
    # Level 5 (應該更難，怪物更多)
    config_lv5 = create_default_level_config(5)
    assert config_lv5.level_id == 5
    
    # 檢查難度提升邏輯 (Level 5 應該比 Level 1 有更多怪物類型)
    assert len(config_lv5.monster_pool.monsters) > len(config_lv1.monster_pool.monsters)
    
    # 檢查地圖尺寸擴張
    assert config_lv5.grid_width > config_lv1.grid_width

def test_load_from_specific_path(temp_loader, sample_level_config):
    """測試從指定路徑載入配置"""
    # 保存到一個自定義名稱的文件
    custom_path = temp_loader.config_dir / "custom_dungeon.json"
    
    # 我們手動將物件轉為 dict 並存入，模擬外部文件的創建
    data = sample_level_config.to_dict()
    with open(custom_path, 'w', encoding='utf-8') as f:
        json.dump(data, f)
        
    # 測試載入
    loaded_config = temp_loader.load_level_from_file(str(custom_path))
    
    assert loaded_config is not None
    assert loaded_config.level_name == sample_level_config.level_name

def test_directory_auto_creation(tmp_path):
    """測試當目錄不存在時，save_level 是否會自動創建目錄"""
    new_dir = tmp_path / "subdir" / "configs"
    # 注意：這裡傳入的路徑還不存在
    loader = LevelConfigLoader(config_dir=str(new_dir))
    
    config = create_default_level_config(1)
    success = loader.save_level(config)
    
    assert success is True
    assert new_dir.exists()
    assert (new_dir / "level_1.json").exists()