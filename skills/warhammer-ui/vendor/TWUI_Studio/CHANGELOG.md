# TWUI Studio 통합 업데이트 노트

앞으로 변경 이력은 이 파일에 버전별로 누적합니다. 개별 RELEASE 파일은 배포하지 않습니다.

## 공개 배포 문서 정리

- README의 현재 버전을 0.22.2로 통일하고, 이전 버전별 상세 내역은 이 CHANGELOG로 통합했습니다.
- RPFM 또는 AssetEditor로 게임의 `ui` 폴더 전체를 추출한 뒤 최상위 `ui` 폴더를 경로로 지정해야 한다는 필수 설정을 README 첫 부분에 명시했습니다.
- 소스 수정과 비영리 파생 버전 배포는 허용하되 원본과 모든 파생물의 영리 이용을 금지하는 비영리 소스 공개 라이선스로 통일했습니다.
- GitHub 공개 묶음에서는 개발 내부 보고서와 전체 추출 게임 리소스를 제외하도록 정리했습니다.

## 0.22.2

- 일반 정의(states만 존재, part_of_template=true 아님)는 docking + dock_offset, 템플릿 인스턴스(state_uniqueguids만 존재, part_of_template=true)는 dock_point + offset으로 미리보기 위치를 계산합니다.
- Center Right는 자식 오른쪽 모서리와 부모 오른쪽 모서리를 맞추고 세로 중앙에 정렬합니다. dock_point는 dock_offset 없이도 작동하며 offset을 더합니다.
- 속성 후보와 직접 추가에서 확인된 형식에 맞지 않는 도킹 속성을 제한합니다. 템플릿 인스턴스에는 docking/dock_offset/component_anchor_point를 추가하지 않으며, 일반 정의에는 dock_point를 추가하지 않습니다.
- 기존 파일에 이미 있는 비호환 속성은 자동 삭제하지 않습니다. 속성 창에 보존하여 표시하고, 값 수정은 막되 명시적 삭제와 실행 취소는 지원합니다.
- 상태 형식이 혼합되거나 불명확한 항목에는 위 제한을 강제하지 않습니다. 미리보기에서 템플릿 파일을 새로 읽지 않습니다.
- 잘못 추가했던 dock_position 후보/해석을 제거했습니다. 기존 XML의 해당 속성은 자동 삭제하지 않습니다. 아래 0.22.1의 dock_position 기능 설명은 철회하며 이 정정이 우선합니다.
- 화면 이동·크기 변경 및 붙여넣기 위치 수정도 같은 도킹 형식 판정을 사용합니다.
- 기존 목록 간격, XML 링크, 문서별 편집 기능을 유지합니다.
- 검증: 자동 테스트 256개 통과(가상 화면의 Tk GUI 검사 포함). Windows EXE 실제 빌드 및 게임 실행 검증은 하지 않았습니다.
- 전체 소스와 BUILD_WINDOWS.bat 포함. Windows x64에서 빌드 시 exe_version_package/TWUI_Studio_0.22.2_Windows_x64.zip을 생성합니다.

### 도킹 형식 조사 근거와 한계

- 확인 가능한 DLC XML 70개와 hud_battle, units_panel, hud_campaign 3개: 총 73개 파일, 컴포넌트 8,258개. 바이트가 동일한 파일은 중복 제외하며, 다른 파일에 반복되는 정의는 각각 집계했습니다.
- states만 있는 일반 정의 5,706개: docking 3,460개, dock_offset 1,982개, dock_point 0개, part_of_template=true 0개.
- state_uniqueguids만 있는 정의 2,552개: 모두 part_of_template=true. dock_point 1,553개, docking/dock_offset 0개.
- 나머지는 해당 도킹 속성이 생략된 항목입니다. 이 통계만으로 생략된 항목의 게임 기본값이나 상속 동작을 확정하지 않습니다.
- 같은 parchment_slider_vertical 템플릿 GUID를 사용하는 원본 vslider 사례에서 dock_point="Center Right", offset="-5.00,0.00"을 확인했습니다(dlc24_formless_horror.twui.xml, 10192줄).
- 결론: 두 속성 계열이 템플릿 인스턴스/일반 정의의 직렬화 형식에 따라 구분된다는 가설을 강하게 뒷받침합니다. state_uniqueguids 자체가 처리 방식을 결정한다는 인과관계는 확정할 수 없습니다. 게임 엔진 실행 검증은 하지 않았습니다.
- 예전 campaign ui.zip은 현재 로컬 사본이 유효한 ZIP이 아니어서 제외했습니다. 전체 templates 원본도 이번 조사에 포함하지 못했습니다.


아래는 과거 배포 당시 기록입니다. 위 정정 사항이 과거 설명보다 우선합니다.

---

# TWUI Studio 0.22.1

## 목록 간격
- List에서 itemsperrow가 2 이상이면 각 아이템의 실제 컴포넌트 폭 + 부모 LayoutEngine.spacing.x로 다음 아이템을 배치합니다.
- 다음 행은 해당 행의 최대 아이템 높이 + spacing.y로 배치합니다. 음수 spacing도 그대로 적용합니다.
- 이전 버전은 columnwidths의 단일 값 202를 모든 아이템에 반복 적용하여 폭 100 + spacing 30인 아이템 사이의 빈 간격이 132가 됐습니다. 여러 아이템을 배치하는 행에서는 이 고정 열 슬롯을 반복 적용하지 않습니다.
- columnwidths XML 값은 보존합니다. 단일 열 List와 HorizontalList의 기존 열 너비 처리는 유지합니다.
- 실제 사격 학교 XML에 아이템 5개를 구성하여 상대 위치 (0,0), (130,0), (260,0), (390,0), (0,245), 가로 빈 간격 30, 세로 빈 간격 60을 확인했습니다.

## dock_position
- 컴포넌트의 dock_position을 docking과 별개로 읽습니다. center_right 같은 밑줄 표기와 대소문자를 정규화하여 해석합니다.
- center_right는 부모 오른쪽 / 세로 중앙에 정렬합니다. dock_offset과 명시된 component_anchor_point를 반영합니다.
- 두 속성이 함께 있으면 명시적인 dock_position을 미리보기에서 우선합니다. XML 속성은 서로 변환하거나 덮어쓰지 않습니다.
- 속성 창에서 dock_position 방향을 변경하면 앵커도 해당 방향으로 갱신합니다. 이 변경은 docking 값 자체를 바꾸지 않습니다.
- 도킹 위치의 이동/크기 변경과 이미지 레이어의 별도 도킹 표기도 처리합니다.
- 이번 제공 자료에서는 실제 dock_position 선언을 찾지 못하여, 요청한 속성과 값으로 구성한 재현 XML/노드로 검증했습니다. 특정 게임 파일에서의 두 속성 동시 사용 우선순위는 확인되지 않았습니다.

## 이미지 확인 및 검증
- 추가 이미지 4장은 XML 링크 기능의 의도 확인에만 사용했습니다. Creator 아래 레이아웃을 가져오는 구조가 기존 구현과 일치함을 확인했습니다. 링크 동작은 변경하지 않았습니다.
- Linux 실제 Tk 환경에서 자동 테스트 249개 통과(건너뜀 없음).
- 실제 사격 학교 XML의 간격, 여러 높이의 행 간격, 음수 간격, dock_position 정렬/오프셋/크기 변경, 기존 docking 보존 검증 포함.
- 원본 XML/PNG는 수정하지 않았습니다. NEAREST 줌 렌더링 유지.
- Windows EXE 빌드/실행 및 게임 내 검증은 수행하지 않았습니다.

## 빌드
전체 소스와 BUILD_WINDOWS.bat 포함.
Windows x64에서 실행하면 exe_version_package/TWUI_Studio_0.22.1_Windows_x64.zip을 생성합니다.


---

# TWUI Studio 0.22.0

