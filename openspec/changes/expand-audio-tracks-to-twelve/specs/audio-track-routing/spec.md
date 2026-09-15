## Purpose

사용자가 여러 오디오 소스를 최대 12개의 독립 트랙에 배정하고 원하는 조합으로 분리 녹음할 수 있게 한다. 새 소스의 기본 배정, 기존 장면과 확장 버전 장면의 저장·복원, 번들 원격 제어가 동일한 트랙 상태를 다루도록 보장한다.

## ADDED Requirements

### Requirement: Twelve independent audio mixes

시스템은 1~12번 독립 오디오 트랙을 제공하고 각 소스를 원하는 트랙 조합에 배정할 수 있어야 한다(SHALL). 각 트랙 안의 기존 모노·스테레오·서라운드 구성과 소스 볼륨·음소거·필터·동기 오프셋의 의미는 유지해야 한다(SHALL).

#### Scenario: Isolated high-numbered tracks

- **WHEN** 서로 다른 시험음을 내는 소스 A를 7번, 소스 B를 12번에만 배정한다
- **THEN** 7번에는 A만, 12번에는 B만 출력된다
- **AND** 배정하지 않은 트랙에는 두 소스의 오디오가 나타나지 않는다

#### Scenario: Combined and isolated tracks

- **WHEN** A를 1·7번, B를 1·12번에 배정한다
- **THEN** 1번은 A와 B의 혼합, 7번은 A만, 12번은 B만 포함한다

#### Scenario: Existing audio processing on track twelve

- **WHEN** 12번에 배정한 소스의 음소거·볼륨·필터·동기 오프셋을 변경한다
- **THEN** 기존 1~6번에 적용되던 것과 같은 의미로 해당 소스의 출력이 변경된다
- **AND** 같은 소스를 포함한 중첩 장면이나 번들 전환에서도 배정한 오디오가 유지된다

### Requirement: Default routing for newly created sources

시스템은 새 오디오 소스를 생성할 때 1~12번 트랙을 모두 켜야 한다(SHALL). 소스의 기본 배정과 녹화 파일에 포함할 트랙의 기본 선택은 별개여야 한다(SHALL).

#### Scenario: Create a source in an existing or new scene collection

- **WHEN** 사용자가 새 장면 모음 또는 이전 버전에서 가져온 장면 모음에 새 오디오 소스를 추가한다
- **THEN** 그 소스의 1~12번 트랙 배정이 모두 켜진다
- **AND** 기존 소스의 배정과 현재 녹화 트랙 선택은 바뀌지 않는다

### Requirement: Preserve effective routing when importing legacy sources

시스템은 6트랙 버전에서 저장한 소스를 불러올 때 기존에 유효했던 1~6번 배정을 보존하고 7~12번은 꺼야 한다(SHALL). 과거 데이터에 남은 지원 범위 밖의 비트를 새 트랙 배정으로 해석해서는 안 된다(MUST NOT).

#### Scenario: Legacy source with explicit routing

- **WHEN** 이전 OBS에서 1·3·6번에 배정한 소스를 불러온다
- **THEN** 1·3·6번만 켜지고 7~12번을 포함한 나머지 트랙은 꺼진다

#### Scenario: Legacy default contains unused high bits

- **WHEN** 이전 OBS의 기본값 때문에 저장된 트랙 배정 값이 255인 소스를 불러온다
- **THEN** 기존 유효 범위인 1~6번만 켜진다
- **AND** 7·8번에 해당하는 과거의 숨은 비트가 새 배정으로 활성화되지 않는다

#### Scenario: Legacy source has no saved routing value

- **WHEN** 기존 트랙 배정 항목이 없는 이전 버전 소스를 불러온다
- **THEN** 이전 버전의 기본 배정인 1~6번을 켜고 7~12번을 끈다

#### Scenario: Legacy source has all routes disabled

- **WHEN** 기존 소스의 저장된 배정이 모두 꺼진 상태이다
- **THEN** 불러온 뒤에도 1~12번이 모두 꺼진 상태이다

### Requirement: Preserve twelve-track routing across persistence operations

시스템은 확장 버전에서 저장한 소스를 이전 버전 소스와 구별하고 1~12번 배정을 그대로 복원해야 한다(SHALL). 재시작, 장면 모음 내보내기·가져오기, 소스 복제 후에도 같은 배정을 보존해야 한다(SHALL).

#### Scenario: Save and reload a migrated source

- **WHEN** 이전 버전에서 불러온 소스에 사용자가 7·12번을 추가로 배정하고 저장한 뒤 다시 연다
- **THEN** 기존 배정과 새 7·12번 배정이 모두 유지된다
- **AND** 이후 다시 저장하고 열어도 이전 버전 이전 처리가 반복 적용되지 않는다

#### Scenario: Export or duplicate a twelve-track source

- **WHEN** 2·8·12번에 배정한 소스를 복제하거나, 포함된 장면 모음을 내보내고 확장 버전에 가져온다
- **THEN** 2·8·12번 배정이 그대로 유지된다

### Requirement: Built-in remote control reflects all twelve routes

번들 obs-websocket은 오디오 트랙 조회와 변경 이벤트에 문자열 키 `1`부터 `12`까지의 켜짐 상태를 반환해야 한다(SHALL). 부분 변경 요청은 지정한 트랙에만 적용하고 나머지 트랙을 보존해야 하며, 새 키에도 기존 boolean 값 검증을 적용해야 한다(SHALL).

#### Scenario: Update track twelve remotely

- **WHEN** 클라이언트가 `SetInputAudioTracks`로 `12`번만 켜는 부분 요청을 보낸다
- **THEN** 12번만 요청대로 변경되고 1~11번의 상태는 유지된다
- **AND** 조회 응답과 `InputAudioTracksChanged` 이벤트 및 고급 오디오 속성 UI가 같은 12개 상태를 표시한다

#### Scenario: Existing client sends six track keys

- **WHEN** 기존 클라이언트가 1~6번 키만 포함한 변경 요청을 보낸다
- **THEN** 7~12번 배정은 변경되지 않는다

#### Scenario: Invalid type for a new track

- **WHEN** 클라이언트가 새 트랙 키의 값으로 boolean이 아닌 값을 보낸다
- **THEN** 기존 형식 오류 방식으로 요청이 거절되고 소스 배정은 변경되지 않는다
