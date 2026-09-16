## Context

동기는 [proposal.md](proposal.md)의 Why를 따른다. 조사한 본체 업데이트 경로는 여러 프런트엔드 파일과 플랫폼 빌드에 나뉘어 있다.

| 영역 | 현재 경로와 제약 |
| --- | --- |
| 시작·수동 확인 | `OBSBasic.cpp`의 `TimedCheckForUpdates()`, `OBSBasic_MainControls.cpp`의 업데이트 메뉴, `OBSBasic_Updater.cpp`의 확인 로직이 이어진다. |
| 설정 | `OBSBasicSettings.cpp`에서 자동 확인·채널을 읽고 저장하며, `forceUpdateCheck`가 설정 종료 후 재확인을 시작한다. |
| Windows | `AutoUpdateThread`가 브랜치·매니페스트·`updater.exe`를 받아 팝업을 표시하고 실행한다. 복구 메뉴도 같은 스레드를 사용한다. |
| macOS | `MacUpdateThread`의 채널 조회 이후 `OBSSparkle`이 업데이트를 관리한다. 기본 macOS preset에도 피드와 공개 키가 있고, 번들 임베드 설정은 별도 CMake 파일에 있다. |
| 새 소식 | `OnFirstLoad()`와 새 소식 메뉴가 `WhatsNewInfoThread`를 시작한다. `FetchAndVerifyFile()`은 Windows·macOS 업데이트 조회에도 공유된다. |
| 기존 비활성화 수단 | `--disable-updater`와 표식 파일은 자동 확인을 막고 일부 UI를 비활성화한다. 원본 구현·빌드 대상과 별도의 새 소식 경로는 남아 있다. |
| 보조 데이터 | 방송 서비스·서버 정보와 게임 캡처 호환성 데이터는 `shared/file-updater`를 사용한다. 이 경로는 사용자가 유지하도록 확정했다. |

main spec은 아직 없고, 진행 중인 12트랙 변경에서는 업데이트 체계를 범위 밖으로 두었다. 이번 독립 변경은 해당 오디오 계약을 수정하지 않는다. 다중 파일·플랫폼 빌드와 Qt 자동 생성 코드가 함께 바뀌므로 별도 설계를 작성한다.

## Goals / Non-Goals

**Goals:**

- 원본을 보존한 주석 처리와 빌드 제외가 함께 작동하여 기존 설정으로 다시 켤 수 없는 상태를 만든다.
- Qt UI 생성·메타 객체·선언·호출부·종료 시 정리를 일관되게 제외해 모든 플랫폼에서 빌드 가능한 상태를 유지한다.
- 빌드 결과와 실제 실행 관찰을 함께 사용해 UI만 사라지고 업데이트 작업은 남는 상황을 검출한다.

**Non-Goals:**

- 업데이트를 끄는 새 사용자 설정이나 다시 켜는 빌드 옵션, 포크용 업데이트 서버를 만들지 않는다.
- 일반 HTTP·암호화 도구, 브라우저 기능, 플러그인 데이터 갱신을 일괄 차단하지 않는다.
- 기존 캐시·개인 설정을 청소하거나 빌드 의존성 다운로드 체계를 재설계하지 않는다. 운영체제 패키지 관리자나 외부 실행기의 업데이트도 제어하지 않는다.

## Decisions

### 1. 원본 코드를 보존한 정적 제외를 사용한다

작은 C/C++ 문장은 `//`, 연속된 기능 블록은 사유를 적은 `#if 0` 영역으로 보존한다. CMake는 `#` 또는 bracket comment, Qt UI와 plist는 XML 주석을 사용한다. 각 제외 지점에는 Dodeca의 본체 업데이트 비활성화임을 짧게 명시한다. C/C++의 기존 블록 주석이나 XML 주석을 중첩해 문법을 깨뜨리지 않는다.

업데이트 전용 소스 파일 전체는 원본을 유지하고 CMake 소스 목록·하위 디렉터리 추가를 주석 처리해 컴파일에서 제외한다. 단순한 런타임 `return`, 기본 설정 OFF, `--disable-updater` 강제 추가만으로 완료하지 않는다. 이런 대안은 요청된 주석 처리와 원본 보존을 충분히 표현하지 못하고 다른 진입점이나 기존 캐시 설정에 영향을 받기 때문이다.

### 2. UI 정의와 그 참조를 함께 제외한다

`OBSBasic.ui`의 `actionCheckForUpdates`, `actionRepair`, `actionShowWhatsNew` 정의와 메뉴 등록을 주석 처리한다. `OBSBasicSettings.ui`의 `updateSettingsGroupBox` 전체와 업데이트 위젯의 tabstop도 제외한다. 그러면 생성된 UI에 해당 객체가 없으므로 C++의 접근·삭제·null 대입, macOS menu role 설정, 자동 연결 슬롯 선언과 정의도 함께 주석 처리해야 한다.

