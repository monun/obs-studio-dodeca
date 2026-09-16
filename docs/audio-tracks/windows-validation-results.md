# Windows 검증 결과

## 2026-09-16: 본체 업데이트 비활성화 후 회귀 검사

`disable-application-updates` 변경 후 브라우저를 포함한 Windows 전체 빌드·별도 설치, CTest `audio-tracks` 1/1, portable 버전 조회가 통과했다. Portable 모드의 업데이트 플래그·표식 네 조합, 저장 후 재시작, 새 업데이트 설정 등 6회 실행에서 업데이트 UI·요청·실행기 부재 및 기존 업데이트 설정·캐시 보존을 확인했다.

12초 MKV 녹화에서 12개 트랙의 이름·디코딩·300~1400Hz 시험음 분리와 패킷 연속성을 확인했다. 트랙 간 동기 오차는 0ms, 다른 시험음 누설 최대 -48.7dB, 패킷 간격 오차 최대 약 1ms였다. 방송 서비스·캡처 데이터 요청, 브라우저 소스·도크, 캡처 소스 초기화와 릴리스 노트 URL 전달도 확인했다. 설치본과 같은 Qt 6.11.1로 만든 임시 검증 모듈을 사용했다.

일반 모드 시험에서는 설정 격리에 실패해 기존 `user.ini`와 프로필 `basic.ini`가 저장됐다. 해당 시도는 중단했고 장면 JSON과 기존 `global.ini`의 저장 시각은 유지됐다. 사고 이후 설정·장면·프로필 백업을 작업 공간에 남겼으며 사전 백업은 사용자에게 요청했다. 일반 모드 검증은 통과로 처리하지 않았다. 상세 범위·명령·사고 기록은 [본체 업데이트 검증 문서](../application-updates.md)에 있다.

현재 코드 해시와 이번 검증은 [요약 JSON](windows-validation-summary.json)의 `application_updates_followup`에 추가했다. 아래의 이전 기록과 해시는 보존했다. 이번 제한된 회귀 검사는 이전 12트랙 작업의 Windows 전체 출력·리플레이·리먹스·100%/200% 배율 검증을 완료한 것으로 간주하지 않으며 OpenSpec 7.4를 체크하지 않는다.

검증일: **2026-09-15 (KST)**. **재부팅 없이 Windows 전체 빌드·설치와 오디오 CTest 1/1이 통과했다. Portable ZIP을 만들고 압축 해제한 실행 파일의 버전 조회까지 확인했다.** 사용자가 ZIP으로 직접 시험하기로 했으며, 실제 녹화·리플레이·리먹스·GUI 검사는 남아 있다. OpenSpec 7.4와 macOS 7.5는 체크하지 않았다. 최초 실패부터 최종 빌드까지의 기록을 아래에 구분한다.

## 최신 ZIP: 트랙 번호를 한 행으로 표시

사용자가 최초 portable ZIP을 확인한 뒤 트랙을 한 줄로 표시하도록 요청했다. 고급 오디오 속성, 간단·고급 녹화, 사용자 지정 FFmpeg, FLV, 방송 및 VOD 선택을 **1~12번 순서의 한 행**으로 배치했다. 기존 스크롤 영역을 유지하고 UI 검사 스크립트를 각 번호까지 스크롤한 뒤 확인하도록 갱신했다. 라디오 키보드 검사는 오른쪽 화살표의 6→7, 11→12 이동을 기준으로 한다.

