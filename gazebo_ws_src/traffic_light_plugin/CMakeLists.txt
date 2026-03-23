cmake_minimum_required(VERSION 3.10)
project(TrafficLightPlugin)

find_package(gz-sim8 REQUIRED)

add_library(TrafficLightPlugin SHARED TrafficLightPlugin.cc)

target_link_libraries(TrafficLightPlugin
  gz-sim8::gz-sim8)
