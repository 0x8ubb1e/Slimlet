import os, io, sys, json, math, base64, sqlite3, datetime
from PIL import Image, ImageTk

import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
from matplotlib import rcParams
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter, date2num
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 兼容 PyInstaller 与常规运行
if getattr(sys, 'frozen', False):
	# 打包后的可执行文件目录
	BASE_DIR = os.path.dirname(sys.executable)
else:
	# 源码运行时脚本所在目录
	BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"{BASE_DIR=}")

REFRESH_ICON_DATA = b"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"
REFRESH_ICON = io.BytesIO(base64.b64decode(REFRESH_ICON_DATA))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
DB_PATH = os.path.join(BASE_DIR, 'slim.db')

# 让中文正常
rcParams['font.family'] = 'SimHei'
rcParams['axes.unicode_minus'] = False

matplotlib.use("TkAgg")

# ---------------- 工具 ----------------
def center(win):
	win.update_idletasks()
	x = (win.winfo_screenwidth() - win.winfo_width()) // 2
	y = (win.winfo_screenheight() - win.winfo_height()) // 2
	win.geometry(f"+{x}+{y}")

# 划时间区间 当前时间 - 时间维度
def subtract_months(date, months):
	if months == 0:
		return date.replace(year=1900, month=1, day=1)  # 全部：远早起点
	elif months < 1:
		days = int(months * 30.44)  # 平均每月天数
		return date - datetime.timedelta(days=days)
	else:
		month = date.month - months
		print(f"date: {date.date()} {months=} {month=}")
		year = date.year
		while month <= 0:
			month += 12
			year -= 1
		# print(f"start: {date.replace(year=year, month=month, day=1).date()} end: {date.date()}")
		# print(f"{date.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)}")
		return date.replace(year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0)

# ---------------- 数据层 ----------------
def load_cfg():
	if not os.path.exists(CONFIG_PATH):
		return {"persons": []}
	return json.load(open(CONFIG_PATH, encoding='utf-8'))