- [한 줄 배치 Portable ZIP](../../artifacts/obs-studio-32.2.2-dodeca-windows-x64-portable-single-row.zip): **178,798,714 bytes**, 압축 해제 후 436,749,561 bytes, 2,072개 파일.
- [SHA-256](../../artifacts/obs-studio-32.2.2-dodeca-windows-x64-portable-single-row.zip.sha256): `2d2d363095b8ebc93bbe386975e7b4e65dbbb0afdb8a845fb79d9ebc7453be78`.
- 새 폴더에 풀고 `Start-OBS.bat`를 실행한다. 시험 설정은 해당 폴더에 저장된다.
- 세 C++ 파일의 clang-format 22.1.3, 기존 preset 전체 빌드, 별도 `build_x64/install_single_row` 설치, 오디오 CTest **1/1**(0.16초)이 통과했다.
- ZIP CRC·전체 압축 해제·설치본과의 내용 비교·압축 해제한 `obs64.exe --portable --version`이 통과했다. 기존 ZIP과 사용 중인 OBS 프로세스는 보존했다.
- 수정한 UI 검사 스크립트의 문법은 확인했다. 이 한 행 배치를 실제 GUI에서 자동화하거나 100%/200% 배율로 실행한 결과는 아직 없다. 이전 Linux의 두 행 배치 검사 결과는 새 배치의 검증으로 간주하지 않는다.

원시 증거는 `build_windows_validation/2026-09-15/single-row/`의 `build-final.*`, `install.*`, `ctest.*`, `package.*`, `zip-runtime.*`, `package-manifest.json`에 있다. 아래 절은 최초 portable ZIP까지의 빌드 기록이다.

## 전체 빌드와 portable ZIP

기존 `windows-x64` preset과 `RelWithDebInfo`, `ENABLE_BROWSER=ON`을 유지하고 libobs·프런트엔드·활성 번들 모듈 전체를 함께 빌드했다. `ENABLE_AUDIO_TRACK_TESTS=ON`, `ENABLE_TEST_INPUT=ON`인 검증용 구성이다. 다른 작업에 대한 부하를 줄이기 위해 실행 우선순위는 `BelowNormal`, MSBuild 병렬 프로젝트 수와 프로젝트별 컴파일러 병렬 수는 각각 2로 제한했다.

| 실행 | 결과 |
| --- | --- |
| `cmake --fresh --preset windows-x64 '-DENABLE_AUDIO_TRACK_TESTS=ON' '-DENABLE_TEST_INPUT=ON' '-DOBS_BUILD_NUMBER=1' '-DOBS_VERSION_OVERRIDE=32.2.2-dodeca'` | 0, MSVC 기본 옵션과 링커 경로 정상 생성 |
| `cmake --build --preset windows-x64 --parallel 2 -- /nodeReuse:false /p:CL_MPCount=2` | 최종 종료 코드 **0** |
| `cmake --install build_x64 --prefix build_x64/install --config RelWithDebInfo` | **0**, 작업 폴더에 설치 |
| `ctest --test-dir build_x64 -C RelWithDebInfo -N` | **0**, `audio-tracks` 1개 등록 |
| `ctest --test-dir build_x64 -C RelWithDebInfo --output-on-failure` | **0**, `audio-tracks` **1/1 통과**, 0.18초 |
| 수정한 C++ 파일 2개의 clang-format 22.1.3 `--dry-run --Werror` | **0** |
| ZIP CRC·전체 압축 해제·설치 원본과 파일 내용 비교 | **통과**, 2,072개 파일 |
| 압축 해제한 `obs64.exe --portable --version` | **0**, `OBS Studio - 32.2.2-dodeca` |

CMake·CTest는 증거 루트의 가상환경에 설치한 4.4.3 실행 파일을 사용했다. CTest 실행 시 `build_x64/install/bin/64bit`를 PATH 앞에 추가했다. ZIP 실행 검사는 PATH를 압축 해제한 `bin/64bit`와 Windows 시스템 경로로만 제한했다. 이 검사는 주 실행 파일과 시작 시 필요한 DLL 로드 확인이며, 플러그인 전체 로드나 GUI 기능 검사를 대신하지 않는다. 버전 조회는 설정 디렉터리를 생성하지 않았다.

### 산출물과 실행

