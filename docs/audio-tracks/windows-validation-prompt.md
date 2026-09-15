# Windows 세션 실행 프롬프트

아래 내용을 Windows의 코딩 에이전트 세션에 전달한다. 이 파일을 읽고 실행하라는 요청만 해도 된다.

---

이 저장소의 **독립 오디오 트랙 6 → 12 확장**을 Windows에서 빌드하고 실제 OBS로 검증하라.
구현을 진행한 환경은 WSL이며 Windows 검증은 이 세션에 위임되었다. 계획만 제시하지 말고 가능한 검사를 실행하고, 발견한 범위 내 결함을 수정한 뒤 관련 검사를 다시 실행하라.

## 1. 작업 상태와 환경 확인

- 저장소의 `AGENTS.md`를 읽고, `git status --short`, 현재 브랜치와 diff를 확인한다. 구현 브랜치는 `feat/twelve-audio-tracks`다. upstream 원격 clone에는 이 변경이 없을 수 있으므로 **WSL 작업 브랜치의 구현 커밋과 테스트 파일까지** 가져왔는지 확인한다. 추가 미커밋 변경이 있다면 함께 확인하고 기존 수정은 보존한다.
- `openspec/changes/expand-audio-tracks-to-twelve/{proposal,design,tasks}.md`와 그 안의 `specs/`를 읽는다. 명세는 구현과 함께 Git으로 관리한다. 파일이 없다면 작업 브랜치에서 가져온다. 명세를 확보하지 못하면 이 문서와 `docs/audio-tracks/README.md`를 기준으로 검증하되 명세 체크를 했다고 보고하지 않는다.
- 12는 트랙 수다. 각 트랙의 스테레오/서라운드 채널 수는 기존 그대로다. 녹화·리플레이·MKV → MP4 리먹스를 대상으로 한다. 고급 방송 주 트랙/VOD 후보는 1~12지만 전송 개수는 유지한다. SRT/RIST는 12개 후보 중 최대 6개다. 제삼자 플러그인 바이너리 호환은 범위 밖이다.
- Windows 네이티브 PowerShell과 도구를 사용한다. WSL에서 Windows 실행 성공을 대신 추정하지 않는다. UNC/WSL 경로에 소스가 있다면 사용자 작업을 덮어쓰지 않는 새 NTFS 작업 디렉터리에 작업 브랜치를 가져오고, 추가 작업 파일이 있다면 함께 옮긴다. 원본 경로·복사 경로를 기록한다. 기존 `.git`, 빌드 디렉터리와 의존성 캐시를 무작정 복사하거나 삭제하지 않는다.
- `CMakePresets.json`과 `.github/scripts/Build-Windows.ps1`, `.github/scripts/.Wingetfile`을 현재 체크아웃에서 확인한다. 작성 시 x64 preset은 **Visual Studio 18 2026**, Windows SDK **10.0.26100.0**, `RelWithDebInfo`를 사용한다. 해당 generator에는 [CMake 4.2 이상](https://cmake.org/cmake/help/v4.2/generator/Visual%20Studio%2018%202026.html)이 필요하다. preset을 과거 VS 버전으로 조용히 바꾸지 않는다. `cmake --version`, `cmake --help`, `vswhere`로 실제 설치를 확인한다. 도구가 없으면 정확한 누락 항목을 보고하고 가능한 비의존 검사를 계속한다.
- CMake가 준비하는 OBS 의존성/Qt/CEF 버전을 사용한다. FFmpeg 실행 파일(`ffmpeg`, `ffprobe`)과 Python 3도 확인한다. Python 시험 의존성은 별도 가상환경에 `numpy`, `websocket-client`를 설치한다. 임의의 PyQt6 wheel을 OBS 프로세스에 로드하면 Qt 버전이 충돌할 수 있으므로 UI 자동화는 버전 호환이 확인된 경우에만 쓰고, 그 외에는 실제 UI로 검사한다.

## 2. 기존 preset으로 빌드와 CTest

저장소 루트에서 실행한다. 네이티브 명령마다 종료 코드를 확인하고 stdout/stderr를 결과 디렉터리에 보관한다.

```powershell
$ErrorActionPreference = 'Stop'
cmake --preset windows-x64 '-DENABLE_AUDIO_TRACK_TESTS=ON' '-DENABLE_TEST_INPUT=ON' '-DOBS_BUILD_NUMBER=1' '-DOBS_VERSION_OVERRIDE=32.2.2-dodeca'
if ($LASTEXITCODE) { throw 'CMake configure failed' }
cmake --build --preset windows-x64 --parallel
if ($LASTEXITCODE) { throw 'Build failed' }
cmake --install build_x64 --prefix build_x64/install --config RelWithDebInfo
if ($LASTEXITCODE) { throw 'Install failed' }
$env:PATH = (Join-Path (Get-Location) 'build_x64/install/bin/64bit') + ';' + $env:PATH
ctest --test-dir build_x64 -C RelWithDebInfo -N
ctest --test-dir build_x64 -C RelWithDebInfo --output-on-failure
if ($LASTEXITCODE) { throw 'CTest failed' }
```

`ENABLE_BROWSER` 등 기본 번들 모듈을 유지한 전체 빌드를 우선한다. 환경상 모듈을 껐다면 이유와 미검증 범위를 별도로 기록한다. 테스트 DLL 탐색 오류는 실제 설치 경로와 DLL 의존성을 확인해 해결한다. CTest 목록에 `audio-tracks`가 있고 실제 실행되는지 확인한다.

Windows PowerShell 5.1은 따옴표 없는 `-DOBS_VERSION_OVERRIDE=32.2.2-dodeca`를 두 인자로 나눌 수 있으므로 위 명령의 따옴표를 유지한다. 빌드 도구와 무관하게 시험 설정의 한글 경로·UTF-8 저장은 `python -m unittest discover -s test/audio-tracks -p test_prepare.py -v`로 확인할 수 있다.

VS와 컴파일러가 설치되어 있는데도 CMake가 컴파일러를 찾지 못하면 `CMakeFiles/CMakeConfigureLog.yaml`의 실제 원인을 확인한다. 샌드박스의 MSBuild `FileTracker`에서 `E_ACCESSDENIED`가 발생한 경우에는 설치·재부팅 문제로 단정하지 말고, 허용된 실행 권한으로 같은 구성을 다시 확인한다.

컴파일러 탐지에 실패했던 빌드 디렉터리를 재사용하면 `CMakeCache.txt`의 `CMAKE_CXX_FLAGS`와 구성별 최적화 옵션이 빈 값으로 남을 수 있다. 실제로 `/EHsc` 누락에 따른 C4530/C2220 오류가 발생하면 캐시를 보관하고 위 구성 명령에 `--fresh`를 추가해 기본 옵션을 다시 생성한다. 이 세션에서는 `/EHsc`, `/O2 /Ob1 /DNDEBUG`와 MSVC 링커 경로가 복원됐다. 경고 검사나 번들 모듈을 끄는 방식으로 처리하지 않는다.

## 3. 기존 사용자 설정과 분리하여 OBS 실행

- 설치 산출물을 새 테스트 디렉터리로 배치하고 Windows OBS의 `--portable` 모드로 실행한다. 평소 사용하는 OBS의 `%APPDATA%/obs-studio`를 변경하지 않는다. 새 테스트 복사본에만 설정·스크립트·녹화 파일을 만든다.
- `test/audio-tracks/prepare.py`는 `<directory>/obs-studio` 구조를 만든다. portable OBS가 사용하는 `<portable-root>/config/obs-studio`에 맞춰 새 `<portable-root>/config`를 인자로 전달한다. 예:

```powershell
python test/audio-tracks/prepare.py C:/obs-dodeca-test/config C:/obs-dodeca-test/recordings
```

- portable 루트에는 빌드의 `bin`, `data`, `obs-plugins` 구조가 있어야 한다. 실행 파일은 보통 `bin/64bit/obs64.exe`다. 실제 설치 트리를 확인한 뒤 그 디렉터리를 작업 디렉터리로 실행한다. **`test/audio-tracks/launch.py`는 Linux 전용이므로 그대로 실행하지 않는다.**
- 시험 설정의 obs-websocket은 인증 없는 로컬 자동화용이다. Windows에서는 서버가 외부 인터페이스에도 열릴 수 있으므로 테스트 인스턴스에 대한 인바운드 네트워크 접근을 차단하고 로컬 연결만 사용한다. 기존 방송 서비스 계정과 키를 가져오지 않는다.
- 버전과 로드된 `test-input`, `obs-ffmpeg`, `obs-outputs`, `obs-websocket`을 OBS 로그로 확인한다. 창이 열리는 것만으로 실행 검증을 완료 처리하지 않는다.

## 4. 실제 파일 및 UI 검증

기본 시험 장면은 640×360/30fps, 48kHz 스테레오, 트랙 1~12에 각각 300~1400Hz의 서로 다른 시험음, 1초마다 변하는 영상/오디오 동기 표시다.

```powershell
python test/audio-tracks/integration.py --seconds 20 --replay --report C:/obs-dodeca-test/recording.json
python test/audio-tracks/verify_media.py C:/obs-dodeca-test/recordings/실제파일.mkv --video-sync --report C:/obs-dodeca-test/inspection.json
```

보고서의 실제 녹화 및 리플레이 경로를 사용한다. `ffprobe -show_streams -show_format -of json` 결과도 보관한다. 단순 스트림 수 외에 모든 트랙을 디코딩해 음의 정체·분리·순서·이름·시간 관계를 확인한다.

- **필수 Windows 검사:** AAC/MKV 12트랙 녹화, 리플레이 두 번 저장, OBS 메뉴의 수동 MKV → MP4 리먹스, 자동 리먹스. MP4의 `handler_name`에 트랙 이름이 유지되는지 확인한다. 입력/출력 오디오 패킷 해시가 같아 재인코딩하지 않았는지도 검사한다.
- **선택과 재시작:** 1·7·12만 선택하면 그 순서의 3개 스트림, 12개를 녹화한 다음 12번만 선택하면 정확히 1개 스트림. 리플레이 재시작에서 7·12 두 트랙. 녹화 일시정지/재개와 지원 형식의 파일 분할에서도 동일하게 확인한다.
- **출력 매트릭스:** 간단 AAC/Opus 다중 녹화, 고급 MKV/일반 MP4/Fragmented MP4/Hybrid MP4/Hybrid MOV, Opus/MKV, 사용자 지정 FFmpeg AAC/MKV·AAC/MP4, 일반 FLV의 12번 단독. 형식 자체의 기존 제한은 유지한다.
- **방송:** 외부 서비스로 송출하지 않고 로컬 수신기 또는 출력 인코더 구성으로 검사한다. 고급 주 12/VOD 11, 둘 다 12, VOD 미지원 서비스, 간단 모드 주 1/VOD 2를 검사한다. 방송·녹화·리플레이를 동시에 켰다가 녹화/리플레이만 재시작해도 방송 선택이 유지되어야 한다. SRT/RIST 1·2·3·7·11·12는 허용, 7개 선택은 UI 및 외부 수정 프로필 양쪽에서 명확히 거절되어야 한다.
- **UI:** 영어와 한국어, Windows 배율 100%/200%에서 고급 오디오 속성, 간단/고급 녹화, 사용자 지정 FFmpeg, FLV, 방송/VOD, 고급 오디오 이름·비트레이트를 검사한다. 트랙 번호 선택은 1~12번이 한 행으로 표시되고, 좁은 창에서는 가로 스크롤로 10~12번까지 접근되며 탭·스페이스·라디오 좌우 화살표 키로 선택되는지 확인한다. 접근성 검사 도구 또는 Windows 내레이터로 번호를 구분할 수 있어야 한다. 12번 체크를 바꾸면 obs-websocket 조회/이벤트와 실제 출력이 일치해야 한다.
- **보존:** 기존 6트랙 장면의 1~6 배정, 명시적 무배정과 프로필 이름/비트레이트는 유지되고 7~12는 꺼져야 한다. 새 소스의 기본 배정은 12개 모두 켜짐, 새 녹화 프로필 기본 선택은 1번이다. 10~12의 이름/비트레이트, 주/VOD 선택은 설정 재열기·프로필 전환·OBS 재시작 후 유지되어야 한다.
- **장시간/성능:** 여건이 되면 같은 장면의 1/6/12트랙 CPU·메모리·파일 크기와 30분 이상 녹화의 초반/중반/후반 동기를 검사한다. 수행하지 않은 항목은 실행하지 않았다고 기록한다.

## 5. 결과와 인계

- `docs/audio-tracks/windows-validation-results.md`에 날짜, Windows/CPU/GPU/드라이버, 커밋과 작업 diff 상태, 도구·Qt·FFmpeg 버전, 정확한 명령/종료 코드, 활성·비활성 모듈, 각 검사 결과, 로그·ffprobe·분석 JSON·스크린샷 경로를 기록한다. 대용량 녹화 파일을 Git에 넣지 않는다.
- 발견한 결함은 관련 코드와 테스트를 수정하고 해당 빌드/실행 검사를 다시 한다. 변경이 없는 Linux/macOS에서 통과했다고 추정하지 않는다.
- `openspec/.../tasks.md`가 있다면 실제 통과한 항목만 갱신한다. 특히 **7.4는 Windows 필수 빌드와 실행/UI 검사가 모두 끝난 뒤** 체크한다. macOS 7.5는 Windows 결과로 체크하지 않는다.
- 최종 답변은 한국어로 빌드 결과, 실제 12트랙 검증 결과, 수정 사항, 남은 검증을 구분해 간결히 보고한다. 요청 없이 커밋·푸시·PR 생성·OpenSpec 보관은 하지 않는다.
