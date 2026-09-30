from i18n import tr, trf
"""Versioned project snapshots and transactional, path-preserving exports."""
import json, os, tempfile, zipfile, re, math
from pathlib import Path, PurePosixPath
from model import Document

def atomic_write(path, data):
    path=Path(path)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def validate_project(data):
    if isinstance(data,dict) and data.get('format')=='TWUIStudio' and data.get('version')==2:
        docs=data.get('documents')
        if not isinstance(docs,list) or not docs:raise ValueError(tr('프로젝트 문서가 없습니다.'))
        for doc in docs:
            if not isinstance(doc,dict) or doc.get('version')!=1:raise ValueError(tr('문서 형식 오류'))
            validate_project(doc)
        active=data.get('active',0)
        if type(active) is not int or not 0<=active<len(docs):raise ValueError(tr('활성 문서 오류'))
        return data
    if not isinstance(data,dict) or data.get('format')!='TWUIStudio' or data.get('version')!=1:
        raise ValueError(tr('지원하지 않는 프로젝트 형식/버전입니다.'))
    for key in ('xml','original_xml'):
        if not isinstance(data.get(key),str):raise ValueError(tr('XML 원문이 없습니다.'))
        Document(data[key])
    if not isinstance(data.get('source_name',''),str) or not isinstance(data.get('bom',False),bool):raise ValueError(tr('파일 정보 오류'))
    if 'checkpoint_xml' in data:
        if not isinstance(data['checkpoint_xml'],str):raise ValueError(tr('탭 저장 상태 오류'))
        Document(data['checkpoint_xml'])
    view=data.setdefault('view',{})
    if not isinstance(view,dict):raise ValueError(tr('보기 설정 오류'))
    if not isinstance(view.get('query',''),str):raise ValueError(tr('검색 설정 오류'))
    if not isinstance(view.get('expanded',[]),list) or not all(isinstance(g,str) for g in view.get('expanded',[])):raise ValueError(tr('목록 설정 오류'))
    scroll=view.get('scroll',[])
    if not isinstance(scroll,list) or len(scroll)>2 or any(not isinstance(p,list) or len(p)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in p) for p in scroll):raise ValueError(tr('스크롤 설정 오류'))
    z=view.get('zoom',1)
    if isinstance(z,bool) or not isinstance(z,(int,float)) or not math.isfinite(z) or not .02<=z<=8:raise ValueError(tr('배율 설정 오류'))
    for key in ('selected','focus'):
        if view.get(key) is not None and not isinstance(view[key],str) and not (key=='focus' and isinstance(view[key],list) and all(isinstance(g,str) for g in view[key])):raise ValueError(tr('선택 설정 오류'))
    if not isinstance(view.get('hidden',[]),list) or not all(isinstance(v,str) for v in view.get('hidden',[])):raise ValueError(tr('숨김 설정 오류'))
    if not isinstance(view.get('root_lock',True),bool) or not isinstance(view.get('locks',[]),list) or not all(isinstance(v,str) for v in view.get('locks',[])):raise ValueError(tr('잠금 설정 오류'))
    for key in ('preview','loc'):
        value=data.get(key,{})
        if not isinstance(value,dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in value.items()):raise ValueError(tr('텍스트 설정 오류'))
    if not isinstance(data.get('mod_resource_root',''),str):raise ValueError(tr('리소스 경로 오류'))
    if not isinstance(data.get('resource_root',''),str):raise ValueError(tr('리소스 경로 오류'))
    return data

def save_project(path,data):
    validate_project(data)
    atomic_write(path,json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False).encode('utf-8'))

def load_project(path):return validate_project(json.loads(Path(path).read_text('utf-8-sig')))

def safe_ui_path(path):
    path=path.replace('\\','/')
    parts=path.split('/')
    if not path.startswith('ui/') or any(p in ('','..','.') for p in parts) or any(':' in p for p in parts):
        raise ValueError(tr('ui/로 시작하는 상대 경로를 사용하세요: ')+path)
    return str(PurePosixPath(path))

def image_paths(doc):
    paths={n.get('imagepath') for n in doc.nodes if n.get('imagepath')}
    # Explicit image references in XML strings, including tooltips.
    for n in doc.nodes:
        for value in n.attrs.values():paths.update(re.findall(r'\[\[img:(ui/[^\]]+)\]\]',value))
    return sorted(paths)

def export_zip(path,doc,resources,xml_path,bom=False):
    xml_path=safe_ui_path(xml_path)
    if not xml_path.lower().endswith('.xml'):raise ValueError(tr('XML 경로는 .xml로 끝나야 합니다.'))
    found=[];missing=[];invalid=[]
    for ref in image_paths(doc):
        try:normalized=safe_ui_path(ref)
        except ValueError:invalid.append(ref);continue
        asset=resources.resolve(ref)
        if asset:found.append((normalized,asset))
        else:missing.append(ref)
    if missing or invalid:return {'missing':missing,'invalid':invalid,'written':False}
    if any(ref.casefold()==xml_path.casefold() for ref,_ in found):raise ValueError(tr('XML과 이미지 출력 경로가 충돌합니다.'))
    fd,tmp=tempfile.mkstemp(prefix='.twui-export-',dir=Path(path).parent);os.close(fd)
    try:
        with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr(xml_path,(b'\xef\xbb\xbf' if bom else b'')+doc.source.encode('utf-8'))
            seen=set()
            for ref,asset in found:
                if ref.casefold() not in seen:z.write(asset,ref);seen.add(ref.casefold())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return {'missing':[],'invalid':[],'written':True,'images':len(seen)}
