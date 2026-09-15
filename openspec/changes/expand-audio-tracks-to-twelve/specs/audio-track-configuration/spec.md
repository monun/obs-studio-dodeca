## Purpose

사용자가 운영체제와 출력 모드에 관계없이 지원되는 12개 오디오 트랙의 배정·녹화 선택·이름·비트레이트를 설정할 수 있게 한다. 기존 프로필을 보존하며 방송용 트랙 선택 범위와 실제 동시 전송 수를 구별한다.

## ADDED Requirements

### Requirement: Accessible configuration of twelve tracks

Windows·macOS·Linux의 고급 오디오 속성은 1~12번 배정을 표시해야 한다(SHALL). 다중 트랙을 지원하는 간단·고급 일반 녹화와 사용자 지정 FFmpeg 녹화의 트랙 선택도 1~12번을 제공해야 한다(SHALL). 모든 트랙은 마우스와 키보드로 접근 가능하고 구분되는 접근성 이름을 가져야 한다(SHALL).

고급 오디오 속성과 녹화·방송·VOD의 트랙 번호 선택은 1~12번을 오름차순의 한 행으로 표시해야 한다(SHALL). 창 너비가 부족하면 가로 스크롤과 키보드 이동으로 모든 번호에 접근할 수 있어야 한다(SHALL).

#### Scenario: Select tracks in one horizontal row

- **WHEN** 사용자가 고급 오디오 속성 또는 녹화·방송·VOD의 트랙 번호 선택을 연다
- **THEN** 1~12번이 한 행에 순서대로 표시된다
- **AND** 창이 좁아져도 두 행으로 접히지 않고 가로 스크롤이나 키보드 이동으로 마지막 번호까지 접근할 수 있다

#### Scenario: Operate tracks ten through twelve

- **WHEN** 사용자가 각 운영체제에서 100% 또는 200% 배율로 설정과 고급 오디오 속성을 연다
- **THEN** 10·11·12번 표시가 서로 구분되고 잘림 때문에 선택할 수 없는 항목이 없다
- **AND** 필요한 스크롤 또는 탭 이동으로 모든 트랙에 접근할 수 있다

#### Scenario: Record only the last track

- **WHEN** 다중 트랙 녹화 설정에서 1~11번을 끄고 12번만 켠다
- **THEN** 유효한 한 트랙 선택으로 저장된다
- **AND** 트랙이 선택되지 않았다는 오류가 표시되지 않는다

### Requirement: Persist per-track configuration and existing profile values

고급 출력의 1~12번 트랙은 각각 이름과 지원되는 비트레이트를 설정하고 저장·복원할 수 있어야 한다(SHALL). 기존 프로필의 1~6번 설정과 녹화 선택은 유지하고, 새 프로필의 녹화 선택은 1번만 켜진 기존 기본값을 유지해야 한다(SHALL). 설정이 없는 7~12번에는 160 kbps를 기준으로 기존 인코더의 비트레이트 보정 규칙과 트랙 번호 기반 기본 이름을 적용해야 한다(SHALL).

#### Scenario: Open an existing profile

- **WHEN** 1~6번의 사용자 이름·비트레이트와 녹화 선택이 있는 기존 프로필을 연다
- **THEN** 해당 값들이 유지되고 7~12번 녹화 선택은 자동으로 켜지지 않는다
- **AND** 새 트랙 설정은 유효한 기본값으로 제공된다

#### Scenario: Save high-numbered track settings

- **WHEN** 10·11·12번에 서로 다른 이름과 지원 비트레이트를 지정하고 프로필 전환 또는 재시작을 한다
- **THEN** 각 트랙의 설정과 녹화 선택이 번호에 맞게 복원된다
- **AND** 출력 모드 전환으로 저장된 고급 트랙 설정이 지워지지 않는다

#### Scenario: Separate source defaults from recording defaults

- **WHEN** 새 프로필에 새 오디오 소스를 추가한다
- **THEN** 소스 배정은 12개 모두 켜져 있어도 녹화 선택은 1번만 켜진 상태이다

### Requirement: Estimates and encoder-dependent settings include high tracks

리플레이 버퍼 용량 추정, 방송 지연 용량 추정, 오디오 인코더 변경에 따른 비트레이트 보정과 UI 활성 상태는 7~12번을 정확히 반영해야 한다(SHALL). 고급 녹화의 용량 추정은 선택한 각 트랙 비트레이트의 합을 사용해야 하며, 간단 모드는 기존 공통 비트레이트 규칙을 선택한 트랙 수에 적용해야 한다(SHALL).

#### Scenario: Replay buffer includes track twelve bitrate

