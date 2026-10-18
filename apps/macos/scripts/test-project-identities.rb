#!/usr/bin/env ruby
# Source-only checks; no Xcode, shared host, signing or app launch.
require 'xcodeproj'
require 'tmpdir'
require 'fileutils'
require 'rbconfig'

ROOT = File.expand_path('..', __dir__)
SUFFIXES = {'Musia' => '', 'MusiaCore' => '.core', 'MusiaMacTests' => '.mactests'}.freeze

def check_project(path)
  project = Xcodeproj::Project.open(path)
  raise 'Unexpected targets' unless project.targets.map(&:name).sort == SUFFIXES.keys.sort
  project.build_configurations.each do |config|
    raise 'Production prefix changed' unless config.build_settings['MUSIA_MAC_BUNDLE_PREFIX'] == 'art.lazying.musia'
  end
  project.targets.each do |target|
    raise 'Missing Debug/Release' unless target.build_configurations.map(&:name).sort == %w[Debug Release]
    target.build_configurations.each do |config|
      settings = config.build_settings
      raise 'Target shadows project prefix' if settings.key?('MUSIA_MAC_BUNDLE_PREFIX')
      expected = "$(MUSIA_MAC_BUNDLE_PREFIX)#{SUFFIXES.fetch(target.name)}"
      raise "Wrong identity template: #{target.name}/#{config.name}" unless settings['PRODUCT_BUNDLE_IDENTIFIER'] == expected
    end
  end
  %w[art.lazying.musia art.lazying.musia.compatibilityqa].each do |prefix|
    %w[Debug Release].each do |configuration|
      ids = project.targets.map do |target|
        config = target.build_configurations.find { |item| item.name == configuration }
        template = config.build_settings.fetch('PRODUCT_BUNDLE_IDENTIFIER')
        template.sub('$(MUSIA_MAC_BUNDLE_PREFIX)', prefix)
      end
      raise 'Duplicate identity' unless ids.uniq.size == 3
      raise 'Wrong identity set' unless ids.sort == SUFFIXES.values.map { |suffix| prefix + suffix }.sort
    end
  end
  app = project.targets.find { |target| target.name == 'Musia' }
  app.build_configurations.each do |config|
    settings = config.build_settings
    raise 'Sandbox changed' unless settings['ENABLE_APP_SANDBOX'] == 'YES'
    raise 'Hardened runtime changed' unless settings['ENABLE_HARDENED_RUNTIME'] == 'YES'
    profile = config.name == 'Debug' ? '$(MUSIA_DEBUG_PROFILE)' : '$(MUSIA_MAC_PROFILE)'
    raise 'Profile changed' unless settings['PROVISIONING_PROFILE_SPECIFIER'] == profile
  end
end

check_project(File.join(ROOT, 'Musia.xcodeproj'))
# Regenerate only an ephemeral fixture, never the checked-in project or plist.
Dir.mktmpdir('musia-project-identities-') do |temp|
  FileUtils.mkdir_p(File.join(temp, 'scripts'))
  FileUtils.mkdir_p(File.join(temp, 'Musia/Resources'))
  generator = File.join(temp, 'scripts/generate-project.rb')
  FileUtils.cp(File.join(__dir__, 'generate-project.rb'), generator)
  FileUtils.cp(File.join(ROOT, 'Musia/Resources/Info.plist'), File.join(temp, 'Musia/Resources/Info.plist'))
  raise 'Generator failed' unless system(RbConfig.ruby, generator)
  check_project(File.join(temp, 'Musia.xcodeproj'))
end
puts 'PASS: checked-in and regenerated project identities, Debug/Release, production/QA, sandbox and signing defaults'
