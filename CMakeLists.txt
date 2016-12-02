cmake_minimum_required(VERSION 2.8.3)
project(gencpp_subsystem_buffers)
find_package(catkin REQUIRED COMPONENTS genmsg)

catkin_package(
  CATKIN_DEPENDS genmsg
  CFG_EXTRAS gencpp_subsystem_buffers-extras.cmake
)

add_subdirectory(scripts)

file(WRITE ${CATKIN_DEVEL_PREFIX}/${GENMSG_LANGS_DESTINATION}/gencpp_subsystem_buffers "C++")
install(FILES ${CATKIN_DEVEL_PREFIX}/${GENMSG_LANGS_DESTINATION}/gencpp_subsystem_buffers
  DESTINATION ${GENMSG_LANGS_DESTINATION})

catkin_python_setup()