- [Portable ZIP](../../artifacts/obs-studio-32.2.2-dodeca-windows-x64-portable.zip): **178,798,670 bytes** (약 179 MB), 압축 해제 후 436,749,456 bytes.
- [SHA-256 파일](../../artifacts/obs-studio-32.2.2-dodeca-windows-x64-portable.zip.sha256): `eb260a44aa185d7ccef4db8c2d83d4b5f7a74146f54506d41102f7e88e7917e3`.
- 새 폴더에 전체 압축을 풀고 `Start-OBS.bat`를 실행한다. 루트의 `portable_mode.txt`가 직접 `bin/64bit/obs64.exe`를 실행하는 경우에도 portable 모드를 지정한다.
- 설정은 해제한 폴더의 `config/obs-studio`에 저장된다. 개인 설정·시험 자동화용 웹소켓 설정은 포함하지 않았다. 시험 빌드의 자동 업데이트는 `disable_updater.txt`로 비활성화했다.
- 설치본의 `bin`, `data`, `obs-plugins`를 ZIP에 담았다. PDB 디버그 심볼은 로컬 빌드·설치본에 보관하고 ZIP에서는 제외했다. `test-input`과 브라우저를 포함한 기본 번들 모듈은 포함했다.

### 빌드를 막은 문제와 해결

첫 전체 빌드는 C4530/C2220으로 종료 코드 1을 반환했다. 컴파일러 탐지에 실패했던 캐시의 C/C++·링커 옵션이 모두 비어 있었다. 별도의 새 CMake 시험 구성에서는 정상 옵션이 생성됐고, OBS도 캐시를 보관한 뒤 `--fresh`로 구성하자 `/EHsc`, `/O2 /Ob1 /DNDEBUG`와 MSVC 링커 경로가 복원됐다. 경고를 무시하거나 모듈을 끄지 않았다.

이후 MSVC가 오디오 트랙 변경 코드의 정수 축소 변환을 검출했다. 아래의 C++ 수정 후 전체 빌드와 CTest가 통과했다. 최초 빌드, 캐시 복구 후 빌드, 최종 빌드의 로그를 각각 `build.*`, `build-after-fresh.*`, `build-final.*`로 보관했다. 원시 로그·패키징 스크립트·파일별 SHA-256은 증거 루트의 `portable-build/`에 있다.

## 설치 후 재부팅 없는 도구 점검

사용자가 Visual Studio Community 2026을 설치한 뒤 재부팅 없이 도구 사용 가능 여부를 확인했다. 다른 작업을 진행 중이라는 조건에 맞춰 작은 시험 프로그램을 병렬 2개로 빌드하고 OBS는 구성 단계까지 실행했다.

| 확인 항목 | 결과 |
| --- | --- |
| Visual Studio | Community 2026 `18.10.12201.205`, 경로 `C:/Program Files/Microsoft Visual Studio/18/Community` |
| 설치 상태 | `isComplete=true`, `isLaunchable=true`, `isRebootRequired=false` |
| C/C++ 컴파일러 | MSVC `19.51.36257.0`, 도구 디렉터리 `14.51.36231` |
| MSBuild | `18.10.1.42706` |
| 작은 시험 구성·빌드·실행 | CMake 4.4.3, VS 2026 generator, SDK `10.0.26100.0`, `RelWithDebInfo`에서 모두 종료 코드 **0** |
| 실제 실행 | C 프로그램 및 Windows 리소스를 포함한 C++20 프로그램 **2/2 통과** |
| OBS preset 구성 | 기존 `windows-x64`, 시험 옵션 ON, `32.2.2-dodeca`로 **종료 코드 0**, `build_x64` 프로젝트 생성 완료 |
| 준비된 의존성 | preset의 obs-deps/Qt `2026-07-15`, Qt `6.11.1`, FFmpeg `8.1`, CEF `127.145.7`(배포 번들 `6533` revision 2) |
| 번들 모듈 | 브라우저·프런트엔드·오디오 관련 기본 모듈 활성화. 구성 출력의 비활성 모듈은 기존 `obs-libfdk`이며 추가로 끈 모듈은 없음 |

처음에는 샌드박스에서 MSBuild의 `FileTracker`가 `E_ACCESSDENIED`로 실패해 CMake가 컴파일러를 찾지 못했다고 보고했다. 컴파일러 자체는 실행됐으며, 준비된 동일 시험과 OBS 구성을 허용된 샌드박스 외부 실행으로 다시 수행하자 통과했다. 재부팅이나 재설치로 해결한 결과가 아니다.