설정의 HookWidget 연결, 로드·저장, `LoadBranchesList`, `forceUpdateCheck` 멤버와 사용 지점을 함께 제외한다. 단순 `hide()` 또는 `setEnabled(false)` 방식은 객체와 호출 경로가 남으므로 선택하지 않는다. 업데이트와 무관한 주변 메뉴 및 릴리스 노트 웹 링크는 유지한다.

### 3. 진입점부터 작업 스레드까지 연결을 끊는다

- `OBSBasic.cpp`: 자동 베타 채널 선택, 시작 시 확인, `OnFirstLoad()`의 새 소식 요청, 업데이트 스레드 종료 대기를 제외한다.
- `OBSBasic_MainControls.cpp`와 `OBSBasic.hpp`: 업데이트·복구·새 소식 슬롯, 완료 콜백, 관련 include·스레드 멤버·메서드 선언을 제외한다.
- `ui-widgets.cmake`: `OBSBasic_Updater.cpp`를 소스 목록에서 제외한다. 파일은 원본 그대로 남긴다.
- `OBSApp.*`: 업데이트 채널 모델·캐시 파싱·접근 API·상태와 업데이트 기본값 등록 및 전용 `updates` 디렉터리 생성을 제외한다. 다른 설정 디렉터리 생성과 전역 버전 이전 로직은 보존한다.
- `IsUpdaterDisabled()`는 호환용으로 남기고 원래 반환문을 주석 처리한 뒤 항상 true를 반환한다. `obs-main.cpp`의 기존 `--disable-updater` 인자와 표식 처리는 계속 허용하되 실제 기능을 제어하지 않는 호환 입력으로 문서화한다.

최종 빌드에서 작업 스레드와 호출부가 모두 사라지므로 기존 `branches.json`, `manifest.json`, `whatsnew.json`, `updater.exe`를 보존해도 앱이 사용하지 않는다. 캐시 파일 삭제로 동작을 막는 대안은 기존 사용자 데이터를 변경하고 재다운로드 경로도 남기므로 사용하지 않는다.

### 4. 플랫폼 빌드와 패키징을 함께 제외한다

| 파일·영역 | 처리 방향 |
| --- | --- |
| `frontend/cmake/os-windows.cmake` | `OBSUpdate` 대화상자·폼, `AutoUpdateThread`, 새 소식 스레드와 전용 helper 소스, updater manifest 대상·연결, updater용 커밋 정의와 `add_subdirectory(updater)`를 주석 처리한다. |
| `frontend/cmake/ui-dialogs.cmake` | `OBSWhatsNew` 대화상자 소스를 주석 처리한다. |
| `frontend/cmake/feature-whatsnew.cmake` | 기존 기능 활성화 블록을 주석 처리해 `ENABLE_WHATSNEW=ON` 캐시가 있어도 소스·기능 정의가 추가되지 않게 한다. |
| `frontend/cmake/feature-sparkle.cmake` | Sparkle 검색·소스·링크·활성화 블록을 주석 처리하고 비활성 상태를 명시한다. |
| `frontend/cmake/feature-macos-update.cmake` | 업데이트·새 소식 helper를 등록하는 블록을 제외한다. 기존 포함 관계에서도 재등록되지 않게 한다. |
| `cmake/macos/helpers.cmake` | 피드·키만 보고 Sparkle을 임베드하던 블록을 주석 처리한다. |
| `frontend/cmake/macos/Info.plist.in` | `SUFeedURL`, `SUPublicEDKey`, `SUScheduledCheckInterval`의 키·값 쌍을 XML 주석 처리하여 실제 plist에 활성 항목이 남지 않게 한다. |

전용 의존성의 검색·연결은 남은 사용처가 없을 때만 함께 제외한다. 일반 JSON·CURL·암호화 의존성과 플러그인의 `OBS::file-updater` 연결은 필요한 곳에 유지한다. `CMakePresets.json`의 기존 피드·키 등 입력이 남아도 활성 코드가 이를 사용하지 않게 하며, JSON 파일에 주석 문법을 추가하지 않는다.

기본 옵션만 OFF로 바꾸는 방식은 기존 캐시와 macOS preset에 의해 다시 켜질 수 있어 선택하지 않는다. Windows updater와 macOS 프레임워크는 새 빌드·새 설치 위치의 결과물에서 제외되어야 하며, 이전 설치에 남은 파일을 자동 삭제하는 절차는 추가하지 않는다.

### 5. 검증은 설정·UI·생성 결과·실행 부작용을 확인한다

기존 `test/audio-tracks/prepare.py`는 자동 업데이트를 false로 설정하므로 그 설정만으로는 회귀를 검출할 수 없다. 별도 시험 설정에서 자동 업데이트 true, 마지막 확인 시점 0, 이전 버전 값, stable·beta 채널 및 확인 전 새 소식 상태를 준비한다. 일반 설정을 저장하고 재시작한 뒤 기존 값과 오디오 설정 보존도 확인한다. 개인 설정을 사용하지 않는다.

