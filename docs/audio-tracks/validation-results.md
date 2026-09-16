# 12트랙 확장 검증 결과

## 2026-09-16 추가 변경 이후 확인

본체 업데이트를 제외한 현재 코드는 기존 Ubuntu 24.04 검증 이미지에서 `ENABLE_BROWSER=OFF`, `ENABLE_WHATSNEW=ON`으로 전체 빌드·설치와 Xvfb CTest `audio-tracks` 1/1을 통과했다. CEF 배포본이 없어 브라우저 ON 구성은 실패했으며 해당 GUI 검증은 남아 있다. 이전 상세 녹화·UI·장시간 결과는 이번 변경으로 재실행한 것으로 간주하지 않는다.

현재 코드와 실행 증거는 [Linux 요약 JSON](linux-validation-summary.json)의 `application_updates_followup`에 추가했고 아래의 이전 기록은 보존했다. 같은 변경의 Windows 짧은 12트랙 녹화·portable GUI 결과 및 일반 모드 설정 격리 실패는 [Windows 기록](windows-validation-results.md)과 [본체 업데이트 문서](../application-updates.md)에 구분했다.

검증일: 2026-09-15. 기준은 OBS 32.2.2 커밋 `ba2f32bdf791005443988a4955e963663e16b1ed`에 `feat/twelve-audio-tracks`의 변경을 적용한 작업 파일이다. 검증은 커밋 전에 수행했으며, 당시 구현·테스트 파일의 SHA-256은 [검증 요약 JSON](linux-validation-summary.json)에 기록했다. Windows·macOS 실기 검증은 아직 수행하지 않았다.

## 환경과 재현 위치

- WSL2 호스트의 Ubuntu 24.04.4 Docker 컨테이너, GCC 13, CMake 3.28, Ninja, Qt 6.4.2, FFmpeg 6.1.1.
- Intel Core Ultra 7 270K Plus, 논리 CPU 24개, 메모리 약 32GB. Xvfb 2560×1440, Mesa llvmpipe 소프트웨어 렌더링.
- 기존 `ubuntu` Debug preset으로 libobs, 프런트엔드와 관련 번들 모듈을 빌드했다. preset의 AJA/WebRTC 비활성화와 로컬 CEF 부재에 따른 `ENABLE_BROWSER=OFF`를 사용했다. NVIDIA·DeckLink 등 실제 장치가 필요한 기능은 실기 검증하지 않았다.
- 시험 설정: 640×360, 30fps, 48kHz 스테레오, 서로 다른 12개 시험음, x264. CTest 및 `test-input`은 opt-in이다.
- 컨테이너 `obs-dodeca-ui`의 `/work`는 호스트 `/tmp/obs-dodeca-build`, `/baseline`은 `/tmp/obs-dodeca-baseline`이다. 아래 증거 경로는 컨테이너 기준이다. 주요 수치는 [검증 요약 JSON](linux-validation-summary.json)에도 보관한다. 녹화·상세 JSON·스크린샷은 해당 임시 디렉터리에 보관했다.
- 재현 명령과 의존성은 [사용·검증 안내](README.md) 및 `test/audio-tracks/Dockerfile`에 있다. UI 자동화는 별도 프로필과 obs-websocket, OBS와 같은 Qt를 사용하는 PyQt6에서 실행했다. 실제 송출은 네트워크를 차단한 컨테이너의 loopback 수신기만 사용했다.

## 빌드와 기능 검사

