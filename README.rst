오디오 트랙을 12개로 확장한 OBS Studio 비공식 포크입니다.
=========================================================

한국어
------

OBS Studio **32.2.2** 기반 포크입니다. ``gpt-6-astra`` 모델로 오디오 트랙을 **6개에서 12개로** 확장했습니다.

원본: `obsproject/obs-studio <https://github.com/obsproject/obs-studio>`_ · 라이선스: `GPL-2.0-or-later <COPYING>`_

빌드 (Windows x64)
~~~~~~~~~~~~~~~~~~

- Git, CMake **4.2 이상** (PATH에 추가)
- Visual Studio **2026** — **C++를 사용한 데스크톱 개발** 워크로드
- Windows SDK **10.0.26100.0**

PowerShell에서 실행합니다. 빌드 의존성은 자동으로 내려받습니다.

.. code-block:: powershell

   git clone --recurse-submodules https://github.com/monun/obs-studio-dodeca.git
   cd obs-studio-dodeca
   cmake --preset windows-x64 '-DOBS_VERSION_OVERRIDE=32.2.2-dodeca'
   cmake --build --preset windows-x64 --parallel
   cmake --install build_x64 --prefix build_x64/install --config RelWithDebInfo

실행 파일: ``build_x64/install/bin/64bit/obs64.exe``

포터블 ZIP까지 한 번에 만들려면 PowerShell 5.1 이상에서 실행합니다.

.. code-block:: powershell

   powershell -NoProfile -ExecutionPolicy Bypass -File .\build-portable.ps1

빌드부터 새 폴더 설치, 포터블 버전 확인, ZIP 내용 검증까지 실행합니다. 결과 ZIP과 SHA-256 파일은
``artifacts/``에 생성하며, 압축을 풀고 ``Start-OBS.bat``로 실행합니다. 시험 모듈은 끄고 ZIP에서
디버그 심볼을 제외합니다. ``-Parallel 4``로 병렬 수를 변경할 수 있습니다(기본 2).
CMake는 PATH 또는 기존 빌드 캐시에서 찾으며, ``-CMakePath 'C:\Program Files\CMake\bin\cmake.exe'``로 지정할 수도 있습니다.

English
-------

A fork of OBS Studio **32.2.2**, modified using the ``gpt-6-astra`` model to expand audio tracks from **6 to 12**.

Upstream: `obsproject/obs-studio <https://github.com/obsproject/obs-studio>`_ · License: `GPL-2.0-or-later <COPYING>`_

Build (Windows x64)
~~~~~~~~~~~~~~~~~~~

- Git, CMake **4.2+** (on PATH)
- Visual Studio **2026** — **Desktop development with C++** workload
- Windows SDK **10.0.26100.0**

Run in PowerShell. Build dependencies are downloaded automatically.

.. code-block:: powershell

   git clone --recurse-submodules https://github.com/monun/obs-studio-dodeca.git
   cd obs-studio-dodeca
   cmake --preset windows-x64 '-DOBS_VERSION_OVERRIDE=32.2.2-dodeca'
   cmake --build --preset windows-x64 --parallel
   cmake --install build_x64 --prefix build_x64/install --config RelWithDebInfo

Executable: ``build_x64/install/bin/64bit/obs64.exe``

To build and package a portable ZIP in one step, use PowerShell 5.1 or later:

.. code-block:: powershell

   powershell -NoProfile -ExecutionPolicy Bypass -File .\build-portable.ps1

The script builds, installs into a new folder, checks the portable version, and verifies the ZIP contents.
ZIPs and SHA-256 files are created in ``artifacts/``; extract a ZIP and run ``Start-OBS.bat``.
Test modules are disabled and debug symbols are excluded from the ZIP. Use ``-Parallel 4`` to change
the parallelism (default: 2). CMake is found on PATH or in the existing build cache;
``-CMakePath 'C:\Program Files\CMake\bin\cmake.exe'`` selects an explicit executable.
