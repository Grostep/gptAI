from __future__ import annotations
import base64, calendar, json, os, platform, sys, tempfile
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz

APP_VERSION='0.2.0'
PAGE_W, PAGE_H = 841.89, 1190.55
A4_W, A4_H = 595.276, 841.89
TITLE_Y, TITLE_SIZE = 250.6214, 60.0
TITLE_COLOR=(61/255,76/255,140/255)
COLS=[136.5091,229.2358,321.1990,414.7390,508.3270,601.8814,692.9878]
CAL_TOP, CAL_BOTTOM, ROW_STEP = 624.1647,956.0,82.51
DATE_SIZE, DATE_BASE = 24.0,8.68
DATE_DARK=(52/255,52/255,53/255); DATE_SUN=(238/255,44/255,42/255); DATE_SAT=(0,174/255,239/255); DATE_OUT=(188/255,190/255,192/255)
MAIN_R, BADGE_R = 29.128,14.644
BADGE_DX,BADGE_DY,BADGE_SIZE,BADGE_BASE=-22.988,-22.611,16.0,5.30
LEGEND_Y,LEGEND_X,LEGEND_R,LEGEND_SIZE=1019.36,130.807,8.504,12.0
LEGEND_GAP,LEGEND_ITEM=12.0,26.0
SIX_SCALE=.86
GROUP_ORDER=['tue_thu','wed_fri','mon','sat']

def exe_dir():
    return Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent

def background_path():
    p=exe_dir()/'assets'/'schedule_bg.pdf'
    if not p.exists():
        raise RuntimeError('배경 파일을 찾을 수 없습니다. exe 옆의 assets 폴더에 schedule_bg.pdf를 넣어 주세요.')
    return p

def rgb(v):
    v=v.lstrip('#'); return tuple(int(v[i:i+2],16)/255 for i in (0,2,4))

def rows(n):
    if n<=1:return [CAL_TOP]
    if n<=5:
        span=ROW_STEP*(n-1); top=CAL_TOP+max(0,(CAL_BOTTOM-CAL_TOP-span)/2)
        return [top+i*ROW_STEP for i in range(n)]
    step=(CAL_BOTTOM-CAL_TOP)/(n-1); return [CAL_TOP+i*step for i in range(n)]

def month_grid(y,m): return calendar.Calendar(firstweekday=6).monthdatescalendar(y,m)
def positions(y,m):
    weeks=month_grid(y,m); ys=rows(len(weeks))
    return {d:(COLS[c],ys[r],r,c) for r,w in enumerate(weeks) for c,d in enumerate(w)}

@dataclass
class Group:
    key:str; label:str; target_count:int; main_color:str; badge_color:str; date_text_color:str; selected_dates:list[str]=field(default_factory=list)
    def dates(self):
        out=[]
        for x in self.selected_dates:
            try: out.append(date.fromisoformat(x))
            except: pass
        return sorted(set(out))
    def set_dates(self,ds): self.selected_dates=[d.isoformat() for d in sorted(set(ds))]
    def toggle(self,d):
        s=set(self.dates()); s.remove(d) if d in s else s.add(d); self.set_dates(s)
    def session_map(self): return {d:i+1 for i,d in enumerate(self.dates())}

DEFAULTS={
 'tue_thu':Group('tue_thu','화/목',8,'#F4BE39','#FBB040','#343435'),
 'wed_fri':Group('wed_fri','수/금',8,'#00A650','#52BB70','#343435'),
 'mon':Group('mon','월',4,'#F36C21','#F79455','#FFFFFF'),
 'sat':Group('sat','토',4,'#224192','#396AB3','#FFFFFF')}

