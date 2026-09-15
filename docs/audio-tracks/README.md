# 독립 오디오 트랙 12개

이 변경은 OBS 32.2.2의 소스별 오디오 믹스와 녹화 트랙을 6개에서 **12개**로 확장한다. 각 트랙 안의 스테레오/서라운드 채널 수는 기존과 같다.

## 설정 방법

1. **고급 오디오 속성**에서 각 소스를 보낼 트랙을 선택한다. 체크박스는 1~6, 7~12의 두 행이다. 예를 들어 마이크는 12번, 게임은 7번, 전체 소리를 합친 트랙은 1번에 배정한다.
2. **설정 → 출력 → 녹화**에서 파일에 저장할 트랙을 고른다. 고급 출력의 **오디오** 탭에서 각 트랙의 이름과 비트레이트를 지정할 수 있다.
3. 독립 트랙 녹화에는 MKV 또는 지원되는 MP4/MOV 형식을 사용한다. OBS의 수동·자동 MKV → MP4 리먹스는 모든 트랙을 복사하며, MP4에서는 트랙 이름이 `handler_name`으로 표현된다.
4. 편집기에서 각 오디오 스트림을 불러온다. 재생기는 여러 오디오 트랙 중 하나만 재생할 수 있으므로 재생기에서 들리는 소리만으로 나머지 트랙의 유무를 판단하지 않는다.

1·7·12번만 선택하면 파일에는 그 순서의 **3개 오디오 스트림**이 생긴다. 파일의 세 번째 오디오 스트림은 OBS의 12번 믹스다. 리플레이 버퍼는 녹화의 트랙 선택을 따른다.

