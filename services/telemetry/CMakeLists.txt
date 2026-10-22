cmake_minimum_required(VERSION 3.16)

project(telemetry LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include(FetchContent)

FetchContent_Declare(
    Crow
    GIT_REPOSITORY https://github.com/CrowCpp/Crow.git
    GIT_TAG v1.2.1
)

FetchContent_MakeAvailable(Crow)

find_package(PkgConfig REQUIRED)
pkg_check_modules(RDKAFKA REQUIRED IMPORTED_TARGET rdkafka)

add_executable(telemetry
    src/main.cpp
    src/KafkaProducer.cpp
)

target_link_libraries(telemetry PRIVATE
    Crow::Crow
    PkgConfig::RDKAFKA
)

