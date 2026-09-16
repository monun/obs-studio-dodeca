# 프로젝트 지침

## 범위와 동작

- OBS 32.2.2 기반으로 독립 오디오 믹스·녹화 트랙을 12개로 확장한 프로젝트다. 트랙 내부의 스테레오·서라운드 채널 수(`MAX_AUDIO_CHANNELS`)와 구분한다.
- 새 소스는 1~12번 모두 켜며, 새 녹화 프로필은 1번만 선택한다. 기존 장면은 유효했던 1~6번 배정과 명시적 무배정을 보존한다.
- 고급 방송·VOD는 1~12번 중 선택한다. SRT/RIST의 동시 전송은 최대 6개이며, 간단 방송의 주 1/VOD 2 배정은 유지한다.
- 공개 오디오 구조체 크기가 바뀌므로 libobs·프런트엔드·번들 모듈을 함께 다시 빌드한다. 기존 제삼자 플러그인 바이너리 호환은 검증 범위 밖이다.
- 명세와 진행 상태는 `openspec/changes/expand-audio-tracks-to-twelve/`에 있다. Linux 결과로 Windows·macOS 검증 항목을 완료 처리하지 않는다.
- `README.rst`는 한국어 다음 영어 순서로 간결하게 유지한다. OBS Studio Dodeca 이름, 32.2.2 기반 포크와 원본 저장소, 12트랙 확장과 `gpt-6-astra` 수정 사실, Windows 빌드 필수 요소와 명령을 안내한다.

## 코드 위치와 주의점

- `libobs/media-io/audio-io.h`, `libobs/obs-output.h`: 믹스·출력 인코더 용량과 유효 비트 집합.
- `libobs/obs.c`: 소스 저장 표식 `dodeca_audio_tracks_version: 1`과 구버전 6비트 배정 이전. `obs-source.c`는 새 소스 기본값과 배정 변경 API의 유효 범위를 처리한다.
- `frontend/utility/AudioTracks.hpp`: 트랙 선택 집계와 방송 동시 수 제한. 설정 화면과 고급 오디오 속성은 12개 위젯 컬렉션을 사용한다.
- `AdvancedOutput.cpp`, `SimpleOutput.cpp`: 선택한 믹스를 오름차순의 연속 출력 슬롯에 연결한다. 재시작 시 이전 연결을 정리하되 동작 중인 출력·공유 인코더의 연결은 보존한다.
- `plugins/obs-ffmpeg/`, `plugins/obs-outputs/mp4-mux.c`, `libobs/media-io/media-remux.c`: 파일 출력·리플레이·리먹스 및 트랙 이름 메타데이터 경로. MKV의 `title`과 MP4/MOV의 `handler_name` 표현 차이를 고려한다.
- 트랙 번호 선택은 고급 오디오 속성과 녹화·방송·VOD 화면에서 1~12번을 한 행에 배치한다. 좁은 창에서는 기존 스크롤로 접근한다.
- 남은 상수 6은 구버전 배정이나 방송 동시 수 제한일 수 있다. 공간 채널 수나 프로토콜 필드까지 일괄 치환하지 않는다.

## 빌드와 검증

