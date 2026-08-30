from pathlib import Path

p = Path('schedule_batch/final_app.py')
s = p.read_text(encoding='utf-8')

s = s.replace("APP_VERSION='0.3.0'", "APP_VERSION='0.4.0'")

old_block = """        b=ttk.LabelFrame(left,text='출력에 표시할 반',padding=8); b.pack(fill=tk.X,pady=(0,8))
        for k in GROUP_ORDER: ttk.Checkbutton(b,text=self.p.groups[k].label,variable=self.visible[k],command=self.schedule_refresh).pack(side=tk.LEFT,padx=(0,8))
        f=ttk.Frame(b); f.pack(fill=tk.X,pady=(8,0)); ttk.Checkbutton(f,text='범례 표시',variable=self.legend,command=self.schedule_refresh).pack(side=tk.LEFT); ttk.Checkbutton(f,text='전/다음달 날짜 표시',variable=self.outside,command=self.schedule_refresh).pack(side=tk.LEFT,padx=10)
"""
new_block = """        b=ttk.LabelFrame(left,text='PDF에 포함할 반 선택',padding=8); b.pack(fill=tk.X,pady=(0,8))
        row=ttk.Frame(b); row.pack(fill=tk.X)
        for k in GROUP_ORDER: ttk.Checkbutton(row,text=self.p.groups[k].label,variable=self.visible[k],command=self.schedule_refresh).pack(side=tk.LEFT,padx=(0,8))
        selbar=ttk.Frame(b); selbar.pack(fill=tk.X,pady=(7,0))
        ttk.Button(selbar,text='전체 선택',command=lambda:self.set_all_visible(True)).pack(side=tk.LEFT)
        ttk.Button(selbar,text='전체 해제',command=lambda:self.set_all_visible(False)).pack(side=tk.LEFT,padx=(6,0))
        f=ttk.Frame(b); f.pack(fill=tk.X,pady=(8,0)); ttk.Checkbutton(f,text='범례 표시',variable=self.legend,command=self.schedule_refresh).pack(side=tk.LEFT); ttk.Checkbutton(f,text='전/다음달 날짜 표시',variable=self.outside,command=self.schedule_refresh).pack(side=tk.LEFT,padx=10)
"""
if old_block not in s:
    raise RuntimeError('output selection UI block not found')
s = s.replace(old_block, new_block)

s = s.replace("ttk.Button(b,text='체크한 반 PDF 저장',command=self.export_selected_pdf)",
              "ttk.Button(b,text='선택한 반 PDF 저장',command=self.export_selected_pdf)")
s = s.replace("messagebox.showwarning('선택 필요','출력에 표시할 반에서 하나 이상 체크해 주세요.')",
              "messagebox.showwarning('선택 필요','PDF에 포함할 반을 하나 이상 선택해 주세요.')")

anchor = "    def schedule_refresh(self):"
if anchor not in s:
    raise RuntimeError('schedule_refresh method not found')
method = """    def set_all_visible(self, value):
        for v in self.visible.values():
            v.set(value)
        self.schedule_refresh()

"""
s = s.replace(anchor, method + anchor, 1)

for required in ("APP_VERSION='0.4.0'", 'PDF에 포함할 반 선택', '전체 선택', '전체 해제', '선택한 반 PDF 저장', 'def set_all_visible'):
    if required not in s:
        raise RuntimeError(f'Required v0.4 feature missing: {required}')

p.write_text(s, encoding='utf-8')