증거는 아래 원시 증거 루트의 `toolchain-after-install/`에 있다. `vswhere.*`, `smoke-{configure,build,test}-unsandboxed.*`, `obs-configure-unsandboxed.*`에 실제 인자·종료 코드·stdout/stderr를 기록했다. 이 도구 점검 단계의 CTest 2개는 OBS의 `audio-tracks` 회귀 검사와 별개다. 이후 전체 빌드·설치·오디오 CTest 결과는 위 절에 기록했다.

## 최초 체크아웃과 설치 전 환경

- 작업 위치: `C:/Users/monun/proj/obs-studio-dodeca`의 NTFS 체크아웃. 이 세션에서 WSL 실행이나 별도 소스 복사는 하지 않았다.
- 브랜치: `feat/twelve-audio-tracks`, HEAD: `2bbadcd3651ea9ef09748f525c2548b733593b7b` (`feat: 독립 오디오 트랙을 12개로 확장`).
- 수정 전 구현·검증 파일 **48/48개의 SHA-256**이 [Linux 검증 당시 기록](linux-validation-summary.json)과 일치했다. OpenSpec proposal/design/tasks 및 세 capability 명세도 존재하며 읽었다.
- 시작부터 Unix 빌드/형식 스크립트의 실행 권한 변경, 심볼릭 링크의 빈 일반 파일 전환, obs-browser/obs-websocket 내부 스크립트 권한 변경이 있었다. 원래 diff를 보관했고 작업 후에도 동일함을 확인했다. 이 변경들은 수정하지 않았다.
- 이번 세션의 명령, 종료 코드, 환경, 최종 소스 해시는 [Windows 요약 JSON](windows-validation-summary.json)에 있다. Linux의 과거 해시 기록은 덮어쓰지 않았다.

| 항목 | 확인 결과 |
| --- | --- |
| Windows | x64, 25H2, 빌드 `26200.9445` (레지스트리 조회) |
| CPU | Intel Core Ultra 7 270K Plus, 논리 CPU 24개 |
| GPU / 드라이버 | NVIDIA GeForce RTX 5090 / `32.0.15.9649`; Parsec Virtual Display Adapter / `0.45.0.0` |
| 셸 | 네이티브 Windows PowerShell `5.1.26100.9444` |
| Visual Studio | Build Tools 2022 `17.14.37502.11`만 발견. VS 2026 없음 |
| Windows SDK | `10.0.26100.0`의 Include, x64 `rc.exe`, `kernel32.lib`, `ucrt.lib` 확인 |
| 초기 CMake | VS 2022 번들의 `3.31.6-msvc6`; 기본 PATH에는 없음 |
| 검증용 CMake | 프로젝트 내 가상환경에 `4.4.3` 설치, VS 2026 generator 지원 확인 |
| Python / 시험 패키지 | Python `3.10.11`, numpy `2.2.6`, websocket-client `1.9.2`; 기본 텍스트 인코딩 `cp949` |
| 분석용 FFmpeg / ffprobe | `8.0.1-essentials_build-www.gyan.dev`; OBS에 링크한 라이브러리 버전은 아님 |
| OBS 의존성 / Qt / CEF | preset 선언은 obs-deps/Qt `2026-07-15`, CEF `6533` Windows x64 revision 2. 구성 실패로 다운로드·링크·로드 버전은 미확인 |

환경 식별에 사용한 Python/Windows 레지스트리의 ProductName은 `Windows 10 Pro`로 반환된다. 실제 빌드 식별에는 함께 기록한 DisplayVersion과 CurrentBuild/UBR을 사용했다. 샌드박스에서 CIM 조회는 접근 거절되어 레지스트리로 확인했다.

## 최초 빌드 시도와 중단 원인

