from __future__ import annotations
import base64, os, platform, sys, tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import fitz

PAGE_W,PAGE_H=841.89,1190.55; A4_W,A4_H=595.276,841.89
MONTHS=['January','February','March','April','May','June','July','August','September','October','November','December']
TITLE_COLOR=(34/255,65/255,146/255); SUB_COLOR=(195/255,196/255,198/255); TEXT_COLOR=(35/255,31/255,32/255)
TITLE_BASE,SUB_BASE=222.8489,262.1976; TITLE_SIZE,SUB_SIZE,CLASS_SIZE,NOTICE_SIZE=60.0,24.0,14.0,18.0
NOTICE_X=36.43; NOTICE_BASES=[1027.3157,1055.3057,1083.2957]

def exe_dir(): return Path(sys.executable).resolve().parent if getattr(sys,'frozen',False) else Path(__file__).resolve().parent
def asset(name):
    p=exe_dir()/'assets'/name
    if not p.exists(): raise RuntimeError(f'필수 파일을 찾을 수 없습니다: assets/{name}')
    return p

def font_dirs():
    if platform.system()=='Windows': return [Path(os.environ.get('WINDIR',r'C:\Windows'))/'Fonts',Path(os.environ.get('LOCALAPPDATA',''))/'Microsoft'/'Windows'/'Fonts']
    return [Path('/usr/share/fonts'),Path.home()/'.local/share/fonts']
def maple_font():
    fallback=None
    for root in font_dirs():
        if not root.exists(): continue
        try:
            for p in root.rglob('*'):
                if not p.is_file() or p.suffix.lower() not in {'.ttf','.otf','.ttc'}: continue
                n=p.name.lower().replace('_','').replace('-','').replace(' ','')
                if 'maplestory' in n:
                    fallback=fallback or str(p)
                    if 'bold' in n:return str(p)
        except: pass
    if fallback:return fallback
    raise RuntimeError('메이플스토리 Bold 글꼴을 찾을 수 없습니다. 해당 폰트를 설치한 뒤 다시 실행해 주세요.')

def centered(page,font,fontname,text,x,y,size,color):
    w=font.text_length(text,fontsize=size); page.insert_text(fitz.Point(x-w/2,y),text,fontsize=size,fontname=fontname,color=color,overlay=True)

CELLS={}
xs=[(97.70,196.04),(200.89,299.23),(304.23,402.93),(407.42,506.12),(510.09,608.79)]
ys=[(383.48,476.06),(483.57,576.15),(583.66,676.24),(683.59,776.17),(783.69,876.27),(883.79,976.37)]
for c,day in enumerate(['MON','TUE','WED','THU','FRI']):
    for r in range(6):CELLS[f'{day}{r+1}']=fitz.Rect(xs[c][0],ys[r][0],xs[c][1],ys[r][1])
sys=[(383.57,459.42),(466.93,542.77),(550.28,626.12),(633.63,709.47)]
for r in range(4):CELLS[f'SAT{r+1}']=fitz.Rect(707.35,sys[r][0],805.95,sys[r][1])

