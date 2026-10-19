import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')

_default_config = None

def get_config():
    """載入並回傳設定字典。若已載入則回傳快取版本。"""
    global _default_config
    if _default_config is None:
        _default_config = load_config(CONFIG_FILE)
    return _default_config

def load_config(path):
    """從 JSON 檔案載入設定。"""
    if not os.path.exists(path):
        raise FileNotFoundError(f"設定檔不存在: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config, path=None):
    """將設定儲存到 JSON 檔案。"""
    if path is None:
        path = CONFIG_FILE
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def get_modbus_mode():
    """回傳目前的 Modbus 模式: 'tcp' 或 'rtu'"""
    return get_config().get('modbus_mode', 'tcp').lower()

def get_machine_name():
    """回傳機台名稱"""
    return get_config().get('machine_name', 'F01')

def get_tcp_settings():
    """回傳 Modbus TCP 設定字典"""
    return get_config().get('modbus_tcp', {})

def get_rtu_settings():
    """回傳 Modbus RTU 設定字典"""
    return get_config().get('modbus_rtu', {})

def get_modbus_requests():
    """回傳 Modbus 請求列表"""
    return get_config().get('modbus_requests', [])

def get_sql_settings():
    """回傳 SQL Server 連線設定字典"""
    return get_config().get('sql_server', {})

def build_sql_connection_string(sql_settings=None):
    """根據設定建立 SQLAlchemy 連線字串"""
    if sql_settings is None:
        sql_settings = get_sql_settings()
    host = sql_settings.get('host', 'localhost')
    database = sql_settings.get('database', '')
    username = sql_settings.get('username', '')
    password = sql_settings.get('password', '')
    driver = sql_settings.get('driver', 'ODBC Driver 17 for SQL Server')
    return f'mssql+pyodbc://{username}:{password}@{host}/{database}?driver={driver}'
