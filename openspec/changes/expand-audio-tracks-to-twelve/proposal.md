## Why

OBS Studio 32.2.2의 독립 오디오 트랙 6개로는 마이크·게임·음악 등 여러 소스를 편집용으로 충분히 분리해 녹화하기 어렵다. Windows·macOS·Linux에서 최대 12개 트랙을 녹화하고 리플레이 저장과 MKV→MP4 리먹스까지 유지할 수 있도록 확장한다.

## What Changes

- 독립 오디오 믹스와 출력 오디오 인코더의 최대 수를 6개에서 12개로 확장한다. 각 트랙의 모노·스테레오·서라운드 채널 구성은 기존과 같다.
- 고급 오디오 속성의 소스별 트랙 배정, 다중 트랙 녹화 선택, 트랙 이름·비트레이트, 설정 저장·복원과 리플레이 버퍼 용량 계산을 1~12번에 맞춘다.
- 새 오디오 소스는 1~12번에 모두 연결한다. 기존 장면은 유효했던 1~6번 배정을 보존하고 7~12번은 끈다. 확장 버전에서 저장한 장면은 12개 배정을 그대로 복원한다.
- 기본 녹화 선택은 기존처럼 1번 트랙을 유지한다. 다중 트랙을 지원하는 일반 녹화와 사용자 지정 FFmpeg 파일 출력에서 최대 12개를 선택할 수 있게 한다. 기존 단일 트랙 전용 모드와 형식의 제약은 유지한다.
- 일반 녹화, 지원되는 리플레이 버퍼, 수동·자동 MKV→MP4 리먹스에서 선택한 모든 트랙의 오디오와 순서를 보존한다. FFmpeg 경로와 OBS 자체 Hybrid MP4/MOV 경로를 각각 검증한다.
- 기존 고급 출력의 방송·VOD 트랙 선택 범위를 1~12번으로 넓힌다. 방송의 동시 전송 수는 늘리지 않는다. SRT/RIST의 기존 다중 오디오 선택은 12개 후보 중 최대 6개로 제한한다.
- 번들 obs-websocket의 트랙 조회·부분 변경·변경 이벤트에 7~12번을 포함한다.
- **BREAKING**: 공개 `obs_source_audio_mix` 구조체 크기와 오디오 관련 컴파일 상수 계약이 달라진다. libobs와 번들 모듈을 함께 빌드하며, 추가 플러그인의 기존 바이너리 호환은 이번 범위에 포함하지 않는다.

## Capabilities

### New Capabilities

- `audio-track-routing`: 12개 독립 믹스, 새 소스 기본 배정, 기존 장면 이전 및 12개 배정의 저장·복원, 번들 원격 제어.
- `audio-track-configuration`: 세 운영체제의 트랙 UI, 프로필 설정, 이름·비트레이트, 출력 제약과 방송·VOD 선택.
- `multitrack-recording`: 최대 12트랙 녹화·리플레이·리먹스와 오디오 분리, 순서, 시간 동기 보존.

### Modified Capabilities

없음. 현재 OpenSpec에 등록된 기존 capability가 없다.

## Impact

- **코어:** `libobs/media-io/audio-io.*`, `libobs/obs-output.*`, `libobs/obs-source.*`, `libobs/obs.c`, 오디오를 렌더링하는 장면·전환·번들 소스.
- **프런트엔드:** `frontend/components/OBSAdvAudioCtrl.*`, `frontend/settings/OBSBasicSettings*`, 관련 Qt 폼, `frontend/utility/{AdvancedOutput,SimpleOutput}.*`, 프로필 기본값과 번역 문자열.
- **출력 및 연동:** `plugins/obs-ffmpeg`, `plugins/obs-outputs`의 MP4/FLV/RTMP 경로, `libobs/media-io/media-remux.c`, `plugins/obs-websocket`.
- **의존성:** 조사한 코드와 FFmpeg 6.1.1의 12개 스테레오 AAC 트랙 실험에서 MKV 생성 및 MP4 리먹스 가능성을 확인했다. FFmpeg 라이브러리 자체의 수정·버전 교체는 계획하지 않는다. 실제 OBS와 각 플랫폼의 번들 의존성에 대한 통합 검증은 구현 단계에 수행한다.
- **검증:** 세 운영체제 빌드·실행, 12개 서로 다른 신호의 녹화와 리플레이·리먹스, 기존 6트랙 장면 이전, 방송과 녹화 동시 실행, 설정·UI·원격 제어 회귀 검증을 포함한다.
- **범위 제외:** 한 트랙의 물리 채널을 12개로 늘리는 기능, 새로운 캡처 장치 지원, 방송 동시 트랙 수 증가, 추가 플러그인 호환 보장, 새 코덱·컨테이너 도입, 설치·업데이트·서명·배포 체계 변경.
