## Purpose

선택한 최대 12개 독립 오디오 트랙을 녹화 파일과 리플레이에 담고, MKV에서 MP4로 리먹스한 뒤에도 편집에 사용할 수 있도록 보존한다. 파일의 트랙 수뿐 아니라 신호 분리, 번호 순서, 이름, 시간 정보가 유지되는지를 계약으로 정의한다.

## ADDED Requirements

### Requirement: Record up to twelve selected audio tracks

시스템은 기존에 다중 오디오 트랙을 지원하는 녹화 경로에서 최대 12개의 선택된 트랙을 녹화할 수 있어야 한다(SHALL). 간단 출력의 다중 트랙 녹화 품질과 고급 일반 녹화, 호환되는 사용자 지정 FFmpeg 파일 출력이 이 요구사항을 충족해야 한다(SHALL). 각 경로의 기존 코덱·컨테이너 지원 조건은 유지해야 한다(SHALL).

#### Scenario: Record twelve stereo AAC tracks

- **WHEN** 서로 구분되는 시험음을 배정한 1~12번을 모두 선택하고 지원되는 AAC/MKV 녹화를 실행한 뒤 정상 종료한다
- **THEN** 파일에 오디오 트랙이 정확히 12개 존재하고 모든 트랙에 디코딩 가능한 오디오 데이터가 있다
- **AND** 각 트랙은 해당 번호에 배정한 시험음만 포함한다

#### Scenario: MP4 recording paths

- **WHEN** 기존에 지원되는 일반 MP4, Fragmented MP4 또는 Hybrid MP4 경로에서 12트랙 AAC 녹화를 정상 종료한다
- **THEN** 각각의 파일에서 12개 트랙의 오디오가 재생·추출 가능하다
- **AND** Hybrid MOV 등 같은 구현을 공유하는 기존 다중 트랙 경로도 7~12번 때문에 중단되거나 누락되지 않는다

#### Scenario: Custom FFmpeg file output

- **WHEN** 사용자 지정 FFmpeg 녹화에서 기존에 지원되는 AAC/MKV 또는 AAC/MP4 조합과 12개 트랙을 선택한다
- **THEN** 선택한 12개 믹스가 각각 별도 오디오 스트림으로 저장된다

### Requirement: Preserve selected-track identity and order

출력 파일은 선택된 트랙만 원래 OBS 트랙 번호의 오름차순으로 포함해야 한다(SHALL). 인코더 슬롯 또는 파일 스트림 번호가 재배치돼도 원래 믹스와 해당 출력 모드가 제공하는 트랙 이름·비트레이트 설정의 연결을 유지해야 한다(SHALL). 트랙 이름은 해당 형식이 지원하는 메타데이터로 보존해야 한다(SHALL).

#### Scenario: Sparse selection across the old boundary

- **WHEN** 서로 다른 이름·지원 비트레이트·시험음을 가진 1·7·12번만 녹화한다
- **THEN** 정확히 세 개의 오디오 스트림이 1·7·12번 순서로 저장된다
- **AND** 각 스트림의 오디오와 이름 및 인코딩 설정이 원래 트랙에 대응한다

#### Scenario: Only track twelve selected

- **WHEN** 12번만 녹화한다
- **THEN** 첫 번째이자 유일한 파일 오디오 스트림에 12번 믹스가 저장된다
- **AND** 1~11번의 빈 스트림을 추가하지 않는다

#### Scenario: Reduce the selection between recordings

- **WHEN** 12개 트랙 녹화를 종료한 뒤 선택을 12번 하나로 줄여 다시 녹화한다
- **THEN** 두 번째 파일에는 12번 오디오 스트림만 있다
- **AND** 이전 녹화의 인코더 연결 때문에 다른 트랙이 남지 않는다

### Requirement: Replay buffers retain the configured audio tracks

기존에 리플레이 버퍼를 지원하는 녹화 모드에서 시스템은 현재 녹화 설정의 최대 12개 트랙을 버퍼에 보관하고 저장해야 한다(SHALL). 저장된 리플레이의 트랙 집합·순서·이름은 해당 녹화 설정과 일치해야 한다(SHALL).

