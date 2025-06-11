import tkinter as tk
from tkinter import messagebox
import pandas as pd
import json
import random

# ------------------ 干员生成逻辑核心类 ------------------

class OperatorDataGenerator:
    def __init__(self):
        self.class_types = ['先锋', '特种', '近卫', '重装', '辅助', '射手', '术士']
        self.class_configs = {
            '先锋': {'atk_range': (400, 1000), 'hp_range': (1000, 1500), 'def_range': (200, 350),
                   'cost_range': (8, 15), 'mdef': 0, 'block_count': 1, 'atk_speed': 1.0},
            '特种': {'atk_range': (1000, 3500), 'hp_range': (2500, 4000), 'def_range': (350, 500),
                   'cost_range': (15, 20), 'mdef': 0, 'block_count': 1, 'atk_speed': 1.0},
            '近卫': {'atk_range': (2000, 3500), 'hp_range': (2500, 4000), 'def_range': (500, 700),
                   'cost_range': (15, 20), 'mdef': 0, 'block_count': 1, 'atk_speed': 1.0},
            '重装': {'atk_range': (1500, 2000), 'hp_range': (4000, 6000), 'def_range': (800, 1000),
                   'cost_range': (21, 25), 'mdef': 0, 'block_count': 3, 'atk_speed': 1.0},
            '辅助': {'atk_range': (1000, 1500), 'hp_range': (1500, 2500), 'def_range': (80, 200),
                   'cost_range': (15, 20), 'mdef': 0, 'block_count': 1, 'atk_speed': 1.0},
            '射手': {'atk_range': (4000, 5000), 'hp_range': (1500, 2500), 'def_range': (80, 200),
                   'cost_range': (15, 20), 'mdef': 0, 'block_count': 1, 'atk_speed_range': (1.0, 2.25)},
            '术士': {'atk_range': (4000, 5000), 'hp_range': (1500, 2500), 'def_range': (80, 200),
                   'cost_range': (15, 20), 'mdef_range': (15, 30), 'block_count': 1, 'atk_speed_range': (0.6, 1.0)}
        }
        self.operator_names = [
            '银灰', '陈', '斯卡蒂', '艾雅法拉', '伊芙利特', '能天使', '推进之王', '闪灵',
            '夜莺', '白面鸮', '凛冬', '德克萨斯', '拉普兰德', '蓝毒', '白金', '陨星',
            '梅尔', '华法琳', '雷蛇', '红', '崖心', '凯尔希', '山', '棘刺',
            '森蚺', '煌', '鞭刃', '诗怀雅', '空爆', '送葬人', '玫兰莎', '杜林',
            '安德切尔', '史都华德', '芬', '香草', '翎羽', '克洛丝', '炎熔', '芙蓉',
            '杰西卡', '流星', '白雪', '安赛尔', '嘉维尔', '缠丸', '月见夜', '泡普卡'
        ]
        self.available_names = self.operator_names.copy()
        random.shuffle(self.available_names)

    def apply_random_deviation(self, value, percent=1.0):
        deviation = value * (percent / 100)
        return value + random.uniform(-deviation, deviation)

    def get_attack_type(self, class_type):
        if class_type == '术士':
            return '法术伤害'
        if class_type == '射手':
            return '物理伤害'
        return '法术伤害' if random.random() < 0.05 else '物理伤害'

    def generate_single_operator(self, class_type):
        if not self.available_names:
            return None

        config = self.class_configs[class_type]
        name = self.available_names.pop()
        atk = int(self.apply_random_deviation(random.randint(*config['atk_range'])))
        hp = int(self.apply_random_deviation(random.randint(*config['hp_range'])))
        defense = int(self.apply_random_deviation(random.randint(*config['def_range'])))
        cost = int(self.apply_random_deviation(random.randint(*config['cost_range'])))
        atk_speed = config.get('atk_speed', random.uniform(*config.get('atk_speed_range', (1.0, 1.5))))
        atk_speed = round(self.apply_random_deviation(atk_speed), 2)
        mdef = config.get('mdef', random.randint(*config.get('mdef_range', (0, 0))))
        mdef = int(self.apply_random_deviation(mdef)) if mdef else 0

        return {
            '名称': name,
            '职业类型': class_type,
            '生命值': max(500, min(hp, 6000)),
            '攻击力': max(400, min(atk, 5000)),
            '攻击速度': max(0.5, min(atk_speed, 3.0)),
            '攻击类型': self.get_attack_type(class_type),
            '防御力': max(80, min(defense, 1000)),
            '法抗': max(0, min(mdef, 30)),
            '部署费用': max(1, cost),
            '阻挡数': config['block_count']
        }

    def generate_operators(self, count):
        operators = []
        base = count // len(self.class_types)
        remainder = count % len(self.class_types)
        distribution = {t: base for t in self.class_types}
        for _ in range(remainder):
            distribution[random.choice(self.class_types)] += 1

        for t, n in distribution.items():
            for _ in range(n):
                op = self.generate_single_operator(t)
                if op:
                    operators.append(op)
                else:
                    return operators
        return operators

    def save_all_formats(self, operators, filename="output"):
        df = pd.DataFrame(operators)
        df.to_excel(f"{filename}.xlsx", index=False, engine='openpyxl')
        df.to_csv(f"{filename}.csv", index=False, encoding='utf-8-sig')
        with open(f"{filename}.json", 'w', encoding='utf-8') as f:
            json.dump([{ 'name': op['名称'], 'class_type': op['职业类型'], 'hp': op['生命值'],
                         'atk': op['攻击力'], 'atk_speed': op['攻击速度'], 'atk_type': op['攻击类型'],
                         'def': op['防御力'], 'mdef': op['法抗'], 'cost': op['部署费用'],
                         'block_count': op['阻挡数']} for op in operators], f, ensure_ascii=False, indent=2)

# ------------------ 图形界面 ------------------

def generate():
    try:
        num = int(entry.get())
        if num <= 0:
            raise ValueError

        gen = OperatorDataGenerator()
        ops = gen.generate_operators(num)

        if not ops:
            messagebox.showwarning("已达上限", "干员名称已全部用尽，生成自动终止。")
            return

        gen.save_all_formats(ops)
        messagebox.showinfo("生成完成", f"已生成 {len(ops)} 位干员数据！\n输出文件：output.json / .csv / .xlsx")
    except ValueError:
        messagebox.showerror("输入错误", "请输入有效的整数（大于 0）")

# 窗口设置
root = tk.Tk()
root.title("明日方舟干员数据生成器")
root.geometry("360x180")

tk.Label(root, text="请输入生成的干员数量：", font=("微软雅黑", 12)).pack(pady=10)
entry = tk.Entry(root, font=("微软雅黑", 12), justify="center")
entry.pack()
tk.Button(root, text="开始生成", font=("微软雅黑", 12), command=generate).pack(pady=20)

root.mainloop()
