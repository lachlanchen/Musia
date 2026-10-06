#!/usr/bin/env ruby
# Optional maintainer tool. The generated project is checked in; Mac builds need no gem or XcodeGen.
require 'xcodeproj'

root = File.expand_path('..', __dir__)
project = Xcodeproj::Project.new(File.join(root, 'Musia.xcodeproj'))
project.object_version = '56' if project.respond_to?(:object_version=)
project.build_configurations.each do |config|
  config.build_settings.merge!({
    'SWIFT_VERSION' => '5.0', 'IPHONEOS_DEPLOYMENT_TARGET' => '17.0',
    'TARGETED_DEVICE_FAMILY' => '1,2', 'MARKETING_VERSION' => '0.1.3',
    'CURRENT_PROJECT_VERSION' => '5', 'DEVELOPMENT_TEAM' => '', 'CODE_SIGN_STYLE' => 'Manual',
    'ENABLE_USER_SCRIPT_SANDBOXING' => 'YES', 'CLANG_ENABLE_MODULES' => 'YES',
    'SWIFT_OPTIMIZATION_LEVEL' => config.name == 'Debug' ? '-Onone' : '-O',
    'ENABLE_TESTABILITY' => config.name == 'Debug' ? 'YES' : 'NO'
  })
end

app = project.new_target(:application, 'Musia', :ios, '17.0')
core = project.new_target(:framework, 'MusiaCore', :ios, '17.0')
tests = project.new_target(:unit_test_bundle, 'MusiaTests', :ios, '17.0')
ui_tests = project.new_target(:ui_test_bundle, 'MusiaUITests', :ios, '17.0')
app_group = project.main_group.new_group('Musia', 'Musia')
core_group = project.main_group.new_group('MusiaCore', 'Musia/Core')
test_group = project.main_group.new_group('MusiaTests', 'Tests/MusiaCoreTests')
ui_test_group = project.main_group.new_group('MusiaUITests', 'Tests/MusiaUITests')

Dir.glob(File.join(root, 'Musia/**/*.swift')).sort.each do |path|
  is_core = path.include?('/Musia/Core/')
  group = is_core ? core_group : app_group
  base = File.join(root, is_core ? 'Musia/Core/' : 'Musia/')
  reference = group.new_file(path.delete_prefix(base))
  (is_core ? core : app).source_build_phase.add_file_reference(reference)
end
Dir.glob(File.join(root, 'Tests/MusiaCoreTests/*.swift')).sort.each do |path|
  tests.source_build_phase.add_file_reference(test_group.new_file(File.basename(path)))
end
Dir.glob(File.join(root, 'Tests/MusiaUITests/*.swift')).sort.each do |path|
  ui_tests.source_build_phase.add_file_reference(ui_test_group.new_file(File.basename(path)))
end
%w[Resources/Assets.xcassets Resources/PrivacyInfo.xcprivacy].each do |path|
  app.resources_build_phase.add_file_reference(app_group.new_file(path))
end
app_group.new_file('Resources/Info.plist')

{app => 'art.lazying.musia', core => 'art.lazying.musia.core', tests => 'art.lazying.musia.tests',
 ui_tests => 'art.lazying.musia.uitests'}.each do |target, identifier|
  target.build_configurations.each do |config|
    config.build_settings.merge!({
      'PRODUCT_BUNDLE_IDENTIFIER' => identifier,
      'PRODUCT_NAME' => '$(TARGET_NAME)', 'SWIFT_VERSION' => '5.0',
      'TARGETED_DEVICE_FAMILY' => '1,2', 'CODE_SIGN_STYLE' => 'Manual',
      'LD_RUNPATH_SEARCH_PATHS' => ['$(inherited)', '@executable_path/Frameworks', '@loader_path/Frameworks']
    })
  end
end
app.build_configurations.each do |config|
  config.build_settings.merge!({
    'INFOPLIST_FILE' => 'Musia/Resources/Info.plist',
    'ASSETCATALOG_COMPILER_APPICON_NAME' => 'AppIcon',
    'ASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME' => 'AccentColor',
    'SUPPORTS_MACCATALYST' => 'NO',
    'PROVISIONING_PROFILE_SPECIFIER' => '$(MUSIA_APP_PROFILE)'
  })
end
core.build_configurations.each do |config|
  config.build_settings.merge!({'GENERATE_INFOPLIST_FILE' => 'YES', 'DEFINES_MODULE' => 'YES', 'SKIP_INSTALL' => 'YES'})
end
tests.build_configurations.each do |config|
  config.build_settings.merge!({
    'GENERATE_INFOPLIST_FILE' => 'YES', 'TEST_HOST' => '$(BUILT_PRODUCTS_DIR)/Musia.app/Musia',
    'BUNDLE_LOADER' => '$(TEST_HOST)'
  })
end
ui_tests.build_configurations.each do |config|
  config.build_settings.merge!({'GENERATE_INFOPLIST_FILE' => 'YES', 'TEST_TARGET_NAME' => 'Musia'})
end
app.add_dependency(core)
app.frameworks_build_phase.add_file_reference(core.product_reference)
embed = app.new_copy_files_build_phase('Embed Frameworks')
embed.dst_subfolder_spec = '10'
entry = embed.add_file_reference(core.product_reference)
entry.settings = {'ATTRIBUTES' => ['CodeSignOnCopy', 'RemoveHeadersOnCopy']}
tests.add_dependency(app)
tests.add_dependency(core)
tests.frameworks_build_phase.add_file_reference(core.product_reference)
ui_tests.add_dependency(app)
# xcodeproj's bundled SDK version must not pin the project to an absent SDK.
project.files.select { |reference| reference.path&.end_with?('/Foundation.framework') }.each do |reference|
  reference.source_tree = 'SDKROOT'
  reference.path = 'System/Library/Frameworks/Foundation.framework'
end
project.save

scheme = Xcodeproj::XCScheme.new
scheme.add_build_target(app)
scheme.set_launch_target(app)
scheme.add_test_target(tests)
scheme.add_test_target(ui_tests)
scheme.test_action.code_coverage_enabled = true
scheme.save_as(project.path, 'Musia', true)
puts "Generated #{project.path}"