- **WHEN** 고정 비트레이트 녹화에서 다른 설정을 유지하고 12번 트랙을 추가로 선택한다
- **THEN** 리플레이 메모리 추정에 해당 트랙의 오디오 비트레이트가 추가된다

#### Scenario: Change encoder or use service-controlled streaming

- **WHEN** 사용자가 오디오 인코더를 변경하거나 방송 서비스가 인코더 설정을 관리하는 모드를 사용한다
- **THEN** 7~12번에도 기존 트랙과 같은 비트레이트 보정 및 활성·비활성 규칙이 적용된다
- **AND** 방송·VOD에 선택되지 않은 녹화 전용 트랙의 설정이 잘못 비활성화되지 않는다

### Requirement: Choose streaming and VOD mixes from twelve candidates

기존 고급 출력에서 제공하는 방송 및 VOD 트랙 선택은 각각 1~12번을 허용해야 한다(SHALL). 트랙 후보 확장은 프로토콜의 동시 전송 수, VOD를 지원하는 서비스 조건 또는 방송과 VOD에 같은 트랙을 골랐을 때의 기존 동작을 바꾸어서는 안 된다(MUST NOT). 간단 출력에서 고정된 방송·VOD 배정은 유지해야 한다(SHALL).

#### Scenario: High-numbered streaming and VOD tracks

- **WHEN** VOD 트랙을 지원하는 출력에서 방송은 12번, VOD는 11번으로 설정한다
- **THEN** 방송 오디오는 12번 믹스, VOD 오디오는 11번 믹스에서 가져온다
- **AND** 기존의 주 방송과 추가 VOD 역할 및 전송 트랙 수가 유지된다
- **AND** 저장·재시작 후에도 선택이 유지된다

#### Scenario: Streaming service has no VOD support

- **WHEN** VOD를 지원하지 않는 방송 출력에서 주 방송 트랙으로 12번을 선택한다
- **THEN** 기존과 동일한 한 방송 오디오 역할에 12번 믹스를 사용한다
- **AND** VOD 출력이 새로 활성화되지 않는다

#### Scenario: Same track for streaming and VOD

- **WHEN** 주 방송과 VOD에 모두 12번을 선택한다
- **THEN** 같은 번호의 기존 트랙을 양쪽에 선택했을 때와 동일하게 처리된다
- **AND** 중복 VOD 인코더가 추가되지 않는다

### Requirement: Preserve the simultaneous SRT and RIST audio limit

SRT/RIST의 기존 다중 오디오 방송은 1~12번 중에서 최대 6개를 선택할 수 있어야 한다(SHALL). 7개 이상을 동시에 전송하도록 설정할 수 없어야 하며, 외부에서 수정한 설정으로도 제한을 우회하거나 선택한 일부 트랙을 조용히 누락시켜서는 안 된다(MUST NOT).

#### Scenario: Six selected tracks include track twelve

- **WHEN** SRT 또는 RIST 방송에 1·2·3·7·11·12번을 선택한다
- **THEN** 해당 여섯 믹스만 기존 방식으로 전송하도록 구성된다

#### Scenario: More than six streaming tracks requested

- **WHEN** UI에서 일곱 번째 트랙을 추가하려 하거나 외부 수정된 프로필에 일곱 개 이상의 방송 트랙이 선택돼 있다
- **THEN** UI는 초과 선택을 막거나 저장을 거절한다
- **AND** 출력 시작 단계에서도 초과 설정을 거절하고 최대 6개 제한을 설명한다
- **AND** 임의의 여섯 트랙만 골라 방송하지 않는다

### Requirement: Retain existing single-track and output-mode restrictions

시스템은 기존 단일 트랙 출력 및 기능 지원 조건을 유지해야 한다(SHALL). 고급 일반 FLV의 단일 트랙 선택 후보는 1~12번으로 확장하되 한 번에 한 트랙만 사용해야 한다(SHALL). 간단 출력의 방송과 동일한 녹화 품질, 단일 트랙 전용 경로, 사용자 지정 FFmpeg의 리플레이 미지원 조건은 기존 동작을 유지해야 한다(SHALL).

#### Scenario: Record one high track to ordinary FLV

- **WHEN** 고급 일반 FLV 녹화에서 12번을 선택한다
- **THEN** 12번 믹스만 하나의 오디오 트랙으로 녹화된다

#### Scenario: Enter a mode with existing restrictions

- **WHEN** 사용자가 간단 출력의 방송과 동일한 녹화 품질 또는 사용자 지정 FFmpeg 녹화를 선택한다
- **THEN** 각각의 기존 단일 트랙 동작 또는 리플레이 미지원 상태가 유지된다
- **AND** 지원하지 않는 12트랙 녹화나 리플레이를 사용할 수 있는 것처럼 표시하지 않는다
