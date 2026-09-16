## 1. 업데이트 UI와 연결 제외

- [x] 1.1 `OBSBasic.ui`의 업데이트 확인·복구·새 소식 action과 메뉴 등록, `OBSBasicSettings.ui`의 업데이트 설정 그룹·tabstop을 원본이 남는 XML 주석으로 제외하고, XML 파싱 및 Qt UI 생성에서 해당 객체가 만들어지지 않음을 확인한다.
- [x] 1.2 `OBSBasic.cpp`, `OBSBasic_MainControls.cpp`, `OBSBasic.hpp`의 관련 UI 접근·삭제·macOS menu role, 메뉴 슬롯 선언·정의와 완료 콜백을 주석 처리하고, 활성 코드에 제거된 action 참조가 없으며 릴리스 노트 등 주변 메뉴가 보존됐음을 확인한다.
- [x] 1.3 `OBSBasicSettings.*`의 업데이트 위젯 연결·로드·저장, 채널 목록 처리, `forceUpdateCheck` 상태와 재확인을 주석 처리하고, 활성 코드에 제거된 위젯 참조가 없고 일반 설정의 나머지 저장 흐름이 유지됨을 확인한다.

## 2. 본체 업데이트와 새 소식 실행 경로 제외

- [x] 2.1 `OBSBasic.cpp`의 자동 베타 채널 선택·시작 시 확인·첫 실행 새 소식 요청·스레드 종료 처리와 관련 include·멤버·선언을 주석 처리하고, `ui-widgets.cmake`에서 `OBSBasic_Updater.cpp`를 제외한다. 원본 구현이 남아 있고 활성 진입점에서 업데이트·새 소식 스레드를 생성하지 않음을 확인한다.
- [x] 2.2 `OBSApp.*`의 업데이트 채널 모델·상태·캐시 파싱·API, 업데이트 기본값 등록 및 전용 캐시 디렉터리 생성을 주석 처리한다. `IsUpdaterDisabled()`의 원래 반환문을 보존하고 항상 true를 반환하게 하며, 기존 CLI·표식 입력 수용과 일반 설정·버전 이전 로직 보존을 확인한다.

## 3. 플랫폼 빌드와 패키징 제외

- [x] 3.1 `os-windows.cmake`의 updater 대화상자·폼·스레드·전용 helper 소스, manifest 대상·연결, updater 커밋 정의와 하위 디렉터리 추가를 주석 처리한다. 전용 의존성만 정리하고 Windows 생성 프로젝트에 updater 대상이나 제외한 소스가 없음을 확인한다.
- [x] 3.2 `ui-dialogs.cmake`, `feature-whatsnew.cmake`, `feature-macos-update.cmake`의 새 소식 및 업데이트 helper 등록을 주석 처리하고, `ENABLE_WHATSNEW=ON`에서도 새 소식 기능 정의·소스가 생성되지 않으며 브라우저 소스·도크의 빌드 설정은 보존됐음을 확인한다.
- [x] 3.3 `feature-sparkle.cmake`의 활성화·소스·링크, `cmake/macos/helpers.cmake`의 임베드, `Info.plist.in`의 Sparkle 키·값을 주석 처리한다. 기존 피드·키 입력이 있어도 업데이트 연결·임베드가 생성되지 않고 plist가 유효함을 확인한다.

## 4. 통합 검증