| 범위 | 결과 | 증거 / 실행기 |
| --- | --- | --- |
| Linux 빌드·CTest | 통과, `audio-tracks` 1/1 | `/work/build/Testing/Temporary/LastTest.log` |
| 기본 배정·유효 마스크·12번째 출력 슬롯 | 통과 | CTest `audio-tracks` |
| 구 장면 11가지 로드·저장·재로드·복제 | 통과 | `fixtures/legacy-sources.json`, CTest |
| obs-websocket 12키 조회·부분 변경·이벤트·비-boolean 요청 원자적 거절 | 통과 | `integration.py`, `/work/buffered-recording.json` |
| 기존/새 프로필 기본값, 10~12 이름·비트레이트·선택 저장 | 통과 | `/work/buffered-profiles.json`, `/work/buffered-ui-regression-final.json` |
| 중첩 장면·전환·7번 음소거·12번 gain/sync offset | 통과 | `/work/routing-fixed/routing.json` |
| UI 빈 녹화/FFmpeg 선택 경고, FLV 단일 선택, 코덱 변경·서비스 제어 상태 | 통과 | `/work/buffered-ui-regression-final.json`, `/work/buffered-ui-modes-final.json` |
| 선택 비트레이트에 따른 용량 추정 | 통과 | 1·7·12 선택의 리플레이 112MiB → 12 해제 시 94MiB, 방송 주 12/VOD 11 지연 추정 111MB, 간단 모드 VOD 켜짐 99MB / 꺼짐 87MB |
| 영어·한국어 100%/200% | 통과 | `/work/ui-{en,ko}-{100,200}.json`, `/work/buffered-ui/*.png` |
| 다른 언어의 기존 번역과 새 키 대체 표시 | 통과 | `/work/ui-de-100.json`: 기존 `Spur 1`~`Spur 6`, 새 `Track 7`~`Track 12` |
| 키보드·접근성 | 통과 | 12개 체크박스 탭/스페이스, 2행 라디오 화살표 이동, 이름·비트레이트의 12번까지 자동 스크롤, 소스명+트랙명 접근성 이름 |

UI 검사는 Qt 위젯의 실제 보이는 영역·최소 크기·배율을 검사하고 스크린샷도 확인했다. Windows 내레이터나 macOS VoiceOver 검사를 대신하지 않는다.

### 출력 매트릭스

모든 파일의 각 오디오 스트림을 디코딩해 300~1400Hz의 배정·순서와 다른 시험음의 누설을 검사했다. 일반 트랙 이름도 검사했다. 트랙 간 동기 기준은 AAC 한 프레임(48kHz에서 약 21.33ms) 또는 Opus 한 프레임(20ms)에 컨테이너 시간 단위와 1ms 측정 분해능을 더한 값이다. 영상 비교에는 영상 한 프레임을 추가한다.

| 출력 | 선택 | 결과 / 증거 |
| --- | --- | --- |
| 고급 AAC/MKV | 1~12 | 통과, `/work/buffered-matrix/mkv12.json` |
| 일반 / Fragmented / Hybrid MP4 | 각각 1~12 | 통과, `/work/buffered-matrix/{mp4,fragmented_mp4,hybrid_mp4}.json` |
| Hybrid MOV | 1~12 | 통과, `/work/buffered-matrix/hybrid_mov.json` |
| 고급 Opus/MKV | 1~12 | 통과, `/work/buffered-matrix/opus_mkv.json` |
| 간단 AAC / Opus 다중 녹화 | 각각 1~12 | 통과, `/work/buffered-matrix/simple_{aac,opus}.json` |
| 일반 FLV | 12만 | 통과, `/work/buffered-matrix/flv12.json` |
| 사용자 지정 FFmpeg AAC/MKV·AAC/MP4 | 각각 1~12 및 12만 | 통과, `/work/buffered-custom/custom_*.json` |
| 희소 선택 | 1·7·12 | 통과, `/work/sparse-inspection.json` |
| 같은 출력 객체의 재시작 | 12개 → 12만 | 통과, `/work/buffered-scenarios/scenarios.json` |
| 리플레이 반복 저장·재시작 | 12개 두 번 → 7·12 | 통과, 같은 `scenarios.json` |
| 일시정지·재개, Hybrid MP4/MOV 수동 분할 | 12개 | 통과, 같은 `scenarios.json` |
| OBS 수동·자동 AAC/MKV → MP4 리먹스 | 12개 | 통과, 같은 `scenarios.json`: 패킷별 SHA-256, 스트림 순서·이름·시간 관계 보존 |

### 방송

`/work/buffered-streaming/streaming.json`에서 다음을 확인했다.

- 고급 주 12/VOD 11: 실제 출력 인코더의 믹스 12·11, 주 트랙 수신음 1400Hz. 동시에 12트랙 녹화·리플레이를 시작·중지·재시작해도 방송은 계속되고 선택이 유지됨.
- 주/VOD 모두 12: 하나의 오디오 인코더. VOD 미지원 서비스도 주 12 하나.
- 간단 출력: 주 1/VOD 2 유지, 주 트랙 수신음 300Hz.
- SRT: 1·2·3·7·11·12 여섯 스트림을 실제 수신·디코딩하여 주파수와 연결 순서 확인.
- UI의 일곱 번째 선택 비활성화, 강제로 만든 7개 선택 저장 거절, 외부 수정 프로필의 방송 시작 거절 확인. 영어·한국어 모두 최대 6개라는 설명이 나옴. `/work/stream-limit.json`, `/work/ui-ko-stream-limit.json`.