Hybrid MOV의 handler 이름은 최대 255바이트를 UTF-8 문자 경계에 맞춰 기록하며, 원래 이름은 별도 메타데이터에 보존한다. FFmpeg 6.1에서는 128바이트 이상 MOV 이름의 표시 제약이 확인됐다. 자세한 내용은 [검증 결과](validation-results.md#긴-mov-이름)를 참고한다.

일반 FLV 녹화는 선택한 트랙 하나만 저장한다. 간단 출력의 방송과 방송과 동일한 품질/무손실 등 기존 단일 트랙 경로, 사용자 지정 FFmpeg의 리플레이 미지원 같은 형식·모드 제약은 유지한다.

### 새 소스와 기존 설정

- **새 소스:** 1~12번 모두 켜짐.
- **기존 장면:** 원래 유효했던 1~6번 배정을 유지하고 7~12번은 꺼짐. 구버전이 전체 배정으로 저장하던 `255`도 1~6번만 켜진다. 명시적 무배정 `0`은 그대로다.
- **새 녹화 프로필:** 기본 선택은 1번. 추가한 7~12번 비트레이트 기본값은 기존 트랙과 같은 160kbps다.
- **저장·재시작:** 새 버전에서 배정한 상위 트랙과 트랙 이름·비트레이트는 다시 불러와도 유지된다.

### 방송과 VOD

고급 출력의 주 방송 트랙과 지원 서비스의 VOD 트랙을 각각 1~12번에서 선택할 수 있다. 주 12/VOD 11은 두 역할을 유지하며, 둘 다 12번이면 기존처럼 중복된 VOD 인코더를 연결하지 않는다. VOD 미지원 서비스에는 추가 트랙을 보내지 않는다. 간단 방송은 기존 주 1/VOD 2 배정을 사용한다.

SRT/RIST는 1~12 중 **동시에 최대 6개**를 선택한다. 6개를 선택하면 나머지 선택지가 비활성화되고, 프로필을 외부에서 수정해 7개 이상 요청해도 방송 시작을 거절한다. 12트랙 녹화를 위해 방송 프로토콜의 전송 개수를 늘리지는 않는다.

### obs-websocket

함께 빌드한 obs-websocket의 `GetInputAudioTracks`와 `InputAudioTracksChanged`는 문자열 키 `"1"`~`"12"`의 boolean 상태를 제공한다. `SetInputAudioTracks`는 전달한 키만 바꾼다.

```json
{
  "requestType": "SetInputAudioTracks",
  "requestData": {
    "inputName": "마이크",
    "inputAudioTracks": {"12": true}
  }
}
```

기존 클라이언트가 1~6번 키만 보내면 7~12번은 보존된다. `"12": 1`처럼 boolean이 아닌 값은 요청 전체를 거절한다. 조회 결과에 키가 추가되므로 클라이언트는 정확히 6개의 키가 있다고 가정하지 않아야 한다.

## 호환성과 롤백

libobs의 공개 오디오 구조체 크기가 바뀌므로 **libobs, 프런트엔드, 번들 모듈을 함께 다시 빌드**해야 한다.

기존 제삼자 플러그인 바이너리의 호환성은 보장하지 않으며 이번 검증 범위에서 제외한다.

처음 실행하기 전에 OBS를 종료하고 기존 **장면 모음과 프로필을 함께 백업**한다. 구 OBS로 돌아갈 때는 구 실행 파일과 함께 그 백업을 복원하는 방법을 권장한다. 상위 번호가 들어 있는 새 프로필을 구 OBS에 그대로 전달하면 녹화 선택이나 방송 트랙 인덱스를 올바르게 해석하지 못할 수 있다. 백업이 없다면 새 빌드에서 방송/VOD/FLV 선택을 1~6으로 옮기고, 소스·녹화·FFmpeg 선택도 1~6으로 조정하여 별도로 내보낸 뒤 구 버전에서 확인한다. 7~12번 정보는 구 버전에서 편집·저장하면 보존되지 않을 수 있다.

소스 저장 형식에는 `dodeca_audio_tracks_version: 1`과 정규화된 12비트 `mixers`를 기록한다. 표식이 없거나 알려지지 않은 표식이면 보수적으로 기존 6비트 배정을 사용한다. OBS의 기존 `prev_ver`와 오래된 모니터링 설정 이전 절차도 유지한다.

## 검증 실행

자동화는 **별도 시험 설정에서만** 실행한다. `test-input`과 Python UI 스크립트는 검증용이며 일반 배포에서는 기본 OFF다. 시험음은 200ms의 선행 데이터를 제공해 시험 실행기의 스케줄링 지연을 흡수한다. 실제 녹화 파일은 Git에 추가하지 않는다.

### Linux: 기존 ubuntu preset

검증에 사용한 의존성 목록은 `test/audio-tracks/Dockerfile`에 있다. Ubuntu 24.04의 Qt/FFmpeg 패키지를 이용하며, CEF가 없는 로컬 환경에서는 브라우저만 추가로 비활성화한다. 기본 ubuntu preset의 AJA/WebRTC 비활성화도 결과에 명시한다.

```sh
docker build -t obs-dodeca-test:local -f test/audio-tracks/Dockerfile test/audio-tracks
mkdir -p /tmp/obs-dodeca-verification
docker run --rm --init \
  -v "$PWD:/src:ro" -v /tmp/obs-dodeca-verification:/work -w /src \
  obs-dodeca-test:local cmake --preset ubuntu -B /work/build \
  -DOBS_VERSION_OVERRIDE=32.2.2-dodeca -DOBS_BUILD_NUMBER=1 \
  -DENABLE_BROWSER=OFF -DENABLE_TEST_INPUT=ON -DENABLE_AUDIO_TRACK_TESTS=ON \
  -DCMAKE_INSTALL_PREFIX=/work/install
docker run --rm --init \
  -v "$PWD:/src:ro" -v /tmp/obs-dodeca-verification:/work \
  obs-dodeca-test:local cmake --build /work/build --parallel
docker run --rm --init \
  -v "$PWD:/src:ro" -v /tmp/obs-dodeca-verification:/work \
  obs-dodeca-test:local cmake --install /work/build
docker run --rm --init \
  -v "$PWD:/src:ro" -v /tmp/obs-dodeca-verification:/work \
  obs-dodeca-test:local xvfb-run -a ctest --test-dir /work/build --output-on-failure
```

설치 prefix와 실행 위치를 일치시킨다. 같은 실행에서 서로 다른 버전의 플러그인 검색 경로를 함께 노출하지 않는다.

```sh
docker run -d --init --name obs-dodeca-verification --network none --shm-size=512m \
  -v "$PWD:/src:ro" -v /tmp/obs-dodeca-verification:/work \
  -e DISPLAY=:99 -e QT_QPA_PLATFORM=xcb -e LIBGL_ALWAYS_SOFTWARE=1 \
  obs-dodeca-test:local Xvfb :99 -screen 0 2560x1440x24 -nolisten tcp -ac
docker exec obs-dodeca-verification python3 /src/test/audio-tracks/prepare.py \
  /work/config /work/recordings --bridge /work/ui
docker exec obs-dodeca-verification python3 /src/test/audio-tracks/launch.py \
  /work/install /work/config /work/obs.log
docker exec obs-dodeca-verification python3 /src/test/audio-tracks/integration.py \
  --seconds 20 --replay --report /work/recording.json
docker exec obs-dodeca-verification python3 /src/test/audio-tracks/matrix.py /work/matrix
docker exec obs-dodeca-verification python3 /src/test/audio-tracks/matrix.py /work/custom \
  --cases custom_mkv,custom_mp4,custom_mkv_12,custom_mp4_12
docker exec obs-dodeca-verification python3 /src/test/audio-tracks/scenarios.py /work/scenarios
docker exec obs-dodeca-verification python3 /src/test/audio-tracks/routing.py /work/routing
docker exec obs-dodeca-verification python3 /src/test/audio-tracks/performance.py /work/performance
docker exec obs-dodeca-verification python3 /src/test/audio-tracks/streaming.py /work/streaming
docker exec obs-dodeca-verification python3 /src/test/audio-tracks/stream_limit.py /work/stream-limit.json
docker exec obs-dodeca-verification python3 /src/test/audio-tracks/ui_regression.py /work/ui-regression.json
docker exec obs-dodeca-verification python3 /src/test/audio-tracks/ui_modes.py /work/ui-modes.json
docker exec obs-dodeca-verification python3 /src/test/audio-tracks/profiles.py /work/profiles.json
docker exec obs-dodeca-verification python3 /src/test/audio-tracks/metadata.py /work/metadata
```

`matrix.py` 등 UI를 조작하는 실행기는 영어 UI를 전제로 한다. 순서대로 실행하고, 출력이 동작 중일 때 다른 실행기로 같은 프로필이나 소스를 수정하지 않는다. `ui_regression.py`는 시험 창에 키보드 포커스를 둔 상태에서 실행한다. 배율 검사는 OBS 종료 후 `launch.py --scale 2`로 다시 실행한다. `ui_layout.py report.json --locale ko-KR --scale 2`는 해당 언어·배율로 이미 실행된 OBS를 검사한다. 시험 설정의 `user.ini`에서 `[General]`의 `Language=ko-KR`를 지정한 뒤 재시작하거나 실제 언어 설정 UI를 사용한다. INI 키와 `=` 사이에 공백을 넣지 않는다. UI 브리지의 PyQt6는 OBS와 같은 Qt 라이브러리를 사용해야 한다.

### 파일 검사와 30분 시험

아래 `recording.mkv`는 실행 보고서에 기록된 실제 경로로 바꾼다. 희소 선택 파일은 `--tracks 1,7,12`처럼 원래 OBS 트랙 번호를 파일 순서대로 지정한다.

```sh
python3 test/audio-tracks/verify_media.py recording.mkv --video-sync --report inspection.json
python3 test/audio-tracks/verify_remux.py recording.mkv recording.mp4 --report remux.json
python3 test/audio-tracks/integration.py --seconds 1810 --report long-recording.json
python3 test/audio-tracks/verify_media.py recording.mkv --starts 0,900,1800 --video-sync --report long-inspection.json
python3 test/audio-tracks/verify_continuity.py recording.mkv --report continuity.json
```

파일 검사는 스트림 수뿐 아니라 모든 트랙의 주파수(300~1400Hz), 다른 시험음의 누설, 1초 동기 표시, 이름 및 압축 패킷을 검사한다. 트랙 간 시간 허용치는 코덱 한 프레임 + 컨테이너 시간 단위이며, 측정에는 1ms 분해능을 더한다. 영상 비교에는 영상 한 프레임을 추가한다. 전체 패킷 검사는 트랙별 개수·시작/종료 시간·연속성도 확인한다.

형식 검사에는 저장소가 요구하는 clang-format 22.1.3과 gersemi 0.25.0을 사용한다.

6트랙 기준 빌드는 원본 커밋 `ba2f32bdf791005443988a4955e963663e16b1ed`의 별도 체크아웃으로 만든다. 동일한 시험음을 위해 `test/test-input/sync-pair-aud.c`의 주파수 설정·연속 샘플 시계·선행 버퍼 변경만 기준 빌드에 적용하고 `ENABLE_TEST_INPUT=ON`으로 빌드한다. 새 시험 설정을 `prepare.py --tracks 6 --port 4477`로 생성하고 `integration.py --tracks 6 --sources 12 --port 4477`로 검사한다. 12개의 같은 입력 스레드를 유지하되 기준 빌드에서는 뒤의 여섯 소스를 무배정으로 둔다. 두 빌드의 설정·설치·포트는 분리한다.

### Windows와 macOS

Windows 작업자는 [Windows 세션 실행 프롬프트](windows-validation-prompt.md)를 실행한다. Windows 결과는 실제 네이티브 빌드와 실행 후 별도로 기록한다. macOS도 기존 preset과 실제 앱에서 같은 필수 흐름을 검사해야 한다. Linux 통과를 다른 플랫폼의 통과로 간주하지 않는다.

실행 결과와 제한은 [검증 결과](validation-results.md)에 기록한다.
