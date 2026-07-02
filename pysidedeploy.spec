[app]

# title of your application
title = WakfuAutoBuilder

# project root directory. default = The parent directory of input_file
project_dir = .

# source file entry point path. default = main.py
input_file = main.py

# directory where the executable output is generated
exec_directory = .

# path to the project file relative to project_dir
project_file = auto_builder.pyproject

# application icon
icon = /Users/jeremycotineau/perso/wakfu_auto_builder/.venv/lib/python3.12/site-packages/PySide6/scripts/deploy_lib/pyside_icon.icns

[python]

# python path
python_path = /Users/jeremycotineau/perso/wakfu_auto_builder/.venv/bin/python3

# python packages to install
packages = Nuitka==2.7.11

# buildozer = for deploying Android application
android_packages = buildozer==1.5.0,cython==0.29.33

[qt]

# paths to required qml files. comma separated
# normally all the qml files required by the project are added automatically
# design studio projects include the qml files using qt resources
qml_files = views/mainPage.qml,views/ConstraintGrid.qml,views/ConstraintSelector.qml,views/MaximizeConstraintSelector.qml,views/MaximizeRatioConstraintSelector.qml,views/Resultitem.qml,views/BuildComparison.qml,views/SavedBuilds.qml,views/StatProfiles.qml,views/ItemFilterDialog.qml,views/ItemIcon.qml

# excluded qml plugin binaries
excluded_qml_plugins = QtCharts,QtSensors,QtWebEngine,QtQuickShapesDesignHelpers

# qt modules used. comma separated
modules = Core,DBus,Gui,Network,OpenGL,Qml,QmlMeta,QmlModels,QmlWorkerScript,Quick,QuickControls2,QuickTemplates2

# qt plugins used by the application. only relevant for desktop deployment
# for qt plugins used in android application see [android][plugins]
plugins = accessiblebridge,egldeviceintegrations,generic,iconengines,imageformats,networkaccess,networkinformation,platforminputcontexts,platforms,platforms/darwin,platformthemes,qmllint,qmltooling,scenegraph,tls,xcbglintegrations

[android]

# path to pyside wheel
wheel_pyside = 

# path to shiboken wheel
wheel_shiboken = 

# plugins to be copied to libs folder of the packaged application. comma separated
plugins = 

[nuitka]

# usage description for permissions requested by the app as found in the info.plist file
# of the app bundle. comma separated
# eg = extra_args = --show-modules --follow-stdlib
macos.permissions = 

# mode of using nuitka. accepts standalone or onefile. default = onefile
mode = onefile

# specify any extra nuitka arguments
# --include-data-dir bundles the source-relative dirs into the frozen
# binary so paths.resource_path() finds them at runtime.
extra_args = --quiet --noinclude-qt-translations --assume-yes-for-downloads --include-data-dir=data=data --include-data-dir=data_overrides=data_overrides --include-data-dir=assets=assets --include-data-dir=views=views --noinclude-dlls=*qtquickshapesdesignhelpers* --noinclude-dlls=*/qml/QtQuick/Shapes/DesignHelpers/* --include-package=ortools --include-package-data=ortools --nofollow-import-to=unittest

[buildozer]

# build mode
# possible values = ["aarch64", "armv7a", "i686", "x86_64"]
# release creates a .aab, while debug creates a .apk
mode = debug

# path to pyside6 and shiboken6 recipe dir
recipe_dir = 

# path to extra qt android .jar files to be loaded by the application
jars_dir = 

# if empty, uses default ndk path downloaded by buildozer
ndk_path = 

# if empty, uses default sdk path downloaded by buildozer
sdk_path = 

# other libraries to be loaded at app startup. comma separated.
local_libs = 

# architecture of deployed platform
arch = 