## 도킹 위치
- docking, dock_offset, component_anchor_point로 부모/자식의 정렬점을 계산합니다.
- 앵커가 생략되면 Center는 중심끼리, Left/Right는 해당 방향의 모서리끼리 정렬합니다. Top/Center/Bottom으로 세로 정렬을 나눕니다.
- External은 부모 바깥쪽으로 정렬합니다. 파일에 명시된 앵커는 읽을 때 존중합니다.
- 속성 창에서 docking 방향을 변경하면 component_anchor_point도 그 방향에 맞춰 갱신합니다. dock_offset만 바꾸면 앵커는 유지합니다.
- docking/dock_offset 제거 시 함께 사용하던 앵커도 제거합니다. 변경은 기존 속성 창 undo로 되돌릴 수 있습니다.
- 상태가 없는 템플릿 인스턴스는 XML 자체의 dimensions를 크기 기본값으로 사용합니다. 화면 확대/이동에서 템플릿을 읽지 않습니다.

## 목록 배치와 옵션
- List의 itemsperrow를 적용하여 한 줄에 지정 개수까지 가로 배치하고 다음 줄로 넘깁니다.
- HorizontalList, spacing, margins, secondary_margins, columnwidths, reverse_order, horizontal_alignment, sizetocontent 및 min_dimensions를 배치 계산에 반영합니다.
- 편집창/원본 미리보기는 동일한 배치 계산을 사용합니다. 원본 미리보기의 XML은 계속 최초 불러온 내용입니다.
- DLC XML 70개 + hud_battle.twui.xml + units_panel.twui.xml 총 72개를 읽어 옵션 후보를 병합했습니다(읽기 실패 없음).
- 레이아웃 옵션 11종과 템플릿 ID 후보 29개를 추가했습니다. itemsperrow와 parchment_slider_vertical 포함.
- 옵션 후보 추가가 모든 게임 레이아웃/CCO 규칙의 시뮬레이션을 의미하지는 않습니다.

## 외부 레이아웃 가져오기
- ComponentCreator 콜백의 layout 경로를 감지합니다. 미가져오기 항목은 회색 이름과 사슬/가져오기 아이콘으로 나타납니다.
- 더블클릭 또는 우클릭의 레이아웃 가져오기 → 확인 시 원본 UI 리소스 경로에서 읽습니다. 경로는 대소문자와 .twui.xml/.xml 확장자를 처리합니다.
- 해당 Creator 아래로 원본 레이아웃의 root 가지를 복사하고, 그 root 이름은 레이아웃 파일 이름으로 표시합니다. GUID를 새로 배정하며 내부 참조를 함께 바꿉니다.
- 가져온 root의 사슬 아이콘은 유지합니다. 출처 정보는 XML 주석으로 기록되어 저장/다시 열기와 undo/redo에 보존됩니다.
- 취소/찾기 실패/중복 가져오기 시 XML을 변경하지 않습니다. 소스 리소스 파일도 변경하지 않습니다.
- 실제 XML에 컴포넌트를 추가하는 기능입니다. 기존 ComponentCreator 콜백을 자동 삭제하거나 비활성화하지 않으므로, 게임에 내보낼 때 동적 생성과 중복되지 않도록 콜백/정적 자식 구성을 검토해야 합니다.

## 프로젝트 제목
- TWUI Studio 0.22.0 · 프로젝트 파일 이름으로 표시합니다. 새 프로젝트는 new 프로젝트(영문 설정에서는 new project)입니다.

## 검증
- Linux 실제 Tk 환경에서 자동 테스트 245개 통과(건너뜀 없음).
- 9방향 도킹, External, 명시 앵커, 리사이즈 좌표, 행바꿈/열 너비, 외부 링크 취소/가져오기/중복 방지/undo/redo, 프로젝트 제목, 줌 중 링크 재조회 방지 확인.
- 실제 dlc25_don_main(43개 정의)에 gunnery_school(48개 정의)을 가져온 뒤 총 91개 정의를 보존하고 새 연결 오류가 없음을 확인했습니다.
- 실제 gunnery_school에서 아이템 5개를 생성해 첫 줄 x 좌표 -15/217/449/681, y 177, 다섯 번째 (-15,422) 배치를 확인했습니다.
- 실제 속성 창에서 Center 선택 시 앵커 값과 화면 필드가 0.50,0.50으로 함께 바뀌는 것을 확인했습니다.
- Windows EXE 빌드/실행과 게임 내 검증은 수행하지 않았습니다. 전체 이미지 리소스는 이번 검증에 포함하지 않았습니다.

## 빌드
전체 소스와 BUILD_WINDOWS.bat이 포함되어 있습니다.
Windows x64에서 BUILD_WINDOWS.bat 실행 시 exe_version_package/TWUI_Studio_0.22.0_Windows_x64.zip을 생성합니다.


---

# TWUI Studio 0.21.3

- Components 창의 no parent 선택을 보기·잠금 명령에서 그룹 전체 선택으로 처리합니다.
- 표시/숨김, Isolate, 선택한 구성요소만 보기, 잠그기/해제, 이 대상만 편집을 그룹 구성원에게 적용합니다.
- 자식 보이기/숨기기 및 자식 잠그기도 no parent 구성원 전체에 적용합니다.
- 다른 컴포넌트와 함께 선택하면 기존 선택 대상과 그룹 구성원을 함께 처리합니다.
- 빈 그룹에 대한 개별 명령은 아무것도 변경하지 않습니다.
- 그룹 단위 상태 변경은 기존 탭별 undo/redo에서 한 번의 작업으로 기록됩니다. XML 소스 및 실제 부모·자식 관계는 변경하지 않습니다.
- 0.21.2의 NEAREST 줌 렌더링과 기존 편집 기능을 유지합니다.

검증: Linux 실제 Tk 환경에서 자동 테스트 234개 통과(건너뜀 없음). 그룹 숨김/격리/잠금/자식 명령, 혼합 선택, 빈 그룹, undo/redo 및 XML 보존 검증 포함.
Windows EXE 빌드·실행은 수행하지 않았습니다.
압축을 풀고 Windows x64에서 BUILD_WINDOWS.bat을 실행하면 exe_version_package/TWUI_Studio_0.21.3_Windows_x64.zip이 생성됩니다.


---

# TWUI Studio 0.21.2

## 변경
- 확대·축소 시 최근접 보간(NEAREST)을 사용합니다. 확대 시 픽셀이 각져 보이는 것은 의도한 동작입니다.
- 처음 구성한 기본 이미지 캐시를 재사용합니다. 초기 XML 크기/타일/테두리/색상 구성 처리는 유지합니다.
- 조작 종료 후 고품질 갱신을 추가하지 않습니다. 모든 줌 배율에서 동일한 빠른 보간을 사용합니다.
- 보이는 영역만 그리는 처리, 이미지 공유와 제한된 캐시, 원본 파일 및 XML 좌표·크기는 유지합니다.
- 템플릿 상태 조회는 기존처럼 속성 창을 열 때 수행합니다.

## 검증
- Linux 실제 Tk 환경에서 자동 테스트 229개 통과(건너뜀 없음).
- 확대 결과의 기본 픽셀 보존, 투명도, 잘라낸 영역, 캐시 재사용과 이미지 변경 감지를 확인했습니다.
- 제공된 XML 및 장식 PNG 2개로 줌·이동 비교: 장식 표시 시 중앙값 0.21.1 36.23ms → 0.21.2 22.53ms. 최대값 98.78ms → 99.92ms. 콜백 오류 없음.
- 단일 비교 실행이며 다른 테스트와 실행 시간이 겹쳤으므로 성능 수치는 참고용입니다. 전체 이미지 리소스나 Windows에서의 최대 줌 지연 해결을 보장하지 않습니다.

