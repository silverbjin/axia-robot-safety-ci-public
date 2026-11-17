cmake_minimum_required(VERSION 3.16)
project(axia_g07_cm120_tf_diag LANGUAGES CXX)
# Diagnostic-only shared object. NEVER deployed with official Safety runtime.
find_package(ament_cmake REQUIRED)
find_package(nav2_util REQUIRED)
find_package(rclcpp REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
add_library(axia_g07_cm120_tf_diag SHARED cm_tf_gettransform_preload.cpp)
target_compile_features(axia_g07_cm120_tf_diag PRIVATE cxx_std_17)
ament_target_dependencies(axia_g07_cm120_tf_diag
  nav2_util rclcpp tf2 tf2_ros)
target_link_libraries(axia_g07_cm120_tf_diag dl)
set_target_properties(axia_g07_cm120_tf_diag PROPERTIES PREFIX "lib")
