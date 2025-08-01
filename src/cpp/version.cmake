﻿
set(VERSION_MAJOR 10)
set(VERSION_MINOR 7)
set(VERSION_PATCH 7)
set(VERSION_REVISION 0)
set(LUNA_VERSION "{${VERSION_MAJOR},${VERSION_MINOR},${VERSION_PATCH},${VERSION_REVISION}}")
add_library(VERSION_DEF ${CMAKE_CURRENT_LIST_DIR}/version_def.cpp)
target_compile_definitions(VERSION_DEF PRIVATE
    LUNA_VERSION_=${LUNA_VERSION})
include(${CMAKE_CURRENT_LIST_DIR}/version/generate_product_version.cmake)

generate_product_version(
	versioninfo
   NAME "LunaTranslator"
   COMPANY_COPYRIGHT "HIllya51 (C) 2025"
   ICON ${PATH_TO_APPLICATION_ICON}
   VERSION_MAJOR ${VERSION_MAJOR}
   VERSION_MINOR ${VERSION_MINOR}
   VERSION_PATCH ${VERSION_PATCH}
   VERSION_REVISION ${VERSION_REVISION}
)