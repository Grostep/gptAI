from pathlib import Path

p=Path('schedule_batch/final_app.py')
s=p.read_text(encoding='utf-8')

s=s.replace("APP_VERSION='0.6.0'","APP_VERSION='0.7.0'")

old_session="    def session_map(self): return {d:i+1 for i,d in enumerate(self.dates())}"
new_session="    def session_map(self):\n        count=max(1,int(self.target_count))\n        return {d:(i % count)+1 for i,d in enumerate(self.dates())}"
if old_session not in s: raise RuntimeError('session_map block not found')
s=s.replace(old_session,new_session,1)

old_help="날짜순으로 1회, 2회…가 자동 부여됩니다."
new_help="날짜순으로 회차가 자동 부여되며, 기준 회차를 넘으면 1회부터 다시 시작합니다."
if old_help not in s: raise RuntimeError('schedule help text not found')
s=s.replace(old_help,new_help,1)

old_validate="        if len(g.dates())!=g.target_count: warns.append(f'{g.label}: 선택 {len(g.dates())}회 / 목표 {g.target_count}회')"
new_validate="        if len(g.dates())<g.target_count: warns.append(f'{g.label}: 선택 {len(g.dates())}개 / 기준 회차 {g.target_count}회')"
if old_validate not in s: raise RuntimeError('validation count rule not found')
s=s.replace(old_validate,new_validate,1)

old_refresh="""    def refresh_list(self):
        g=self.p.groups[self.active.get()]; ds=g.dates(); self.sel.config(text=f'{g.label}: {len(ds)}회 선택 / 목표 {g.target_count}회'); self.lst.delete(0,tk.END)
        for i,d in enumerate(ds,1): self.lst.insert(tk.END,f'{i:>2}회   {d.year}.{d.month}.{d.day}')
"""
new_refresh="""    def refresh_list(self):
        g=self.p.groups[self.active.get()]; ds=g.dates(); sm=g.session_map(); self.sel.config(text=f'{g.label}: {len(ds)}개 날짜 선택 / 회차 1~{g.target_count} 반복'); self.lst.delete(0,tk.END)
        for d in ds: self.lst.insert(tk.END,f'{sm[d]:>2}회   {d.year}.{d.month}.{d.day}')
"""
if old_refresh not in s: raise RuntimeError('refresh_list block not found')
s=s.replace(old_refresh,new_refresh,1)

for required in ("APP_VERSION='0.7.0'", '(i % count)+1', '회차 1~{g.target_count} 반복', '기준 회차를 넘으면 1회부터 다시 시작'):
    if required not in s: raise RuntimeError(f'v0.7 requirement missing: {required}')

p.write_text(s,encoding='utf-8')
