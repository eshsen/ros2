cmake_minimum_required(VERSION 3.20)
project(course_simulation)

find_package(ament_cmake REQUIRED)

install(PROGRAMS
  scripts/odom_adapter.py
  scripts/drive_adapter.py
  DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY
  launch
  config
  worlds
  models
  DESTINATION share/${PROJECT_NAME}
)


if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)

  ament_add_pytest_test(
    test_odom_adapter
    test/test_odom_adapter.py
    APPEND_ENV PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/scripts
    TIMEOUT 60
  )

  ament_add_pytest_test(
    test_drive_adapter
    test/test_drive_adapter.py
    APPEND_ENV PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/scripts
    TIMEOUT 60
  )
endif()

ament_package()