수신 FFmpeg 6.1은 OBS의 VOD용 Enhanced RTMP 오디오 태그를 디코딩하지 못한다. 따라서 RTMP **주 트랙은 실제 수신·디코딩**, VOD는 **OBS 출력에 연결된 인코더·믹스와 중복 제거**로 확인했다. 외부 방송 서비스의 VOD 생성이나 Multitrack Video 서버 협상은 실행하지 않았다. RIST는 SRT와 공유하는 선택·시작 검증 코드를 확인했으며 별도 RIST 수신은 실행하지 않았다.

## 장시간 동기와 성능

200ms 선행 버퍼를 적용한 **12트랙 1810초 녹화가 통과**했다. 0·900·1800초부터 각각 8초 동안 모든 트랙을 디코딩했으며 트랙 간 차이는 모두 **0ms**였다. 영상과의 최대 차이는 각각 33.67·12.67·12.67ms로 허용 범위 안이었다.

전체 파일에는 트랙마다 84,844개의 AAC 패킷이 있었고, 시작 -0.021초·마지막 1809.963초가 모든 트랙에서 같았다. 모든 패킷의 시간은 증가했고, 시간 단위 반올림에 따른 최대 간격 차이는 약 1ms였다. 증거: `/work/buffered-long-{recording,inspection,continuity}.json`, 약 461MB의 MKV 파일.

원본 **6트랙 1810초 비교 녹화도 통과**했다. 같은 0·900·1800초 구간의 트랙 간 차이는 모두 **0ms**, 영상과의 최대 차이는 34·13·13ms였다. 각 트랙에 84,845개 패킷이 있었고 시작·종료 시간과 연속성이 일치했다. 두 녹화의 종료 시점은 약 한 AAC 프레임 차이가 있으며, 각 파일 안에서는 모든 트랙의 패킷 수가 같다. 이 조건에서 12트랙 확장에 따른 추가 누적 드리프트나 트랙별 패킷 누락은 관찰되지 않았다. 증거: `/baseline/buffered-{recording,inspection,continuity}.json`.

30초씩 같은 12소스 장면에서 녹화 선택만 바꾼 측정값은 다음과 같다. AAC는 트랙당 160kbps이다. `/work/performance/performance.json`.

| 녹화 트랙 수 | 평균 OBS CPU | 평균 OBS 메모리 | 파일 크기 |
| --- | ---: | ---: | ---: |
| 1 | 1.668% | 405.695MB | 4,070,756 bytes |
| 6 | 1.898% | 407.368MB | 5,700,187 bytes |
| 12 | 2.059% | 411.043MB | 7,645,208 bytes |

CPU는 OBS의 기기 전체 기준 보고값이다. 낮은 해상도의 합성 장면·소프트웨어 렌더러·단일 측정이므로 실제 게임 녹화 성능이나 장치별 부하를 일반화하지 않는다.

### 시험 입력과 발견한 기존 동작

- 초기 동기 시험 소스는 늦게 깨어난 오디오 스레드의 시계를 과거 영상 시간으로 되돌렸다. 이로 인해 입력 타임스탬프가 뒤로 가는 현상이 있어, **검증용 소스만** 연속 샘플 시계로 수정했다.
- 선행 버퍼 없는 10ms 생산 주기의 시험에서는 12트랙 파일 후반에 최대 42ms, 원본 6트랙 파일에서도 최대 64ms의 트랙 간 오차가 관찰됐다. 오디오 패킷의 타임스탬프가 연속이라는 사실만으로 PCM 내용의 동기가 맞는 것은 아니었다. 이 시험은 통과로 처리하지 않았다.
- 최종 비교는 양쪽 빌드에 동일한 **200ms 선행 입력**을 제공해 실행기 스케줄링 지연을 흡수한다. 원본 6트랙 빌드도 12개 입력 스레드를 유지하고 뒤의 여섯 소스만 무배정으로 둔다. 원본에는 시험 소스 변경만 적용했다. 이 비교는 안정된 입력에서의 확장 효과를 검사하며, 모든 실제 장치의 동기나 선행 버퍼 없는 WSL 부하 상황을 보장하지 않는다. 프로덕션 오디오 타이밍 코드는 변경하지 않았다.
- 동기 오프셋 시험은 기존 1ms 설정을 100ms로 변경해 정확한 100ms 이동을 확인했다. 원본 `obs-source.c`의 0→비제로 오프셋 실시간 적용 조건은 이번 변경에서 수정하지 않았다.

