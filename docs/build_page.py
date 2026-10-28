"""The GitHub Pages article (docs/index.html), built from docs/page.md, the page's own text in the author's words.
Images are served from the site itself, and the video is embedded at the top.

    python3 docs/build_page.py"""
import html
import re
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
SITE = "https://blaiselabs.github.io/GuessWithAnki/"
VIDEO = "j-xJ8mhyt0E"


def sections(md):
    title = re.search(r'^title: "(.*)"$', md, re.M).group(1)
    return title, md.split("---", 2)[2].strip()


def main():
    md = (HERE / "page.md").read_text(encoding="utf-8")
    title, text = sections(md)
    text = text.replace("https://raw.githubusercontent.com/BlaiseLabs/GuessWithAnki/main/docs/", "")
    content = markdown.markdown(text, extensions=["tables"])
    content = content.replace("<img ", '<img loading="lazy" ')
    desc = ("Measuring how often you can guess a word you've never seen, from the pieces it's built from, and an Anki "
            "add-on that orders your cards so more words arrive guessable. Japanese, Chinese, Korean, English and medicine.")
    page = TEMPLATE.format(title=html.escape(title), desc=html.escape(desc), site=SITE, video=VIDEO, content=content)
    (HERE / "index.html").write_text(page, encoding="utf-8")
    (HERE / ".nojekyll").write_text("")
    print("wrote docs/index.html,", len(page), "bytes")


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{site}">
<meta property="og:image" content="{site}article/thumbnail.png">
<meta property="og:image:width" content="1280">
<meta property="og:image:height" content="720">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{site}article/thumbnail.png">
<style>
  :root {{ --bg: #14181c; --panel: #1d2630; --ink: #eef0ec; --mute: #9aa3ab; --blue: #3987e5; --yellow: #f2c14e; }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: var(--bg); color: var(--ink); font: 18px/1.7 system-ui, -apple-system, "Segoe UI",
         "Noto Sans", "Noto Sans CJK JP", sans-serif; }}
  main {{ max-width: 780px; margin: 0 auto; padding: 32px 20px 80px; }}
  h1 {{ font-size: 2.1em; line-height: 1.2; margin: 0.4em 0 0.6em; }}
  h2 {{ font-size: 1.55em; margin: 2em 0 0.6em; border-bottom: 1px solid #2a3540; padding-bottom: 0.2em; }}
  h3 {{ font-size: 1.25em; margin: 1.8em 0 0.5em; color: var(--yellow); }}
  h4 {{ font-size: 1.05em; margin: 1.5em 0 0.3em; color: #7fb3f0; }}
  a {{ color: #7fb3f0; }}
  img {{ max-width: 100%; height: auto; border-radius: 10px; display: block; margin: 1.2em auto; }}
  .video {{ position: relative; padding-top: 56.25%; margin: 0 0 1.5em; border-radius: 12px; overflow: hidden;
           background: #000; }}
  .video iframe {{ position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1.2em 0; font-size: 0.92em; display: block; overflow-x: auto; }}
  th, td {{ border: 1px solid #2f3a45; padding: 8px 10px; text-align: left; vertical-align: top; }}
  th {{ background: var(--panel); }}
  code {{ background: var(--panel); padding: 1px 6px; border-radius: 5px; font-size: 0.9em; }}
  blockquote {{ border-left: 4px solid var(--blue); margin: 1em 0; padding: 0.2em 1em; color: var(--mute); }}
  footer {{ max-width: 780px; margin: 0 auto; padding: 0 20px 48px; color: var(--mute); font-size: 0.9em; }}
</style>
</head>
<body>
<main>
<h1>{title}</h1>
<div class="video"><iframe src="https://www.youtube-nocookie.com/embed/{video}" title="GuessWithAnki video"
  allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
  referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>
{content}
</main>
<footer>GuessWithAnki is free and open source, on <a href="https://github.com/BlaiseLabs/GuessWithAnki">GitHub</a>.</footer>
</body>
</html>
"""

if __name__ == "__main__":
    main()
