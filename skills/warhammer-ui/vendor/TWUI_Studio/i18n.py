"""UI translations only. XML names, values, GUIDs and paths are never translated."""
import json,os
from pathlib import Path

def saved_language(path=None):
 path=Path(path) if path is not None else Path(os.getenv('APPDATA',str(Path.home())))/'TWUIStudio'/'settings.json'
 try:value=json.loads(path.read_text(encoding='utf-8')).get('language','ko')
 except (OSError,ValueError,AttributeError):return 'ko'
 return value if value in ('ko','en') else 'ko'

LANGUAGE=os.getenv('TWUI_STUDIO_LANGUAGE') or saved_language()
if LANGUAGE not in ('ko','en'):LANGUAGE='ko'
try:EN=json.loads(Path(__file__).with_name('en.json').read_text(encoding='utf-8'))
except (OSError,ValueError):EN={}

def tr(text):return EN.get(text,text) if LANGUAGE=='en' else text

def trf(template,*args):return tr(template).format(*args)