- OBS 원본의 GitHub Actions 워크플로는 제거했다. upstream 갱신 시 `.github/workflows/`의 자동 실행이 다시 추가되는지 확인한다. 로컬 빌드 스크립트와 CMake preset은 유지한다.
- 재현 명령·의존성·실행기 사용법: `docs/audio-tracks/README.md`, `test/audio-tracks/Dockerfile`.
- 기존 플랫폼 CMake preset을 사용한다. `ENABLE_AUDIO_TRACK_TESTS=ON`, `ENABLE_TEST_INPUT=ON`은 검증할 때만 켠다. 일반 빌드에서는 기본 OFF다.
- Windows `windows-x64` preset은 Visual Studio 2026과 CMake 4.2 이상이 필요하다. PowerShell 5.1에서는 `'-DOBS_VERSION_OVERRIDE=32.2.2-dodeca'`처럼 점을 포함한 CMake 인수를 따옴표로 감싼다.
- Windows의 MSBuild FileTracker `E_ACCESSDENIED`는 실행 환경의 권한을 먼저 확인한다. 실패한 컴파일러 탐지 뒤 CMake 플래그가 비어 있으면 캐시를 보존하고 기존 옵션으로 `--fresh` 구성한다. C++ `/EHsc`와 RelWithDebInfo `/O2 /Ob1 /DNDEBUG`가 복원됐는지 확인한다.
- 코어 회귀 검사: `ctest --test-dir <build-dir> --output-on-failure`. Visual Studio 같은 다중 구성 빌드는 `-C RelWithDebInfo`를 추가한다. Linux headless 환경에서는 `xvfb-run -a`로 실행한다.
- Windows 설치 prefix는 작업 공간 안에 지정하고, CTest 실행 시 해당 설치의 `bin/64bit`를 `PATH` 앞에 추가해 DLL을 찾게 한다.
- C/C++ 형식은 clang-format 22.1.3, CMake 형식은 gersemi 0.25.0을 사용한다.
- 명세 검사: `openspec validate expand-audio-tracks-to-twelve --type change --strict --no-interactive`.
- Windows 네이티브 검증은 `docs/audio-tracks/windows-validation-prompt.md`를 따른다. 실제 플랫폼별 실행 결과와 제한은 `docs/audio-tracks/validation-results.md`와 OpenSpec 작업 목록을 확인한다.
- Windows portable ZIP은 같은 설치의 `bin/`, `data/`, `obs-plugins/`와 루트의 `portable_mode.txt`를 포함한다. ZIP 무결성 및 `obs64 --portable --version` 성공과 실제 GUI·녹화 검증 결과를 각각 기록한다.

## 시험 실행과 인계

- UI 자동화는 별도 시험 설정과 loopback 수신기를 사용한다. OBS와 UI 브리지의 PyQt6가 같은 Qt 라이브러리를 사용해야 한다.
- 같은 OBS를 조작하는 실행기는 순서대로 실행한다. 긴 도구 호출이 중간 출력을 반환해도 실행 완료가 아닐 수 있다. 실제 종료 코드를 확인한 뒤 프로필을 바꾸거나 OBS를 종료한다.
- 설치 prefix와 실행 위치를 일치시켜 서로 다른 빌드의 플러그인이 중복 로드되지 않게 한다. OBS INI는 `key=value`로 작성한다(`configparser` 사용 시 `space_around_delimiters=False`). 한국어 Windows의 기본 인코딩에 의존하지 않도록 시험 INI·JSON은 UTF-8을 명시해 저장한다.
- 파일 검사는 스트림 개수뿐 아니라 각 트랙의 디코딩·시험음 분리·이름·내용 동기와 패킷 연속성을 확인한다. 30분 기준 비교는 양쪽 빌드에 같은 200ms 선행 입력을 제공한다. 버퍼 없는 시험에서 관찰한 기존 드리프트와 사용자 지정 FFmpeg 종료 구간 등의 제한은 검증 결과 문서에 남긴다.
- 검증 당시 구현·테스트 파일의 SHA-256은 `docs/audio-tracks/`의 `linux-validation-summary.json`과 `windows-validation-summary.json`에 있다. 코드가 바뀌면 영향받는 플랫폼의 검사를 실행하고 해당 결과를 갱신하며, 다른 플랫폼의 이전 검증 기록은 보존한다.
- 사용자 설정으로 실행하거나 구 OBS로 롤백하기 전 장면 모음과 프로필을 함께 백업한다. 대용량 녹화·스크린샷·의존성 캐시·개인 설정은 Git에 넣지 않는다.
- 루트 `.gitignore`는 허용 목록 방식이다. 새 최상위 파일·디렉터리를 추가하면 의도한 파일이 추적되는지 확인한다. `AGENTS.md`와 `openspec/`는 구현 및 Windows 인계 문서와 함께 관리한다.