- [x] 4.1 Windows `windows-x64` preset으로 프런트엔드와 번들 모듈을 빌드하고 별도 설치 prefix에 설치한다. 브라우저와 기존 새 소식 활성 입력을 포함해 AUTOUIC/AUTOMOC·링크 성공, updater 대상·새 설치 결과물 부재, `obs64 --portable --version` 성공 및 `ctest --test-dir <build-dir> -C RelWithDebInfo --output-on-failure` 통과를 기록한다.
- [ ] 4.2 별도 Windows 시험 설정에서 새 설정과 자동 업데이트 true·오래된 확인 시점·stable/beta·무해한 기존 캐시를 가진 설정을 실행한다. 일반/portable 및 `--disable-updater`·표식 유무, 시작·설정 저장·재시작을 확인하고, UI·팝업·대상 네트워크 요청·캐시 변경·updater 실행이 없다는 관찰 결과와 설정 보존을 기록한다.
- [x] 4.3 Windows에서 기존 도구로 트랙 설정 저장·복원과 짧은 12트랙 녹화를 확인하고, 방송 서비스·서버 데이터와 게임 캡처 호환성 갱신·캡처 초기화, 브라우저 소스·도크, 릴리스 노트 열기가 유지됨을 기록한다. 녹화는 스트림 수와 각 트랙 디코딩·시험음 분리를 확인한다.
- [ ] 4.4 Linux 네이티브 환경에서 기존 preset으로 빌드·CTest·UI/실행 검사를 수행하고 브라우저 ON·새 소식 ON 입력에서도 본체 업데이트와 새 소식이 제외됨을 기록한다. 환경이 없으면 제한을 기록하고 이 항목을 미완료로 유지한다.
- [ ] 4.5 macOS 네이티브 환경에서 기존 피드·키를 가진 preset으로 빌드·실행하고, 애플리케이션 메뉴·일반 설정·새 소식 부재 및 번들의 Sparkle 프레임워크·활성 피드 항목 부재를 확인한다. 기존 자동 업데이트 설정에서도 작업이 시작되지 않음을 기록하며, 환경이 없으면 제한을 기록하고 이 항목을 미완료로 유지한다.

## 5. 문서와 최종 확인

- [x] 5.1 `docs/application-updates.md`에 제외·유지 범위, 주석·빌드 제외 위치, 기존 CLI·설정 호환성, 복원 방법 및 재현 가능한 플랫폼별 검증 명령·결과를 작성한다. 문서가 실제 변경과 일치하고 새 파일이 Git 허용 목록에 포함되는지 확인한다.
- [x] 5.2 실제 재검증한 플랫폼의 `docs/audio-tracks/` 결과와 SHA-256 기록을 해당 검증 범위·시점과 함께 갱신한다. 과거 검증과 이번 회귀 검사 범위를 구분하고 다른 플랫폼의 이전 증거를 보존했음을 확인한다.
- [x] 5.3 변경한 C/C++·CMake에 지정된 clang-format 22.1.3·gersemi 0.25.0 검사를 적용하고 `git diff --check`와 `openspec validate disable-application-updates --type change --strict --no-interactive`를 통과시킨다. 최종 diff에서 원본 코드가 주석 또는 제외된 파일로 보존되고 방송 서비스·캡처 데이터 updater에 불필요한 변경이 없는지 확인한다.

## 검증 상태 메모 (2026-09-16)

- 구현과 Windows 전체 빌드·CTest, Portable UI·실행 6회 및 12트랙 짧은 녹화 검증을 완료했다. 결과와 제한은 `docs/application-updates.md`와 플랫폼별 요약 JSON에 기록했다.
- 4.2는 Portable 플래그·표식 네 조합, 새 설정, 저장 후 재시작·설정 보존까지만 통과했다. 일반 모드 시도에서 설정 격리가 실패해 기존 사용자 INI 두 파일이 저장됐고, 해당 시험을 중단했다. 사고 이후 백업을 보존하고 사용자에게 사전 백업을 요청했다. 일반 모드 검증은 미완료다.
- 4.4는 브라우저 OFF의 Linux 전체 빌드·설치·CTest 1/1을 통과했다. CEF 부재로 브라우저 ON 구성과 해당 GUI 검증은 미완료다.
- 4.5는 macOS 네이티브 실행 환경이 없어 미검증이다. CMake 기능·plist 정적 검사로 완료 처리하지 않았다.
