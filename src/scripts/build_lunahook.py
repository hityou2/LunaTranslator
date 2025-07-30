import os, sys, re, shutil
import subprocess

rootDir = os.path.dirname(__file__)
if not rootDir:
    rootDir = os.path.abspath(".")
rootDir = os.path.abspath(os.path.join(rootDir, "../cpp/LunaHook"))

if len(sys.argv) and sys.argv[1] == "merge":
    # os.chdir(rootDir) # <--- 이 줄을 제거하거나 주석 처리합니다.
    # 워크플로의 'run' 명령은 이미 리포지토리 루트에서 실행되므로,
    # 스크립트가 리포지토리 루트를 기준으로 경로를 찾도록 합니다.

    # build 디렉토리가 이미 워크플로의 download-artifact 단계에서 생성되므로
    # 이 부분도 필요 없을 수 있지만, 안전을 위해 dirs_exist_ok=True와 함께 유지합니다.
    # os.mkdir("../build") # 이 줄도 필요 없을 수 있습니다.
    # os.mkdir("builds") # 이 줄은 builds/Release.zip을 위해 필요할 수 있습니다.

    # shutil.copytree의 원본 경로를 리포지토리 루트 기준으로 수정합니다.
    # rootDir가 src/cpp/LunaHook이므로, build 폴더는 rootDir의 상위 2단계에 있습니다.
    shutil.copytree(
        os.path.abspath(os.path.join(rootDir, "../../build/64/Release")), # <--- 경로 수정
        os.path.abspath(os.path.join(rootDir, "builds/Release/64")), # <--- 대상 경로도 명확히
        dirs_exist_ok=True,
    )
    shutil.copytree(
        os.path.abspath(os.path.join(rootDir, "../../build/x86/Release")), # <--- 경로 수정 (winxp는 x86으로 다운로드됨)
        os.path.abspath(os.path.join(rootDir, "builds/Release/x86")), # <--- 대상 경로도 명확히
        dirs_exist_ok=True,
    )

    # 최종 결과물은 builds/Release 폴더에 있을 것이므로, targetdir을 조정합니다.
    targetdir = os.path.abspath(os.path.join(rootDir, "builds/Release"))
    target = os.path.abspath(os.path.join(rootDir, "builds/Release.zip")) # builds 폴더는 rootDir 안에 있습니다.
    os.system(
        rf'"C:\Program Files\7-Zip\7z.exe" a -m0=Deflate -mx9 {target} {targetdir}'
    )
    exit()

print(sys.version)
print(__file__)
print(rootDir)

os.chdir(rootDir) # 이 부분은 'build' 및 'plugin' 명령에 여전히 필요합니다.
if sys.argv[1] == "plugin":
    bits = sys.argv[2]
    with open("buildplugin.bat", "w") as ff:
        if bits == "32":
            ff.write(
                rf"""
cmake -DBUILD_CORE=OFF -DUSESYSQTPATH=1 -DBUILD_PLUGIN=ON ./CMakeLists.txt -G "Visual Studio 17 2022" -A win32 -T host=x86 -B ./build/plugin32
cmake --build ./build/plugin32 --config Release --target ALL_BUILD -j 14
"""
            )
        else:
            ff.write(
                rf"""
cmake -DBUILD_CORE=OFF -DUSESYSQTPATH=1 -DBUILD_PLUGIN=ON ./CMakeLists.txt -G "Visual Studio 17 2022" -A x64 -T host=x64 -B ./build/plugin64
cmake --build ./build/plugin64 --config Release --target ALL_BUILD -j 14
"""
            )
    os.system(f"cmd /c buildplugin.bat")
elif sys.argv[1] == "build":
    arch = sys.argv[2]
    core = int(sys.argv[3])
    target = sys.argv[4]

    archA = ("win32", "x64")[arch == "x64"]
    vsver = "Visual Studio 17 2022"
    Tool = "v141_xp" if target == "winxp" else f"host={arch}"
    config = (
        "-DWIN10ABOVE=ON"
        if target == "win10"
        else (" -DWINXP=ON " if target == "winxp" else "")
    )
    config += " -DBUILD_PLUGIN=OFF "
    if not core:
        config += " -DBUILD_GUI=ON "

    subprocess.run(
        f'cmake {config} ./CMakeLists.txt -G "{vsver}" -A {archA} -T {Tool} -B ./build/{arch}_{target}'
    )
    subprocess.run(
        f"cmake --build ./build/{arch}_{target} --config Release --target ALL_BUILD -j 14"
    )
