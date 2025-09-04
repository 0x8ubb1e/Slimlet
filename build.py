import os
import shutil
import subprocess

NAME = "Slimlet"
MAIN = "main.py"
DIST_DIR = "dist"
ICON_PATH = "slimlet.ico"  # 图标文件名

# 确保图标文件存在
if not os.path.exists(ICON_PATH):
	print(f"错误：图标文件 '{ICON_PATH}' 不存在，请确保它在项目根目录下。")
	exit(1)

# 清理旧产物
if os.path.exists(DIST_DIR):
	shutil.rmtree(DIST_DIR)

# 用 PyInstaller 单文件打包
cmd = [
	"pyinstaller",
	"-F", "-w",
	"-n", NAME,
	"--clean",
	f"--icon={ICON_PATH}",
	"--add-data", "slim.db;.",
	"--add-data", "config.json;.",
	MAIN
]
subprocess.run(cmd, check=True)

print("✅ 打包完成！")