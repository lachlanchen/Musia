#!/usr/bin/env ruby
require 'xcodeproj'

root = File.expand_path('..', __dir__)
# Register the native authentication callback when regenerating the Mac project.
# ASWebAuthenticationSession owns callback handling; no embedded browser is used.
info_path = File.join(root, 'Musia/Resources/Info.plist')
info = Xcodeproj::Plist.read_from_path(info_path)
info['CFBundleURLTypes'] = [{
  'CFBundleURLName' => 'art.lazying.musia.auth',
  'CFBundleURLSchemes' => ['art.lazying.musia'], 'CFBundleTypeRole' => 'Editor'
}]
Xcodeproj::Plist.write_to_path(info, info_path)
project = Xcodeproj::Project.new(File.join(root, 'Musia.xcodeproj'))
project.build_configurations.each do |config|
  config.build_settings.merge!({
    'SWIFT_VERSION' => '5.0', 'MACOSX_DEPLOYMENT_TARGET' => '14.0',
    'MARKETING_VERSION' => '0.2.0', 'CURRENT_PROJECT_VERSION' => '8',
    'DEVELOPMENT_TEAM' => 'Q8M2S2FY77', 'CODE_SIGN_STYLE' => 'Manual',
    'ENABLE_USER_SCRIPT_SANDBOXING' => 'YES', 'CLANG_ENABLE_MODULES' => 'YES',
    'SWIFT_OPTIMIZATION_LEVEL' => config.name == 'Debug' ? '-Onone' : '-O',
    'ENABLE_TESTABILITY' => config.name == 'Debug' ? 'YES' : 'NO'
  })
end
app = project.new_target(:application, 'Musia', :osx, '14.0')
core = project.new_target(:framework, 'MusiaCore', :osx, '14.0')
tests = project.new_target(:unit_test_bundle, 'MusiaMacTests', :osx, '14.0')

[[core, '../ios/Musia/Core'], [app, '../ios/Musia/Services'], [app, '../ios/Musia/Views'],
 [app, 'Musia'], [tests, '../ios/Tests/MusiaCoreTests'], [tests, 'Tests']].each do |target, relative|
  group = project.main_group.new_group(relative, relative)
  Dir.glob(File.join(root, relative, '**/*.swift')).sort.each do |path|
    ref = group.new_file(path.delete_prefix(File.join(root, relative) + '/'))
    target.source_build_phase.add_file_reference(ref)
  end
end
resources = project.main_group.new_group('Resources', 'Musia/Resources')
resources.new_file('Info.plist')
resources.new_file('Musia.entitlements')
app.resources_build_phase.add_file_reference(resources.new_file('Assets.xcassets'))
shared = project.main_group.new_group('Shared Resources', '../ios/Musia/Resources')
app.resources_build_phase.add_file_reference(shared.new_file('PrivacyInfo.xcprivacy'))

{app => 'art.lazying.musia', core => 'art.lazying.musia.core', tests => 'art.lazying.musia.mactests'}.each do |target, identifier|
  target.build_configurations.each do |config|
    config.build_settings.merge!({
      'PRODUCT_BUNDLE_IDENTIFIER' => identifier, 'PRODUCT_NAME' => '$(TARGET_NAME)',
      'SWIFT_VERSION' => '5.0', 'CODE_SIGN_STYLE' => 'Manual',
      'CODE_SIGN_IDENTITY' => config.name == 'Debug' ? '-' : 'Apple Distribution',
      'LD_RUNPATH_SEARCH_PATHS' => ['$(inherited)', '@executable_path/../Frameworks', '@loader_path/../Frameworks']
    })
  end
end
app.build_configurations.each do |config|
  config.build_settings.merge!({
    'INFOPLIST_FILE' => 'Musia/Resources/Info.plist',
    'CODE_SIGN_ENTITLEMENTS' => 'Musia/Resources/Musia.entitlements',
    'ENABLE_APP_SANDBOX' => 'YES', 'ENABLE_HARDENED_RUNTIME' => 'YES',
    'ASSETCATALOG_COMPILER_APPICON_NAME' => 'AppIcon',
    'PROVISIONING_PROFILE_SPECIFIER' => config.name == 'Debug' ? '$(MUSIA_DEBUG_PROFILE)' : '$(MUSIA_MAC_PROFILE)'
  })
end
core.build_configurations.each do |config|
  config.build_settings.merge!({'GENERATE_INFOPLIST_FILE' => 'YES', 'DEFINES_MODULE' => 'YES', 'SKIP_INSTALL' => 'YES'})
end
tests.build_configurations.each do |config|
  config.build_settings.merge!({'GENERATE_INFOPLIST_FILE' => 'YES',
    'TEST_HOST' => '$(BUILT_PRODUCTS_DIR)/Musia.app/Contents/MacOS/Musia', 'BUNDLE_LOADER' => '$(TEST_HOST)'})
end
app.add_dependency(core)
app.frameworks_build_phase.add_file_reference(core.product_reference)
embed = app.new_copy_files_build_phase('Embed Frameworks')
embed.dst_subfolder_spec = '10'
embed.add_file_reference(core.product_reference).settings = {'ATTRIBUTES' => ['CodeSignOnCopy', 'RemoveHeadersOnCopy']}
tests.add_dependency(app)
tests.add_dependency(core)
tests.frameworks_build_phase.add_file_reference(core.product_reference)
project.files.select { |ref| ref.path&.end_with?('/Foundation.framework') }.each do |ref|
  ref.source_tree = 'SDKROOT'
  ref.path = 'System/Library/Frameworks/Foundation.framework'
end
project.save
scheme = Xcodeproj::XCScheme.new
scheme.add_build_target(app)
scheme.set_launch_target(app)
scheme.add_test_target(tests)
scheme.test_action.code_coverage_enabled = true
scheme.save_as(project.path, 'Musia', true)
puts "Generated #{project.path}"