## Windows 빌드
이 ZIP은 전체 소스와 BUILD_WINDOWS.bat을 포함한 빌드 준비본입니다.
Linux 환경에서는 Windows EXE를 빌드/실행하지 않았습니다.
Windows x64에서 BUILD_WINDOWS.bat 실행 시 exe_version_package/TWUI_Studio_0.21.2_Windows_x64.zip을 생성합니다.


---

# TWUI Studio 0.21.1

## 원인과 변경

기존에는 확대 시 화면 밖의 장식 이미지도 전체 확대 크기로 리사이즈하고 Tk 이미지로 만들었습니다. 작은 template_cost를 화면에 맞춰 크게 확대해도 다른 표시 상태의 구성요소 이미지는 함께 확대 처리됐습니다. page_decor_holder의 자식 이미지 여러 개가 이 비용을 크게 늘렸습니다. 템플릿 상태 조회는 줌 경로에 없습니다.

- 실제 화면 영역과 사방 128px 이동 여유 영역에 해당하는 이미지 부분만 리사이즈합니다.
- 화면 밖 이미지의 픽셀 변환은 생략하지만 전체 이미지 경계와 구성요소 좌표는 유지하여 선택·화면 맞춤·스크롤 범위를 보존합니다.
- 확대 전 목표 화면 위치를 계산하여 새 배율의 올바른 영역을 그립니다.
- 이동/스크롤/창 크기 변경으로 준비된 영역을 벗어날 때 이미지 영역을 갱신합니다. 요청은 16ms 예약으로 합치고 이동 여유 영역을 재사용합니다.
- 이미 예약된 격자 그리기는 즉시 격자를 그릴 때 취소하여 중복 호출을 줄입니다.
- LANCZOS 품질과 원본 XML을 유지합니다. 상태 조회는 기존처럼 속성 창을 열 때 수행합니다.

## 재현 측정

사용자가 제공한 dlc25_don_gunnery_school XML과 page_decor_left_tab_1.png, page_decor_right_tab_1.png를 연결했습니다. 다른 PNG는 제공되지 않아 이 측정에 포함하지 않았습니다.
Linux 가상 화면 1600×1000의 실제 Tk 창에서 template_cost를 선택한 후 2.0~7.02 배율의 10개 확대 단계에 대해 set_zoom 및 이벤트 처리 시간을 측정했습니다.

| 장식 상태 | 0.21.0 중앙값 | 0.21.1 중앙값 | 0.21.0 최대 | 0.21.1 최대 |
|---|---:|---:|---:|---:|
| 표시 | 493.97ms | 24.29ms | 2077.77ms | 53.11ms |
| 숨김 | 22.75ms | 21.41ms | 48.01ms | 94.61ms |

단일 로컬 실행 결과이며 Windows/전체 리소스 환경의 개선 폭을 보장하지 않습니다. 첨부 장식이 표시된 경우의 지연은 재현했고, 이미지 처리 범위를 줄여 해당 비용이 크게 감소했습니다. 다른 실제 PNG를 포함한 전체 리소스의 성능 측정은 아직입니다.

## 검증

자동 테스트 228개 통과(건너뜀 없음). 줌 중심/기존 편집 기능 회귀, 캐시, 화면 밖 제외, 이미지 처리 크기 제한, 상세 색상·알파 이미지에서 전체 확대 후 자른 결과와 동일 픽셀임을 검증했습니다. 실제 첨부 XML에서 이동 후 화면 영역이 다시 준비되는 것도 확인했으며 Tk 콜백 오류는 없었습니다.
Windows EXE 빌드·실행은 이 환경에서 검증하지 않았습니다.

## 빌드와 수동 확인

BUILD_WINDOWS.bat 실행 결과: exe_version_package/TWUI_Studio_0.21.1_Windows_x64.zip.
1. 기존 원본 UI 경로로 gunnery school XML을 엽니다.
2. page_decor_holder 표시 상태에서 template_cost 화면 맞춤 후 Ctrl+휠 확대/축소를 비교합니다.
3. 장식을 숨긴 상태와 upgrade_level / upgrade_effects_list 표시 상태도 비교합니다.
4. 휠 클릭 이동과 스크롤바 이동 후 새 영역의 이미지가 나타나며 선택 위치·화면 맞춤이 유지되는지 확인합니다.


---

# TWUI Studio 0.21.0

기준: 사용자가 다시 첨부한 0.20.13 전체 소스. 이후 패치 버전은 0.21.1부터 증가합니다.

## 줌 이미지 처리

- 편집 화면과 원본 화면이 같은 이미지·크기·색상으로 그리는 경우 확대된 Tk 이미지를 공유합니다. 이전에는 각 화면에서 리사이즈와 Tk 이미지 변환을 반복했습니다.
- 최근 확대 이미지를 LRU 캐시에 보관하여 같은 배율 재사용 시 중복 변환을 줄입니다. 보관 한도는 픽셀 데이터 기준 약 64 MiB이며 앱 전체 메모리 한도를 뜻하지 않습니다.
- 큰 이미지는 한 번의 두 화면 그리기 동안 공유하며, 캐시 한도를 초과하면 장기 보관하지 않습니다.
- 이미지 파일의 크기나 수정 시각이 바뀌면 기존 캐시를 재사용하지 않습니다.
- LANCZOS 리사이즈, 픽셀 결과, 기존 화면 맞춤·줌 중심·표시 동작은 유지합니다. 처음 방문하는 배율에서는 필요한 이미지 변환이 수행됩니다.

## 템플릿 / 상태 조회

0.20.13에서도 줌 경로에는 템플릿 조회가 없었습니다. 따라서 템플릿 재로딩이 사용자 환경의 지연 원인이었다고 단정하지 않습니다.
상태 조회는 기존처럼 속성 창을 열 때 수행합니다. States 페이지 클릭 때만 조회하는 방식으로 바꾸지 않았으며, 페이지 이동을 위한 추가 렌더링도 넣지 않았습니다.
템플릿 파일 읽기는 원본 UI 경로별 캐시를 사용하고 명시적인 새로고침 시 갱신합니다. 원본 템플릿은 수정하지 않습니다.

## 검증 및 범위

자동 테스트 226개 통과, 건너뜀 없음. 실제 Tk GUI 테스트 포함.
- 줌/화면 맞춤 시 템플릿 load 호출 0회.
- 속성 창 생성 시 상태 원본 조회 확인, States/Component 페이지 왕복 시 추가 resolve 없음.
- 두 화면 이미지 공유, 배율 재사용, 캐시 한도 및 파일 변경 시 갱신 확인.
- 최종 이미지 픽셀이 기존 LANCZOS 리사이즈 결과와 동일함을 확인.
- 기존 탭·편집·실행 취소 회귀 테스트 통과.

사용자의 Windows 환경과 전체 PNG 리소스를 이용한 지연 재현 및 개선 폭 측정은 수행하지 못했습니다. 줌 지연이 완전히 해소되었다고 보장하지 않습니다.
Windows EXE 빌드/실행은 이 Linux 환경에서 검증하지 않았습니다.

## 빌드 및 확인 순서

Windows x64에서 BUILD_WINDOWS.bat을 실행하면 exe_version_package/TWUI_Studio_0.21.0_Windows_x64.zip이 생성됩니다.
원본 ui 리소스 경로는 기존 설정을 유지합니다.
1. dlc25_don_gunnery_school XML을 열고 square_medium_text_button을 화면에 맞춥니다.
2. Ctrl+휠로 확대/축소를 왕복하며 이전 버전과 반응을 비교합니다.
3. 속성 창을 열어 States 정보를 확인하고 다른 속성 페이지와 왕복합니다.
4. 편집/원본 이미지와 줌 중심이 유지되는지 확인합니다.


---

# TWUI Studio 0.20.13

## 원본 UI 폴더와 템플릿

