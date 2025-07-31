import os
import json
import math
import sqlite3
import datetime
from PIL import Image, ImageTk

import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage

import matplotlib
from matplotlib import rcParams
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter, date2num
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

def subtract_months(date, months):
	month = date.month - months
	print(f"date: {date} months: {months} month: {month}")
	year = date.year
	while month <= 0:
		month += 12
		year -= 1
	print(f"start: {date.replace(year=year, month=month, day=1)}")
	return date.replace(year=year, month=month, day=1)

def load_cfg():
	if not os.path.exists(CONFIG):
		return {"persons": []}
	return json.load(open(CONFIG, encoding='utf-8'))

def save_cfg(cfg):
	json.dump(cfg, open(CONFIG, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

def init_db():
	with sqlite3.connect(DB) as conn:
		conn.execute('''
			CREATE TABLE IF NOT EXISTS records (
				id   INTEGER PRIMARY KEY AUTOINCREMENT,
				person TEXT NOT NULL,
				time    TEXT NOT NULL,
				weight REAL NOT NULL,
				note  TEXT,
				bmi   REAL
			)
		''')

def insert_rec(person, time, weight, note, bmi):
	with sqlite3.connect(DB) as conn:
		conn.execute('''
			INSERT INTO records(person, time, weight, note, bmi)
			VALUES(?,?,?,?,?)
		''', (person, time, weight, note, bmi))

def fetch_rec(person):
	with sqlite3.connect(DB) as conn:
		return conn.execute(
			'SELECT time, weight, note, bmi FROM records WHERE person=? ORDER BY time',
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

def calc_bmi(weight: float, height: float) -> float:
	"""计算 BMI，保留 2 位小数"""
	if height <= 0:
		return 0.0
	return round(weight / ((height / 100) ** 2), 2)

# ---------------- 主程序 ----------------
class App(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title("体重记录器")
		self.minsize(540, 1)

		self.cfg = load_cfg()
		self.person = None
		init_db()

		# ① 先建界面
		self.show_input = False          # 是否展开输入框
		self.build_ui_collapsed()        # 先建折叠界面

		center(self)

		self.draw_chart()
		# ② 再向导  ③ 最后统一刷新人物
		self.after_idle(self.wizard_if_need)

	# ---------------- UI ----------------
	def build_ui_collapsed(self):
		# 顶部人物栏
		self.bar = ttk.Frame(self)
		self.bar.grid(row=0, column=0, sticky='ew', padx=20, pady=(10, 5))
		self.bar.grid_columnconfigure(2, weight=1)

		ttk.Label(self.bar, text='人物').grid(row=0, column=0)
		self.cb_person = ttk.Combobox(self.bar, state='readonly', width=10)
		self.cb_person.grid(row=0, column=1, padx=(10, 0))
		self.cb_person.bind('<<ComboboxSelected>>', self.switch_person)

		# 添加空白
		ttk.Label(self.bar, text=(' ' * int((self.winfo_width() - 150 - 200) / 4))).grid(row=0, column=2, sticky='nsew', padx=5, pady=5)

		# 折叠/展开按钮
		self.btn_toggle = ttk.Button(self.bar, text='添加数据', command=self.toggle_input)
		self.btn_toggle.grid(row=0, column=4)
		ttk.Button(self.bar, text='编辑人物', command=self.edit_person_win).grid(row=0, column=5, padx=5)

		ico = Image.open('icons/refresh.png')
		self.ico_img = ImageTk.PhotoImage(ico.resize((17, 17)))
		self.btn_refresh = ttk.Button(self.bar, image=self.ico_img, command=self.refresh)
		
		self.btn_refresh.grid(row=0, column=6)

		# 输入框容器（初始隐藏）
		self.input_frm = ttk.Frame(self)
		
		# 时间
		ttk.Label(self.input_frm, text='时间').grid(row=1, column=0)
		self.var_time = tk.StringVar(value=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
		ttk.Entry(self.input_frm, textvariable=self.var_time, width=18).grid(row=1, column=1, padx=(5, 10))

		# 体重
		ttk.Label(self.input_frm, text='体重(kg)').grid(row=1, column=2)
		self.var_w = tk.DoubleVar(value=75.00)   # 默认75
		ttk.Entry(self.input_frm, textvariable=self.var_w, width=6).grid(row=1, column=3, padx=(5, 10))
		self.lbl_unit = ttk.Label(self.input_frm, text='kg')   # ← 加这一行
		self.lbl_unit.grid(row=1, column=4, padx=(0, 5))

		# 备注
		ttk.Label(self.input_frm, text='备注').grid(row=1, column=4)
		self.var_note = tk.StringVar()
		ttk.Entry(self.input_frm, textvariable=self.var_note, width=12).grid(row=1, column=5, padx=(5, 10))

		ttk.Button(self.input_frm, text='确认添加', command=self.add_record).grid(row=1, column=6, padx=(5, 0))

		self.input_frm.lower()  # 先放到最底层
		self.input_frm.grid(row=1, column=0, sticky='ew', padx=20, pady=5)
		self.input_frm.grid_remove()

		# 图表
		self.fig = Figure(figsize=(5, 2.8), dpi=100)
		self.ax = self.fig.add_subplot(111)
		self.canvas = FigureCanvasTkAgg(self.fig, self)
		self.canvas.get_tk_widget().grid(row=2, column=0, sticky='nsew', padx=20, pady=(5, 20))

		# 时间维度按钮区
		self.time_bar = ttk.Frame(self)
		self.time_bar.grid(row=3, column=0, sticky='ew', padx=10, pady=2)

		self.time_vars = ['1月', '3月', '半年', '1年', '3年', '5年', '全部']
		for i in range(len(self.time_vars) + 2):
			self.time_bar.grid_columnconfigure(i, weight=1)

		self.time_btn = {}
		for i, t in enumerate(self.time_vars):
			btn = ttk.Button(self.time_bar, text=t, width=6, command=lambda x=t: self.switch_time_scope(x))
			btn.grid(row=0, column=i+1, padx=2)
			self.time_btn[t] = btn

		self.current_scope = self.cfg.setdefault('time_scope', '1月')  # 默认
		self.switch_time_scope(self.current_scope)

		# 鼠标悬停提示
		self.anno = None
		self.canvas.mpl_connect('motion_notify_event', self.on_hover)

	def update_scope_buttons(self):
		"""根据现有数据跨度，决定哪些时间维度可见"""
		if not self.person:  # 没人就全隐藏
			scopes = []
		else:
			rows = fetch_rec(self.person['name'])
			if not rows:  # 只有“全部”
				scopes = ['全部']
			else:
				# 最早-最晚 相差天数
				times = [datetime.datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S') for r in rows]
				span_days = (max(times) - min(times)).days
				scopes = ['全部']
				if span_days >= 0:  # 任何数据都有“全部”
					scopes.append('1月')
				if span_days >= 30:
					scopes.append('3月')
				if span_days >= 90:
					scopes.append('半年')
				if span_days >= 365:
					scopes.append('1年')
				if span_days >= 365*3:
					scopes.append('3年')
				if span_days >= 365*5:
					scopes.append('5年')

		# 统一按钮显隐
		for s, btn in self.time_btn.items():
			if s in scopes:
				btn.grid()
				btn.state(['!pressed'])
			else:
				btn.grid_remove()
		
		scopes = [s for s in self.time_vars if s in scopes]
		# 默认选中第一个可用
		if scopes:
			self.switch_time_scope(scopes[0])
		
		# 动态调整布局
		self.adjust_time_buttons_layout(scopes)

	def adjust_time_buttons_layout(self, scopes):
		"""动态调整时间按钮布局，确保居中且间距均匀"""
		# 清除旧的权重配置
		for i in range(len(self.time_vars) + 2):
			self.time_bar.grid_columnconfigure(i, weight=0)

		# 重新配置权重
		for i in range(len(scopes) + 2):
			self.time_bar.grid_columnconfigure(i, weight=1)

		# 重新放置按钮
		for i, scope in enumerate(scopes):
			self.time_btn[scope].grid(row=3, column=i + 1)

	def switch_time_scope(self, scope):
		"""根据时间维度过滤并重绘"""
		self.current_scope = scope
		self.cfg['time_scope'] = scope
		save_cfg(self.cfg)

		# 高亮按钮
		for b in self.time_btn.values():
			b.state(['!pressed'])
		self.time_btn[scope].state(['pressed'])

		self.draw_chart()

	def draw_chart(self):
		self.ax.clear()

		# --------- 数据 ---------
		if not self.person:
			self.show_placeholder()
			return
		rows = fetch_rec(self.person['name'])
		if not rows:
			self.show_placeholder()
			return
		
		# 时间过滤
		now = datetime.datetime.now()
		delta_map = {'1月': 1, '3月': 3, '半年': 6, '1年': 12, '3年': 12*3, '5年': 12*5, '全部': 0}
		months = delta_map[self.current_scope]
		cutoff = subtract_months(now, months=months)
		if months != 0:
			rows = [r for r in rows if datetime.datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S') >= cutoff]

		if not rows:
			self.show_placeholder()
			return

		times = [datetime.datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S') for r in rows]
		weights = [r[1] for r in rows]
		bmis = [r[3] for r in rows]
		notes = [r[2] for r in rows]

		# --------- Y 轴动态整十 ---------
		y_min, y_max = min(weights), max(weights)
		y_low  = math.floor(y_min / 10) * 10
		y_high = math.ceil(y_max / 10) * 10
		self.ax.set_ylim(y_low, y_high)
		self.ax.set_ylabel('体重(kg)')
		self.ax.set_yticks(range(y_low, y_high + 1, 10))

		# --------- X 轴仅三个刻度 ---------
		if months != 0:  # 不为全部
			start = cutoff
		else:  # 为全部
			start = times[0]
		end = now
		mid = start + (end - start) / 2

		self.ax.set_xlim(start, end)
		self.ax.set_xticks([start, mid, end])
		self.ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
		self.ax.set_xlabel('')

		# 只留坐标轴
		self.ax.spines['top'].set_visible(False)
		self.ax.spines['right'].set_visible(False)

		# --------- 画折线+点 ---------
		self.ax.plot(times, weights, marker='o')

		# 保存数据用于悬停
		self.hover_time = times
		self.hover_weight = weights
		self.hover_bmi = bmis
		self.hover_note = notes

		self.canvas.draw()

	def show_placeholder(self):
		self.ax.text(0.5, 0.5, "暂无数据", ha='center', va='center')
		self.canvas.draw()

	def toggle_input(self):
		self.show_input = not self.show_input
		if self.show_input:
			self.input_frm.grid()
			self.btn_toggle.config(text='收起输入')
			# 刷新时间为“年-月-日 时:分:秒”
			self.var_time.set(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
		else:
			self.input_frm.grid_remove()
			self.btn_toggle.config(text='添加数据')

	def on_hover(self, event):
		if not hasattr(self, 'hover_time'):
			return
		
		x, y = event.xdata, event.ydata
		if x is None or y is None:
			if self.anno:
				self.anno.remove()
				self.anno = None
				self.canvas.draw_idle()
			return

		# 找最近点
		idx = min(range(len(self.hover_time)),key=lambda i: abs(date2num(self.hover_time[i]) - x))
		d, w, b, n = self.hover_time[idx], self.hover_weight[idx], self.hover_bmi[idx], self.hover_note[idx]
		if n:
			txt = f"{d.strftime('%Y.%m.%d')}\n{w:.2f} kg\nBMI {b:.1f} {bmi_level(b, self.person['sex'])}\n{n}"
		else:
			txt = f"{d.strftime('%Y.%m.%d')}\n{w:.2f} kg\nBMI {b:.1f} {bmi_level(b, self.person['sex'])}"
		
		# 计算提示框坐标
		x, y = date2num(d), w
		ax = self.ax

		# 把提示放在点右边，如超出右边界就改放左边
		if x > ax.get_xlim()[1] * 0.9:        # 距离右边界 10% 以内
			xytext = (-40, 10)                  # 向左偏移
		else:
			xytext = (10, 10)                   # 默认向右
		
		if self.anno:
			self.anno.set_text(txt)
			self.anno.xy = (date2num(d), w)
		else:
			self.anno = self.ax.annotate(
				txt, xy=(date2num(d), w),
				xytext=xytext, textcoords='offset points',
				bbox=dict(boxstyle='round', alpha=0.7, facecolor='lightyellow'))
		self.canvas.draw_idle()

	# ---------------- 向导 ----------------
	def wizard_if_need(self):
		# 阻塞向导直到有人物
		while not self.cfg['persons']:
			self.wizard()
			self.cfg = load_cfg()

		# 现在一定有人物
		self.refresh_persons()

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
			self.cfg = load_cfg()
			if edit is None:  # 新增用户
				self.cfg['persons'].append(person)
			else:  # 编辑用户
				idx = next(i for i, p in enumerate(self.cfg['persons']) if p['name'] == edit['name'])
				self.cfg['persons'][idx] = person
			save_cfg(self.cfg)
			self.cfg = load_cfg()   # 立刻重新读文件
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
		self.cfg = load_cfg()
		names = [p['name'] for p in self.cfg['persons']]
		self.cb_person.config(values=names)
		if names:
			self.cb_person.current(0)
			self.switch_person()
		else:
			self.person = None
			self.show_placeholder()

	def switch_person(self, *_):
		name = self.cb_person.get()
		self.person = next((p for p in self.cfg['persons'] if p['name'] == name), None)
		if self.person:
			self.lbl_unit.config(text=self.person['unit'])
			self.update_scope_buttons()

	def refresh(self):
		"""重新读取配置+数据库并重绘界面"""
		self.cfg = load_cfg()          # 重新读配置
		self.refresh_persons()         # 刷新人物下拉框
		self.update_scope_buttons()    # 刷新时间维度按钮
		self.draw_chart()              # 重绘折线图

	# ---------------- 单位换算 ----------------
	UNIT2KG = {'kg': 1, '公斤': 1, '斤': 0.5, 'lb': 0.453592}
	KG2UNIT = {k: 1/v for k, v in UNIT2KG.items()}

	def to_kg(self, val):
		return val * self.UNIT2KG[self.person['unit']]

	def to_show_unit(self, kg):
		return round(kg * self.KG2UNIT[self.person['unit']], 2)

	# ---------------- 添加记录 ----------------
	def add_record(self):
		if not self.person:
			messagebox.showwarning("提示", "请先选择人物")
			return
		try:
			w_show = round(self.var_w.get(), 2)
			w_kg = self.to_kg(w_show)
			bmi = calc_bmi(w_kg, self.person['height'])
			insert_rec(self.person['name'], self.var_time.get(), w_kg, self.var_note.get(), bmi)
			
			# self.draw_chart()
			self.update_scope_buttons()
			time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
			self.var_time.set(time)
		except Exception as e:
			messagebox.showerror("错误", str(e))

# ---------- 启动 ----------
if __name__ == '__main__':
	App().mainloop()
