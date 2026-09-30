# TWUI Studio 0.22.2 — Total War: WARHAMMER III TWUI XML 편집기

TWUI Studio는 Total War: WARHAMMER III 모딩을 위한 비공식 시각적 TWUI XML 편집기입니다. XML 구성요소 트리, 근사 미리보기, 속성·상태·레이아웃 편집, 원본 비교, 프로젝트 저장 및 XML+이미지 내보내기를 제공합니다.

> **프로젝트 상태: 유지관리 모드**  
> 프로그램과 소스는 현 상태로 제공됩니다. 버그 보고와 개선 제안은 환영하지만 업데이트나 답변은 보장되지 않습니다.

## 가장 먼저 해야 할 설정

TWUI Studio는 게임의 `.pack` 파일을 직접 읽지 않습니다.

1. **RPFM 또는 AssetEditor**를 사용해 게임의 `ui` 폴더 전체를 Extract(추출)합니다.
2. TWUI Studio에서 **설정 → 원본 UI 리소스 → 경로 설정**을 엽니다.
3. 추출 결과 중 `skins`, `campaign ui`, `battle ui`, `templates` 등이 들어 있는 **최상위 `ui` 폴더 자체**를 지정합니다.

예: `D:\ModData\ui`

게임 설치 폴더만 지정해서는 `.pack` 내부 이미지와 XML을 읽을 수 없습니다. `sprite_anims`와 `units`도 필요하다면 각각 추출한 `ui\sprite_anims`, `ui\units` 위치에 배치하세요. 전체 게임 리소스는 이 배포물이나 GitHub 저장소에 포함되지 않습니다.

## 소스 실행

1. Python 3.10 이상을 설치합니다. Windows에서는 Tcl/Tk와 Python Launcher를 포함하세요.
2. ZIP을 쓰기 가능한 폴더에 모두 풉니다.
3. `START_WINDOWS.bat`을 실행합니다.

첫 실행은 가상 환경을 만들고 Pillow를 설치하므로 인터넷 연결이 필요합니다. 직접 실행하려면 다음 명령을 사용하세요.

```text
python -m pip install -r requirements.txt
python app.py
```

## Windows 실행 파일 빌드

64비트 Python 3.12가 설치된 Windows 10/11에서 `BUILD_WINDOWS.bat`을 실행합니다. 성공하면 `exe_version_package/TWUI_Studio_0.22.2_Windows_x64.zip`이 생성됩니다. 자세한 내용은 `BUILD_README_KO.md`를 참고하세요.

## 기본 사용 흐름

1. 추출한 원본 `ui` 폴더를 설정합니다.
2. XML을 가져오거나 포함된 예제를 엽니다.
3. 트리 또는 캔버스에서 구성요소를 선택하고 속성창에서 편집합니다.
4. `Ctrl+Z` / `Ctrl+Shift+Z`로 실행 취소·다시 실행합니다.
5. 프로젝트를 저장하거나 XML+이미지를 내보냅니다.
6. 내보낸 파일을 RPFM으로 가져와 게임 안에서 최종 동작을 확인합니다.

미리보기는 게임 엔진의 완전한 재현이 아닙니다. Lua, CCO 실행 결과, 글꼴 기반 자동 크기, 모든 셰이더·애니메이션·클리핑 동작은 게임에서 확인해야 합니다.

## 주요 기능

- 여러 TWUI XML 문서 탭과 구성요소 트리
- 원본 비교가 가능한 확대·이동식 시각 미리보기
- 컴포넌트 ID, 위치, 크기, 도킹, 콜백, CCO, 이미지, States, Layout 편집
- 프로젝트 저장·복원과 XML 원문 보존 중심 편집
- LOC TSV 및 동적 텍스트 미리보기
- XML 코드 보기·검색·복사
- XML과 참조 이미지를 원래 `ui/` 경로로 묶어 내보내기
- 한국어·영어 UI

세부 변경 이력과 버전별 검증 내용은 [CHANGELOG.md](CHANGELOG.md)를 참고하세요.

## 예제와 게임 리소스

`examples/`에는 프로그램 동작을 보여주기 위한 작은 XML, LOC, 아이콘 예제가 포함됩니다. 전체 게임 UI 자료는 포함하지 않습니다. 게임 원본 XML·이미지·상표의 권리는 Creative Assembly, SEGA, Games Workshop 등 각 권리자에게 있습니다.

## 이용 조건

소스 열람, 수정, 비영리 목적의 파생 버전 제작·재배포는 허용됩니다. TWUI Studio 또는 그 파생물을 판매하거나 유료 서비스·광고 수익 등 영리 목적으로 이용하는 것은 금지됩니다. 이는 OSI 승인 오픈 소스 라이선스가 아닌 **비영리 소스 공개 라이선스**입니다. 정확한 조건은 [LICENSE.txt](LICENSE.txt)를 확인하세요.

공동 제작: Steam Workshop 모드 크리에이터 **Backmechuisa & gpt-6 Astra**

