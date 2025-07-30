import os, sys, re, shutil
import subprocess

rootDir = os.path.dirname(__file__)
if not rootDir:
    rootDir = os.path.abspath(".")
rootDir = os.path.abspath(os.path.join(rootDir, "../cpp/LunaHook"))

if len(sys.argv) and sys.argv[1] == "merge":
    # 'merge' 명령의 경우, 스크립트의 현재 작업 디렉토리는 리포지토리 루트입니다.
    # 따라서 os.chdir(rootDir)는 제거합니다.
    # os.mkdir("../build")도 download-artifact에 의해 이미 생성되므로 제거합니다.
    
    # 최종 결과물이 저장될 'builds' 디렉토리를 rootDir 내부에 생성합니다.
    # 예: D:\a\LunaTranslator\LunaTranslator\src\cpp\LunaHook\builds
    os.makedirs(os.path.join(rootDir, "builds", "Release"), exist_ok=True)

    # shutil.copytree의 원본 경로는 리포지토리 루트 기준의 상대 경로로 직접 지정합니다.
    # 대상 경로는 rootDir 내의 'builds/Release' 하위 폴더로 명확히 지정합니다.
    shutil.copytree(
        "build/64/Release", # 리포지토리 루트 기준: D:\a\LunaTranslator\LunaTranslator\build\64\Release
        os.path.abspath(os.path.join(rootDir, "builds/Release/64")), # 대상: D:\a\LunaTranslator\LunaTranslator\src\cpp\LunaHook\builds\Release\64
        dirs_exist_ok=True,
    )
    shutil.copytree(
        "build/x86/Release", # 리포지토리 루트 기준: D:\a\LunaTranslator\LunaTranslator\build\x86\Release
        os.path.abspath(os.path.join(rootDir, "builds/Release/x86")), # 대상: D:\a\LunaTranslator\LunaTranslator\src\cpp\LunaHook\builds\Release\x86
        dirs_exist_ok=True,
    )

    # 최종 ZIP 파일의 대상 디렉토리와 파일명을 조정합니다.
    # ZIP에 포함될 내용의 루트는 rootDir 내의 'builds/Release'입니다.
    targetdir = os.path.abspath(os.path.join(rootDir, "builds/Release"))
    target = os.path.abspath(os.path.join(rootDir, "builds/Release.zip"))
    
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
