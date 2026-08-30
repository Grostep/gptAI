from pathlib import Path
p=Path('schedule_batch/final_app.py')
s=p.read_text(encoding='utf-8')
if 'from timetable import TimetableWindow' not in s:
    s=s.replace('import fitz\n','import fitz\nfrom timetable import TimetableWindow\n')
s=s.replace("APP_VERSION='0.4.0'","APP_VERSION='0.5.0'").replace("APP_VERSION='0.3.0'","APP_VERSION='0.5.0'")
needle="        b=ttk.LabelFrame(left,text='기준 월',padding=8);"
if needle not in s: raise RuntimeError('schedule UI insertion point not found')
s=s.replace(needle,"        ttk.Button(left,text='시간표 만들기',command=self.open_timetable).pack(fill=tk.X,pady=(0,8))\n"+needle,1)
marker="\nif __name__=='__main__': App().mainloop()"
if marker not in s: raise RuntimeError('main marker not found')
method="\n    def open_timetable(self):\n        TimetableWindow(self)\n"
s=s.replace(marker,method+marker,1)
p.write_text(s,encoding='utf-8')
