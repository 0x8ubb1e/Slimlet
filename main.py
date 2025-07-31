#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
体重记录器 – 终极版
1  主窗体 & 向导同时存在且居中
2  向导控件左对齐、默认值、单位/性别/中文
3  数据库存 kg，前端可随意切换单位
4  图表中文正常显示、可拖动、y=0 起点
5  人物表格编辑、退出确认
6  单位换算、长高反算身高、双曲线
"""
import os
import json
import math
import sqlite3
import datetime

import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
from matplotlib import rcParams
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# 自动设置当前工作目录为脚本所在路径
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
print(f'work_path:{script_dir}')

# 让中文正常
rcParams['font.family'] = 'SimHei'
rcParams['axes.unicode_minus'] = False

matplotlib.use("TkAgg")
DB = 'data.db'
CONFIG = 'config.json'

# ---------------- 工具 ----------------
def center(win):
	win.update_idletasks()
	x = (win.winfo_screenwidth()  - win.winfo_width())  // 2
	y = (win.winfo_screenheight() - win.winfo_height()) // 2
	win.geometry(f"+{x}+{y}")

def load_cfg():
	if not os.path.exists(CONFIG):
		return {"persons": []}
	return json.load(open(CONFIG, encoding='utf-8'))

def save_cfg(cfg):
	json.dump(cfg, open(CONFIG, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

def init_db():
	with sqlite3.connect(DB) as conn:
		conn.execute('''
			CREATE TABLE IF NOT EXISTS records(
				pid   INTEGER PRIMARY KEY AUTOINCREMENT,
				person TEXT NOT NULL,
				ts    TEXT NOT NULL,
				weight_kg REAL NOT NULL,
				note  TEXT,
				bmi   REAL
			)
		''')

def insert_rec(person, ts, weight_kg, note, bmi):
	with sqlite3.connect(DB) as conn:
		conn.execute('''
			INSERT INTO records(person, ts, weight_kg, note, bmi)
			VALUES(?,?,?,?,?)
		''', (person, ts, weight_kg, note, bmi))

def fetch_rec(person):
	with sqlite3.connect(DB) as conn:
		return conn.execute(
			'SELECT ts, weight_kg, note, bmi FROM records WHERE person=? ORDER BY ts',
			(person,)
		).fetchall()

# ---------------- BMI 评价 ----------------
BMI_MALE   = [(0, 18.4,'偏瘦'), (18.5, 23.9, '正常'), (24, 27.9, '超重'), (28, 999, '肥胖')]
BMI_FEMALE = [(0, 17.4, '偏瘦'), (17.5, 22.9, '正常'), (23, 26.9, '超重'), (27, 999, '肥胖')]

def bmi_level(bmi, sex):
	tbl = BMI_MALE if sex == '男' else BMI_FEMALE
	for low, high, level in tbl:
		if low <= bmi <= high:
			return level
	return '未知'

def calc_bmi(weight_kg: float, height_cm: float) -> float:
	"""计算 BMI，保留 2 位小数"""
	if height_cm <= 0:
		return 0.0
	return round(weight_kg / ((height_cm / 100) ** 2), 2)

# ---------------- 主程序 ----------------
class App(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title("体重记录器")
		# self.geometry("540")
		self.minsize(540, 1)
		center(self)

		self.cfg   = load_cfg()
		init_db()
		self.person = None   # 当前人物 dict

		self.show_input = False          # 是否展开输入框
		self.build_ui_collapsed()        # 先建折叠界面

		self.draw_chart()
		self.after_idle(self.wizard_if_need)

	# ---------------- UI ----------------
	def build_ui_collapsed(self):
		# 主窗口改用 grid
		# self.grid_rowconfigure(1, weight=1)   # 图表可纵向扩展
		# self.grid_columnconfigure(0, weight=1)
		# self.config(relief='solid', borderwidth=1)  # 添加边框

		# 顶部人物栏
		self.bar = ttk.Frame(self)
		# bar.pack(fill='x', padx=10, pady=5)
		self.bar.grid(row=0, column=0, sticky='ew', padx=20, pady=(10, 5))

		# ttk.Label(bar, text='人物').pack(side='left')
		ttk.Label(self.bar, text='人物').grid(row=0, column=0)
		self.cb_person = ttk.Combobox(self.bar, state='readonly', width=10)
		# self.cb_person.pack(side='left', padx=5)
		self.cb_person.grid(row=0, column=1, padx=(10, 0))
		self.cb_person.bind('<<ComboboxSelected>>', self.switch_person)

		# 添加空白
		label = ttk.Label(self.bar, text=(' ' * int((self.winfo_width() - 150 - 200) / 4))).grid(row=0, column=2, sticky='nsew', padx=5, pady=5)

		# 折叠/展开按钮
		self.btn_toggle = ttk.Button(self.bar, text='添加数据', command=self.toggle_input)
		# self.btn_toggle.pack(side='right', padx=10)
		self.btn_toggle.grid(row=0, column=4)
		# ttk.Button(bar, text='编辑人物', command=self.edit_person_win).pack(side='right', padx=10)
		ttk.Button(self.bar, text='编辑人物', command=self.edit_person_win).grid(row=0, column=5, padx=(5, 0))

		# 输入框容器（初始隐藏）
		self.input_frm = ttk.Frame(self)
# 时间
		ttk.Label(self.input_frm, text='时间').grid(row=1, column=0)
		self.var_ts = tk.StringVar(value=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
		ttk.Entry(self.input_frm, textvariable=self.var_ts, width=18).grid(row=1, column=1, padx=(5, 10))

		# 体重
		ttk.Label(self.input_frm, text='体重(kg)').grid(row=1, column=2)
		self.var_w = tk.DoubleVar(value=75.00)   # 默认75
		ttk.Entry(self.input_frm, textvariable=self.var_w, width=6).grid(row=1, column=3, padx=(5, 10))

		# 备注
		ttk.Label(self.input_frm, text='备注').grid(row=1, column=4)
		self.var_note = tk.StringVar()
		ttk.Entry(self.input_frm, textvariable=self.var_note, width=12).grid(row=1, column=5, padx=(5, 10))

		ttk.Button(self.input_frm, text='确认添加', command=self.add_record).grid(row=1, column=6, padx=(5, 0))

		# self.input_frm.pack()
		# self.input_frm.pack_forget()
		self.input_frm.lower()  # 先放到最底层
		self.input_frm.grid(row=1, column=0, sticky='ew', padx=20, pady=5)
		self.input_frm.grid_remove()

		# 图表
		# 1. 建滚动条
		self.xscroll = ttk.Scrollbar(self, orient='horizontal')
		self.xscroll.grid(row=3, column=0, sticky='ew')

		# 2. 建超长画布
		self.fig = Figure(figsize=(15 * 0.4, 2.8), dpi=100)   # 30 天 ≈ 6 英寸
		self.ax = self.fig.add_subplot(111)
		self.canvas = FigureCanvasTkAgg(self.fig, self)
		w = self.canvas.get_tk_widget()
		# self.canvas.get_tk_widget().pack(fill='both', expand=True, padx=10, pady=5)
		w.grid(row=2, column=0, sticky='nsew', padx=20, pady=(5, 20))

		# 3. 绑定滚动
		w.configure(xscrollcommand=self.xscroll.set)
		self.xscroll.configure(command=w.xview)

		# 4. 让 Canvas 可滚动
		w.configure(scrollregion=(0, 0, 15 * 0.4 * 100, 0))   # 宽度像素

		self.canvas.mpl_connect('scroll_event', self.on_scroll)
		self.canvas.mpl_connect('button_press_event', self.on_pan)

		self.pan_start = None

	def toggle_input(self):
		self.show_input = not self.show_input
		if self.show_input:
		# if not self.input_frm.winfo_ismapped():
			# self.input_frm.pack(fill='x', padx=10, pady=5)
			self.input_frm.grid()
			self.btn_toggle.config(text='收起输入')
			# 刷新时间为“年-月-日 时:分:秒”
			self.var_ts.set(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
		else:
			# self.input_frm.pack_forget()
			self.input_frm.grid_remove()
			self.btn_toggle.config(text='添加数据')

	def draw_chart(self):
		self.ax.clear()

		# 1. Y 轴固定
		self.ax.set_ylim(50, 100)
		self.ax.set_ylabel('体重(kg)')

		# 2. X 轴：今天起 15 天
		today = datetime.datetime.now()
		days = [today + datetime.timedelta(days=i) for i in range(15)]
		# days = [today - datetime.timedelta(days=i) for i in range(14, 0, -1)] + [today + datetime.timedelta(days=i) for i in range(15)]
		print(days)
		self.ax.set_xlim(days[0], days[-1])
		# self.ax.xaxis.set_major_formatter(lambda x, pos: x.strftime('%m.%d'))
		self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))   # 每天一格
		self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m.%d'))
		self.fig.autofmt_xdate(rotation=0)

		# 3. 如果有数据再画线
		if self.person:
			rows = fetch_rec(self.person['name'])
			if rows:
				ts = [datetime.datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S') for r in rows]
				weights = [r[1] for r in rows]
				self.ax.plot(ts, weights, marker='o')
			else:
				self.ax.text(0.5, 0.5, "暂无数据", ha='center', va='center')
		else:
			self.ax.text(0.5, 0.5, "暂无数据", ha='center', va='center')

		self.canvas.draw()

	# ---------------- 向导 ----------------
	def wizard_if_need(self):
		if not self.cfg['persons']:
			self.wizard()

	def wizard(self, edit=None):
		top = tk.Toplevel(self)
		top.title('添加人物' if edit is None else '修改人物')
		center(top)
		
		# 默认值
		defaults = edit or dict(name='默认', height=175, unit='kg', sex='男', source='日常')

		fields = {}
		labels = ['姓名', '身高(cm)', '性别', '单位', '数据源']
		keys   = ['name', 'height', 'sex', 'unit', 'source']
		widgets = []

		for i, (lab, key) in enumerate(zip(labels, keys)):
			ttk.Label(top, text=lab).grid(row=i, column=0, sticky='w', padx=5, pady=3)
			if key == 'sex':
				cb = ttk.Combobox(top, state='readonly', values=['男', '女'], width=17)
				cb.set(defaults[key])
				cb.grid(row=i, column=1, padx=5)
				widgets.append(cb)
			elif key == 'unit':
				cb = ttk.Combobox(top, state='readonly', values=['kg', 'lb', '公斤', '斤'], width=17)
				cb.set(defaults[key])
				cb.grid(row=i, column=1, padx=5)
				widgets.append(cb)
			else:
				ent = ttk.Entry(top, width=20)
				ent.insert(0, str(defaults[key]))
				ent.grid(row=i, column=1, padx=5)
				widgets.append(ent)
			fields[key] = widgets[-1]

		def save():
			name = fields['name'].get().strip()
			if not name:
				messagebox.showerror('错误', '姓名不能为空')
				return
			person = {
				'name': name,
				'height': float(fields['height'].get()),
				'sex': fields['sex'].get(),
				'unit': fields['unit'].get(),
				'source': fields['source'].get()
			}
			# 去重
			self.cfg['persons'] = [p for p in self.cfg['persons'] if p['name'] != name]
			if edit is None:
				self.cfg['persons'].append(person)
			else:
				idx = next(i for i, p in enumerate(self.cfg['persons']) if p['name'] == edit['name'])
				self.cfg['persons'][idx] = person
			save_cfg(self.cfg)
			self.refresh_persons()
			top.destroy()

		ttk.Button(top, text='保存', command=save).grid(row=len(labels), columnspan=2, pady=8)
		top.transient(self)   # 保持主窗可见
		self.wait_window(top)

	# ---------------- 人物编辑窗口 ----------------
	def edit_person_win(self):
		top = tk.Toplevel(self)
		top.title('人物管理')
		top.transient(self)
		center(top)

		cols = ('姓名', '身高(cm)', '性别', '单位', '数据源')
		tree = ttk.Treeview(top, columns=cols, show='headings', height=6)
		for c in cols:
			tree.heading(c, text=c)
			tree.column(c, width=80, anchor='center')
		tree.pack(padx=10, pady=5)
		

		def refresh():
			for item in tree.get_children():
				tree.delete(item)
			for p in self.cfg['persons']:
				tree.insert('', 'end', values=(p['name'], p['height'], p['sex'], p['unit'], p['source']))

		refresh()

		bar = ttk.Frame(top)
		bar.pack(pady=5)
		ttk.Button(bar, text='新增', command=lambda: (self.wizard(), refresh())).pack(side='left', padx=5)
		ttk.Button(bar, text='修改', command=lambda: self.modify_selected(tree, refresh)).pack(side='left', padx=5)
		ttk.Button(bar, text='删除', command=lambda: self.delete_selected(tree, refresh)).pack(side='left', padx=5)

	def modify_selected(self, tree, refresh):
		sel = tree.selection()
		if not sel:
			return
		vals = tree.item(sel[0], 'values')
		person = dict(name=vals[0], height=float(vals[1]), sex=vals[2], unit=vals[3], source=vals[4])
		self.wizard(edit=person)
		refresh()

	def delete_selected(self, tree, refresh):
		sel = tree.selection()
		if not sel:
			return
		name = tree.item(sel[0], 'values')[0]
		self.cfg['persons'] = [p for p in self.cfg['persons'] if p['name'] != name]
		save_cfg(self.cfg)
		refresh()
		self.refresh_persons()

	# ---------------- 逻辑 ----------------
	def refresh_persons(self):
		names = [p['name'] for p in self.cfg['persons']]
		self.cb_person.config(values=names)
		if not self.person or self.person['name'] not in names:
			if names:
				self.cb_person.current(0)
				self.switch_person()
			else:
				self.person = None
				self.draw_chart()

	def switch_person(self, *_):
		name = self.cb_person.get()
		self.person = next((p for p in self.cfg['persons'] if p['name'] == name), None)
		if self.person:
			self.lbl_unit.config(text=self.person['unit'])
			self.draw_chart()

	# ---------------- 单位换算 ----------------
	UNIT2KG = {'kg': 1, '公斤': 1, '斤': 0.5, 'lb': 0.453592}
	KG2UNIT = {k: 1/v for k, v in UNIT2KG.items()}

	def to_kg(self, val):
		return val * self.UNIT2KG[self.person['unit']]

	def to_show_unit(self, kg):
		return round(kg * self.KG2UNIT[self.person['unit']], 2)

	# ---------------- 图表拖动 ----------------
	def on_scroll(self, event):
		ax = self.ax
		xlim = ax.get_xlim()
		scale = 0.9 if event.step > 0 else 1.1
		# ax.set_xlim([x*scale for x in xlim])
		self.canvas.draw()

	def on_pan(self, event):
		if event.button != 2:
			return
		if self.pan_start is None:
			self.pan_start = (event.xdata, event.ydata)
		else:
			dx = event.xdata - self.pan_start[0]
			xlim = self.ax.get_xlim()
			self.ax.set_xlim([x - dx for x in xlim])
			self.pan_start = (event.xdata, event.ydata)
			self.canvas.draw()

	# ---------------- 添加记录 ----------------
	def add_record(self):
		if not self.person:
			messagebox.showwarning("提示", "请先选择人物")
			return
		try:
			w_show = round(self.var_w.get(), 2)
			w_kg = self.to_kg(w_show)
			bmi = calc_bmi(w_kg, self.person['height'])
			ts = datetime.datetime.now().strftime('%m/%d %H:%M:%S')
			insert_rec(self.person['name'], ts, w_kg, self.var_note.get(), bmi)
			self.draw_chart()
			self.var_ts.set(ts)
		except Exception as e:
			messagebox.showerror("错误", str(e))

# ---------- 启动 ----------
if __name__ == '__main__':
	App().mainloop()
