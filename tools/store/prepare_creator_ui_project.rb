#!/usr/bin/env ruby
# Create a private test project; leave app source and its generated project intact.
require 'fileutils'
require 'xcodeproj'

root = File.expand_path('../..', __dir__)
output = File.expand_path(ARGV.fetch(0))
runtime = File.join(root, 'store/.runtime') + '/'
abort 'Output must be a new private runtime directory' unless output.start_with?(runtime) && !File.exist?(output)
FileUtils.mkdir_p(output, mode: 0o700)
project = Xcodeproj::Project.open(File.join(root, 'apps/ios/Musia.xcodeproj'))
project.main_group.source_tree = '<absolute>'
project.main_group.path = File.join(root, 'apps/ios')
app = project.targets.find { |target| target.name == 'Musia' }
tests = project.targets.find { |target| target.name == 'MusiaUITests' }
abort 'Expected native app and UI-test targets' unless app && tests
entitlements = File.join(output, 'Simulator.entitlements')
Xcodeproj::Plist.write_to_path({
  'application-identifier' => 'Q8M2S2FY77.art.lazying.musia',
  'com.apple.developer.team-identifier' => 'Q8M2S2FY77',
  'keychain-access-groups' => ['Q8M2S2FY77.art.lazying.musia']
}, entitlements)
app.build_configurations.each do |configuration|
  configuration.build_settings['INFOPLIST_FILE'] = File.join(root, 'apps/ios/Musia/Resources/Info.plist')
  configuration.build_settings['CODE_SIGN_ENTITLEMENTS'] = entitlements
end
tests.source_build_phase.files.to_a.each(&:remove_from_project)
source = project.main_group.new_file(File.join(root, 'tools/store/CreatorNativeUITests.swift'), :absolute)
tests.source_build_phase.add_file_reference(source)
fixture = File.join(root, 'store/.runtime/creator-apple-20261009/creator-qa-fixture.json')
abort 'Stage the authorized private login fixture first' unless File.file?(fixture) && File.stat(fixture).mode & 0o077 == 0
tests.resources_build_phase.add_file_reference(project.main_group.new_file(fixture, :absolute))
path = File.join(output, 'MusiaCreatorQA.xcodeproj')
project.save(path)
# Reopen so scheme references use the copied project, not the original name.
project = Xcodeproj::Project.open(path)
app = project.targets.find { |target| target.name == 'Musia' }
tests = project.targets.find { |target| target.name == 'MusiaUITests' }
scheme = Xcodeproj::XCScheme.new
scheme.add_build_target(app)
scheme.set_launch_target(app)
scheme.add_test_target(tests)
scheme.save_as(path, 'MusiaCreatorQA', true)
puts path
