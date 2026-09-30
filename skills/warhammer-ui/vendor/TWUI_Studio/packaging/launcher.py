"""Windowed executable entry point with persistent error reporting."""
import logging
import os
from pathlib import Path
import sys


def main():
    log_dir = Path(os.getenv('APPDATA', str(Path.home()))) / 'TWUIStudio' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    from logging.handlers import RotatingFileHandler
    handler = RotatingFileHandler(log_dir / 'TWUI_Studio.log', maxBytes=1024*1024, backupCount=2, encoding='utf-8')
    logging.basicConfig(handlers=[handler], level=logging.ERROR,
                        format='%(asctime)s %(levelname)s %(message)s')
    smoke = '--smoke-test' in sys.argv
    def report(kind, value, tb):
        logging.error('TWUI Studio 0.22.2 error', exc_info=(kind, value, tb))
        if not smoke:
            from tkinter import messagebox
            messagebox.showerror('TWUI Studio', f'{value}\n\nLog: {log_dir / "TWUI_Studio.log"}')
    sys.excepthook = report
    try:
        from app import Studio, BASE
        app = Studio()
        app.report_callback_exception = report
        if smoke:
            import json
            for name in ('cco_catalog', 'component_options', 'layout_options', 'state_catalog', 'user_property_catalog', 'en'):
                json.loads((BASE / (name + '.json')).read_text(encoding='utf-8'))
            app.update_idletasks()
            app.destroy()
        else:
            app.mainloop()
    except Exception:
        report(*sys.exc_info())
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
