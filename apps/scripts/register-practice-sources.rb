#!/usr/bin/env ruby
# Add new practice sources without regenerating project IDs or signing settings.
require 'xcodeproj'

root = File.expand_path('..', __dir__)
{
  'ios' => {
    ['MusiaCore', 'Musia/Core'] => %w[PracticeWorkshop.swift PitchPractice.swift],
    ['Musia', 'Musia'] => %w[Services/PitchCapture.swift Views/PitchMatchView.swift],
    ['MusiaTests', 'Tests/MusiaCoreTests'] => %w[PracticeWorkshopTests.swift]
  },
  'macos' => {
    ['MusiaCore', '../ios/Musia/Core'] => %w[PracticeWorkshop.swift PitchPractice.swift],
    ['Musia', '../ios/Musia/Services'] => %w[PitchCapture.swift],
    ['Musia', '../ios/Musia/Views'] => %w[PitchMatchView.swift],
    ['MusiaMacTests', '../ios/Tests/MusiaCoreTests'] => %w[PracticeWorkshopTests.swift]
  }
}.each do |platform, entries|
  project = Xcodeproj::Project.open(File.join(root, platform, 'Musia.xcodeproj'))
  entries.each do |(target_name, group_path), files|
    target = project.targets.find { |item| item.name == target_name } or abort "Missing target #{target_name}"
    group = project.groups.find { |item| item.path == group_path } or abort "Missing group #{group_path}"
    files.each do |path|
      abort "Missing source #{path}" unless File.file?(File.join(root, platform, group_path, path))
      reference = group.files.find { |item| item.path == path } || group.new_file(path)
      unless target.source_build_phase.files_references.include?(reference)
        target.source_build_phase.add_file_reference(reference)
      end
    end
  end
  project.save
end
