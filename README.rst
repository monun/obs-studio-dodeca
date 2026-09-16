OBS Studio Dodeca
=================

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