기존 `windows-x64` preset의 generator, SDK, `RelWithDebInfo`, 기본 `ENABLE_BROWSER=ON`을 유지했다. 비활성화한 번들 모듈은 없다. 구성 실패로 libobs, 프런트엔드, test-input, obs-ffmpeg, obs-outputs, obs-websocket, 브라우저를 포함한 모든 모듈의 빌드·실행 상태는 **미검증**이다.

VS 2026 generator는 [CMake 4.2에서 추가](https://cmake.org/cmake/help/v4.2/generator/Visual%20Studio%2018%202026.html)되었다. 초기 CMake 3.31.6은 generator를 만들지 못했다. 이후 가상환경에 준비한 CMake 4.4.3은 preset을 읽었지만 다음 오류로 종료 코드 **1**을 반환했다.

```text
CMake Error at CMakeLists.txt:5 (project):
  Generator
    Visual Studio 18 2026
  could not find any instance of Visual Studio.
```

구성 성공이 선행되어야 하므로 빌드·설치·CTest 실행을 진행하지 않았다. `audio-tracks` CTest 등록·실행 성공도 주장하지 않는다. OBS 실행 파일을 만들지 못했으므로 portable OBS를 시작하거나 네트워크 수신기·인증 없는 웹소켓 서버를 열지 않았다. 기존 `%APPDATA%/obs-studio`도 사용하지 않았다.

### 주요 명령과 종료 코드

아래는 저장소 루트 기준이다. 실제 실행 인자는 요약 JSON의 `commands`와 원시 로그 옆의 `*.command.json`에 보관했다.

```powershell
$Evidence = 'build_windows_validation/2026-09-15'
$Python = "$Evidence/venv/Scripts/python.exe"
$CMake = "$Evidence/venv/Lib/site-packages/cmake/data/bin/cmake.exe"
```

| 명령 | 종료 코드 / 결과 |
| --- | --- |
| `vswhere -all -products '*' -utf8 -format json` | 0, VS 2022 한 설치만 확인 |
| VS 번들 `cmake --version`, `cmake --help` | 각 0, 3.31.6 및 VS 2026 generator 부재 확인 |
| `python -m venv build_windows_validation/2026-09-15/venv` | 0 |
| `& $Python -m pip install --disable-pip-version-check --no-cache-dir numpy websocket-client 'cmake>=4.2,<5'` | 0 |
| `& $CMake --version`, `& $CMake --help`, `& $CMake --list-presets` | 각 0 |
| `& $CMake --preset windows-x64 '-DENABLE_AUDIO_TRACK_TESTS=ON' '-DENABLE_TEST_INPUT=ON' '-DOBS_BUILD_NUMBER=1' '-DOBS_VERSION_OVERRIDE=32.2.2-dodeca'` | **1**, VS 2026 미설치 |
| `python -m unittest discover -s test/audio-tracks -p 'test_*.py' -v` | **0**, 회귀 검사 4개 통과 |
| `openspec validate expand-audio-tracks-to-twelve --type change --strict --no-interactive` | **0**; 설치된 OpenSpec의 Node 진입점으로 실행 |
| `git -c core.safecrlf=false diff --check` | **0** |

## 발견한 문제와 수정

### 1. 한글 경로의 시험 설정 인코딩

`prepare.py`의 `Path.write_text()`가 한국어 Windows 기본 CP949를 사용해 한글 녹화 경로를 저장했다. OBS 설정 읽기는 `libobs/util/config-file.c`의 `os_fread_utf8()`을 사용한다. 생성한 6·12트랙 프로필을 UTF-8로 읽는 회귀 검사에서 모두 `UnicodeDecodeError`를 재현했다.

시험 설정의 INI/JSON 저장 인코딩을 UTF-8로 명시했다. 수정 후 회귀 검사가 통과했고, 별도 점검에서 ASCII/한글 경로 × 6/12트랙 네 조합의 경로·설정·브리지 JSON과 기존 설정 덮어쓰기 거절을 확인했다. 이 검사는 설정 파일 생성 검사이며 OBS의 실제 프로필 로드 검사는 아니다.

### 2. FFmpeg 8의 첫 AAC 패킷 길이 생략

합성 AAC/MKV를 ffprobe 8.0.1로 읽으면 첫 패킷이 PTS `-0.021`이고 `duration_time=N/A`인 경우가 재현됐다. 기존 `verify_continuity.py`는 이를 실수로 변환하다 중단됐다.

첫 패킷·음수 PTS·AAC-LC·`initial_padding=1024` 조건이 모두 확인될 때만 1024 샘플과 실제 sample rate로 길이를 계산하도록 수정했다. 추론한 횟수를 `inferred_priming_durations`에 남기며, 그 밖의 알 수 없는 길이는 거절한다. 다음 패킷까지의 간격 검사도 유지한다. ffprobe 프로세스는 오류 때에도 닫고 회수한다.

정상 MKV/MP4의 패킷 검사가 통과했다. 실제로 첫 트랙의 패킷 하나를 제거한 MKV는 약 **22ms의 간격 오류**로 거절됐고, 회귀 검사에서도 priming 직후 누락과 다른 위치의 알 수 없는 길이를 거절했다.

### 3. PowerShell 명령 예제

PowerShell 5.1이 따옴표 없는 `-DOBS_VERSION_OVERRIDE=32.2.2-dodeca`를 `-DOBS_VERSION_OVERRIDE=32`, `.2.2-dodeca`로 나누는 것을 실제 인자 로그로 확인했다. Windows 실행 프롬프트의 `-D` 인자를 따옴표로 감싸고 CMake 4.2 이상 요구사항을 명시했다.

이 단계에서는 C/C++ 구현과 preset을 변경하지 않았다. 이후 실제 Windows 빌드에서 확인한 C++ 수정은 다음과 같다.

### 4. MSVC가 검출한 정수 축소 변환

`frontend/settings/OBSBasicSettings.cpp`의 트랙 수 집계는 `size_t`를 반환하지만 `uint32_t`에 저장하고, 리플레이 비트레이트 계산에서는 `int`에 암묵적으로 저장해 C4267/C2220이 발생했다. 집계값은 반환 타입으로 유지하고 비트레이트 곱셈에 쓰는 0~12 범위의 트랙 수만 명시적으로 `int`로 변환했다.

`test/audio-tracks/audio-tracks.cpp`도 신호와 JSON의 64비트 정수를 `uint32_t`에 저장해 C4244/C2220이 발생했다. 반환값을 축소하지 않고 비교하도록 수정했다. 변경한 두 파일의 clang-format 22.1.3 검사, 전체 Windows 빌드와 기존 오디오 CTest가 통과했다.

플랫폼 preset과 코어 오디오 구현은 변경하지 않았다. 이번 C++·Python 수정을 Linux/macOS에서 재실행하지 않았으며 과거 플랫폼 검증을 이번 수정의 실행 결과로 간주하지 않는다.

## 빌드 없이 실행한 파일 분석 점검

**아래 파일은 FFmpeg CLI로 생성한 4초 합성 오디오이며 OBS 출력물이 아니다.** 각 트랙은 48kHz 스테레오, 300~1400Hz 시험음, 1초 주기의 게이트를 사용한다. MP4의 이름은 양성 대조군을 만들기 위해 CLI의 `handler_name` 메타데이터로 명시했다.

| 항목 | 결과 |
| --- | --- |
| AAC/MKV와 MP4 | 각각 오디오 스트림 12개, 파일 크기 526,895 / 535,029 bytes |
| 각 트랙 디코딩·주파수·순서·이름 | 통과, `Track01`~`Track12` |
| 다른 시험음의 최대 누설 | 약 -42.64dB, 검사 기준 -35dB 이하 |
| 트랙 간 게이트 동기 | 0ms |
| 패킷 연속성 | 수정 후 양쪽 통과, 트랙마다 189개 패킷; MKV는 트랙당 첫 패킷 길이 1회 추론 |
| 리먹스 대조군 | 트랙마다 189개 압축 패킷의 SHA-256·순서·이름 일치, 상대 시간 최대 차이 약 0.5ms |
| 고의로 패킷 하나를 제거한 MKV | 종료 코드 1로 거절, `missing or overlapping packet` |
| 기타 정적 검사 | 수정 전 48개 해시 일치, 수정 후 Python 21개 문법·Qt UI XML 2개 파싱·OpenSpec strict·diff 공백 검사 통과 |

영상이 없는 대조군이므로 A/V 동기, OBS 믹서 배정, 인코더 연결, UI, 리플레이, OBS 자체 리먹스는 검사하지 않았다.

## 실제 Windows OBS 검사 상태

아래 기능 검사는 **미실행**이다. 빌드·CTest·ZIP 실행 파일 확인은 완료했으며, 사용자가 portable ZIP으로 직접 시험하기로 했다.

| 범위 | 남은 실행 |
| --- | --- |
| 필수 흐름 | 12트랙 AAC/MKV, 리플레이 두 번, OBS 메뉴 수동 리먹스·자동 리먹스, 실제 파일 디코딩·패킷 비교 |
| 선택·재시작 | 1·7·12, 12개→12번만, 리플레이 7·12, 일시정지/재개·분할 |
| 출력 매트릭스 | 간단 AAC/Opus, 고급 MKV/MP4/Fragmented/Hybrid MP4/MOV, Opus/MKV, 사용자 지정 FFmpeg MKV/MP4, FLV 12번 |
| 방송 | 주 12/VOD 11, 둘 다 12, VOD 미지원, 간단 주 1/VOD 2, 동시 방송 중 녹화·리플레이 재시작, SRT/RIST 6개 허용·7개 거절 |
| UI·원격 제어 | 영어/한국어 100%/200%, 10~12번 표시·키보드·접근성, 웹소켓 조회/변경/이벤트와 실제 출력 일치 |
| 보존 | 기존 6트랙 장면·무배정·프로필 값, 새 소스·프로필 기본값, 10~12번 설정의 전환·재시작 보존 |
| 장시간·성능 | Windows 1/6/12트랙 비교 및 30분 이상 녹화·6트랙 기준 비교 |

## 증거 위치와 재개 조건

원시 증거 루트: `C:/Users/monun/proj/obs-studio-dodeca/build_windows_validation/2026-09-15/`.

- 환경·수정 전 해시: `preflight.json`; 최초 작업 상태: `git-{status,head,branch,diff,submodules}.*`.
- 빌드 실패: `configure-native.{command.json,stdout.log,stderr.log}`. 초기 구형 CMake/PowerShell 인자 오류도 별도 로그로 남아 있다.
- 회귀 검사: `prepare-regression-before.*`, `prepare-regression-after.*`, `python-regressions.*`, `prepare-after/result.json`.
- 미디어: `synthetic-ffmpeg/control12.{mkv,mp4}`, `{mkv,mp4}-inspection.json`, `mkv-continuity.json`, `mp4-continuity-after.json`, `remux.json`.
- ffprobe 전체 결과: `control-{mkv,mp4}-ffprobe.stdout.log`. 실제 누락 검출: `control-missing-packet-copyts-rejected.stderr.log`.
- Windows 전체 빌드·설치·CTest·ZIP 검사: `portable-build/{configure-fresh,build-final,install,ctest,package,zip-runtime}.*`; 상세 패키지/파일 해시: `package-result.json`, `package-manifest.json`.
- OBS GUI 로그·UI 스크린샷: **없음(GUI를 시작하지 않음)**. 실행 파일 버전 조회 결과는 `portable-build/zip-runtime-result.json`에 있다.

가상환경·미디어·원시 로그·빌드 캐시는 루트 `.gitignore`의 허용 목록 밖에 있으며 Git에 추가하지 않았다. 커밋·푸시·PR 생성·OpenSpec 보관도 하지 않았다.

Portable ZIP을 사용해 [Windows 실행 프롬프트](windows-validation-prompt.md)의 실제 OBS 기능 검사를 진행할 수 있다. 필수 녹화·리플레이·리먹스·방송 선택·UI 검사가 모두 통과해야만 7.4를 완료 처리한다.