DEFAULTS={
'MON1':'초3\nGrammar1','TUE1':'롸잇투게더2\n정규1-1','WED1':'롸잇투게더2\n정규2-3','THU1':'롸잇투게더2\n정규1-1','FRI1':'롸잇투게더2\n정규2-3',
'MON2':'초3\nGrammar2','TUE2':'Evan Moor\nClass','WED2':'롸잇투게더1\n정규4-1','THU2':'Evan Moor\nClass','FRI2':'롸잇투게더1\n정규4-1',
'MON3':'롸잇투게더1\n정규1-2','TUE3':'롸잇투게더2\n정규1-2','WED3':'롸잇투게더2\n정규2-3','THU3':'롸잇투게더2\n정규1-2','FRI3':'롸잇투게더2\n정규2-3',
'MON4':'','TUE4':'드림스타터\n정규3-1','WED4':'프리스타터\n정규4-3','THU4':'드림스타터\n정규3-1','FRI4':'프리스타터\n정규4-3',
'MON5':'','TUE5':'고등선행반','WED5':'중등선행반','THU5':'고등선행반','FRI5':'중등선행반','MON6':'','TUE6':'','WED6':'고등선행반','THU6':'','FRI6':'고등선행반',
'SAT1':'Inquiry\nWelcome','SAT2':'Evan Moor\nClass','SAT3':'Evan Moor\nClass','SAT4':'Sing it\nSay it'}
DEFAULT_NOTICES='* 추석 연휴 기간인 9/24(목)~26(토)은 추석 연휴로 수업을 진행하지 않습니다.\n* 수업스케쥴은 센터 사정에 따라 변동될 수 있습니다.\n* 각 클래스 관련 문의사항은 센터로 연락주세요. (T.010-8105-0500)'

@dataclass
class Cell: text:str=''; closed:bool=False
@dataclass
class Project:
    month:int=9; cells:dict[str,Cell]=field(default_factory=dict); notices:str=DEFAULT_NOTICES
    @classmethod
    def new(cls,m):return cls(m,{k:Cell(DEFAULTS.get(k,''),False) for k in CELLS},DEFAULT_NOTICES)

def draw_text(page,font,text,rect):
    lines=[x.strip() for x in text.splitlines() if x.strip()]
    if not lines:return
    step=CLASS_SIZE*1.2; first=rect.y0+rect.height/2-((len(lines)-1)*step)/2+CLASS_SIZE*.35
    for i,line in enumerate(lines):
        size=CLASS_SIZE; w=font.text_length(line,fontsize=size); maxw=rect.width-10
        if w>maxw and w>0:size=max(9.0,size*maxw/w); w=font.text_length(line,fontsize=size)
        page.insert_text(fitz.Point(rect.x0+(rect.width-w)/2,first+i*step),line,fontsize=size,fontname='MapleBold',color=TEXT_COLOR,overlay=True)

def render_a3(p,out):
    doc=fitz.open(str(asset('timetable_bg.pdf'))); page=doc[0]; ff=maple_font(); page.insert_font(fontname='MapleBold',fontfile=ff); font=fitz.Font(fontfile=ff)
    centered(page,font,'MapleBold',f'{MONTHS[p.month-1]} Time Table',PAGE_W/2,TITLE_BASE,TITLE_SIZE,TITLE_COLOR)
    centered(page,font,'MapleBold',f'{p.month}월 수업 스케쥴',PAGE_W/2,SUB_BASE,SUB_SIZE,SUB_COLOR)
    for key,rect in CELLS.items():
        c=p.cells.get(key,Cell()); draw_text(page,font,c.text,rect)
        if c.closed:page.insert_image(rect,filename=str(asset('closed.png')),keep_proportion=False,overlay=True)
    for i,line in enumerate(p.notices.splitlines()[:3]):
        if line.strip():page.insert_text(fitz.Point(NOTICE_X,NOTICE_BASES[i]),line.strip(),fontsize=NOTICE_SIZE,fontname='MapleBold',color=TEXT_COLOR,overlay=True)
    doc.save(str(out),garbage=4,deflate=True); doc.close()
def render_pdf(p,out,size):
    out=Path(out)
    if size=='A3':return render_a3(p,out)
    tmp=out.with_suffix('.a3tmp.pdf');render_a3(p,tmp);src=fitz.open(tmp);d=fitz.open();pg=d.new_page(width=A4_W,height=A4_H);pg.show_pdf_page(pg.rect,src,0,keep_proportion=True);d.save(out,garbage=4,deflate=True);d.close();src.close();tmp.unlink(missing_ok=True)

