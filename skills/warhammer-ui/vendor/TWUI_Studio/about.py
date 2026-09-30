"""Credits and distribution notices, shared by the app and build output."""
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import i18n

VERSION = '0.22.2'
CREATORS = 'Backmechuisa & gpt-6 Astra'
KO = '''TWUI Studio 0.22.2

공동 제작
스팀 워크숍 모드 크리에이터 Backmechuisa & gpt-6 Astra
Backmechuisa와 AI 협업 도구 gpt-6 Astra가 함께 개발한 팬 제작 도구입니다.

비영리 소스 공개 이용 조건
1. 개인적·교육적·연구적·커뮤니티 모딩 등 비영리 목적으로 무료로 사용할 수 있습니다.
2. 소스 열람·수정과 비영리 파생 버전 제작·재배포를 허용합니다. 수정본은 변경 내용을 표시하고 소스, 제작자 표시, LICENSE.txt 및 제3자 고지를 유지해야 하며 동일한 비영리 조건을 적용해야 합니다.
3. Backmechuisa의 별도 서면 허가 없이 원본이나 파생물을 판매하거나 유료 서비스·광고 수익 등 직접·간접적인 영리 목적으로 이용할 수 없습니다. 이 제한은 모든 후속 파생 버전에 계속 적용됩니다. 제작자 표시의 삭제·변경 및 제작자 사칭을 금지합니다.
4. 악성 코드 삽입, 불법적인 변조 또는 이 프로그램을 이용한 불법 행위를 금지합니다.
5. 이 제한은 TWUI Studio 자체에 관한 것입니다. 정상 기능을 이용한 UI XML·모드 제작 및 편집은 허용되며, 게임과 사용 자료의 별도 이용 조건을 따라야 합니다.
6. 프로그램은 현 상태로 제공됩니다. 법이 허용하는 범위에서 특정 목적 적합성·무오류 작동을 보증하지 않으며, 이용에 따른 손해에 대한 책임을 제한합니다. 법률상 제한할 수 없는 권리는 제한하지 않습니다.

게임 및 제3자 권리
Total War: WARHAMMER III의 원본 XML, 이미지 및 기타 게임 리소스의 권리는 Creative Assembly 및 SEGA, Games Workshop 등 해당 권리자에게 귀속됩니다. 각 상표는 해당 소유자의 자산입니다. 이 프로그램은 게임 리소스의 소유권이나 별도의 재배포 권한을 부여하지 않습니다.
이 도구는 비공식 팬 제작 도구로, Creative Assembly, SEGA, Games Workshop 또는 OpenAI의 공식 제품이나 공식 후원·승인 제품이 아닙니다.
Python, Tcl/Tk, Pillow, PyInstaller 등 제3자 소프트웨어에는 각각의 라이선스가 적용됩니다. 위 제한은 해당 라이선스에서 부여한 권리를 변경하지 않습니다. 배포본의 licenses 폴더와 THIRD_PARTY_NOTICES.txt를 참조하세요.

허가 문의: 스팀 워크숍 모드 크리에이터 Backmechuisa
'''
EN = '''TWUI Studio 0.22.2

Co-created by
Steam Workshop mod creator Backmechuisa & gpt-6 Astra
A fan-made tool developed collaboratively by Backmechuisa and the AI development tool gpt-6 Astra.

Non-commercial source-available terms
1. Free for personal, educational, research, community modding, and other non-commercial use.
2. Source inspection and modification, and creation and distribution of non-commercial derivative versions, are permitted. Modified versions must identify changes, provide source, retain creator credits, LICENSE.txt, and third-party notices, and remain under the same non-commercial terms.
3. Without separate written permission from Backmechuisa, neither the original nor a derivative may be sold or used directly or indirectly for paid services, advertising revenue, or another commercial purpose. This restriction continues to apply to every downstream derivative. Removing or changing creator credits or falsely claiming authorship is prohibited.
4. Inserting malicious code, unlawful tampering and unlawful use are prohibited.
5. These restrictions concern TWUI Studio itself. Creating and editing UI XML and mods through its normal functions is permitted, subject to the separate terms governing the game and materials used.
6. Provided as is, without warranties of fitness for a particular purpose or error-free operation, to the extent permitted by law. Liability for damages arising from use is limited to the extent permitted by law. Non-excludable statutory rights remain unaffected.

Game and third-party rights
Rights in the original Total War: WARHAMMER III XML, images and other game resources belong to Creative Assembly and the respective rights holders, including SEGA and Games Workshop. Trademarks belong to their respective owners. This tool grants no ownership or separate redistribution rights in game resources.
This is an unofficial fan-made tool, not an official product of, or officially sponsored or endorsed by, Creative Assembly, SEGA, Games Workshop or OpenAI.
Python, Tcl/Tk, Pillow, PyInstaller and other third-party software remain subject to their own licenses. The restrictions above do not alter rights granted by those licenses. See the licenses folder and THIRD_PARTY_NOTICES.txt in the distribution.

Permission requests: Steam Workshop mod creator Backmechuisa
'''

def show_about(owner):
    dialog=tk.Toplevel(owner);dialog.title(i18n.tr('프로그램 정보 / 이용 조건'));dialog.transient(owner)
    dialog.geometry('720x580');dialog.minsize(480,340)
    ttk.Label(dialog,text=f'TWUI Studio {VERSION}',font=('',16,'bold'),padding=12).pack(anchor='w')
    ttk.Button(dialog,text=i18n.tr('닫기'),command=dialog.destroy).pack(side='bottom',anchor='e',padx=12,pady=10)
    area=ttk.Frame(dialog,padding=12);area.pack(fill='both',expand=True)
    text=tk.Text(area,wrap='word',font=('',10),padx=8,pady=8)
    bar=ttk.Scrollbar(area,command=text.yview);bar.pack(side='right',fill='y');text.pack(fill='both',expand=True)
    text.configure(yscrollcommand=bar.set);text.insert('1.0',EN if i18n.LANGUAGE=='en' else KO);text.configure(state='disabled')
    dialog.bind('<Escape>',lambda e:dialog.destroy())