#### Scenario: Save a twelve-track replay

- **WHEN** 12개 트랙으로 리플레이 버퍼를 시작하고 충분한 오디오가 쌓인 뒤 저장한다
- **THEN** 저장된 리플레이에 12개 트랙이 모두 포함되고 영상과 같은 구간을 표현한다
- **AND** 상위 트랙의 타임스탬프나 버퍼 처리 때문에 트랙이 누락되지 않는다

#### Scenario: Restart a replay buffer with fewer tracks

- **WHEN** 버퍼를 중지하고 선택을 7·12번으로 바꾼 뒤 다시 시작해 저장한다
- **THEN** 저장 파일에는 7·12번에 대응하는 두 트랙만 존재한다

### Requirement: Remux all twelve tracks from MKV to MP4

수동 및 자동 MKV→MP4 리먹스는 원본의 모든 선택된 오디오 트랙을 재인코딩 없이 보존해야 한다(SHALL). 트랙 순서와 오디오 신호, MP4에서 표현 가능한 트랙 이름 및 시간 관계를 유지해야 한다(SHALL).

#### Scenario: Manual remux

- **WHEN** 12개 AAC 트랙을 포함한 MKV 녹화 파일을 OBS의 수동 리먹스로 MP4로 변환한다
- **THEN** MP4에 12개 트랙이 동일한 순서로 존재하고 모든 트랙이 디코딩 가능하다
- **AND** 트랙별 오디오 내용과 표현 가능한 이름이 유지된다

#### Scenario: Automatic remux

- **WHEN** 자동 리먹스를 켠 상태에서 12트랙 MKV 녹화를 정상 종료한다
- **THEN** 생성된 MP4에도 12개 트랙이 모두 유지된다

### Requirement: Maintain audio continuity and synchronization

시스템은 트랙 수를 늘려도 각 트랙의 연속성과 설정된 영상·오디오 시간 관계를 유지해야 한다(SHALL). 지원되는 일시정지·재개와 파일 분할은 선택한 모든 트랙에 일관되게 적용돼야 한다(SHALL).

#### Scenario: Long recording of synchronized sources

- **WHEN** 동기화된 합성 영상과 오디오로 12트랙 녹화를 30분 이상 실행한다
- **THEN** 7~12번을 포함한 모든 트랙에서 시간 경과에 따른 추가 동기 오차나 데이터 누락이 발생하지 않는다
- **AND** 같은 조건의 기존 6트랙 기준 결과와 비교해 트랙 확장으로 인한 누적 드리프트가 없다

#### Scenario: Pause or split a supported recording

- **WHEN** 해당 기능을 지원하는 12트랙 녹화에서 일시정지·재개 또는 파일 분할을 수행한다
- **THEN** 모든 선택된 트랙이 같은 녹화 구간을 유지한다
- **AND** 분할 파일마다 같은 오디오 트랙 집합과 순서가 유지된다

### Requirement: Coexist with streaming on all target platforms

12트랙 녹화와 지원되는 리플레이 버퍼는 Windows·macOS·Linux에서 동작해야 한다(SHALL). 방송과 동시에 실행해도 녹화 트랙이 누락되거나 방송·VOD 믹스에 다른 트랙이 섞여서는 안 된다(MUST NOT).

#### Scenario: Stream and record different track selections

- **WHEN** 방송은 12번, 지원되는 VOD는 11번을 사용하면서 1~12번 녹화와 지원되는 리플레이 버퍼를 함께 실행한다
- **THEN** 녹화·리플레이에는 각각 12개 트랙이 보존된다
- **AND** 방송·VOD는 각자 선택한 믹스와 기존 전송 트랙 수를 유지한다

#### Scenario: Native platform verification

- **WHEN** 동일한 검증 장면을 Windows·macOS·Linux의 확장 빌드에서 각각 녹화·리플레이 저장·리먹스한다
- **THEN** 각 운영체제에서 트랙 수·순서·신호 분리·재생 가능성 요구사항을 충족한다