1. 원본 UI 리소스 → 경로 설정에서 추출한 최상위 ui 폴더를 지정하세요. 이미지와 템플릿 참조를 위한 필수 첫 단계로 안내합니다. 게임 설치 경로만 지정해서는 pack 내부를 읽을 수 없습니다.
2. 해당 폴더 아래 templates의 XML을 필요할 때 한 번 읽어 캐시합니다. 폴더 경로가 변경되면 캐시를 교체합니다.
3. DLC 데이터 추가/교체 후 원본 UI 리소스의 새로고침 또는 States의 템플릿 새로고침을 누르세요. 프로그램을 다시 시작해도 새로 읽습니다.
4. 템플릿을 찾지 못해도 XML 자체의 상태 목록과 상태별 텍스트를 표시합니다. 잘못된 파일이나 모호한 원본은 안내하며 임의로 연결하지 않습니다.

## 속성 → States

- 기존 states 직접 정의 편집은 유지합니다.
- state_uniqueguids 형식도 상태 이름 목록과 좌측 탐색 목록에 표시합니다.
- 템플릿 상태는 이름과 사용처 GUID를 읽기 전용으로 표시합니다.
- uniqueguid_in_template를 원본 구성요소에 연결하며, template_id는 현재 구성요소 또는 부모 계층에서 찾아 원본 선택에 사용합니다.
- 원본 템플릿 파일 이름, 원본 상태 GUID, 해당 상태 XML과 연결된 이미지 경로를 읽기 전용으로 표시합니다. 원본 값은 게임에서의 최종 적용값을 의미하지 않습니다.
- 현재 XML의 localised_texts에서 상태 이름이 같은 항목을 연결합니다. text, text_label, is_text_localised 등 실제 항목의 속성을 편집할 수 있습니다.
- 적용 시 변경한 텍스트 속성만 합쳐 다른 속성 페이지의 편집 내용을 유지합니다. 실제 XML 적용 후 문서 undo/redo를 지원합니다.
- 템플릿 상태의 추가/복제/삭제/현재 상태/기본 상태 버튼은 비활성화합니다. 원본 템플릿이나 사용처 GUID를 변경하지 않습니다.
- 템플릿을 이용한 게임 화면 전체 재현 또는 로컬 텍스트 항목이 없는 상태에 새 항목을 만드는 기능은 이번 범위에 포함하지 않습니다.

## 검증

자동 테스트 222개: 기존 테스트 및 템플릿 연결, 캐시/새로고침, 누락·손상·중복, 텍스트 병합, 기존 states 유지, 실제 Tk 속성 창 탐색·적용·undo/redo 검증 통과.
제공된 templates 131개와 검사 XML 78개에서 템플릿 구성요소 2,274개를 모두 연결했고 상태 이름도 모두 일치했습니다. 템플릿 읽기 실패는 0건입니다.
Windows GUI 및 Windows EXE 빌드/실행은 이 Linux 환경에서 검증하지 않았습니다.

## Windows 빌드

전체 소스와 BUILD_WINDOWS.bat을 제공합니다. Windows x64에서 실행하면 exe_version_package/TWUI_Studio_0.20.13_Windows_x64.zip이 생성됩니다. 게임 템플릿 원본은 이 소스 ZIP에 포함하지 않습니다.


---

# TWUI Studio 0.20.12

기준: 0.20.11 전체 소스.

- XML 탭 이동 버튼을 오른쪽 끝에 `<` `>` 순서로 모았습니다. 탭 폭 유지, 휠 스크롤, 선택 탭 자동 표시 동작은 유지합니다.
- 처음 시작하거나 모든 탭 닫기 후 생성된 기본 문서가 실제로 편집된 적 없으면 프로젝트를 열 때 저장되지 않은 프로젝트 폐기 확인을 생략합니다. 초기 화면 맞춤·선택·스크롤 변화는 편집으로 보지 않습니다.
- 파일 이름만으로 기본 문서를 판단하지 않습니다. 불러온 XML/프로젝트에는 기존 확인을 유지합니다. 실제 XML 편집 이력은 undo로 원래 내용으로 돌아가도 유지합니다. LOC나 미리보기 설정 내용이 있으면 기본 문서 예외를 적용하지 않습니다.
- 모든 탭 닫기로 초기화하면 이전 프로젝트 저장 경로도 해제합니다.
- 구성요소 우클릭 → 보기 → **선택한 구성요소만 보기 / Show selected only** 추가. 선택한 항목 자체만 표시하고 선택하지 않은 부모·자식·다른 항목을 숨깁니다. 다중 선택 지원, 원래 좌표 유지, undo/redo 지원. 전체 보이기로 해제합니다.
- 기존 Isolate(선택 대상과 자식만 보기)는 그대로 유지합니다.
- 화면 제목과 도움말의 버전 표기를 0.20.12로 수정했습니다.

검증: 자동 테스트 214개 통과, 건너뛴 테스트 없음. Linux 가상 화면의 실제 Tk 위젯에서 탭 버튼 배치, 스크롤, 문서 전환·닫기, 초기 문서 확인 생략을 검증했습니다. 편집 후 undo, 불러온 문서 구분, 정확한 선택 항목 표시와 실행 취소도 검사했습니다.

Windows GUI와 EXE 빌드/실행은 이 환경에서 검증하지 않았습니다. 전체 소스와 BUILD_WINDOWS.bat이 포함된 빌드 준비본입니다. Windows x64에서 BUILD_WINDOWS.bat을 실행하면 exe_version_package/TWUI_Studio_0.20.12_Windows_x64.zip이 생성됩니다.


---

# TWUI Studio 0.20.11

기준 소스: 0.20.10. 이번 패치는 XML 문서 탭 영역만 개선합니다.

- 탭이 많아져도 파일 이름과 닫기 버튼의 폭을 압축하지 않습니다.
- 탭 스트립이 내부에서 가로로 늘어나며, 넘칠 때만 양쪽에 얇은 `<` / `>` 이동 버튼을 표시합니다. 별도 스크롤바는 없습니다.
- 탭 위 휠: 위로 돌리면 왼쪽, 아래로 돌리면 오른쪽으로 이동합니다. 휠과 화살표는 선택 문서를 바꾸지 않습니다.
- 탭 클릭 또는 문서 열기/선택 시 해당 탭이 보이도록 이동합니다. 마지막 탭을 선택하면 오른쪽 끝에 맞춥니다.
- 스크롤 후 닫기 버튼과 우클릭 메뉴가 해당 탭을 정확히 가리킵니다.
- 기존 문서별 편집, 실행 취소/다시 실행, 변경사항 확인 및 닫기 취소 동작을 유지합니다.

## 검증

- 자동 테스트 206개 통과(기존 197개 + 새 탭 UI/통합 테스트 9개).
- Linux 가상 화면에서 실제 Tk 위젯을 사용해 폭 유지, 화살표, Windows 방식 휠 이벤트 및 Linux 휠 버튼, 클릭, 자동 표시, 닫기와 우클릭 좌표, 크기 변경, 탭 초기화를 검증했습니다.
- 실제 Studio 창에서 12개 문서의 전환, 편집 복원, undo/redo, 변경된 문서 닫기 취소/확인, 다른 탭 닫기, 프로젝트 초기화를 확인했습니다.
- Windows 운영체제 GUI 및 Windows EXE 빌드/실행은 검증하지 않았습니다. Linux에서는 Windows x64 빌드 스크립트가 명시적으로 실행을 거부합니다.

## 빌드

이 ZIP은 전체 소스와 빌드 도구 묶음이며 Windows EXE가 포함된 배포판은 아닙니다.
Windows x64에서 압축을 풀고 `BUILD_WINDOWS.bat`을 실행하세요.
성공하면 `exe_version_package/TWUI_Studio_0.20.11_Windows_x64.zip`이 생성됩니다.

수동 확인: 긴 파일 이름을 포함해 XML 10개 이상 열기 → 탭 위 휠/화살표 이동 → 문서가 바뀌지 않는지 확인 → 마지막 탭 클릭 → 이름과 닫기 버튼 확인 → 수정 후 닫기 취소 → 문서 전환 후 Ctrl+Z/Ctrl+Shift+Z 확인.


