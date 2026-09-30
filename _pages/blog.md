---
layout: default
permalink: /blog/
title: blog
nav: true
nav_order: 5
---

{%- comment -%}
Post index, in the article style (_sass/_article.scss). Every post is listed
on one page; the translations of a post (same translation_key) share a row,
shown in the language of whichever comes first in site.posts.
{%- endcomment -%}

{% include article_fonts.liquid %}

<div class="ar-page ar-index">
  <header class="ar-head">
    <h1>{{ site.blog_name }}</h1>
    {% if site.blog_description %}
      <p class="ar-lede">{{ site.blog_description }}</p>
    {% endif %}
  </header>

  <ol class="ar-posts">
    {% assign seen = '|' %}
    {% for post in site.posts %}
      {% if post.translation_key %}
        {% assign key = post.translation_key | prepend: '|' | append: '|' %}
        {% if seen contains key %}{% continue %}{% endif %}
        {% assign seen = seen | append: key %}
      {% endif %}

      {% if post.reading_time %}
        {% assign read_time = post.reading_time %}
      {% else %}
        {% assign read_time = post.content | strip_html | number_of_words: 'auto' | divided_by: 200 | plus: 1 %}
      {% endif %}

      {% if post.redirect contains '://' %}
        {% assign href = post.redirect %}
      {% elsif post.redirect %}
        {% assign href = post.redirect | relative_url %}
      {% else %}
        {% assign href = post.url | relative_url %}
      {% endif %}

      <li class="ar-post"{% if post.lang == 'zh' %} lang="zh-CN"{% endif %}>
        <time class="ar-post-date" datetime="{{ post.date | date_to_xmlschema }}">{{ post.date | date: '%b %-d, %Y' }}</time>
        <div class="ar-post-body">
          <h2>
            <a href="{{ href }}"{% if post.redirect contains '://' %} target="_blank" rel="noopener"{% endif %}>
              {{- post.title -}}
              {%- if post.redirect contains '://' %} <span class="ar-ext" aria-hidden="true">↗</span>{% endif -%}
            </a>
          </h2>
          {% if post.description %}
            <p>{{ post.description }}</p>
          {% endif %}
          <div class="ar-meta" lang="en">
            <span>{{ read_time }} min read</span>
            {% if post.translation_key %}
              {% assign translations = site.posts | where: 'translation_key', post.translation_key | sort: 'lang' %}
              {% if translations.size > 1 %}
                <span class="ar-dot" aria-hidden="true">·</span>
                <span class="ar-lang">
                  {% for t in translations %}
                    {% if t.lang == 'zh' %}{% assign label = '中文' %}{% else %}{% assign label = 'EN' %}{% endif %}
                    {% unless forloop.first %}<span class="ar-slash" aria-hidden="true">/</span>{% endunless %}
                    <a href="{{ t.url | relative_url }}" hreflang="{% if t.lang == 'zh' %}zh-CN{% else %}en{% endif %}">{{ label }}</a>
                  {% endfor %}
                </span>
              {% endif %}
            {% endif %}
            {% if post.external_source %}
              <span class="ar-dot" aria-hidden="true">·</span>
              <span>{{ post.external_source }}</span>
            {% endif %}
          </div>
        </div>
      </li>
    {% endfor %}

  </ol>
</div>