@dataclass
class Project:
    year:int; month:int; groups:dict[str,Group]=field(default_factory=dict); show_legend:bool=True; show_outside_dates:bool=True
    @classmethod
    def new(cls,y,m): return cls(y,m,{k:Group(**asdict(v)) for k,v in DEFAULTS.items()})
    def save(self,p):
        d={'version':2,'year':self.year,'month':self.month,'show_legend':self.show_legend,'show_outside_dates':self.show_outside_dates,'groups':{k:asdict(v) for k,v in self.groups.items()}}
        Path(p).write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    @classmethod
    def load(cls,p):
        d=json.loads(Path(p).read_text(encoding='utf-8')); gs={}
        for k,v in DEFAULTS.items(): gs[k]=Group(**d.get('groups',{}).get(k,asdict(v)))
        return cls(int(d['year']),int(d['month']),gs,bool(d.get('show_legend',True)),bool(d.get('show_outside_dates',True)))

def font_dirs():
    if platform.system()=='Windows':
        return [Path(os.environ.get('WINDIR',r'C:\Windows'))/'Fonts',Path(os.environ.get('LOCALAPPDATA',''))/'Microsoft'/'Windows'/'Fonts']
    return [Path('/usr/share/fonts'),Path.home()/'.local/share/fonts']
def find_font(tokens):
    for root in font_dirs():
        if not root.exists(): continue
        try:
            for p in root.rglob('*'):
                n=p.name.lower().replace('_','-')
                if p.is_file() and p.suffix.lower() in {'.ttf','.otf','.ttc'} and any(t in n for t in tokens): return str(p)
        except: pass
    return None
def fonts():
    light=find_font(['pretendard-light','pretendard light']); semi=find_font(['pretendard-semibold','pretendard semibold'])
    if not light or not semi: raise RuntimeError('Pretendard Light / SemiBold 글꼴을 찾을 수 없습니다. 해당 폰트를 설치한 뒤 다시 실행해 주세요.')
    return light,semi

def validate(prj,keys):
    vis={d for w in month_grid(prj.year,prj.month) for d in w}; warns=[]; occ={}
    for k in keys:
        g=prj.groups[k]
        if len(g.dates())!=g.target_count: warns.append(f'{g.label}: 선택 {len(g.dates())}회 / 목표 {g.target_count}회')
        for d in g.dates():
            if d not in vis: warns.append(f'{g.label}: {d.isoformat()} 날짜가 현재 달력에 보이지 않습니다.')
            occ.setdefault(d,[]).append(g.label)
    for d,labs in occ.items():
        if len(labs)>1: warns.append(f'{d.isoformat()}: '+ ' + '.join(labs)+' 수업이 같은 날짜에 겹칩니다.')
    return warns

def centered(page,font,fontname,text,x,y,size,color):
    w=font.text_length(text,fontsize=size); page.insert_text(fitz.Point(x-w/2,y),text,fontsize=size,fontname=fontname,color=color,overlay=True)

