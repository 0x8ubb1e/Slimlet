#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
import math
import sqlite3
import datetime

import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# 自动设置当前工作目录为脚本所在路径
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
print(f'work_path:{script_dir}')

matplotlib.use("TkAgg")
DB = 'data.db'
CONFIG = 'config.json'

# ---------- 数据库 ----------
def init_db():
	with sqlite3.connect(DB) as conn:
		conn.execute('''
			CREATE TABLE IF NOT EXISTS records(
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				person TEXT,
				ts TEXT,
				weight REAL,
				height REAL,
				unit TEXT,
				source TEXT,
				note TEXT
			)
		''')

def insert_record(person, ts, weight, height, unit, source, note):
	with sqlite3.connect(DB) as conn:
		conn.execute('''
			INSERT INTO records(person,ts,weight,height,unit,source,note)
			VALUES(?,?,?,?,?,?,?)
		''', (person, ts, weight, height, unit, source, note))

def fetch_person(person):
	with sqlite3.connect(DB) as conn:
		return conn.execute(
			'SELECT * FROM records WHERE person=? ORDER BY ts', (person,)
		).fetchall()

# ---------- 配置 ----------
def load_config():
	if not os.path.exists(CONFIG):
		return {"persons": []}
	return json.load(open(CONFIG, encoding='utf-8'))

