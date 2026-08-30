from pathlib import Path

p = Path('schedule_batch/final_app.py')
s = p.read_text(encoding='utf-8')

s = s.replace('import base64, calendar, json, os, platform, sys, tempfile',
              'import base64, calendar, os, platform, sys, tempfile')
s = s.replace("APP_VERSION='0.2.0'", "APP_VERSION='0.3.0'")

# Remove developer-facing JSON project save/load support.
a = s.index('    def save(self,p):')
b = s.index('\ndef font_dirs():', a)
s = s[:a] + s[b+1:]

# Remove PNG output helper entirely.
a = s.index('def render_png(prj,out,size,keys):')
b = s.index('\nclass App(tk.Tk):', a)
s = s[:a] + s[b+1:]

old_ui = """        b=ttk.LabelFrame(left,text='저장 / 출력',padding=8); b.pack(fill=tk.X,pady=(0,8)); ttk.Radiobutton(b,text='A3',value='A3',variable=self.size).pack(side=tk.LEFT); ttk.Radiobutton(b,text='A4',value='A4',variable=self.size).pack(side=tk.LEFT,padx=8); ttk.Button(b,text='현재 보기 PDF',command=self.export_pdf).pack(fill=tk.X,pady=(8,3)); ttk.Button(b,text='현재 보기 PNG',command=self.export_png).pack(fill=tk.X,pady=3); ttk.Button(b,text='전체 + 반별 4종 일괄 PDF',command=self.export_batch).pack(fill=tk.X,pady=3)
        f=ttk.Frame(left); f.pack(fill=tk.X); ttk.Button(f,text='프로젝트 저장',command=self.save).pack(side=tk.LEFT,expand=True,fill=tk.X); ttk.Button(f,text='프로젝트 열기',command=self.load).pack(side=tk.LEFT,expand=True,fill=tk.X,padx=(6,0)); self.status=ttk.Label(left,wraplength=340,justify=tk.LEFT); self.status.pack(fill=tk.X,pady=(10,0))
"""
new_ui = """        b=ttk.LabelFrame(left,text='PDF 저장 / 출력',padding=8); b.pack(fill=tk.X,pady=(0,8)); ttk.Radiobutton(b,text='A3',value='A3',variable=self.size).pack(side=tk.LEFT); ttk.Radiobutton(b,text='A4',value='A4',variable=self.size).pack(side=tk.LEFT,padx=8); ttk.Button(b,text='전체 PDF 저장',command=self.export_all_pdf).pack(fill=tk.X,pady=(8,3)); ttk.Button(b,text='체크한 반 PDF 저장',command=self.export_selected_pdf).pack(fill=tk.X,pady=3); ttk.Button(b,text='전체 + 반별 4종 일괄 PDF',command=self.export_batch).pack(fill=tk.X,pady=3)
        self.status=ttk.Label(left,wraplength=340,justify=tk.LEFT); self.status.pack(fill=tk.X,pady=(10,0))
"""
if old_ui not in s:
    raise RuntimeError('v0.2 output UI block was not found')
s = s.replace(old_ui, new_ui)

a = s.index('    def export_pdf(self):')
b = s.index("\nif __name__=='__main__':", a)
new_methods = '''    def _save_pdf(self, keys, label):
        self.sync()
        if not keys:
            messagebox.showwarning('선택 필요','PDF에 표시할 반을 하나 이상 체크해 주세요.')
            return
        if not self.confirm(keys): return
        safe_label=label.replace('/','')
        p=filedialog.asksaveasfilename(
            defaultextension='.pdf',
            initialfile=f'{self.p.year}-{self.p.month:02d}_{safe_label}_{self.size.get()}.pdf',
            filetypes=[('PDF','*.pdf')])
        if p:
            try:
                render_pdf(self.p,p,self.size.get(),keys)
                messagebox.showinfo('완료',f'PDF를 저장했습니다.\\n{p}')
            except Exception as e:
                messagebox.showerror('오류',str(e))

    def export_all_pdf(self):
        self._save_pdf(GROUP_ORDER,'전체')

    def export_selected_pdf(self):
        keys=self.keys()
        if not keys:
            messagebox.showwarning('선택 필요','출력에 표시할 반에서 하나 이상 체크해 주세요.')
            return
        label='_'.join(self.p.groups[k].label.replace('/','') for k in keys)
        self._save_pdf(keys,label)

    def export_batch(self):
        self.sync(); folder=filedialog.askdirectory(title='일괄 저장 폴더 선택')
        if not folder or not self.confirm(GROUP_ORDER):return
        try:
            variants=[('전체',GROUP_ORDER)]+[(self.p.groups[k].label.replace('/',''),[k]) for k in GROUP_ORDER]
            for label,keys in variants:
                render_pdf(self.p,Path(folder)/f'{self.p.year}-{self.p.month:02d}_{label}_{self.size.get()}.pdf',self.size.get(),keys)
            messagebox.showinfo('완료',f'전체 + 반별 4종, 총 5개 PDF를 저장했습니다.\\n{folder}')
        except Exception as e:
            messagebox.showerror('오류',str(e))
'''
s = s[:a] + new_methods + s[b:]

for forbidden in ('프로젝트 저장', '프로젝트 열기', '현재 보기 PNG', 'def export_png', 'def render_png'):
    if forbidden in s:
        raise RuntimeError(f'Removed feature still present: {forbidden}')
for required in ('전체 PDF 저장', '체크한 반 PDF 저장', "APP_VERSION='0.3.0'"):
    if required not in s:
        raise RuntimeError(f'Required v0.3 feature missing: {required}')

p.write_text(s, encoding='utf-8')
