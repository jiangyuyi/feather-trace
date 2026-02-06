@echo off
chcp 65001 >nul
echo ============================================
echo WingScribe 数据库初始化
echo ============================================

cd /d "%~dp0"

REM 删除旧的数据库文件
echo.
echo [1/2] 清理旧数据库...
if exist "data/db" (
    del /q "data/db\wingscribe.db" 2>nul
    del /q "data/db\wingscribe_new.db" 2>nul
    del /q "data/db\wingscribe_new2.db" 2>nul
    del /q "data/db\wingscribe_test.db" 2>nul
    echo 已清理 data/db 目录下的旧数据库文件
) else (
    mkdir "data\db"
    echo 已创建 data/db 目录
)

REM 重新导入 IOC 数据
echo.
echo [2/2] 正在导入 IOC 分类数据...
python -c "
import sys
sys.path.insert(0, 'src')
from metadata.ioc_manager import IOCManager
import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

ioc = IOCManager('data/db/wingscribe.db')
ioc.import_from_excel(
    'data/references/Multiling IOC 15.1_d.xlsx',
    refs_dir='data/references'
)
ioc.close()
echo 导入完成！
"

echo.
echo ============================================
echo 数据库初始化完成！
echo ============================================
pause
