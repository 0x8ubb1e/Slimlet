# 轻舟·尺素（Slimlet）

> 一叶轻舟，一纸尺素。  
> 记录体重，也记录心情；  
> 曲线即成长信，写给更轻盈的自己。

---

## 一句话介绍

每天 10 秒，把体重和一句话写进尺素，看轻舟如何过万重山。

## 核心功能

- 极简记录：体重 + 心情一句话

- 曲线回顾：体重折线与心情词云

- 里程碑：每减 1 kg 自动生成「轻舟已过 x 重山」海报

- 数据导出：CSV / Apple Health / WeChat 小程序

## 快速开始

1. 克隆仓库

```bash
git clone https://github.com/0x8ubb1e/Slimlet.git
```

2. 安装依赖

```bash
cd Slimlet
pip install -r requirements.txt
```

3. 运行
   
```bash
python main.py
```

## 技术栈
- React Native (iOS / Android)  
- python + SQLite 本地存储  
- matplotlib 轻量曲线
