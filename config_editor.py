"""
設定檔編輯器
可用於程式內動態修改設定，或作為命令列工具使用。

用法 (命令列):
    python config_editor.py [選項]

選項:
    --mode {tcp|rtu}          設定 Modbus 模式
    --machine NAME            設定機台名稱
    --tcp-host HOST           設定 TCP 主機
    --tcp-port PORT           設定 TCP 埠號
    --rtu-port PORT           設定 RTU 串口
    --rtu-baudrate RATE       設定 RTU 鮑率
    --sql-host HOST           設定 SQL Server 主機
    --sql-database DB         設定 SQL 資料庫名稱
    --sql-username USER       設定 SQL 使用者名稱
    --sql-password PASS       設定 SQL 密碼
    --show                    顯示目前設定
"""

import argparse
from config import get_config, save_config, build_sql_connection_string


def show_config():
    """顯示目前所有設定"""
    cfg = get_config()
    print("=" * 50)
    print(" 目前設定")
    print("=" * 50)
    print(f" 機台名稱     : {cfg.get('machine_name', 'N/A')}")
    print(f" Modbus 模式  : {cfg.get('modbus_mode', 'N/A')}")
    print("-" * 50)
    print(" Modbus TCP:")
    tcp = cfg.get('modbus_tcp', {})
    print(f"   主機       : {tcp.get('host', 'N/A')}")
    print(f"   埠號       : {tcp.get('port', 'N/A')}")
    print("-" * 50)
    print(" Modbus RTU:")
    rtu = cfg.get('modbus_rtu', {})
    print(f"   串口       : {rtu.get('port', 'N/A')}")
    print(f"   鮑率       : {rtu.get('baudrate', 'N/A')}")
    print(f"   資料位元   : {rtu.get('bytesize', 'N/A')}")
    print(f"   同位檢查   : {rtu.get('parity', 'N/A')}")
    print(f"   停止位元   : {rtu.get('stopbits', 'N/A')}")
    print("-" * 50)
    print(" SQL Server:")
    sql = cfg.get('sql_server', {})
    print(f"   主機       : {sql.get('host', 'N/A')}")
    print(f"   資料庫     : {sql.get('database', 'N/A')}")
    print(f"   使用者     : {sql.get('username', 'N/A')}")
    print(f"   驅動       : {sql.get('driver', 'N/A')}")
    print(f"   連線字串   : {build_sql_connection_string()}")
    print("=" * 50)


def update_config(args):
    """根據命令列參數更新設定"""
    cfg = get_config()
    updated = False

    if args.mode is not None:
        cfg['modbus_mode'] = args.mode.lower()
        updated = True

    if args.machine is not None:
        cfg['machine_name'] = args.machine
        updated = True

    if args.tcp_host is not None:
        cfg['modbus_tcp']['host'] = args.tcp_host
        updated = True

    if args.tcp_port is not None:
        cfg['modbus_tcp']['port'] = args.tcp_port
        updated = True

    if args.rtu_port is not None:
        cfg['modbus_rtu']['port'] = args.rtu_port
        updated = True

    if args.rtu_baudrate is not None:
        cfg['modbus_rtu']['baudrate'] = args.rtu_baudrate
        updated = True

    if args.sql_host is not None:
        cfg['sql_server']['host'] = args.sql_host
        updated = True

    if args.sql_database is not None:
        cfg['sql_server']['database'] = args.sql_database
        updated = True

    if args.sql_username is not None:
        cfg['sql_server']['username'] = args.sql_username
        updated = True

    if args.sql_password is not None:
        cfg['sql_server']['password'] = args.sql_password
        updated = True

    if updated:
        save_config(cfg)
        print("設定已更新並儲存。")
    else:
        print("沒有提供任何更新參數。")


def main():
    parser = argparse.ArgumentParser(description='NWVN HeatOilDataCollector 設定檔編輯器')
    parser.add_argument('--mode', choices=['tcp', 'rtu'], help='設定 Modbus 模式')
    parser.add_argument('--machine', help='設定機台名稱')
    parser.add_argument('--tcp-host', help='設定 TCP 主機 IP')
    parser.add_argument('--tcp-port', type=int, help='設定 TCP 埠號')
    parser.add_argument('--rtu-port', help='設定 RTU 串口 (例如 COM1)')
    parser.add_argument('--rtu-baudrate', type=int, help='設定 RTU 鮑率')
    parser.add_argument('--sql-host', help='設定 SQL Server 主機')
    parser.add_argument('--sql-database', help='設定 SQL 資料庫名稱')
    parser.add_argument('--sql-username', help='設定 SQL 使用者名稱')
    parser.add_argument('--sql-password', help='設定 SQL 密碼')
    parser.add_argument('--show', action='store_true', help='顯示目前設定')

    args = parser.parse_args()

    if args.show or (not any(vars(args).values())):
        show_config()
    else:
        update_config(args)
        show_config()


if __name__ == '__main__':
    main()