def render_a3(prj,out,keys):
    doc=fitz.open(str(background_path())); page=doc[0]
    lightfile,semifile=fonts(); page.insert_font(fontname='PLight',fontfile=lightfile); page.insert_font(fontname='PSemi',fontfile=semifile)
    light=fitz.Font(fontfile=lightfile); semi=fitz.Font(fontfile=semifile)
    a=f'{prj.month}월 '; b='수업 안내'; aw=light.text_length(a,fontsize=TITLE_SIZE); bw=semi.text_length(b,fontsize=TITLE_SIZE); x=PAGE_W/2-(aw+bw)/2
    page.insert_text(fitz.Point(x,TITLE_Y),a,fontsize=TITLE_SIZE,fontname='PLight',color=TITLE_COLOR,overlay=True)
    page.insert_text(fitz.Point(x+aw,TITLE_Y),b,fontsize=TITLE_SIZE,fontname='PSemi',color=TITLE_COLOR,overlay=True)
    bydate={}
    for k in keys:
        for d,n in prj.groups[k].session_map().items(): bydate.setdefault(d,[]).append((k,n))
    weeks=month_grid(prj.year,prj.month); ys=rows(len(weeks)); sc=SIX_SCALE if len(weeks)>=6 else 1
    for r,w in enumerate(weeks):
        for c,d in enumerate(w):
            cx,cy=COLS[c],ys[r]; aa=bydate.get(d,[])
            if aa:
                k,n=aa[0]; g=prj.groups[k]; bx=cx+BADGE_DX*sc; by=cy+BADGE_DY*sc
                page.draw_circle(fitz.Point(cx,cy),MAIN_R*sc,color=None,fill=rgb(g.main_color),overlay=True)
                page.draw_circle(fitz.Point(bx,by),BADGE_R*sc,color=None,fill=rgb(g.badge_color),overlay=True)
                centered(page,light,'PLight',str(d.day),cx,cy+DATE_BASE*sc,DATE_SIZE*sc,rgb(g.date_text_color))
                centered(page,semi,'PSemi',str(n),bx,by+BADGE_BASE*sc,BADGE_SIZE*sc,(1,1,1))
            else:
                if d.month!=prj.month and not prj.show_outside_dates: continue
                color=DATE_OUT if d.month!=prj.month else DATE_SUN if c==0 else DATE_SAT if c==6 else DATE_DARK
                centered(page,light,'PLight',str(d.day),cx,cy+DATE_BASE,DATE_SIZE,color)
    if prj.show_legend and keys:
        x=LEGEND_X
        for k in keys:
            g=prj.groups[k]; page.draw_circle(fitz.Point(x,LEGEND_Y),LEGEND_R,color=None,fill=rgb(g.main_color),overlay=True)
            tx=x+LEGEND_R+LEGEND_GAP; page.insert_text(fitz.Point(tx,LEGEND_Y+4.72),g.label,fontsize=LEGEND_SIZE,fontname='PLight',color=(35/255,31/255,32/255),overlay=True)
            x=tx+light.text_length(g.label,fontsize=LEGEND_SIZE)+LEGEND_ITEM
    doc.save(str(out),garbage=4,deflate=True); doc.close()
def render_pdf(prj,out,size,keys):
    out=Path(out)
    if size=='A3': return render_a3(prj,out,keys)
    tmp=out.with_suffix('.a3tmp.pdf'); render_a3(prj,tmp,keys); src=fitz.open(tmp); d=fitz.open(); p=d.new_page(width=A4_W,height=A4_H); p.show_pdf_page(p.rect,src,0,keep_proportion=True); d.save(out,garbage=4,deflate=True); d.close(); src.close(); tmp.unlink(missing_ok=True)
