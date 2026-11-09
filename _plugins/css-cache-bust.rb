# Versions main.css by the Sass it is built from.
#
# jekyll-cache-bust's bust_css_cache hashes assets/_sass, which this site does
# not have (the partials live in _sass), so it always produced the hash of an
# empty string and browsers kept serving a stale main.css after style changes.
module Jekyll
  module SassCacheBust
    def bust_sass_cache(file_name)
      site = @context.registers[:site]
      sources = Dir[File.join(site.source, site.config.dig("sass", "sass_dir") || "_sass", "**", "*.scss")].sort
      sources << File.join(site.source, "assets", "css", "main.scss")
      digest = Digest::MD5.hexdigest(sources.select { |f| File.file?(f) }.map { |f| File.read(f) }.join)
      "#{file_name}?v=#{digest}"
    end
  end
end

Liquid::Template.register_filter(Jekyll::SassCacheBust)