---

# TWUI Studio 0.20.10

- 속성 → 레이아웃 엔진 → 자식 순서: 레이아웃 타입이 없거나 List/HorizontalList 이외의 타입이어도 1차 자식 순서를 변경할 수 있습니다. 적용 전에는 속성 창의 초안에 반영됩니다.
- 계층 잘라내기/붙여넣기: 이동한 항목 주변의 빈 줄 누적을 방지하고, 새 부모 깊이에 맞춰 이동한 계층을 들여쓰기합니다. 전체 문서를 매번 정렬하지 않습니다.
- XML 코드 상단의 **XML 정렬 / Format XML**: 현재 탭을 탭 들여쓰기로 정렬합니다. 하이어라키 태그는 간결하게, 컴포넌트 속성은 줄별로 표시합니다. Ctrl+Z로 되돌릴 수 있으며 파일 저장은 별도입니다.
- XML 검색: ↑ 이전 / ↓ 다음 / Aa 대소문자 구분. Enter는 다음, Shift+Enter는 이전 결과로 이동하며 문서 끝에서는 순환합니다. Aa 기본값은 꺼짐입니다.

정렬 시 속성값, GUID, CCO 표현식, 엔티티 표기, 주석과 요소 순서를 유지합니다. 의미 있는 요소 텍스트 등 안전하게 정렬할 수 없는 구조는 안내 후 원본을 유지합니다.

검증: 자동 테스트 197개 통과. 예제 XML 정렬의 멱등성과 노드/속성 보존, CRLF/CCO/주석 보존, 반복 계층 이동 30회의 공백 안정성, 컴포넌트 정의 보존, 검색 방향/대소문자/순환을 검증했습니다.
Windows GUI와 EXE 실행 검증은 이 환경에서 수행하지 않았습니다.

## Windows 패키징

BUILD_WINDOWS.bat을 실행하면 exe_version_package/TWUI_Studio_0.20.10_Windows_x64.zip이 생성됩니다. 압축 해제 후 TWUI_Studio.exe를 실행합니다. 현재 제공 파일은 소스 및 빌드 도구 묶음입니다.


---

# TWUI Studio 0.20.9

## Hierarchy editing

- `no parent` group at the bottom of Components holds unused component definitions with grey triangle annotations. The group is a UI label and is never written to XML.
- Ctrl+X marks one selected component grey, without editing XML. Select a destination and press Ctrl+V to move the hierarchy branch, preserving its GUIDs and descendants. Normal Ctrl+C/Ctrl+V continues to copy.
- A definition from no parent may become a child. An unused definition may also become a parent: a new hierarchy entry for it is created at the top level as needed.
- Choose “Detach to no parent” in the context menu, or cut then paste onto the no parent group, to remove the branch from the hierarchy. All component definitions are preserved. The detached branch's hierarchy relationships are removed, so its former descendants appear individually in no parent; Undo restores the entire previous branch.
- Escape cancels pending cut. Changing tabs cancels cut; a changed document invalidates pending cut. Cut/paste moves operate within the active XML tab.
- Self/descendant moves and ambiguous GUID identities are rejected. Successful edits participate in the active tab's Undo/Redo history.

## Missing component definitions

- Hierarchy entries with no matching definition use a red question mark in Components, the XML gutter, and the diagnostic list.
- The import diagnostic dialog offers “Delete selected hierarchy entry” for the selected missing entry.
- Delete/context-menu deletion also works for missing entries despite their read-only placeholder lock. Only the hierarchy entry is removed; definitions are not deleted. If the missing entry wraps children, its children remain at that location under the previous parent.
- Ambiguous matches to existing definitions remain separate diagnostics; they are not eligible for missing-entry deletion.
- Missing identities and their source nodes are indexed at document load. Selection uses the existing model.

## Selection performance

Selecting a component now redraws only its selection overlay and updates its information. It no longer rerenders both original and edited image scenes. Full scene redraw still occurs after actual document/view changes.

## 한국어 사용 안내

1. 구성요소 하단의 `no parent`에서 미사용 정의를 확인합니다.
2. 옮길 항목을 선택하고 Ctrl+X → 부모로 삼을 항목 선택 → Ctrl+V. 계층과 GUID를 유지한 이동입니다.
3. 우클릭 → 부모 연결 해제 / no parent: 정의는 남기고 해당 가지의 계층 연결을 제거합니다. 가지의 자식들도 각각 미연결 정의가 됩니다.
4. 빨간 물음표는 정의를 찾지 못한 계층입니다. 최초 검사 창에서 해당 행 선택 → 선택한 계층만 삭제, 또는 구성요소 창에서 Delete를 사용합니다. 정상 자식은 보존합니다.
5. 잘라내기 대기 중 Esc를 누르면 취소합니다. 다른 XML 탭으로의 잘라내기 이동은 지원하지 않습니다.
6. 실제 변경은 탭별 실행 취소/다시 실행으로 되돌릴 수 있습니다. 원본 파일은 저장 전까지 덮어쓰지 않습니다.

## Verification / 검증

192 automated tests passed, including missing-entry deletion, child preservation, branch moves, no-parent grouping, cycle prevention, stale-cut rejection and selection without document parsing/full scene redraw. Windows GUI and EXE execution were not available for validation. The newly attached KIS_tower file could not be retrieved in this execution environment; its exact file was not re-tested for this release.

Windows: run BUILD_WINDOWS.bat. Output: exe_version_package/TWUI_Studio_0.20.9_Windows_x64.zip.


---

# TWUI Studio 0.20.8

0.20.7에서 id와 this를 혼동해 적용했던 경고 등급을 정정합니다.

- 하이어라키 태그와 실제 컴포넌트 태그가 같고 id 속성만 다르면 노란색입니다. 예: `<filters_holder>` / `<filters_holder id="sort_holder">`. 최초 XML 가져오기 안내에서는 제외됩니다.
- 하이어라키와 컴포넌트의 this GUID가 다르면 이름이 일치해도 빨간색입니다. 컴포넌트 this/uniqueguid 불일치 역시 빨간색으로 복원했습니다.
- 하이어라키 태그와 실제 컴포넌트 태그 불일치는 빨간색입니다. 서로 다른 태그에 동일한 id만 지정된 경우의 이름 중복 경고는 노란색입니다.
- 여러 문제가 겹치면 가장 높은 등급의 색상을 사용합니다. ID 경고가 GUID 오류를 가리지 않습니다.
- 미사용 정의의 회색 표시와 최초 안내 제외, 괄호 ID의 보존·표시를 유지합니다. state_uniqueguids 기능은 변경하지 않았습니다.
- XML 내용은 검사만으로 자동 변경하지 않습니다.

## 확인 결과

자동 테스트 178개 통과. 기존 혼합 XML 40개 모두 원문 보존 및 정의 누락 없음 확인.
Fusion Wizard의 filters_holder/id=sort_holder는 노란색. GUID 수정 기능 적용 후 남는 ID 불일치 4건은 모두 노란색이며 최초 안내 대상에서 제외됩니다.
Windows GUI/EXE 실행은 이 환경에서 확인하지 못했습니다.

## 빌드

새 폴더에 전체 압축을 풀고 BUILD_WINDOWS.bat을 실행하세요.
배포본: exe_version_package/TWUI_Studio_0.20.8_Windows_x64.zip

## English

Corrected the distinction between id and this. Matching hierarchy/component tags with a different id now produce a yellow warning, excluded from the initial import report. Hierarchy/component GUID mismatches and this/uniqueguid mismatches are red again. Unused definitions remain grey; parenthesized IDs remain supported. 178 automated tests passed. Windows GUI/EXE validation remains outstanding.


---

# TWUI Studio 0.20.7

## 경고 등급