def render_png(prj,out,size,keys):
    tmp=Path(out).with_suffix('.tmp.pdf'); render_pdf(prj,tmp,size,keys); d=fitz.open(tmp); pix=d[0].get_pixmap(matrix=fitz.Matrix(300/72,300/72),alpha=False); pix.save(str(out)); d.close(); tmp.unlink(missing_ok=True)

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title(f'수업시수표 Batch v{APP_VERSION}'); self.geometry('1380x900'); self.minsize(1180,760)
        now=datetime.now(); self.p=Project.new(now.year,now.month); self.active=tk.StringVar(value='tue_thu'); self.y=tk.IntVar(value=self.p.year); self.m=tk.IntVar(value=self.p.month); self.size=tk.StringVar(value='A3'); self.legend=tk.BooleanVar(value=True); self.outside=tk.BooleanVar(value=True)
        self.visible={k:tk.BooleanVar(value=True) for k in GROUP_ORDER}; self.targets={k:tk.IntVar(value=self.p.groups[k].target_count) for k in GROUP_ORDER}; self.img=None; self.pw=self.ph=self.x0=self.y0=0; self.after_id=None; self.build(); self.after(100,self.refresh_all)
    def build(self):
        pan=ttk.Panedwindow(self,orient=tk.HORIZONTAL); pan.pack(fill=tk.BOTH,expand=True,padx=8,pady=8); left=ttk.Frame(pan,padding=10); right=ttk.Frame(pan,padding=4); pan.add(left,weight=0); pan.add(right,weight=1)
        b=ttk.LabelFrame(left,text='기준 월',padding=8); b.pack(fill=tk.X,pady=(0,8)); ttk.Label(b,text='연도').grid(row=0,column=0); sy=ttk.Spinbox(b,from_=2000,to=2100,textvariable=self.y,width=8,command=self.month_changed); sy.grid(row=0,column=1,padx=(6,12)); ttk.Label(b,text='월').grid(row=0,column=2); sm=ttk.Spinbox(b,from_=1,to=12,textvariable=self.m,width=5,command=self.month_changed); sm.grid(row=0,column=3,padx=(6,0)); sy.bind('<FocusOut>',lambda e:self.month_changed()); sm.bind('<FocusOut>',lambda e:self.month_changed())
        b=ttk.LabelFrame(left,text='수업일 직접 지정',padding=8); b.pack(fill=tk.X,pady=(0,8)); ttk.Label(b,text='편집할 반을 고른 뒤 오른쪽 달력에서 실제 수업 날짜를 클릭하세요.\n날짜순으로 1회, 2회…가 자동 부여됩니다.',justify=tk.LEFT).pack(anchor='w',pady=(0,7)); r=ttk.Frame(b); r.pack(fill=tk.X)
        for k in GROUP_ORDER: ttk.Radiobutton(r,text=self.p.groups[k].label,variable=self.active,value=k,command=self.refresh_list).pack(side=tk.LEFT,padx=(0,8))
        c=ttk.Frame(b); c.pack(fill=tk.X,pady=(8,4))
        for i,k in enumerate(GROUP_ORDER):
            f=ttk.Frame(c); f.grid(row=i//2,column=i%2,sticky='w',padx=(0,12),pady=2); ttk.Label(f,text=f'{self.p.groups[k].label} 목표').pack(side=tk.LEFT); sp=ttk.Spinbox(f,from_=1,to=20,textvariable=self.targets[k],width=4,command=lambda kk=k:self.target_changed(kk)); sp.pack(side=tk.LEFT,padx=4); sp.bind('<FocusOut>',lambda e,kk=k:self.target_changed(kk))
        self.sel=ttk.Label(b); self.sel.pack(anchor='w',pady=(8,2)); self.lst=tk.Listbox(b,height=8,width=34); self.lst.pack(fill=tk.X); f=ttk.Frame(b); f.pack(fill=tk.X,pady=(5,0)); ttk.Button(f,text='현재 반 선택 지우기',command=self.clear_active).pack(side=tk.LEFT); ttk.Button(f,text='모든 반 지우기',command=self.clear_all).pack(side=tk.LEFT,padx=6)
        b=ttk.LabelFrame(left,text='출력에 표시할 반',padding=8); b.pack(fill=tk.X,pady=(0,8))
        for k in GROUP_ORDER: ttk.Checkbutton(b,text=self.p.groups[k].label,variable=self.visible[k],command=self.schedule_refresh).pack(side=tk.LEFT,padx=(0,8))
        f=ttk.Frame(b); f.pack(fill=tk.X,pady=(8,0)); ttk.Checkbutton(f,text='범례 표시',variable=self.legend,command=self.schedule_refresh).pack(side=tk.LEFT); ttk.Checkbutton(f,text='전/다음달 날짜 표시',variable=self.outside,command=self.schedule_refresh).pack(side=tk.LEFT,padx=10)
        b=ttk.LabelFrame(left,text='저장 / 출력',padding=8); b.pack(fill=tk.X,pady=(0,8)); ttk.Radiobutton(b,text='A3',value='A3',variable=self.size).pack(side=tk.LEFT); ttk.Radiobutton(b,text='A4',value='A4',variable=self.size).pack(side=tk.LEFT,padx=8); ttk.Button(b,text='현재 보기 PDF',command=self.export_pdf).pack(fill=tk.X,pady=(8,3)); ttk.Button(b,text='현재 보기 PNG',command=self.export_png).pack(fill=tk.X,pady=3); ttk.Button(b,text='전체 + 반별 4종 일괄 PDF',command=self.export_batch).pack(fill=tk.X,pady=3)
        f=ttk.Frame(left); f.pack(fill=tk.X); ttk.Button(f,text='프로젝트 저장',command=self.save).pack(side=tk.LEFT,expand=True,fill=tk.X); ttk.Button(f,text='프로젝트 열기',command=self.load).pack(side=tk.LEFT,expand=True,fill=tk.X,padx=(6,0)); self.status=ttk.Label(left,wraplength=340,justify=tk.LEFT); self.status.pack(fill=tk.X,pady=(10,0))
        ttk.Label(right,text='미리보기 / 날짜 클릭 편집',font=('TkDefaultFont',11,'bold')).pack(anchor='w',padx=4,pady=(0,4)); self.canvas=tk.Canvas(right,bg='#555555',highlightthickness=0); self.canvas.pack(fill=tk.BOTH,expand=True); self.canvas.bind('<Button-1>',self.click); self.canvas.bind('<Configure>',lambda e:self.schedule_refresh())
    def sync(self):
        self.p.year=int(self.y.get()); self.p.month=max(1,min(12,int(self.m.get()))); self.p.show_legend=self.legend.get(); self.p.show_outside_dates=self.outside.get()
        for k in GROUP_ORDER:self.p.groups[k].target_count=int(self.targets[k].get())
    def month_changed(self):
        try:self.sync(); self.refresh_list(); self.schedule_refresh()
        except:pass
    def target_changed(self,k):
        try:self.p.groups[k].target_count=int(self.targets[k].get()); self.refresh_list(); self.schedule_refresh()
        except:pass
    def keys(self): return [k for k in GROUP_ORDER if self.visible[k].get()]
    def refresh_list(self):
        g=self.p.groups[self.active.get()]; ds=g.dates(); self.sel.config(text=f'{g.label}: {len(ds)}회 선택 / 목표 {g.target_count}회'); self.lst.delete(0,tk.END)
        for i,d in enumerate(ds,1): self.lst.insert(tk.END,f'{i:>2}회   {d.year}.{d.month}.{d.day}')
    def clear_active(self): self.p.groups[self.active.get()].set_dates([]); self.refresh_all()
    def clear_all(self):
        if messagebox.askyesno('확인','모든 반의 선택 날짜를 지울까요?'):
            for g in self.p.groups.values():g.set_dates([])
            self.refresh_all()
    def schedule_refresh(self):
        if self.after_id:self.after_cancel(self.after_id)
        self.after_id=self.after(120,self.refresh_preview)
    def refresh_all(self): self.sync(); self.refresh_list(); self.refresh_preview()
    def refresh_preview(self):
        self.after_id=None
        if self.canvas.winfo_width()<100:return
        try:
            fd,tmp=tempfile.mkstemp(suffix='.pdf'); os.close(fd)
            try:
                render_pdf(self.p,tmp,'A3',self.keys()); d=fitz.open(tmp); aw=max(100,self.canvas.winfo_width()-20); ah=max(100,self.canvas.winfo_height()-20); sc=min(aw/PAGE_W,ah/PAGE_H); pix=d[0].get_pixmap(matrix=fitz.Matrix(sc,sc),alpha=False); data=base64.b64encode(pix.tobytes('png')).decode(); d.close()
            finally: os.unlink(tmp) if os.path.exists(tmp) else None
            self.img=tk.PhotoImage(data=data); self.pw,self.ph=self.img.width(),self.img.height(); self.x0=(self.canvas.winfo_width()-self.pw)//2; self.y0=(self.canvas.winfo_height()-self.ph)//2; self.canvas.delete('all'); self.canvas.create_image(self.x0,self.y0,anchor='nw',image=self.img); ws=validate(self.p,self.keys()); self.status.config(text='\n'.join(ws[:5]) if ws else '선택 상태 정상')
        except Exception as e:self.canvas.delete('all'); self.canvas.create_text(20,20,anchor='nw',fill='white',text=f'미리보기 오류:\n{e}'); self.status.config(text=str(e))
    def click(self,e):
        if not self.pw or not(self.x0<=e.x<=self.x0+self.pw and self.y0<=e.y<=self.y0+self.ph):return
        px=(e.x-self.x0)*PAGE_W/self.pw; py=(e.y-self.y0)*PAGE_H/self.ph; best=None; bd=1e9
        for d,(x,y,_,__) in positions(self.p.year,self.p.month).items():
            dist=((px-x)/46)**2+((py-y)/35)**2
            if dist<bd:best,bd=d,dist
        if best and bd<=1:self.p.groups[self.active.get()].toggle(best); self.refresh_list(); self.refresh_preview()
    def confirm(self,keys):
        ws=validate(self.p,keys)
        return True if not ws else messagebox.askyesno('확인 필요','다음 항목을 확인해 주세요:\n\n'+'\n'.join('- '+w for w in ws[:10])+'\n\n그래도 출력할까요?')
    def export_pdf(self):
        self.sync(); keys=self.keys()
        if not self.confirm(keys):return
        p=filedialog.asksaveasfilename(defaultextension='.pdf',initialfile=f'{self.p.year}-{self.p.month:02d}_수업안내_{self.size.get()}.pdf',filetypes=[('PDF','*.pdf')])
        if p:
            try:render_pdf(self.p,p,self.size.get(),keys); messagebox.showinfo('완료',f'저장했습니다.\n{p}')
            except Exception as e:messagebox.showerror('오류',str(e))
    def export_png(self):
        self.sync(); keys=self.keys()
        if not self.confirm(keys):return
        p=filedialog.asksaveasfilename(defaultextension='.png',initialfile=f'{self.p.year}-{self.p.month:02d}_수업안내_{self.size.get()}.png',filetypes=[('PNG','*.png')])
        if p:
            try:render_png(self.p,p,self.size.get(),keys); messagebox.showinfo('완료',f'저장했습니다.\n{p}')
            except Exception as e:messagebox.showerror('오류',str(e))
    def export_batch(self):
        self.sync(); folder=filedialog.askdirectory(title='일괄 저장 폴더 선택')
        if not folder or not self.confirm(GROUP_ORDER):return
        try:
            variants=[('전체',GROUP_ORDER)]+[(self.p.groups[k].label.replace('/',''),[k]) for k in GROUP_ORDER]
            for label,keys in variants:render_pdf(self.p,Path(folder)/f'{self.p.year}-{self.p.month:02d}_{label}_{self.size.get()}.pdf',self.size.get(),keys)
            messagebox.showinfo('완료',f'5종 PDF를 저장했습니다.\n{folder}')
        except Exception as e:messagebox.showerror('오류',str(e))
    def save(self):
        self.sync(); p=filedialog.asksaveasfilename(defaultextension='.json',initialfile=f'{self.p.year}-{self.p.month:02d}_수업시수표.json',filetypes=[('Schedule JSON','*.json')]);
        if p:self.p.save(p); messagebox.showinfo('완료','프로젝트를 저장했습니다.')
    def load(self):
        p=filedialog.askopenfilename(filetypes=[('Schedule JSON','*.json'),('All files','*.*')])
        if not p:return
        try:
            self.p=Project.load(p); self.y.set(self.p.year); self.m.set(self.p.month); self.legend.set(self.p.show_legend); self.outside.set(self.p.show_outside_dates)
            for k in GROUP_ORDER:self.targets[k].set(self.p.groups[k].target_count)
            self.refresh_all()
        except Exception as e:messagebox.showerror('오류',str(e))

if __name__=='__main__': App().mainloop()
