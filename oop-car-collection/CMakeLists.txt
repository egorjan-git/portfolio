cmake_minimum_required(VERSION 3.25)
project(OOP_1_1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(${CMAKE_SOURCE_DIR}/include)

add_executable(oop_lab
        src/main.cpp
        src/Box3D.cpp
        src/KitchenCabinet.cpp
        src/Appliance.cpp
        src/KitchenPlan.cpp
        src/ProcessMemory.cpp
)

target_compile_options(oop_lab PRIVATE -Wall -Wextra -Wpedantic)

if(APPLE)
    target_compile_options(oop_lab PRIVATE -fsanitize=address,undefined)
    target_link_options(oop_lab PRIVATE -fsanitize=address,undefined)
endif()

if (WIN32)
    target_link_libraries(oop_lab PRIVATE user32 gdi32)


    file(WRITE "${CMAKE_BINARY_DIR}/run_cli.bat"
            "@echo off\r\n\
oop_lab.exe cli\r\n\
pause\r\n")

    file(WRITE "${CMAKE_BINARY_DIR}/run_gui.bat"
            "@echo off\r\n\
oop_lab.exe gui\r\n\
pause\r\n")
endif()