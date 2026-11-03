#!/usr/bin/env ruby
# Verify the built pages, since a bad Scholar glob can succeed with empty lists.
require 'bibtex'
require 'nokogiri'

root = File.expand_path('..', __dir__)
destination = ARGV[0] || File.join(root, '_site')
bibliography = Dir[File.join(root, '_bibliography', '*.bib')].sort.map { |path| File.read(path) }.join("\n")
entries = BibTeX.parse(bibliography).entries.values
expected_keys = entries.map { |entry| entry.key.to_s }.sort

page = Nokogiri::HTML(File.read(File.join(destination, 'publications', 'index.html')))
rendered_keys = page.css('.publications .title').map { |title| title.parent['id'] }.sort
abort 'Publication page does not match the bibliography' unless rendered_keys == expected_keys

home = Nokogiri::HTML(File.read(File.join(destination, 'index.html')))
sections = home.css('div.publications')
abort 'Homepage publication sections are missing' unless sections.length == 2
recent_keys = sections[0].css('.title').map { |title| title.parent['id'] }
unless recent_keys.length == [5, entries.length].min && (recent_keys - expected_keys).empty?
  abort 'Homepage recent publications are missing or invalid'
end
selected_keys = entries.select { |entry| entry[:selected].to_s == 'true' }.map { |entry| entry.key.to_s }.sort
rendered_selected = sections[1].css('.title').map { |title| title.parent['id'] }.sort
abort 'Homepage selected publications changed' unless rendered_selected == selected_keys

puts "Publication pages verified: #{entries.length} papers, #{recent_keys.length} recent, #{selected_keys.length} selected."