- 빨강: 계층 참조의 정의를 확정하지 못하거나 GUID 중복, 실제 이름 불일치 등 확인이 필요한 연결 문제. 최초 XML 열기 안내에 표시됩니다.
- 노랑: 대소문자·태그 표기 차이, this/uniqueguid 불일치, 같은 이름으로 정의를 찾았지만 계층 GUID가 다른 경우. 최초 안내에서 제외하고 구성요소와 XML 줄 번호 옆에 노란 삼각형으로 표시합니다.
- 회색: 하이어라키에서 사용하지 않는 정의. 최초 안내에서 제외하고 회색 삼각형으로 표시합니다. 미사용 정의만 있다는 이유로 다른 정상 계층의 순서 변경 등 구조 편집을 막지 않습니다.

도움말 → XML 구조 검사에서는 모든 등급을 확인할 수 있습니다. 한 위치에 여러 등급이 겹치면 가장 높은 등급의 색을 사용합니다. 빨강도 게임의 실행 오류를 확정한다는 뜻은 아닙니다.

## 괄호가 있는 이름

제공된 자르의 탑 파일에는 XML 태그가 `<tx_>`이고 실제 `id`가 `tx_(` 또는 `tx_)`인 항목이 있습니다. 이 형태를 유효한 이름 표기로 인식하며 괄호를 그대로 표시·보존합니다. 같은 부모의 중복 이름 검사도 정규화된 태그 대신 실제 ID를 비교합니다.

속성 적용 시 기존 이름을 바꾸지 않으면 이름 검증으로 차단하지 않습니다. 새 이름에도 괄호를 사용할 수 있으며 ID에는 괄호를 보존하고 계층/정의의 XML 태그에서는 괄호를 제외합니다. 임의의 비표준 XML 태그 문법을 새로 허용하는 변경은 아닙니다.

state_uniqueguids 지원은 이번 변경에 포함하지 않았습니다.

## 검증

- 단위·회귀 테스트 175개 통과.
- 제공된 tower_of_zharr.twui.xml: 185개 항목 보존, 이름 경고 없음. 괄호 ID의 무변경 적용 결과가 원문과 동일함을 확인.
- 이전 혼합 모드 XML 40개: 모두 읽기 성공, 정의 누락 없음, 무편집 원문 동일. 노랑 28건/회색 12건은 최초 안내에서 제외. 빨강 31건은 9개 파일에서 계속 안내.
- Windows GUI와 EXE 실행은 이 환경에서 검증하지 못했습니다.

## 실행 및 빌드

전체 소스를 새 폴더에 풀어 사용하세요. Windows에서 BUILD_WINDOWS.bat을 실행하면 exe_version_package/TWUI_Studio_0.20.7_Windows_x64.zip이 생성됩니다.

## English

Warnings now use three levels: red for connection issues, yellow for minor notation/reference differences, and grey for definitions unused by the hierarchy. Only red issues appear in the initial import dialog; Help > XML structure check includes every level. IDs containing parentheses are preserved and displayed as written, with normalized XML tags. State GUID reference support is unchanged. 175 automated tests passed; Windows GUI/EXE validation remains outstanding.


---

# TWUI Studio 0.20.6 — XML structure diagnostics

XML을 가져올 때 구조 문제가 발견되면 안내 창을 엽니다. 도움말 → XML 구조 검사에서 다시 확인할 수 있습니다.

- GUID 중복이 있어도 계층 목록 전체를 구성합니다. 표시용 키는 원문에 저장하지 않습니다.
- 정의를 찾을 수 없는 계층도 임시 프레임으로 표시하고 자식 항목은 계속 읽습니다. 연결되지 않은 실제 정의는 목록 최상위에 표시합니다.
- 구성요소와 XML 줄 번호 옆에 빨간 느낌표를 표시합니다. 마우스를 올리면 문제 설명이 나타납니다. 검사 목록을 선택하면 관련 항목과 코드로 이동합니다.
- 이름 불일치, 같은 부모의 중복 이름, 중복 GUID/계층 참조, 누락된 정의, 연결되지 않은 정의, this/uniqueguid 불일치, 내부 GUID 중복 및 찾을 수 없는 스테이트/이미지 참조를 검사합니다. 이 검사는 게임 실행 가능 여부를 판정하는 검사가 아닙니다.
- 하이어라키 GUID로 통일: GUID와 이름으로 이미 연결된 정의를 제외하고, 이름으로 남은 정의 하나와 계층 GUID 하나가 확실히 대응할 때만 수정합니다.
- 중복 GUID 재배정: 위 수정 후, 단일 정의를 참조하는 중복 말단 계층에 대해 정의를 복제하고 새 GUID를 부여합니다. 복제한 정의 내부의 상태·이미지 선언과 알려진 GUID 연결도 함께 갱신합니다. 자식이 있는 중복 계층 및 모호한 중복 정의는 자동 수정하지 않습니다.
- 버튼으로 수정한 작업은 현재 탭의 실행 취소/다시 실행 기록에 남습니다. 디스크의 원본은 저장 전까지 변경하지 않습니다.
- 계층 연결이 불명확한 문서는 구조 복사·삭제·이동·순서 변경을 제한합니다. 정의가 없는 임시 항목은 읽기 전용입니다. 실제 정의의 일반 속성은 확인할 수 있습니다.

## 확인 결과

제공된 Fusion Wizard `doc_fw_panel.twui.xml`: 79개 정의 / 83개 계층 항목을 누락 없이 모델에 보존했습니다. GUID 불일치 1건, 중복 정의 GUID 1건, 중복 계층 참조 4건, 이름 불일치 4건을 감지했습니다. 두 GUID 수정 기능 적용 후 이름 불일치 4건만 남으며, 이름은 임의 변경하지 않습니다.

단위·회귀 테스트 168개 통과. 이 실행 환경에서는 Windows GUI 및 EXE 실행을 검증하지 못했습니다. 게임에서의 변경 결과도 별도 확인이 필요합니다.

## Windows 빌드 및 확인

1. 새 폴더에 압축을 풀고 `BUILD_WINDOWS.bat`을 실행합니다.
2. 결과: `exe_version_package/TWUI_Studio_0.20.6_Windows_x64.zip`.
3. 실행 파일: `exe_version_package/TWUI_Studio/TWUI_Studio.exe`. 배포할 때는 같은 폴더의 `_internal` 등을 포함한 전체 배포 ZIP을 사용합니다.
4. 문제 XML을 열어 검사 창과 tx_filter/tx_header 표시를 확인합니다. 검사 창을 닫기만 했을 때 수정 표시가 생기지 않아야 합니다.
5. 도움말에서 검사를 다시 열고 GUID 통일 → 중복 재배정을 적용합니다. 닫은 다음 Ctrl+Z/다시 실행으로 검사 표시와 구조가 함께 복원되는지 확인합니다.
6. 빨간 느낌표에 마우스를 올려 설명을 확인하고, 수정본은 다른 이름으로 저장하여 게임에서 확인합니다.

## English

Import diagnostics preserve all hierarchy entries without silently editing XML. Red warning icons in the component tree and XML gutter explain identity inconsistencies. Help → XML structure check reopens the report. Explicit repair buttons align uniquely matched hierarchy GUIDs and split repeated leaf references by copying their definitions with fresh scoped GUIDs. Ambiguous cases remain for manual review. Repairs are undoable per tab; source files change only when saved. Placeholder entries are read-only. Windows GUI/EXE and in-game validation remain to be performed.


---

# TWUI Studio 0.20.5