### 사용자 지정 FFmpeg 출력의 종료 구간

지연이 있는 사용자 지정 x264 인코더의 8초 파일에서는 오디오 약 7.914초, 디코딩 영상 약 7.233초가 관찰됐다. 마지막 오디오 동기 표시가 이미 끝난 영상의 이전 표시와 비교되어 약 2초 오차로 보고되던 검사기를 수정했다. 두 스트림이 함께 존재하는 구간의 동기는 약 16ms였으며, 검사기는 공통 구간과 비교한 표시 개수를 보고한다. 사용자 지정 FFmpeg 경로의 기존 종료 시 인코더 지연 처리는 변경하지 않았다.

### 긴 MOV 이름

Hybrid MOV는 한 바이트 길이의 handler 필드에 최대 255바이트를 UTF-8 문자 경계에 맞춰 기록하고 원래 이름은 별도 트랙 메타데이터에 보존한다. MP4의 handler 이름은 전체 문자열을 기록한다.

FFmpeg 6.1의 MOV 읽기 코드는 Pascal 길이를 부호 있는 `char`로 비교하므로, 이 환경에서는 128바이트 이상 이름 앞에 잘못된 문자가 표시됐다. 이는 파일의 길이·UTF-8 경계 오류와 구분했다. [FFmpeg 6.1.1의 `mov_read_hdlr`](https://github.com/FFmpeg/FFmpeg/blob/n6.1.1/libavformat/mov.c#L688).

`metadata.py`에서 465바이트의 한글·이모지 이름을 검사했다. MOV에는 UTF-8 문자 경계를 지킨 253바이트 handler와 원래 메타데이터가, MP4에는 전체 465바이트 handler가 보존됐다. 실제 필드 바이트와 오디오 디코딩 검사가 통과했다. 증거: `/work/buffered-metadata/{hybrid_mov,hybrid_mp4}.json`. MOV의 긴 이름이 모든 편집기/ffprobe에서 그대로 표시된다고 주장하지 않는다.

## 최종 설치본 확인

`cmake --install /work/build` 후 같은 설치 위치에서 다시 실행해 20초 12트랙 MKV, 리플레이 두 번 저장, MP4 리먹스를 재검사했다. 모든 오디오 트랙의 디코딩·이름·동기가 통과했고, 리먹스는 12개 트랙의 모든 압축 패킷·이름·상대 시간을 보존했다. 증거: `/work/final-{recording,inspection,remux-inspection,mp4-inspection}.json`, `/work/final-obs.log`.

## 최종 코드 점검

오디오 경로의 배열·순회는 `MAX_AUDIO_MIXES` 또는 `MAX_OUTPUT_AUDIO_ENCODERS`를 따르는지 확인했다. 남긴 6은 구버전 배정의 6비트, SRT/RIST 동시 트랙 제한, UI 한 행의 여섯 열이다. 서라운드 채널·프로토콜 비트 필드와 버전 번호의 6은 독립 트랙 수와 무관하다. 인코더 이름의 고정 버퍼는 동적 문자열로 교체했다.

clang-format 22.1.3, gersemi 0.25.0, Python 문법, Qt 폼 XML, `git diff --check`, OpenSpec strict 검증이 통과했다.

## 남은 플랫폼 검증

- **Windows:** 2026-09-15 Community 2026 설치 후 재부팅 없이 기존 preset의 전체 빌드·설치·오디오 CTest 1/1이 통과했다. CMake 캐시를 복구하고, 설정 화면·회귀 테스트의 MSVC 정수 변환 경고를 수정했다. 시험 설정 인코딩과 FFmpeg 8 패킷 분석 문제도 수정·검증했다. 이후 사용자 요청으로 트랙 번호 선택을 한 행으로 바꾸고 빌드·CTest·새 portable ZIP 검사를 통과했다. 실제 녹화·리플레이·리먹스와 새 배치의 UI 검사는 남아 있으며 OpenSpec 7.4 미완료다. [Windows 결과와 최신 ZIP](windows-validation-results.md), [실행 절차](windows-validation-prompt.md)를 참고한다.
- **macOS:** 사용할 환경이 없어 네이티브 빌드·실행·UI를 검사하지 않았다. OpenSpec 7.5 미완료.
- 제삼자 플러그인의 기존 바이너리 호환은 합의한 범위 밖이다.
