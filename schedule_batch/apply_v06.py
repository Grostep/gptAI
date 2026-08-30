from pathlib import Path

# Timetable: use a frame in the main notebook instead of a separate Toplevel.
tp=Path('schedule_batch/timetable.py')
t=tp.read_text(encoding='utf-8')
old_asset="""def asset(name):
    p=exe_dir()/'assets'/name
    if not p.exists(): raise RuntimeError(f'필수 파일을 찾을 수 없습니다: assets/{name}')
    return p
"""
new_asset="""def asset(name):
    candidates=[]
    if getattr(sys,'frozen',False) and hasattr(sys,'_MEIPASS'):
        candidates.append(Path(sys._MEIPASS)/'assets'/name)
    base=exe_dir()
    candidates += [base/'assets'/name, base/name, Path.cwd()/'assets'/name, Path.cwd()/name]
    for p in candidates:
        if p.exists(): return p
    raise RuntimeError(f'필수 파일을 찾을 수 없습니다: {name}\\n프로그램과 함께 제공된 assets 폴더를 그대로 두어 주세요.')
"""
if old_asset not in t: raise RuntimeError('timetable asset function not found')
t=t.replace(old_asset,new_asset,1)
t=t.replace('class TimetableWindow(tk.Toplevel):','class TimetableFrame(ttk.Frame):',1)
old_init="""    def __init__(self,parent):
        super().__init__(parent);self.title('시간표 제작');self.geometry('1380x900');self.minsize(1100,720);self.p=Project.new(datetime.now().month);self.m=tk.IntVar(value=self.p.month);self.size=tk.StringVar(value='A3');self.img=None;self.pw=self.ph=self.x0=self.y0=0;self.after_id=None;self.build();self.after(150,self.refresh)
"""
new_init="""    def __init__(self,parent):
        super().__init__(parent);self.p=Project.new(datetime.now().month);self.m=tk.IntVar(value=self.p.month);self.size=tk.StringVar(value='A3');self.img=None;self.pw=self.ph=self.x0=self.y0=0;self.after_id=None;self.build();self.after(150,self.refresh)
"""
if old_init not in t: raise RuntimeError('TimetableWindow init block not found')
t=t.replace(old_init,new_init,1)
tp.write_text(t,encoding='utf-8')

# Main window: turn the two tools into notebook tabs.
p=Path('schedule_batch/final_app.py')
s=p.read_text(encoding='utf-8')
s=s.replace('from timetable import TimetableWindow','from timetable import TimetableFrame')
s=s.replace("APP_VERSION='0.5.0'","APP_VERSION='0.6.0'")
s=s.replace("self.title(f'수업시수표 Batch v{APP_VERSION}')","self.title(f'수업시수표 · 시간표 제작기 v{APP_VERSION}')")
s=s.replace("        ttk.Button(left,text='시간표 만들기',command=self.open_timetable).pack(fill=tk.X,pady=(0,8))\n",'',1)
s=s.replace("\n    def open_timetable(self):\n        TimetableWindow(self)\n",'\n',1)
old_state="self.img=None; self.pw=self.ph=self.x0=self.y0=0; self.after_id=None; self.build(); self.after(100,self.refresh_all)"
new_state="self.img=None; self.pw=self.ph=self.x0=self.y0=0; self.after_id=None; self.tabs=ttk.Notebook(self); self.tabs.pack(fill=tk.BOTH,expand=True); self.schedule_tab=ttk.Frame(self.tabs); self.timetable_tab=ttk.Frame(self.tabs); self.tabs.add(self.schedule_tab,text='수업시수표'); self.tabs.add(self.timetable_tab,text='시간표'); self.build(); self.timetable=TimetableFrame(self.timetable_tab); self.timetable.pack(fill=tk.BOTH,expand=True); self.after(100,self.refresh_all)"
if old_state not in s: raise RuntimeError('main app init state block not found')
s=s.replace(old_state,new_state,1)
old_pan="pan=ttk.Panedwindow(self,orient=tk.HORIZONTAL); pan.pack(fill=tk.BOTH,expand=True,padx=8,pady=8)"
new_pan="pan=ttk.Panedwindow(self.schedule_tab,orient=tk.HORIZONTAL); pan.pack(fill=tk.BOTH,expand=True,padx=8,pady=8)"
if old_pan not in s: raise RuntimeError('main schedule panedwindow block not found')
s=s.replace(old_pan,new_pan,1)
for required in ("APP_VERSION='0.6.0'", "text='수업시수표'", "text='시간표'", 'TimetableFrame(self.timetable_tab)'):
    if required not in s: raise RuntimeError(f'v0.6 requirement missing: {required}')
p.write_text(s,encoding='utf-8')