- 각도 다이얼의 0도(3시 방향)에 고정 회색 기준선을 추가했습니다.
- 레이아웃 미리보기를 자식 순서(Children Order)보다 먼저 표시합니다. 레이아웃 타입 변경 및 속성창 재구성 후에도 이 순서를 유지합니다.
- 속성창 텍스트/수치 입력에서 Enter 또는 숫자패드 Enter로 해당 입력을 확정하고 포커스를 해제합니다. XML 전체 반영은 기존처럼 적용 버튼으로 수행합니다.
- Esc로 해당 입력 세션 시작값을 복원하고 포커스를 해제합니다. 각도는 원래 라디안 정밀도를 유지하여 도/라디안/다이얼과 미리보기를 함께 복원합니다. 다이얼 드래그도 Enter/Esc를 지원합니다.
- 여러 줄 CCO 텍스트도 Enter 확정/Esc 취소를 사용합니다. 줄바꿈은 Shift+Enter입니다.
- 기존 콜백/CCO 후보 선택 입력은 전용 확정/취소 동작을 유지합니다.

검증: 자동 테스트 159개 통과. Windows GUI 및 게임 실행 검증은 이 환경에서 하지 않았습니다.

소스/빌드 준비본입니다. Windows에서 BUILD_WINDOWS.bat를 실행하면 TWUI_Studio.exe를 만들 수 있습니다.


---

# TWUI Studio 0.20.4

- RadialList의 starting_angle, arc, spacing을 도(°)와 라디안(rad) 입력으로 함께 표시하며 양방향 연동합니다.
- 라디안 표시는 소수점 8자리입니다. 180° → 3.14159265. 입력 범위는 0~360° / 0~2π입니다. 360°의 반올림 표시 6.28318531은 내부적으로 정확한 2π로 처리합니다.
- 각 항목의 원형 다이얼을 클릭하거나 드래그해서 각도를 조절할 수 있습니다. 0°는 오른쪽, 90°는 위입니다. 숫자 입력과 위/아래 증감 버튼도 지원합니다.
- 단순히 창을 열거나 표시를 반올림하는 것은 기존 XML을 변경하지 않습니다. 값을 수정하면 라디안으로 저장합니다.
- 기본 라디얼 미리보기는 1~5번 버튼을 설정한 spacing 간격으로 배치하고, 설정 반지름의 핑크 곡선을 표시합니다.
- 큰 spacing이 arc를 초과하거나 원을 돌아 버튼이 겹치면 노란 확장 곡선을 추가합니다. 이때 총 6칸을 계산하고, 6번은 숨긴 채 1~5번을 표시합니다. 확장량과 간격 압축은 설명용 근사값이며 XML의 radius/spacing을 덮어쓰지 않습니다.
- List 및 HorizontalList에도 실제 1차 자식 수(최대 5개)를 바탕으로 가상 사각형 미리보기를 추가했습니다. List는 위에서 아래, HorizontalList는 왼쪽에서 오른쪽입니다. 자식 순서를 변경하면 이름과 순서가 갱신됩니다. 사각형 크기와 간격은 방향 설명용 고정값입니다.
- 최대 200% 확대, 휠/가운데 드래그 이동 유지. 한글/영문 번역 및 빌드 버전 갱신.

검증: 자동 테스트 155개 통과. 도/라디안 양방향 연동과 반올림, 범위 제한, 방향, 확장 곡선, 실제 자식 수 제한을 검증했습니다. Windows GUI 및 게임 실행 검증은 이 환경에서 하지 않았습니다.

이 ZIP은 소스/빌드 준비본이며 EXE를 포함하지 않습니다. Windows에서 BUILD_WINDOWS.bat를 실행하면 실행파일을 만들 수 있습니다.


---

# TWUI Studio 0.20.3

- RadialList 속성의 starting_angle / arc를 0~360도 입력과 위/아래 증감 버튼으로 편집합니다. XML에는 라디안으로 저장합니다. 기존 속성값은 창을 열기만 해서는 변경하지 않습니다. 범위 밖 기존 값도 자동 덮어쓰지 않습니다.
- 0도는 3시, 시작 각도 증가는 반시계방향. clockwise=true이면 자식들은 시계방향으로 추가됩니다.
- 라디얼 미리보기는 실제 자식을 읽지 않고 번호가 있는 가상 버튼 5개(지름 48)를 사용합니다. 설정 변화는 즉시 미리보기에 반영됩니다.
- 핑크색 곡선과 시작점/arc 끝점의 안내선을 표시합니다. 휠 이동, 가운데 드래그 이동, Ctrl+휠 최대 200% 확대를 지원합니다.
- arc=0은 각도 제한 없음. arc>0은 슬롯당 arc/버튼 수로 간격을 제한하여 한 바퀴에서 시작/끝 중복을 피합니다. spacing=0이면 겹친 배치를 유지합니다.
- arc에 의해 간격이 줄어든 뒤 버튼이 겹칠 만큼 가까워지면 현 길이로 반지름을 확대합니다. 이 확대량은 게임의 정확한 내부 공식이 아닌 근사값입니다. arc/버튼 수 방식 역시 실험을 설명하는 모델이며 모든 게임 레이아웃의 완전한 재현을 보장하지 않습니다.
- 이번 배치 모델 변경은 속성창의 라디얼 미리보기에 적용됩니다. 실제 XML의 radius/spacing을 계산 결과로 덮어쓰지 않습니다.
- 한글/영문 지원. 버전 표시와 Windows 빌드 설정을 0.20.3으로 갱신했습니다.

검증: 자동 테스트 150개 통과. 이 환경에서는 Windows GUI 및 게임 실행 검증을 하지 않았습니다.

사용: 기존 방식대로 소스를 실행하거나, Windows에서 BUILD_WINDOWS.bat를 실행해 TWUI_Studio.exe를 빌드하세요. 이 ZIP은 Windows 실행파일을 포함하지 않는 소스/빌드 준비본입니다.


---

# TWUI Studio 0.20.2

라디얼 미리보기 확대 범위를 5~200%로 변경했습니다. Ctrl+휠로 확대하며 상한 이후 입력은 무시합니다. 이미지 자체도 100% 이상 확대되도록 수정했습니다. 원본 XML의 크기/레이아웃 값은 변경하지 않습니다.

참고 사례: starting_angle=3.64773798, arc=3.490659, spacing=0.715584993, radius=95, clockwise=true. 사용자가 제공한 게임 스크린샷에서 버튼 수가 증가하면 원호 반지름도 커지는 모습이 관찰됩니다. 반지름 자동 증가/간격 조절 공식은 이 자료만으로 확정되지 않아 이번 버전은 기존 근사 배치식을 유지합니다.

146개 자동 테스트 통과. Windows GUI 실행 검증은 남아 있습니다.
START_WINDOWS.bat 소스 실행 / BUILD_WINDOWS.bat Windows exe 빌드.


---

# TWUI Studio 0.20.1

자식 순서를 레이아웃 엔진 페이지 내부로 이동했습니다. List와 HorizontalList에서만 순서 편집이 활성화되며, 다른 타입 또는 레이아웃 없음에서는 비활성화됩니다.

RadialList를 선택하면 같은 페이지에 근사 미리보기가 표시됩니다. starting_angle, arc, spacing, radius, clockwise의 변경을 반영합니다. 각도/arc/spacing은 라디안으로 해석하며 clockwise=true는 시계 방향, 미지정/false는 반시계 방향으로 표시합니다. radius로 원호 반지름을 정하고, starting_angle부터 arc 구간을 핑크색으로 그립니다. 자식은 spacing 각도마다 배치하고 spacing이 없으면 arc에 균등 배치합니다. 이는 미리보기 가정이며 게임 엔진의 정확한 배치식이 검증된 것은 아닙니다.

각 직접 자식의 현재 스테이트에 연결된 이미지 메트릭을 작은 이미지로 표시합니다. 이미지가 없으면 사각형과 이름으로 표시합니다. 256px보다 큰 이미지는 축소합니다. 휠로 세로 이동, 가운데 버튼 드래그로 평행 이동, Ctrl+휠로 5~100% 확대/축소가 가능합니다. 미리보기 조작은 XML 좌표를 수정하지 않습니다.

