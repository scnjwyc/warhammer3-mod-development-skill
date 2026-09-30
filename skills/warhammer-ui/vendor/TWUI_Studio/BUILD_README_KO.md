# TWUI Studio 0.22.2 Windows 빌드 준비본

이 ZIP은 실행 파일 배포본이 아닙니다. Windows용 exe는 아직 생성되지 않았습니다.
현재 기능 버전 0.22.2을 유지하며, 빌드 시 제목 표시줄과 exe 파일 속성에 버전이 표시됩니다.

1. Windows 10/11 x64 컴퓨터에 64비트 Python 3.12를 설치합니다. Tcl/Tk 및 Python launcher를 포함하세요.
2. 이 ZIP을 압축 해제하고 `BUILD_WINDOWS.bat`를 실행합니다. 최초 빌드에는 패키지 다운로드용 인터넷 연결이 필요합니다.
3. 성공하면 `exe_version_package/TWUI_Studio_0.22.2_Windows_x64.zip`이 생성됩니다.
4. 테스트 사용자에게는 그 ZIP을 전달합니다. 사용자는 Python 없이 압축 해제 후 `TWUI_Studio.exe`를 실행합니다.

빌드 스크립트는 Windows 실행 파일인지 확인하고 실제 생성된 앱을 시작하여 Tk 및 데이터 파일 로드를 검사한 후 ZIP을 만듭니다. 이 검사는 Windows에서 빌드할 때 수행되며 현재 환경에서는 실행되지 않았습니다.

배포 전 별도의 Windows PC에서 실행, 리소스 폴더 설정, XML 가져오기/수정/내보내기, 한영 전환을 확인하세요.
설정과 오류 로그는 사용자 AppData 아래에 저장합니다. 설치나 레지스트리 등록은 사용하지 않습니다.
기존 소스 실행 방식 `START_WINDOWS.bat`도 유지합니다.

출력 폴더: exe_version_package
- TWUI_Studio/: 실행 가능한 프로그램 폴더(EXE와 _internal을 함께 유지)
- TWUI_Studio_0.22.2_Windows_x64.zip: 사람들에게 전달할 배포 ZIP
- _build_work/: 임시 빌드 파일·분석 경고·spec
- _build_venv/: 빌드용 Python 환경

도움말 → 프로그램 정보 / 이용 조건에서 공동 제작자, 버전 및 이용 조건을 확인할 수 있습니다. 배포 ZIP에 LICENSE.txt와 THIRD_PARTY_NOTICES.txt도 포함됩니다.
