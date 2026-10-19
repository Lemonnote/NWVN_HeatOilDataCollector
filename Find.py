import os
import sys

# 獲取 Python 安裝目錄
python_install_dir = os.path.dirname(sys.executable)
print("Python 安裝目錄:", python_install_dir)

# 構建 Scripts 目錄的路徑
scripts_dir = os.path.join(python_install_dir, 'Scripts')
print("Scripts 目錄:", scripts_dir)