class TimetableWindow(tk.Toplevel):
    def __init__(self,parent):
        super().__init__(parent);self.title('시간표 제작');self.geometry('1380x900');self.minsize(1100,720);self.p=Project.new(datetime.now().month);self.m=tk.IntVar(value=self.p.month);self.size=tk.StringVar(value='A3');self.img=None;self.pw=self.ph=self.x0=self.y0=0;self.after_id=None;self.build();self.after(150,self.refresh)
    def build(self):
        pan=ttk.Panedwindow(self,orient=tk.HORIZONTAL);pan.pack(fill=tk.BOTH,expand=True,padx=8,pady=8);left=ttk.Frame(pan,padding=10);right=ttk.Frame(pan,padding=4);pan.add(left,weight=0);pan.add(right,weight=1)
        b=ttk.LabelFrame(left,text='시간표 월',padding=8);b.pack(fill=tk.X,pady=(0,8));ttk.Label(b,text='월').pack(side=tk.LEFT);sp=ttk.Spinbox(b,from_=1,to=12,textvariable=self.m,width=6,command=self.changed);sp.pack(side=tk.LEFT,padx=6);sp.bind('<FocusOut>',lambda e:self.changed());ttk.Label(b,text='제목은 월에 맞춰 자동 변경').pack(side=tk.LEFT,padx=8)
        b=ttk.LabelFrame(left,text='수업명 / 마감 편집',padding=8);b.pack(fill=tk.X,pady=(0,8));ttk.Label(b,text='오른쪽 노란 수업 칸을 클릭해 수업명과 CLOSED를 편집하세요.',wraplength=350).pack(anchor='w');f=ttk.Frame(b);f.pack(fill=tk.X,pady=(8,0));ttk.Button(f,text='모든 CLOSED 해제',command=self.clear_closed).pack(side=tk.LEFT);ttk.Button(f,text='기본 수업명 복원',command=self.reset).pack(side=tk.LEFT,padx=6)
        b=ttk.LabelFrame(left,text='하단 안내사항 (최대 3줄)',padding=8);b.pack(fill=tk.X,pady=(0,8));self.notice=tk.Text(b,height=6,width=46,wrap='none');self.notice.pack(fill=tk.X);self.notice.insert('1.0',self.p.notices);self.notice.bind('<KeyRelease>',lambda e:self.changed())
        b=ttk.LabelFrame(left,text='PDF 저장 / 출력',padding=8);b.pack(fill=tk.X,pady=(0,8));ttk.Radiobutton(b,text='A3',value='A3',variable=self.size).pack(side=tk.LEFT);ttk.Radiobutton(b,text='A4',value='A4',variable=self.size).pack(side=tk.LEFT,padx=8);ttk.Button(b,text='시간표 PDF 저장',command=self.export).pack(fill=tk.X,pady=(8,0));self.status=ttk.Label(left,wraplength=350,justify=tk.LEFT);self.status.pack(fill=tk.X,pady=(10,0))
        ttk.Label(right,text='미리보기 / 노란 칸 클릭 편집',font=('TkDefaultFont',11,'bold')).pack(anchor='w',padx=4,pady=(0,4));self.canvas=tk.Canvas(right,bg='#555555',highlightthickness=0);self.canvas.pack(fill=tk.BOTH,expand=True);self.canvas.bind('<Button-1>',self.click);self.canvas.bind('<Configure>',lambda e:self.schedule())
    def sync(self):self.p.month=max(1,min(12,int(self.m.get())));self.p.notices=self.notice.get('1.0','end-1c')
    def changed(self):
        try:self.sync();self.schedule()
        except:pass
    def schedule(self):
        if self.after_id:self.after_cancel(self.after_id)
        self.after_id=self.after(120,self.refresh)
    def clear_closed(self):
        for c in self.p.cells.values():c.closed=False
        self.schedule()
    def reset(self):
        if messagebox.askyesno('확인','수업명을 기본 시간표 내용으로 되돌릴까요?',parent=self):
            for k in CELLS:self.p.cells[k].text=DEFAULTS.get(k,'')
            self.schedule()
    def refresh(self):
        self.after_id=None
        if self.canvas.winfo_width()<100:return
        try:
            self.sync();fd,tmp=tempfile.mkstemp(suffix='.pdf');os.close(fd)
            try:
                render_pdf(self.p,tmp,'A3');d=fitz.open(tmp);aw=max(100,self.canvas.winfo_width()-20);ah=max(100,self.canvas.winfo_height()-20);sc=min(aw/PAGE_W,ah/PAGE_H);pix=d[0].get_pixmap(matrix=fitz.Matrix(sc,sc),alpha=False);data=base64.b64encode(pix.tobytes('png')).decode();d.close()
            finally:
                if os.path.exists(tmp):os.unlink(tmp)
            self.img=tk.PhotoImage(data=data);self.pw,self.ph=self.img.width(),self.img.height();self.x0=(self.canvas.winfo_width()-self.pw)//2;self.y0=(self.canvas.winfo_height()-self.ph)//2;self.canvas.delete('all');self.canvas.create_image(self.x0,self.y0,anchor='nw',image=self.img);n=len([x for x in self.p.notices.splitlines() if x.strip()]);self.status.config(text='시간표 편집 준비 완료' if n<=3 else '안내사항은 PDF에 앞 3줄만 표시됩니다.')
        except Exception as e:self.canvas.delete('all');self.canvas.create_text(20,20,anchor='nw',fill='white',text=f'미리보기 오류:\n{e}');self.status.config(text=str(e))
    def click(self,e):
        if not self.pw or not(self.x0<=e.x<=self.x0+self.pw and self.y0<=e.y<=self.y0+self.ph):return
        pt=fitz.Point((e.x-self.x0)*PAGE_W/self.pw,(e.y-self.y0)*PAGE_H/self.ph)
        for k,r in CELLS.items():
            if r.contains(pt):self.edit(k);return
    def edit(self,key):
        c=self.p.cells[key];dlg=tk.Toplevel(self);dlg.title(f'{key} 수업 편집');dlg.transient(self);dlg.grab_set();frm=ttk.Frame(dlg,padding=14);frm.pack();ttk.Label(frm,text='수업명 (여러 줄 입력 가능)').pack(anchor='w');txt=tk.Text(frm,height=4,width=34);txt.pack(fill=tk.X,pady=(5,10));txt.insert('1.0',c.text);closed=tk.BooleanVar(value=c.closed);ttk.Checkbutton(frm,text='마감 (CLOSED 표시)',variable=closed).pack(anchor='w')
        def apply():c.text=txt.get('1.0','end-1c').strip();c.closed=closed.get();dlg.destroy();self.schedule()
        btn=ttk.Frame(frm);btn.pack(fill=tk.X,pady=(12,0));ttk.Button(btn,text='적용',command=apply).pack(side=tk.RIGHT);ttk.Button(btn,text='취소',command=dlg.destroy).pack(side=tk.RIGHT,padx=6);ttk.Button(btn,text='수업명 지우기',command=lambda:txt.delete('1.0',tk.END)).pack(side=tk.LEFT);txt.focus_set();dlg.bind('<Control-Return>',lambda e:apply())
    def export(self):
        self.sync();lines=[x for x in self.p.notices.splitlines() if x.strip()]
        if len(lines)>3 and not messagebox.askyesno('안내사항 확인','안내사항이 3줄을 초과합니다. 앞 3줄만 저장됩니다. 계속할까요?',parent=self):return
        p=filedialog.asksaveasfilename(parent=self,defaultextension='.pdf',initialfile=f'{self.p.month:02d}월_시간표_{self.size.get()}.pdf',filetypes=[('PDF','*.pdf')])
        if p:
            try:render_pdf(self.p,p,self.size.get());messagebox.showinfo('완료',f'시간표 PDF를 저장했습니다.\n{p}',parent=self)
            except Exception as e:messagebox.showerror('오류',str(e),parent=self)
