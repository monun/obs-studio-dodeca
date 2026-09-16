# 본체 업데이트 비활성화

OBS Studio Dodeca는 공식 OBS 본체 업데이트를 실행하지 않는다. 업데이트 확인·자동 업데이트·채널 선택, 같은 실행기를 사용하는 Windows 복구, 새 소식(What's New) 메뉴와 팝업을 제외했다. 원본 구현은 주석 또는 빌드 목록에서 제외된 소스 파일로 보존한다.

방송 서비스 목록·서버 정보와 게임 캡처 호환성 데이터 갱신은 유지한다. 일반 브라우저 소스·도크, 릴리스 노트 웹 링크, 인증·방송·녹화·리먹스의 동작도 유지한다. 제삼자 플러그인과 운영체제 패키지 관리자의 자체 업데이트는 이 변경의 대상이 아니다.

## 구현 위치와 복원

| 영역 | 제외 위치 |
| --- | --- |
| 메뉴·설정 | `frontend/forms/OBSBasic.ui`, `OBSBasicSettings.ui`의 XML 주석. action·설정 그룹·tabstop을 함께 제외한다. |
| UI 연결·시작·종료 | `frontend/widgets/OBSBasic.cpp`, `OBSBasic_MainControls.cpp`, `OBSBasic.hpp`의 Dodeca 주석과 `#if 0` 블록. |
| 설정 로드·저장·재확인 | `frontend/settings/OBSBasicSettings.cpp`, `.hpp`의 Dodeca 주석과 `#if 0` 블록. |
| 업데이트 상태·캐시 | `frontend/OBSApp.cpp`, `.hpp`의 업데이트 기본값·채널·캐시 디렉터리 생성 제외. `IsUpdaterDisabled()`는 항상 true다. |
| 전용 소스·Windows 실행기 | `frontend/cmake/{ui-widgets,ui-dialogs,os-windows}.cmake`의 주석. `frontend/updater/`와 업데이트·새 소식 전용 소스는 컴파일하지 않는다. |
| 새 소식·macOS 업데이트 | `frontend/cmake/feature-{whatsnew,macos-update,sparkle}.cmake`의 주석. 기존 활성 옵션이 있어도 기능을 등록하지 않는다. |
| macOS 번들 | `cmake/macos/helpers.cmake`의 Sparkle 임베드 제외, `frontend/cmake/macos/Info.plist.in`의 Sparkle 키·값 주석. |

`--disable-updater`와 `disable_updater[.txt]` 표식은 기존 실행 방법과의 호환성을 위해 계속 허용한다. 없어도 본체 업데이트는 비활성 상태다. 저장된 `EnableAutoUpdates`, `UpdateBranch`, `LastUpdateCheck` 등의 값과 기존 업데이트 캐시는 삭제·재작성하지 않고 사용하지 않는다. 새 설정에서는 업데이트 캐시 디렉터리를 만들지 않는다.

복원하려면 위 Dodeca 주석·컴파일 제외를 소스에서 되돌리고 UI 정의·선언·호출부·빌드 등록을 함께 복원한 뒤 다시 빌드한다. 사용자 설정이나 CMake 옵션만으로 다시 켜는 기능은 없다. `ENABLE_WHATSNEW=ON`과 기존 Sparkle 피드·키는 재활성화 수단이 아니다.

## 빌드와 확인 방법

기존 플랫폼 preset을 사용한다. Windows에서는 Visual Studio 2026과 CMake 4.2 이상이 필요하다. 아래 검증 옵션은 시험 빌드에서만 켠다. CMake 실행 파일이 PATH에 없으면 설치된 실행 파일의 경로를 지정한다.

```powershell
cmake --preset windows-x64 `
  '-DENABLE_AUDIO_TRACK_TESTS=ON' '-DENABLE_TEST_INPUT=ON' `
  '-DENABLE_WHATSNEW=ON' '-DOBS_BUILD_NUMBER=1' `
  '-DOBS_VERSION_OVERRIDE=32.2.2-dodeca' `
  '-DCMAKE_INSTALL_PREFIX=C:/Users/monun/proj/obs-studio-dodeca/build_x64/install_no_updates'
cmake --build --preset windows-x64 --parallel 2 -- /nodeReuse:false /p:CL_MPCount=2
cmake --install build_x64 --config RelWithDebInfo --prefix build_x64/install_no_updates
$env:PATH = (Resolve-Path 'build_x64/install_no_updates/bin/64bit').Path + ';' + $env:PATH
ctest --test-dir build_x64 -C RelWithDebInfo --output-on-failure
& 'build_x64/install_no_updates/bin/64bit/obs64.exe' --portable --version
```

새 설치 위치를 사용해 오래된 updater 파일과 새 결과물을 구분한다. 사용자 설정을 시험에 사용하지 않는다. 사용자 설정으로 전환할 때는 장면 모음과 프로필을 먼저 함께 백업한다.

1. 새 시험 설정과 자동 업데이트 true·마지막 확인 0·이전 버전·stable/beta 채널을 가진 설정을 준비한다. 캐시 검사는 실행 불가능한 시험 파일을 사용하고 실행 전후 SHA-256을 비교한다.
2. 일반/portable 모드 각각에서 `--disable-updater`와 표식 파일의 유무를 확인한다. 일반 모드는 별도 Windows 사용자 계정이나 VM처럼 설정 분리가 보장된 환경에서 실행한다. 이번 시험의 `SHGetFolderPathW` 관찰·경로 교체만으로는 격리가 보장되지 않았으므로 재사용하지 않는다.
3. 도움말·일반 설정에서 업데이트·복구·새 소식 메뉴와 업데이트 설정 그룹이 없음을 확인한다. 관련 없는 설정을 저장하고 종료·재시작한 뒤 기존 업데이트 값과 12트랙 설정을 확인한다.
4. 시작부터 프로세스 종료까지 HTTP URL과 자식 프로세스 실행을 관찰한다. `update_studio/{branches,manifest,updater,whatsnew}` 및 macOS appcast 요청과 updater 실행이 없어야 한다. `obs2_update/rtmp-services`, `obs2_update/win-capture` 요청은 허용한다. 로그가 조용하거나 인터넷이 끊겨 있다는 이유만으로 통과시키지 않는다.
5. 새 Windows 빌드 대상·설치 위치에 updater가 없고 macOS 번들에 Sparkle 및 활성 `SUFeedURL`, `SUPublicEDKey`, `SUScheduledCheckInterval` 키가 없는지 확인한다. Windows 결과로 macOS 검증을 대신하지 않는다.

## 2026-09-16 검증

Windows 빌드는 CMake 4.4.3, Visual Studio 2026, Qt 6.11.1, FFmpeg 8.1, 기존 `windows-x64` preset의 브라우저 ON 구성을 사용했다. 원시 증거는 `build_windows_validation/2026-09-16/disable-updates/`에 있으며 Git에는 대용량 파일과 시험 설정을 넣지 않는다.

| 항목 | 결과 |
| --- | --- |
| 전체 Windows 빌드·별도 설치 | 통과. 최초 sandbox 실행의 FileTracker 권한 오류 이후 동일 옵션의 허용된 네이티브 실행으로 완료. |
| Windows CTest | `audio-tracks` 1/1 통과. |
| 새 설치 결과 | updater 대상·실행 파일 없음, `obs64 --portable --version` 성공. |
| XML·Qt UI 생성 | 업데이트 action·설정 위젯·tabstop 제외, plist 파싱 통과. |
| CMake 기능 검사 | 새 소식 ON 및 Sparkle 피드·키 입력이 있어도 전용 기능을 등록하지 않음. macOS 네이티브 빌드를 대신하지 않음. |
| 실제 Windows GUI·실행 | Portable 모드에서 CLI 플래그·표식 파일의 네 조합, 저장 후 재시작, 업데이트 설정이 없는 새 설정까지 총 6회 통과. 일반 모드의 별도 설정 검증은 미완료. |
| 짧은 12트랙 녹화 | 12초 MKV의 12개 트랙 디코딩·이름·시험음 분리·패킷 연속성 확인. 관찰 구간의 트랙 간 동기 오차 0ms, 다른 시험음 누설 최대 -48.7dB, 패킷 간격 오차 최대 약 1ms. 장시간·전체 컨테이너 검증은 이번 검사 범위 밖이다. |
| 보조 기능 | 방송 서비스·게임 캡처 데이터 요청, 브라우저 소스·도크의 loopback 페이지 로드, 캡처 소스 초기화, 릴리스 노트 URL의 브라우저 전달 확인. |
| Linux 브라우저 ON | CEF 배포본과 wrapper library가 없어 구성 실패. 해당 네이티브 UI 검증은 미완료. |
| Linux 브라우저 OFF | 기존 Ubuntu 24.04 검증 이미지에서 전체 빌드·설치와 Xvfb CTest 1/1 통과. `ENABLE_WHATSNEW=ON`은 유지했다. GUI·브라우저 포함 검증을 대신하지 않는다. |
| macOS | 네이티브 빌드·실행 환경이 없어 미검증. |

실행 관찰에는 시험 프로세스의 libcurl URL 설정, `CreateProcessW`, `ShellExecuteExW`를 기록했다. Qt GUI 검사는 설치본과 같은 Qt로 빌드한 임시 모듈을 사용했다. 초기 PyQt 휠은 번들 Qt와 DLL 호환이 맞지 않아 사용하지 않았다. 시험 INI는 경로를 슬래시로 기록하고 UTF-8 BOM을 처리했으며, 종료 전 시험 웹소켓 연결을 닫았다. 이 조정은 시험 도구에만 적용했다.

`runtime-native-3/`의 케이스별 `result.json`, `trace.json`, 설정 화면과 시험 로그, `runtime-summary.json`이 실제 실행 증거다. 첫 케이스는 앱 종료 후 INI의 BOM 처리 오류를 고친 뒤 저장된 원본 증거로 후속 검사를 마쳤으며, 수정 전 결과도 보존했다. 임시 검증 모듈은 배포 파일이 아니다.

### 일반 모드 시험의 설정 격리 실패

2026-09-16 17:17 KST의 일반 모드 시도에서 경로 격리가 적용되지 않아 기존 사용자 설정을 읽었다. 시험 웹소켓에 연결되지 않은 단계에서 해당 프로세스를 종료했으며, 이 시도는 검증 통과로 계산하지 않는다. 기존 `user.ini`와 프로필 `basic.ini`의 저장 시각이 변경됐다. 기존 `global.ini`와 장면 JSON의 저장 시각은 이전 상태로 유지됐다.

현재 설정·장면·프로필을 작업 공간의 `build_windows_validation/2026-09-16/disable-updates/personal-settings-after-test/`에 복사해 보존했다. 이 백업은 사고 이후 상태이며 실행 전 원본을 증명하지 않는다. 사전 백업 없이 개인 INI를 추정해 되돌리지 않았고, 사용자에게 이전 백업 위치를 요청했다. 이 개인 설정 백업은 Git에 포함하지 않는다. 이후 검사는 명시적인 portable 모드에서만 수행했다.