| 검증 | 관찰할 결과 |
| --- | --- |
| UI | 업데이트·복구·새 소식 action과 업데이트 설정 위젯 부재, 빈 설정 그룹 부재, 주변 설정 저장 성공. 기존 Qt 브리지의 객체 조회·invoke를 활용할 수 있으며 제거된 슬롯은 호출 실패가 정상이다. |
| 실행 | 시작·설정 저장·재시작 중 본체 업데이트 및 새 소식 대상 요청, 업데이트 캐시 생성·변경, updater 자식 프로세스와 팝업이 없어야 한다. 기존 캐시는 실행 가능한 실제 업데이터 대신 무해한 시험 파일과 전후 해시로 확인한다. |
| 통신 | 별도 시험 프로세스의 네트워크 요청 또는 HTTP 호출 관찰을 사용한다. `update_studio`의 본체 브랜치·매니페스트·updater·새 소식 경로와 macOS appcast를 대상으로 구분하며, 방송 서비스·게임 캡처 데이터 요청은 허용한다. 인터넷 연결 실패나 로그가 조용한 것만으로 통과시키지 않는다. |
| 생성 결과 | CMake 대상·컴파일 목록에서 업데이트 전용 소스와 Windows updater 대상 부재를 확인한다. 새 설치/portable 결과의 updater 부재, macOS 번들의 프레임워크·활성 plist 항목 부재를 확인한다. |
| 회귀 | 기존 CTest와 UI 설정·12트랙 짧은 녹화 검사를 실행하고 방송 서비스 데이터 및 Windows 캡처 초기화·호환성 갱신 경로를 확인한다. 일반 브라우저 소스·도크도 확인한다. |

Windows는 `windows-x64`, Visual Studio 2026·CMake 4.2 이상과 작업 공간 내 별도 설치 prefix를 사용한다. 빌드 후 설치 `bin/64bit`를 PATH에 추가해 `ctest --test-dir <build-dir> -C RelWithDebInfo --output-on-failure`를 실행한다. Linux는 기존 preset과 필요 시 Xvfb, macOS는 기존 preset을 사용하며 브라우저 ON과 기존 업데이트 활성 입력이 있는 경우도 포함한다.

플랫폼별 네이티브 검증을 구분한다. 환경이 없어 실행하지 못한 플랫폼 항목은 미검증으로 남기고 다른 OS의 결과로 완료하지 않는다. 결과는 `docs/application-updates.md`에 명령·구성·증거와 함께 기록하고, 실제로 재검증한 플랫폼의 오디오 검증 결과·해시 기록만 갱신한다.

## Risks / Trade-offs

- [Qt 자동 생성 객체나 슬롯의 잔여 참조] → 폼·tabstop·헤더·호출부를 함께 제외하고 실제 AUTOUIC/AUTOMOC 빌드로 검증한다.
- [Windows의 `_WIN32` 조건만으로 전용 코드가 남거나 macOS에서 프레임워크가 재포함됨] → 플랫폼 조건과 별개로 주석 처리하고 기존 캐시를 사용한 생성 결과도 점검한다.
- [업데이트 helper와 플러그인 데이터 updater를 혼동] → 위 파일별 범위를 기준으로 처리하고 `shared/file-updater` 및 서비스·캡처 옵션을 보존한다.
- [기존 설치의 남은 파일을 새 패키지로 오인] → 비어 있는 별도 설치 prefix에서 생성 결과를 확인한다. 기존 파일을 앱이 실행하지 않는 검사는 별도로 수행한다.
- [소스가 남아 upstream 병합에서 다시 활성화될 수 있음] → Dodeca 사유 주석과 검증 문서를 남기고 병합 후 UI·빌드 진입점 검사를 반복한다.
- [실행 관찰이 불가능한 플랫폼 또는 도구] → 정적 점검과 네이티브 결과를 구분해 제한을 기록한다. 미관찰 항목을 통과로 표시하지 않는다.

## Migration Plan

설정 형식 이전은 필요 없다. 구현·검증 후 새 빌드와 별도 설치 위치를 준비하고, 사용자 설정으로 실행하기 전 장면 모음과 프로필을 함께 백업한다. 기존 업데이트 설정·캐시는 그대로 두며 앱에서 사용하지 않는다.

기능 복원은 이 변경의 주석·빌드 제외를 되돌리고 프런트엔드와 관련 모듈을 일관되게 재빌드하는 소스 변경으로만 수행한다. UI에서 다시 활성화하는 경로는 제공하지 않는다. 원래 6트랙 OBS로 롤백하는 경우에는 기존 오디오 문서의 설정 백업·복원 절차를 따른다.
