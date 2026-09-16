## Why

OBS Studio Dodeca는 12트랙 확장을 포함한 비공식 포크이지만, 현재 본체 업데이트 경로는 OBS 공식 배포의 버전 정보와 실행기를 사용한다. 포크를 공식 빌드로 덮어쓰거나 불필요한 업데이트 안내를 표시하지 않도록 본체 업데이트 기능을 원본 코드가 남는 방식으로 제외한다.

## What Changes

- Windows·macOS·Linux에서 본체의 업데이트 확인 메뉴, 자동 업데이트 설정과 채널 선택을 제외한다. 같은 실행기를 사용하는 Windows의 ‘복구’ 메뉴와 실행 경로도 포함한다.
- 업데이트 확인 결과·설치 권유·오류 팝업과 ‘새 소식’(What's New) 메뉴·시작 팝업을 제외한다.
- 시작 시 자동 확인, 수동 확인, 설정 변경 후 재확인, 브랜치·매니페스트 조회, 본체 업데이트 파일 다운로드·검증·설치 및 업데이트를 위한 종료·재시작 경로를 비활성화한다.
- Windows updater 실행 파일의 빌드와 macOS Sparkle의 연결·번들 포함을 제외한다. 기존 사용자 설정이나 CMake 캐시가 기능을 다시 활성화할 수 없게 한다.
- 삭제 대신 주석과 컴파일·빌드 제외 처리를 사용하여 원본 구현을 보존한다. 새로운 업데이트 서버나 대체 업데이트 기능은 추가하지 않는다.
- 사용자가 확정한 범위에 따라 방송 서비스 목록·서버 정보와 게임 캡처 호환성 데이터의 자동 갱신은 유지한다. 기존 장면·프로필과 업데이트 캐시 파일을 삭제하지 않는다.

## Capabilities

### New Capabilities

- `application-update-policy`: 본체 업데이트 UI·팝업·실행·패키징을 항상 제외하고, 기존 설정과 보조 데이터 갱신을 보존하는 포크의 동작 계약.

### Modified Capabilities

없음. 현재 등록된 main spec은 없으며, 진행 중인 `expand-audio-tracks-to-twelve`의 오디오 요구사항은 변경하지 않는다.

## Impact

- **프런트엔드:** `frontend/OBSApp.*`, `frontend/obs-main.cpp`의 업데이트 옵션 호환성, `frontend/widgets/OBSBasic*`, `frontend/settings/OBSBasicSettings.*`, 관련 Qt 폼과 업데이트·새 소식 전용 대화상자 및 스레드.
- **빌드·패키징:** `frontend/cmake/`의 소스 목록과 Windows updater·What's New·Sparkle 설정, `frontend/updater/`의 빌드 진입점, `cmake/macos/helpers.cmake`, macOS `Info.plist.in`의 Sparkle 항목.
- **보존 범위:** `plugins/rtmp-services`, `plugins/win-capture`, `shared/file-updater`, 일반 네트워크·인증·방송·녹화·리먹스 동작. 사용자가 여는 릴리스 노트 웹 링크와 제삼자 플러그인의 자체 업데이트는 본체 업데이트 실행 범위 밖이다.
- **검증:** 새 설정과 업데이트가 켜진 기존 설정에서 UI 부재, 본체 업데이트 통신·다운로드·프로세스 실행 부재, 생성된 빌드·패키지의 updater 제외, 설정 저장·재시작과 12트랙 기능의 기본 회귀를 확인한다. 플랫폼별 실제 실행 결과와 미검증 항목을 구분해 기록한다.
- **문서:** 구현 시 비활성화 범위·복원 위치·검증 방법을 기록한다. 이번 제안 단계에서는 OpenSpec 계획 산출물만 작성한다.