def save_config(cfg):
	json.dump(cfg, open(CONFIG, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# ---------- BMI ----------
def calc_bmi(weight_kg, height_cm):
	if not height_cm:
		return None
	h = height_cm / 100
	return round(weight_kg / (h * h), 2)

# ---------- GUI ----------
class App(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title("轻舟·尺素")
		self.geometry("540x450")

		# 全局变量全部先置空
		self.current_person = None
		self.current_height = None
		self.current_unit   = None
		self.current_source = None

		self.cfg = load_config()
		init_db()

		# 1. 只建框架，不拿数据
		self.init_ui()
		self.show_placeholder()

		# 2. 等事件循环跑起来再决定是否弹向导
		self.after_idle(self._ensure_person_loaded)

	# ------------------------------------------------------------
	def init_ui(self):
		# 顶部人物选择栏
		top_bar = ttk.Frame(self)
		top_bar.pack(fill="x", padx=10, pady=5)
		ttk.Label(top_bar, text="人物：").pack(side="left")
		self.person_cb = ttk.Combobox(top_bar, state="readonly")
		self.person_cb.pack(side="left", padx=5)
		self.person_cb.bind("<<ComboboxSelected>>", self._on_person_change)
		ttk.Button(top_bar, text="编辑人物", command=self.edit_person).pack(side="right")

		# 输入区
		frm = ttk.Frame(self)
		frm.pack(fill="x", padx=10, pady=5)
		ttk.Label(frm, text="时间").grid(row=0, column=0)
		self.var_ts = tk.StringVar(value=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
		ttk.Entry(frm, textvariable=self.var_ts, width=16).grid(row=0, column=1)

		self.lbl_weight = ttk.Label(frm, text="体重")
		self.lbl_weight.grid(row=0, column=2)
		self.var_weight = tk.DoubleVar()
		ttk.Entry(frm, textvariable=self.var_weight, width=6).grid(row=0, column=3)

		ttk.Label(frm, text="备注").grid(row=0, column=4)
		self.var_note = tk.StringVar()
		ttk.Entry(frm, textvariable=self.var_note, width=15).grid(row=0, column=5)

		ttk.Button(frm, text="添加", command=self.add_record).grid(row=0, column=6, padx=5)

		# 图表
		self.fig = Figure(figsize=(5, 2.5), dpi=100)
		self.ax = self.fig.add_subplot(111)
		self.canvas = FigureCanvasTkAgg(self.fig, self)
		self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)

	# ------------------------------------------------------------
	def show_placeholder(self):
		"""没有人物时显示占位文字"""
		self.ax.clear()
		self.ax.text(0.5, 0.5, "请先添加人物", ha='center', va='center')
		self.canvas.draw()

	# ------------------------------------------------------------
	def _ensure_person_loaded(self):
		"""保证至少存在一名人物；否则循环弹向导"""
		while not self.cfg.get("persons"):
			self.setup_wizard()
			self.cfg = load_config()

		# 现在一定有人物，统一赋值
		self.current_person = self.cfg["persons"][0]["name"]
		self.current_height = self.cfg["persons"][0]["height"]
		self.current_unit   = self.cfg["persons"][0]["unit"]
		self.current_source = self.cfg["persons"][0]["source"]

		# 刷新下拉框
		names = [p["name"] for p in self.cfg["persons"]]
		self.person_cb.config(values=names)
		self.person_cb.current(0)

		# 刷新 UI
		self.lbl_weight.config(text=f"体重 ({self.current_unit})")
		self.draw_chart()

	# ------------------------------------------------------------
	def setup_wizard(self):
		"""添加第一个人物（阻塞式）"""
		top = tk.Toplevel(self)
		top.title("添加人物")
		top.grab_set()
		top.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁止点 X

		ttk.Label(top, text="姓名").grid(row=0, column=0, padx=5, pady=5)
		e_name = ttk.Entry(top)
		e_name.grid(row=0, column=1)

		ttk.Label(top, text="身高 (cm)").grid(row=1, column=0)
		e_h = tk.DoubleVar(value=170)
		ttk.Entry(top, textvariable=e_h).grid(row=1, column=1)

		ttk.Label(top, text="单位").grid(row=2, column=0)
		unit_var = tk.StringVar(value="kg")
		ttk.Combobox(top, textvariable=unit_var, values=["kg", "lb"], state="readonly").grid(row=2, column=1)

		ttk.Label(top, text="数据源").grid(row=3, column=0)
		src_var = tk.StringVar(value="日常")
		ttk.Entry(top, textvariable=src_var).grid(row=3, column=1)

		def save():
			name = e_name.get().strip()
			if not name:
				messagebox.showerror("错误", "姓名不能为空")
				return
			# 去重后添加
			self.cfg["persons"] = [p for p in self.cfg["persons"] if p["name"] != name]
			self.cfg["persons"].append({
				"name": name,
				"height": e_h.get(),
				"unit": unit_var.get(),
				"source": src_var.get()
			})
			save_config(self.cfg)
			top.destroy()

		ttk.Button(top, text="保存", command=save).grid(row=4, columnspan=2, pady=10)
		self.wait_window(top)  # 阻塞直到窗口关闭

	# ------------------------------------------------------------
	def edit_person(self):
		"""后期增删改人物"""
		top = tk.Toplevel(self)
		top.title("人物管理")
		top.grab_set()

		lb = tk.Listbox(top, height=6)
		lb.pack(padx=10, pady=5)

		def refresh_list():
			lb.delete(0, tk.END)
			for p in self.cfg["persons"]:
				lb.insert(tk.END, f"{p['name']}  {p['height']}cm  {p['unit']}")

		refresh_list()

		btn_bar = ttk.Frame(top)
		btn_bar.pack(pady=5)

		def add():
			self.setup_wizard()
			self.cfg = load_config()
			refresh_list()

		def delete():
			idx = lb.curselection()
			if not idx:
				return
			name = self.cfg["persons"][idx[0]]["name"]
			self.cfg["persons"].pop(idx[0])
			save_config(self.cfg)
			refresh_list()
			# 如果删的是当前人，重新选人
			if name == self.current_person:
				self.after_idle(self._ensure_person_loaded)

		ttk.Button(btn_bar, text="新增", command=add).pack(side="left", padx=5)
		ttk.Button(btn_bar, text="删除", command=delete).pack(side="left", padx=5)
		self.wait_window(top)

	# ------------------------------------------------------------
	def _on_person_change(self, _=None):
		name = self.person_cb.get()
		person_info = next((p for p in self.cfg["persons"] if p["name"] == name), None)
		if person_info:
			self.current_person = person_info["name"]
			self.current_height = person_info["height"]
			self.current_unit   = person_info["unit"]
			self.current_source = person_info["source"]
			self.lbl_weight.config(text=f"体重 ({self.current_unit})")
			self.draw_chart()

	# ------------------------------------------------------------
	def add_record(self):
		if self.current_person is None:
			messagebox.showwarning("提示", "请先添加人物")
			return
		try:
			weight = self.var_weight.get()
			weight_kg = weight * 0.453592 if self.current_unit == "lb" else weight
			ts = self.var_ts.get()
			insert_record(
				self.current_person,
				ts,
				weight,
				self.current_height,
				self.current_unit,
				self.current_source,
				self.var_note.get()
			)
			self.draw_chart()
		except Exception as e:
			messagebox.showerror("错误", str(e))

	# ------------------------------------------------------------
	def draw_chart(self):
		if self.current_person is None:
			return
		rows = fetch_person(self.current_person)
		self.ax.clear()
		if not rows:
			self.ax.text(0.5, 0.5, "暂无数据", ha='center', va='center')
			self.canvas.draw()
			return
		ts = [r[2][:10] for r in rows]
		weights = [r[3] for r in rows]
		self.ax.plot(ts, weights, marker="o")
		self.ax.set_title(f"{self.current_person} 体重变化")
		self.ax.set_ylabel(f"体重 ({self.current_unit})")
		self.ax.tick_params(axis='x', rotation=45)
		self.fig.tight_layout()
		self.canvas.draw()

# ---------- 主 ----------
if __name__ == "__main__":
	App().mainloop()