def save_cfg(cfg):
	json.dump(cfg, open(CONFIG_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

def init_db():
	with sqlite3.connect(DB_PATH) as conn:
		conn.execute('''
			CREATE TABLE IF NOT EXISTS records (
				id INTEGER PRIMARY KEY AUTOINCREMENT,
				person TEXT NOT NULL,
				time TEXT NOT NULL,
				weight float NOT NULL,
				note TEXT,
				bmi float
			)
		''')

def insert_record(person, time, weight, note, bmi):
	with sqlite3.connect(DB_PATH) as conn:
		conn.execute('''
			INSERT INTO records(person, time, weight, note, bmi)
			VALUES(?,?,?,?,?)
		''', (person, time, weight, note, bmi))

def fetch_records(person):
	with sqlite3.connect(DB_PATH) as conn:
		return conn.execute(
			'SELECT time, weight, note, bmi FROM records WHERE person=? ORDER BY time',
			(person,)
		).fetchall()

# ---------------- BMI 评价 ----------------
BMI_MALE = [(0, 18.4, '偏瘦'), (18.5, 23.9, '正常'), (24, 27.9, '超重'), (28, 999, '肥胖')]
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
	print(f"{weight=} {height=} {round(weight / ((height / 100) ** 2), 2)=}")
	return round(weight / ((height / 100) ** 2), 2)

# ---------------- 单位换算 ----------------
UNIT2KG = {'kg': 1, '公斤': 1, '斤': 0.5, 'lb': 0.453592}
KG2UNIT = {k: 1/v for k, v in UNIT2KG.items()}

def to_kg(val, unit): # 用户输入 → kg
	return val * UNIT2KG[unit]

def to_show_unit(val, unit): # kg → 用户单位
	return round(val * KG2UNIT[unit], 2)

# ---------------- 主程序 ----------------
class App(tk.Tk):
	def __init__(self):
		super().__init__()
		self.title("体重记录器")
		self.minsize(540, 1)
		self._init_data()

		# 先把所有数据读进内存
		self.all_records = {} # {person_name: [(time, weight, note, bmi), ...]}
		self.person = None # 当前人物 dict
		self.unit = None # 当前显示单位
		self.show_input = False
		self.refresh_persons() # 读取所有记录

		self.build_ui() # 渲染UI
		self.after_idle(self.populate_ui) # 统一填充数据

	def populate_ui(self):
		# 填人物下拉框
		names = list(self.all_records.keys())
		self.cb_person['values'] = names
		if names:
			self.cb_person.current(0)
			self.switch_person()

	# ---------------- 逻辑 ----------------
	# ---------- 统一初始化 ----------
	"""返回 (cfg, records) 或触发向导后重新加载"""
	def _init_data(self):
		# 配置文件
		self.cfg = load_cfg()
		if not self.cfg['persons']:
			self.wizard()
			self.cfg = load_cfg()

		# 2. 数据库
		init_db()
		self.records = {}
		with sqlite3.connect(DB_PATH) as conn:
			for name in [p['name'] for p in self.cfg['persons']]:
				rows = conn.execute(
					'SELECT time, weight, note, bmi FROM records WHERE person=? ORDER BY time',
					(name,)
				).fetchall()
				self.records[name] = rows

	"""重新读取配置+数据库并重绘界面"""
	def refresh(self):
		self.refresh_persons() # 刷新人物数据
		self.populate_ui() # 刷新下拉框
		self.update_scope_buttons() # 刷新时间维度按钮
		self.draw_chart() # 重绘折线图

	"""读取所有数据"""
	def refresh_persons(self):
		self.cfg = load_cfg() # 读取配置
		self.wizard_if_need() # 没有人物就跳出向导来创建
		self.person = self.cfg['persons'][0]

		self.all_records.clear()
		for name in [p['name'] for p in self.cfg['persons']]:
			rows = fetch_records(name)
			self.all_records[name] = rows
		
		if not self.all_records:
			init_db()

	def switch_person(self, *_):
		name = self.cb_person.get()
		self.person = next((p for p in self.cfg['persons'] if p['name'] == name), None)
		if self.person:
			self.lbl_unit.config(text=self.person['unit'])
			self.update_scope_buttons()

	# ---------------- 向导 ----------------
	def wizard_if_need(self):
		# 阻塞向导直到有人物
		while not self.cfg['persons']:
			self.wizard()
			self.cfg = load_cfg()

	def wizard(self, edit=None):
		top = tk.Toplevel(self)
		top.title('添加人物' if edit is None else '修改人物')
		center(top)
		
		# 默认值
		defaults = edit or dict(name='默认', height=175, unit='kg', sex='男', source='日常')

		fields = {}
		labels = ['姓名', '身高(cm)', '性别', '单位', '数据源']
		keys = ['name', 'height', 'sex', 'unit', 'source']
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
			if edit is None: # 新增用户
				self.cfg['persons'].append(person)
			else: # 编辑用户
				idx = next(i for i, p in enumerate(self.cfg['persons']) if p['name'] == edit['name'])
				self.cfg['persons'][idx] = person
			save_cfg(self.cfg)
			self.cfg = load_cfg() # 立刻重新读文件
			top.destroy()

		ttk.Button(top, text='保存', command=save).grid(row=len(labels), columnspan=2, pady=8)
		top.transient(self) # 保持主窗可见
		self.wait_window(top)

	# ---------------- UI ----------------
	def build_ui(self):
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

		ico = Image.open(REFRESH_ICON)
		self.ico_img = ImageTk.PhotoImage(ico.resize((17, 17)))
		self.btn_refresh = ttk.Button(self.bar, image=self.ico_img, command=self.refresh)
		
		self.btn_refresh.grid(row=0, column=6)

		# 输入框容器（初始隐藏）
		self.input_frm = ttk.Frame(self)
		
		# 时间
		ttk.Label(self.input_frm, text='时间').grid(row=1, column=0)
		self.var_time = tk.StringVar(value=datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S'))
		ttk.Entry(self.input_frm, textvariable=self.var_time, width=18).grid(row=1, column=1, padx=(5, 10))

		# 体重
		ttk.Label(self.input_frm, text='体重').grid(row=1, column=2)
		self.var_w = tk.DoubleVar(value=75.00) # 默认75
		self.var_w.set(f"{to_show_unit(75, self.person['unit']):.2f}")
		ttk.Entry(self.input_frm, textvariable=self.var_w, width=6).grid(row=1, column=3, padx=(5, 2))
		self.lbl_unit = ttk.Label(self.input_frm) # ← 加这一行
		self.lbl_unit.config(text=self.person['unit'] if self.person else 'kg')
		self.lbl_unit.grid(row=1, column=5, padx=(0, 5))

		# 备注
		ttk.Label(self.input_frm, text='备注').grid(row=1, column=6)
		self.var_note = tk.StringVar()
		ttk.Entry(self.input_frm, textvariable=self.var_note, width=12).grid(row=1, column=7, padx=(5, 10))

		ttk.Button(self.input_frm, text='确认添加', command=self.add_record).grid(row=1, column=8, padx=(5, 0))

		self.input_frm.lower() # 先放到最底层
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

		self.time_vars = ['7天', '15天', '1月', '3月', '半年', '1年', '3年', '5年', '全部']
		for i in range(len(self.time_vars) + 2):
			self.time_bar.grid_columnconfigure(i, weight=1)

		self.time_btn = {}
		for i, t in enumerate(self.time_vars):
			btn = ttk.Button(self.time_bar, text=t, width=6, command=lambda x=t: self.switch_time_scope(x))
			btn.grid(row=0, column=i+1, padx=2)
			self.time_btn[t] = btn

		self.scope = self.cfg.setdefault('time_scope', '7天') # 默认
		self.switch_time_scope(self.scope)

		# 鼠标悬停提示
		self.anno = None
		self.canvas.mpl_connect('motion_notify_event', self.on_hover)

	def update_scope_buttons(self):
		"""根据现有数据跨度，决定哪些时间维度可见"""
		if not self.person: # 没人就全隐藏
			scopes = []
		else:
			rows = fetch_records(self.person['name'])
			if not rows: # 只有“全部”
				scopes = ['全部']
			else:
				# 最早-最晚 相差天数
				times = [datetime.datetime.strptime(r[0], '%Y.%m.%d %H:%M:%S') for r in rows]
				span_days = (max(times) - min(times)).days
				scopes = ['全部']
				if span_days >= 0: # 任何数据都有“全部”
					scopes.append('7天')
				if span_days >= 7:
					scopes.append('15天')
				if span_days >= 15:
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
		self.scope = scope
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
		rows = fetch_records(self.person['name'])
		if not rows:
			self.show_placeholder()
			return
		
		# 时间过滤
		now = datetime.datetime.now()
		delta_map = {'7天': 0.25, '15天': 0.5, '1月': 1, '3月': 3, '半年': 6, '1年': 12, '3年': 12*3, '5年': 12*5, '全部': 0}
		months = delta_map[self.scope]
		cutoff = subtract_months(now, months=months)
		if months != 0:
			rows = [r for r in rows if datetime.datetime.strptime(r[0], '%Y.%m.%d %H:%M:%S') >= cutoff]

		if not rows:
			self.show_placeholder()
			return

		times = [datetime.datetime.strptime(r[0], '%Y.%m.%d %H:%M:%S') for r in rows]
		weights = [to_show_unit(r[1], self.person['unit']) for r in rows]
		bmis = [r[3] for r in rows]
		notes = [r[2] for r in rows]

		# --------- X 轴仅三个刻度 ---------
		if months != 0: # 不为全部
			start = cutoff
		else: # 为全部
			start = times[0]
		end = now
		mid = start + (end - start) / 2
		print(f"start: {start.date()} end: {end.date()}")

		self.ax.set_xlim(start, end)
		self.ax.set_xticks([start, mid, end])
		self.ax.xaxis.set_major_formatter(DateFormatter('%Y.%m.%d'))
		xlim = self.ax.get_xlim()
		pad = (xlim[1] - xlim[0]) * 0.05
		self.ax.set_xlim(xlim[0], xlim[1] + pad)
		self.ax.set_xlabel('')

		# --------- Y 轴动态整十 ---------
		y_min, y_max = min(weights), max(weights)
		print(f"{y_min=}{self.person['unit']} {y_max=}{self.person['unit']}")
		y_low = math.floor(y_min / 5) * 5
		y_high = math.ceil(y_max / 5) * 5
		print(f"{y_low=}{self.person['unit']} {y_high=}{self.person['unit']}")
		self.ax.set_ylim(y_low, y_high)
		self.ax.set_yticks(range(y_low, y_high + 1, 5))
		self.ax.set_ylabel(f'体重({self.person["unit"]})')
		# y_show = [to_show_unit(w, self.person['unit']) for w in weights]
		# self.ax.set_yticks([to_show_unit(v, self.person['unit']) for v in range(y_low, y_high+1, 10)])

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
			self.var_time.set(datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S'))
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
		idx = min(range(len(self.hover_time)), key=lambda i: abs(date2num(self.hover_time[i]) - x))
		d, w, b, n = self.hover_time[idx], self.hover_weight[idx], self.hover_bmi[idx], self.hover_note[idx]
		# print(f"{d=} {w=} {b=} {n=}")
		if n: # 有备注
			# txt = f"{d.strftime('%Y.%m.%d')}\n{w:.2f} kg\nBMI {b:.1f} {bmi_level(b, self.person['sex'])}\n{n}"
			txt = f"{d.strftime('%Y.%m.%d')}\n{d.strftime('%H:%M:%S')}\n{w:.2f} {self.person['unit']}\n{b} {bmi_level(b, self.person['sex'])}\n{n}"
		else:
			# txt = f"{d.strftime('%Y.%m.%d')}\n{w:.2f} kg\nBMI {b:.1f} {bmi_level(b, self.person['sex'])}"
			txt = f"{d.strftime('%Y.%m.%d')}\n{d.strftime('%H:%M:%S')}\n{w:.2f} {self.person['unit']}\n{b} {bmi_level(b, self.person['sex'])}"
		
		# 计算提示框坐标
		x, y = date2num(d), w
		ax = self.ax

		# 把提示放在点右边，如超出右边界就改放左边
		if x > ax.get_xlim()[1] * 0.9: # 距离右边界 10% 以内
			xytext = (-40, 10) # 向左偏移
		else:
			xytext = (10, 10) # 默认向右
		
		if self.anno:
			self.anno.set_text(txt)
			self.anno.xy = (date2num(d), w)
			self.anno.ha ='center'
			self.anno.va='center', 
		else:
			self.anno = self.ax.annotate(
				txt, xy=(date2num(d), w),
				ha='center', va='center', 
				xytext=xytext, textcoords='offset points',
				bbox=dict(boxstyle='round', alpha=0.7, facecolor='lightyellow'))
		self.canvas.draw_idle()

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
		self.refresh()

	def delete_selected(self, tree, refresh):
		sel = tree.selection()
		if not sel:
			return
		name = tree.item(sel[0], 'values')[0]
		self.cfg['persons'] = [p for p in self.cfg['persons'] if p['name'] != name]
		save_cfg(self.cfg)
		refresh()
		self.refresh_persons()

	# ---------------- 添加记录 ----------------
	def add_record(self):
		if not self.person:
			messagebox.showwarning("提示", "请先选择人物")
			return
		try:
			w_show = round(self.var_w.get(), 2)
			w_kg = to_kg(w_show, self.person['unit'])
			bmi = calc_bmi(w_kg, self.person['height'])
			insert_record(self.person['name'], self.var_time.get(), w_kg, self.var_note.get(), bmi)
			
			# self.draw_chart()
			self.update_scope_buttons()
			time = datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S')
			self.var_time.set(time)
		except Exception as e:
			messagebox.showerror("错误", str(e))

# ---------- 启动 ----------
if __name__ == '__main__':
	App().mainloop()