146개 자동 테스트 통과. Windows GUI 실제 조작은 아직 검증하지 못했습니다.
소스 실행 START_WINDOWS.bat / Windows exe 빌드 BUILD_WINDOWS.bat.


---

# TWUI Studio 0.20.0

속성 A 영역에 자식 순서 / Children Order를 추가했습니다. 선택한 컴포넌트의 직접 자식만 표시하며 ↑/↓로 한 칸씩 이동합니다. 맨 위/아래에서는 해당 버튼이 비활성화됩니다. 하위 계층은 해당 자식과 함께 이동하며 컴포넌트 정의와 GUID는 유지합니다. 적용 시 hierarchy의 실제 순서를 변경하고 현재 탭의 속성 적용 한 건으로 기록합니다. 닫으면 임시 변경을 버립니다.

B 영역은 내용이 짧으면 맨 위에 고정합니다. 긴 내용은 위/아래 경계에서 추가 휠 스크롤을 무시합니다. 페이지별 스크롤 위치 및 자식 항목 이동은 유지합니다.

144개 테스트 통과. 순서 반전, 하위 계층/정의 보존, 정확한 원순서 복원과 짧은 페이지의 스크롤 영역을 검사했습니다. Windows GUI의 실제 조작 검증은 남아 있습니다.
START_WINDOWS.bat 소스 실행 / BUILD_WINDOWS.bat Windows exe 빌드.


---

# TWUI Studio 0.19.0

Shift+컴포넌트 본체 또는 중심 핸들 드래그: 처음 이동한 방향을 기준으로 가로/세로 한 축을 고정하여 일반 offset을 변경합니다. 부모 LayoutEngine이 있어도 허용합니다. 크기 조절 핸들의 기존 Shift 기능은 유지합니다. 잠긴 컴포넌트는 이동할 수 없습니다. Alt 복사 동작은 기존대로 우선합니다.
부모 LayoutEngine과 dock_offset을 변경하지 않으므로 최종 배치는 레이아웃/도킹 규칙의 영향을 받습니다.

구성요소 목록에서 단일 선택 후 Ctrl+R: 이름 편집창. Enter/적용으로 변경, Escape/취소로 닫기. 속성 창의 Document.rename과 같은 경로로 ID와 해당 컴포넌트/하이어라키 태그를 변경합니다. GUID 및 임의의 CCO 문자열은 변경하지 않습니다. 다중 선택은 지원하지 않습니다.

142개 테스트 통과. Windows GUI 실제 마우스/키보드 조작은 이 환경에서 검증하지 못했습니다.
START_WINDOWS.bat 소스 실행 / BUILD_WINDOWS.bat Windows exe 빌드.


---

# TWUI Studio 0.18.2

원본/모드 리소스의 파일 목록과 이미지 검색이 동일한 유효 ui 폴더를 사용하도록 통일했습니다. 특히 ui/ui 중첩 폴더에서 기존 목록은 안쪽을 표시하고 검색은 바깥쪽을 사용하던 불일치를 수정했습니다.

XML 가져오기와 탭 활성화 시 리소스 캐시를 재생성하여 현재 원본 설정을 다시 연결합니다. 모드 경로 없이도 원본 경로를 사용하며, 모드가 연결되면 같은 상대 경로만 대체합니다. 각 리소스 창에 실제 사용 경로를 읽기 전용으로 표시합니다.

140개 테스트 통과. 원본만 설정한 상태의 탭 활성화/이미지 검색과 중첩 ui 폴더를 검사했습니다. 사용자 PC의 정확한 폴더 구조 및 Windows GUI는 아직 확인하지 못했습니다.

같은 문제가 지속되면 두 리소스 창에 표시된 실제 경로와 누락 이미지의 imagepath를 제공해주세요.
START_WINDOWS.bat: 소스 실행 / BUILD_WINDOWS.bat: Windows exe 빌드.


---

# TWUI Studio 0.18.1

원본 리소스에서 기본 이미지 경로를 찾고, 현재 탭의 모드 폴더에 동일한 상대 경로가 있으면 대체하도록 변경했습니다. 원본/모드 경로 캐시는 독립적으로 유지합니다. 파일이 없는 모드 경로 또는 접근 오류는 원본 검색 결과를 유지합니다. 실제 이미지는 최종 선택된 파일만 읽습니다.

경로 변경 또는 새로고침 시 두 검색 계층을 갱신합니다. 탭별 모드 경로와 원본 공통 경로는 유지됩니다. 모드 경로를 해제하면 원본을 사용합니다.

138개 테스트 통과. 원본 먼저 검색, 모드 대체, 누락 시 원본 사용, 접근 오류, 삭제된 모드 파일, 탭 간 분리를 검사했습니다. 사용자 PC의 실제 누락 원인은 아직 재현하지 못했으며 Windows GUI 검증도 남아 있습니다.

계속 누락되는 경우 해당 component_image의 imagepath와 원본 폴더 안 실제 파일 위치를 비교해야 합니다. 원본에도 없는 파일은 검색 순서를 바꾸어도 표시할 수 없습니다.

START_WINDOWS.bat: 소스 실행 / BUILD_WINDOWS.bat: Windows exe 빌드.


---

# TWUI Studio 0.18.0

원본 UI 리소스 위에 모드 UI 리소스 창을 추가했습니다. 각각 검색, 폴더/파일 아이콘, 이미지 미리보기, 경로 복사를 지원합니다. 두 리소스 창 사이 경계를 드래그하여 높이를 조정할 수 있습니다.

모드 경로는 현재 XML 탭에만 적용됩니다. 동일한 ui/ 상대 경로는 모드 폴더를 우선 사용하며, 없으면 원본 리소스로 대체합니다. 새 XML/새 가져오기에는 경로가 없고, 닫은 탭의 경로는 폐기됩니다. 탭 복사는 경로도 복사하며 이후 독립적으로 변경할 수 있습니다. 프로젝트 저장/열기는 각 탭의 경로를 보존합니다. XML 파일 자체에는 PC 경로를 기록하지 않습니다.

제공한 모드 ZIP은 skins 폴더부터 들어 있으므로 별도의 ui 폴더 안에 압축을 풀고 그 ui 폴더를 지정하세요. 연결 해제 후 적용하면 원본 경로만 사용합니다. 파일 변경 후 새로고침으로 리소스를 다시 검색할 수 있습니다.

135개 자동 테스트 통과. Windows GUI는 이 환경에서 실행 검증하지 못했습니다.
소스 실행: START_WINDOWS.bat / exe 빌드: BUILD_WINDOWS.bat


---

# TWUI Studio 0.17.1

- CCO 속성값의 원시 &&, & 및 < 표현을 읽을 수 있도록 가져오기 호환성을 수정했습니다.
- 검사에만 호환 처리를 적용합니다. 불러온 원문과 수정하지 않은 표현은 그대로 유지합니다.
- 수정한 속성은 XML 이스케이프 규칙으로 저장하며 다시 읽으면 동일한 값이 됩니다.
- HTML 전용 엔티티 처리로 CCO 문자열 일부가 의도치 않게 변하는 문제를 방지했습니다.
- 태그 짝 오류 등 실제 구조 오류는 계속 검사합니다. 모든 손상된 XML을 무조건 허용하는 방식은 아닙니다.

검증: DLC XML 70개 + 키슬레프 원본 + 사용자 모드, 총 72개/7,395개 컴포넌트. 가져오기, 원문 보존, 노드 위치, 속성 수정 후 재읽기 통과. 자동 테스트 133개 통과.
파일별 결과: XML_COMPATIBILITY_REPORT.json
Windows GUI 및 게임 내 실행은 이 환경에서 검증하지 않았습니다.

소스 실행: START_WINDOWS.bat
Windows 실행 파일 생성: BUILD_WINDOWS.bat
완료 시 dist/TWUI_Studio_0.17.1_Windows_x64.zip 생성.
이 배포물은 소스와 빌드 구성이며 완성된 exe를 포함하지 않습니다.
