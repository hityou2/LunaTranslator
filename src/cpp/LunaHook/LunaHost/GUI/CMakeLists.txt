if(BUILD_GUI)
add_executable(LunaHost WIN32 confighelper.cpp controls.cpp main.cpp processlistwindow.cpp  LunaHost.cpp window.cpp #../../../exec/luna.rc # <--- 이 줄을 주석 처리하거나 삭제합니다.
pluginmanager.cpp Plugin/extensionimpl.cpp Plugin/copyclipboard.cpp QtLoader_inline.cpp app.manifest ${versioninfo})
target_precompile_headers(LunaHost REUSE_FROM pch) 
set_target_properties(LunaHost PROPERTIES OUTPUT_NAME "LunaHost${bitappendix}")

FetchContent_Declare(json 
    URL https://github.com/nlohmann/json/releases/download/v3.12.0/json.tar.xz
    DOWNLOAD_EXTRACT_TIMESTAMP true
)
FetchContent_MakeAvailable(json)

target_link_libraries(LunaHost comctl32 winhttp pch host nlohmann_json::nlohmann_json ${YY_Thunks} lang_ui)
endif()
