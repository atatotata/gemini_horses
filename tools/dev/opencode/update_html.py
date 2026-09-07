import re

with open(r'G:\Downloads\Documents\go-model-benchmarks.html', 'r', encoding='utf-8-sig') as f:
    html = f.read()

# ============================================================
# 1. TITLE: "Updated Sep 2, 2026" -> "Updated Sep 3, 2026"
# ============================================================
html = html.replace('(Updated Sep 2, 2026)', '(Updated Sep 3, 2026)', 1)

# ============================================================
# 2. HEADER PARAGRAPH: Update compiled line and add New Sep 3
# ============================================================
old_header = '(updated Sep 2, 2026). Vendor tech reports'
new_header = '(updated Sep 3, 2026). Vendor tech reports'
html = html.replace(old_header, new_header, 1)

# Add New Sep 3 bullet before New Sep 2
old_new_sep2 = '<strong>New Sep 2:</strong>'
new_sep3_bullet = '<strong>New Sep 3:</strong> Gemini 3.8 Flash GA "Skimaki" (Sep 2, 1M ctx/64K out, TB2.1 90.8%, SWE-Pro 61.6%, GPQA-D 95.3% #1/46, AA 59 #8, speed 304\u2013313 t/s #1/195, $0.75/$3.75 intro thru Dec 31 2026, direct-Google-provider only \u2014 not on OpenCode Go). ' + old_new_sep2
html = html.replace(old_new_sep2, new_sep3_bullet, 1)

# ============================================================
# 3. WATCHLIST: Update Gemini 3.8 Flash (now released)
# ============================================================
old_watchlist = '<div class="note-box"><strong>Watchlist (Sep 2):</strong> Grok 4.7 ~Sep 12 (Musk Sep 1: ~10 days, 2.1T params) \u00b7 Gemini 3.8 Flash "Skimaki" \u2014 WSJ Sep 1: as soon as Sep 2 (not yet released at check) \u00b7 Hy4 GA still preview only (no change)</div>'
new_watchlist = '<div class="note-box"><strong>Watchlist (Sep 3):</strong> Grok 4.7 ~Sep 12 (Musk Sep 1: ~10 days, 2.1T params) \u00b7 Hy4 GA still preview only (no change) \u00b7 Gemini 3.8 Flash Cyber (sister model, cyber-specialized) pending GA</div>'
html = html.replace(old_watchlist, new_watchlist, 1)

# ============================================================
# 4. SECTION 1 QUICK REF: Add Gemini 3.8 Flash row in Direct Provider
# ============================================================
old_gem_row = '<tr><td>Gemini 3.7 Flash</td><td class="num">\u2014</td><td class="num">\u2014</td><td class="num">\u2014</td><td class="num">85.8%</td><td class="num">\u2014</td><td class="num">\u2014</td><td class="num">\u2014</td><td class="num">\u2014</td><td class="num">\u2014</td></tr>'
new_gem_rows = old_gem_row + '\n        <tr><td><strong>Gemini 3.8 Flash</strong></td><td class="num">\u2014</td><td class="num">61.6%</td><td class="num">\u2014</td><td class="num best">90.8%</td><td class="num">\u2014</td><td class="num">59 (#8)</td><td class="num">75.37 (#12)</td><td class="num">~1567 (~#18)</td><td class="num">not listed</td></tr>'
html = html.replace(old_gem_row, new_gem_rows, 1)

# ============================================================
# 5. SECTION 9 AA INDEX: Add Gemini 3.8 Flash row
# ============================================================
old_grok_aa = '<tr><td class="num">~5\u20136</td><td>Grok 4.6</td><td class="num best">61%</td><td class="num">62 (high)</td></tr>'
new_grok_aa = old_grok_aa + '\n          <tr><td class="num">8</td><td>Gemini 3.8 Flash</td><td class="num">59%</td><td class="num">59 (med default)</td></tr>'
html = html.replace(old_grok_aa, new_grok_aa, 1)

# ============================================================
# 6. SECTION 6 BENCHLM: Add Gemini 3.8 Flash note
# ============================================================
old_benchlm_grok = '<tr><td class="num">#47</td><td>Grok 4.6</td><td class="num">63.3</td><td>was Grok 4.5 #8 (75.4) \u2014 composite collapsed under v5.2</td></tr>'
new_benchlm_grok = old_benchlm_grok + '\n        <tr><td class="num">#12</td><td>Gemini 3.8 Flash</td><td class="num">75.37</td><td>NEW Sep 3 \u2014 GPQA-D 95.3% #1, speed 304 t/s #1</td></tr>'
html = html.replace(old_benchlm_grok, new_benchlm_grok, 1)

# ============================================================
# 7. SECTION 7 ARENA: Add Gemini 3.8 Flash note
# ============================================================
old_arena_note = '<p class="lead"><strong>Note:</strong> Arena Elo is JS/Web-only for new models'
new_arena_note = '<p class="lead"><strong>Note:</strong> Gemini 3.8 Flash: ~#18 text Arena, ~1567 Elo (High), Sep 2 \u2014 text-only entry. Arena Elo is JS/Web-only for new models'
html = html.replace(old_arena_note, new_arena_note, 1)

# ============================================================
# 8. SECTION 8 CURSORBENCH: Add note about Gemini 3.8 Flash
# ============================================================
old_cursor_note = '<p class="lead">\u2020 Fable 5.1 cache reads $0.25/1M'
new_cursor_note = '<p class="lead">Gemini 3.8 Flash: not listed on CursorBench 3.2 (Sep 2 release, no Cursor eval yet). \u2020 Fable 5.1 cache reads $0.25/1M'
html = html.replace(old_cursor_note, new_cursor_note, 1)

# ============================================================
# 9. SECTION 12 CAVEATS: Add Gemini 3.8 Flash row
# ============================================================
old_direct_prov_row = '<tr><td><strong>Direct Provider</strong></td><td colspan="5"></td></tr>'
new_gem_caveat = '<tr><td>Gemini 3.8 Flash</td><td>Medium-High</td><td>Google (vendor) + third-party</td><td>Multiple</td><td>Released Sep 2, 2026; TB2.1 90.8% official, 89.4% third-party; GPQA-D 95.3% #1; speed 304\u2013313 t/s; mixed-positive Reddit (speed praised, long-horizon caution, Flash fatigue)</td><td>Sep 3, 2026</td></tr>\n        <tr><td><strong>Direct Provider</strong></td><td colspan="5"></td></tr>'
html = html.replace(old_direct_prov_row, new_gem_caveat, 1)

# ============================================================
# 10. SECTION 15 CROSS-REFERENCE: Update GPQA and TB2.1 rows
# ============================================================
old_gpqa = '<tr><td>GPQA Diamond</td><td>Kimi K3 93.5% (Hy4 92.3%)</td><td>Gemini 3.1 Pro 94.4%</td><td class="num best">Gemini 3.1 Pro</td></tr>'
new_gpqa = '<tr><td>GPQA Diamond</td><td>Kimi K3 93.5% (Hy4 92.3%)</td><td>Gemini 3.8 Flash 95.3% (3.1 Pro 94.4%)</td><td class="num best">Gemini 3.8 Flash</td></tr>'
html = html.replace(old_gpqa, new_gpqa, 1)

old_tb21 = '<tr><td>Terminal-Bench 2.1</td><td><strong>GLM-5.3 88.2%</strong> (Kimi K3 88.3%*)</td><td>Gemini 3.7 Flash 85.8% (Sonnet 5 80.4%)</td><td class="num best">GLM-5.3</td></tr>'
new_tb21 = '<tr><td>Terminal-Bench 2.1</td><td><strong>GLM-5.3 88.2%</strong> (Kimi K3 88.3%*)</td><td>Gemini 3.8 Flash 90.8% (3.7 Flash 85.8%)</td><td class="num best">Gemini 3.8 Flash</td></tr>'
html = html.replace(old_tb21, new_tb21, 1)

# ============================================================
# 11. SECTION 14 DIRECT PROVIDER: Add Gemini 3.8 Flash row + profile
# ============================================================
old_gem_direct_row = '<tr><td>Gemini 3.7 Flash</td><td>(intro half of 3.6F)</td><td class="num">\u2014</td><td class="num">\u2014</td><td class="num">85.8%</td><td class="num">56 high / 53 med / 51 low</td><td>Preview only</td></tr>'
new_gem_direct_rows = old_gem_direct_row + '\n        <tr><td><strong>Gemini 3.8 Flash</strong></td><td>$0.75/$3.75 (intro thru Dec 31 2026) \u2192 $1.50/$7.50 Jan 1 2027; cached ~$0.075</td><td class="num">\u2014</td><td class="num">61.6%</td><td class="num best">90.8%</td><td class="num">59 (high effort)</td><td>GA Sep 2, 2026 \u00b7 1M ctx/64K out \u00b7 built on 3.7 Flash \u00b7 multimodal in (text/image/audio/video) \u00b7 thinking LOW/MEDIUM(default)/HIGH \u00b7 <strong>direct Google provider only \u2014 NOT on OpenCode Go</strong> \u00b7 speed 304\u2013313 t/s #1 \u00b7 GPQA-D 95.3% #1/46 \u00b7 sister model: 3.8 Flash Cyber (cyber-specialized)</td></tr>'
html = html.replace(old_gem_direct_row, new_gem_direct_rows, 1)

# ============================================================
# 12. SECTION 14.5.1: Add Gemini 3.8 Flash profile
# ============================================================
old_gem37_end = """  </details>

  <details>
    <summary><strong>\u00a714.6 Gemini 3.5 Flash (Google DeepMind)</strong>"""

new_gem38_profile = """  </details>

  <details>
    <summary><strong>\u00a714.5.1 Gemini 3.8 Flash "Skimaki" (Google DeepMind)</strong> \u2014 released September 2, 2026, GA</summary>
    <p class="lead">Latest Flash model. Built on 3.7 Flash architecture. 3 reasoning levels: LOW/MEDIUM(default)/HIGH. 1M context, 64K max output. Multimodal input: text, image, audio, video. <strong>$0.75/$3.75 per 1M intro pricing thru Dec 31, 2026</strong> \u2192 $1.50/$7.50 Jan 1, 2027. Cached read ~$0.075. AA blended $0.58. <strong>Direct Google provider only \u2014 NOT on OpenCode Go (Go = open models only, 26-model roster verified Sep 3).</strong> Speed: 304\u2013313 t/s (#1/195 models). Sister model: Gemini 3.8 Flash Cyber (cyber-specialized).</p>
    <div class="note-box"><strong>vs 3.7 Flash (official Google dev guide):</strong> TB2.1 90.8% (vs 81.6), SWE-Pro 61.6% (vs 60.4), SWE-Atlas 51.9% (48.0), \u03c4\u00b3 Banking 38.1% (30.9), CharXiv 86.2% (84.5), GDP.pdf 35.0% (34.0), HLE 45.4% (45.7).</div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>Category</th><th>Benchmark</th><th class="num">Gemini 3.8 Flash</th><th class="num">vs 3.7 Flash</th><th>Source</th></tr></thead>
        <tbody>
          <tr><td rowspan="4">Official (Google)</td><td>Terminal-Bench 2.1</td><td class="num best">90.8%</td><td class="num">81.6%</td><td>Google dev guide</td></tr>
          <tr><td>SWE-bench Pro</td><td class="num">61.6%</td><td class="num">60.4%</td><td>Google dev guide</td></tr>
          <tr><td>SWE-Atlas</td><td class="num">51.9%</td><td class="num">48.0%</td><td>Google dev guide</td></tr>
          <tr><td>\u03c4\u00b3 Banking</td><td class="num">38.1%</td><td class="num">30.9%</td><td>Google dev guide</td></tr>
          <tr><td rowspan="3">Official (Google)</td><td>CharXiv</td><td class="num">86.2%</td><td class="num">84.5%</td><td>Google dev guide</td></tr>
          <tr><td>GDP.pdf</td><td class="num">35.0%</td><td class="num">34.0%</td><td>Google dev guide</td></tr>
          <tr><td>HLE</td><td class="num">45.4%</td><td class="num">45.7%</td><td>Google dev guide</td></tr>
          <tr><td>Official</td><td>Speed (tok/s)</td><td class="num best">304\u2013313</td><td class="num">\u2014</td><td>#1/195 models</td></tr>
          <tr class="section-break"><td colspan="5"><strong>Third-party benchmarks</strong></td></tr>
          <tr><td>Reasoning</td><td>GPQA Diamond</td><td class="num best">95.3%</td><td class="num">#1/46</td><td>Third-party leaderboard</td></tr>
          <tr><td>Reasoning</td><td>HLE-Verified</td><td class="num best">54.9%</td><td class="num">#1/6</td><td>Third-party leaderboard</td></tr>
          <tr><td>Coding</td><td>Terminal-Bench 2.1</td><td class="num">89.4%</td><td class="num">#2/18</td><td>Third-party leaderboard</td></tr>
          <tr><td>Coding</td><td>DeepSWE</td><td class="num">73.7%</td><td class="num">#3/32</td><td>Third-party leaderboard</td></tr>
          <tr><td>Coding</td><td>SciCode</td><td class="num">54.4%</td><td class="num">\u2014</td><td>Third-party leaderboard</td></tr>
          <tr><td>Coding</td><td>SWE-bench Pro</td><td class="num">61.6%</td><td class="num">\u2014</td><td>Official Google dev guide</td></tr>
          <tr><td>Finance</td><td>Finance Agent v2</td><td class="num">61.4%</td><td class="num">#1/4</td><td>Third-party leaderboard</td></tr>
          <tr><td>Agentic</td><td>AA-LCR</td><td class="num">82.0%</td><td class="num">#3/40</td><td>Third-party leaderboard</td></tr>
          <tr><td>Agentic</td><td>AA Index (high/med/low)</td><td class="num">59 / 57 / 52</td><td class="num">#8/41</td><td>Artificial Analysis</td></tr>
          <tr><td>Agentic</td><td>OSWorld</td><td class="num">59.0%</td><td class="num">#4/19</td><td>Third-party leaderboard</td></tr>
          <tr><td>Agentic</td><td>GDPval</td><td class="num">1545</td><td class="num">\u2014</td><td>Third-party leaderboard</td></tr>
          <tr><td>Agentic</td><td>LVBench</td><td class="num best">87.8%</td><td class="num">#1/4</td><td>Third-party leaderboard</td></tr>
          <tr><td>Agentic</td><td>TB4.0</td><td class="num">19.1%</td><td class="num">#7/9</td><td>Third-party leaderboard</td></tr>
          <tr class="section-break"><td colspan="5"><strong>Leaderboard rankings</strong></td></tr>
          <tr><td>Composite</td><td>BenchLM #12</td><td class="num">75.37</td><td class="num">Sep 2, 2026</td><td>benchlm.ai</td></tr>
          <tr><td>Arena</td><td>Chatbot Arena Text (overall)</td><td class="num">~#18</td><td class="num">~1567 Elo (High)</td><td>lmarena.ai</td></tr>
          <tr><td>Speed</td><td>Throughput</td><td class="num best">304\u2013313 t/s</td><td class="num">#1/195</td><td>Artificial Analysis</td></tr>
          <tr><td>CursorBench 3.2</td><td>CursorBench</td><td class="num">not listed</td><td class="num">\u2014</td><td>No Cursor eval yet (Sep 2 release)</td></tr>
        </tbody>
      </table>
    </div>
    <div class="note-box"><strong>Reddit community (Sep 2\u20133, mixed-positive):</strong> Speed and price universally praised. "Genuine step up from 3.7" \u2014 "almost Sol medium/low" quality. One user reported it "found things I missed" on a kafka 5-microservices codebase. Long-horizon caution: not yet proven for sustained agentic loops. Flash fatigue: "weekly new flash" skepticism. Some "disappointed faster" reactions (expected bigger leap). Built on 3.7 Flash, not a new architecture.</div>
    <div class="note-box"><strong>Pricing note:</strong> Intro $0.75/$3.75 thru Dec 31, 2026 \u2192 $1.50/$7.50 Jan 1, 2027. Cached reads ~$0.075. AA blended $0.58. Same pricing on direct Google provider (not on OpenCode Go). NOT on OpenCode Go\u2019s 26-model roster \u2014 Go is open models only (verified Sep 3, 2026).</div>
  </details>

  <details>
    <summary><strong>\u00a714.6 Gemini 3.5 Flash (Google DeepMind)</strong>"""

html = html.replace(old_gem37_end, new_gem38_profile, 1)

# ============================================================
# 13. SECTION 18 SOURCES: Add Gemini 3.8 Flash sources
# ============================================================
old_groksrc = '<li><a href="https://docs.x.ai/docs/grok-4-6">docs.x.ai/docs/grok-4-6</a> (Grok 4.6 API docs'
new_groksrc = '<li><a href="https://blog.google/technology/google-deepmind/gemini-3-8-flash/">blog.google/.../gemini-3-8-flash/</a> (Gemini 3.8 Flash official blog \u2014 Sep 2, 2026)</li>\n        <li><a href="https://deepmind.google/models/model-cards/gemini-3-8-flash/">deepmind.google/.../gemini-3-8-flash/</a> (Gemini 3.8 Flash DeepMind model card)</li>\n        <li><a href="https://cloud.google.com/vertex-ai/generative-ai/docs/learn/models#gemini-3-8-flash">cloud.google.com/.../gemini-3-8-flash</a> (Cloud dev guide \u2014 pricing, benchmarks, API)</li>\n        <li><a href="https://www.wsj.com/articles/google-gemini-3-8-flash">wsj.com/articles/google-gemini-3-8-flash</a> (WSJ Sep 1, 2026 \u2014 launch coverage)</li>\n        <li><a href="https://benchlm.ai/models/gemini-3-8-flash">benchlm.ai/models/gemini-3-8-flash</a> (BenchLM composite #12, 75.37)</li>\n        <li><a href="https://artificialanalysis.ai/models/gemini-3-8-flash">artificialanalysis.ai/models/gemini-3-8-flash</a> (AA Index 59, speed 304 t/s)</li>\n        <li><a href="https://docs.x.ai/docs/grok-4-6">docs.x.ai/docs/grok-4-6</a> (Grok 4.6 API docs'
html = html.replace(old_groksrc, new_groksrc, 1)

# ============================================================
# 14. SECTION 11 ROLES: Update revised date
# ============================================================
html = html.replace('revised Sep 2, 2026', 'revised Sep 3, 2026', 1)
html = html.replace('Revised Sep 2:', 'Revised Sep 3:', 1)

# ============================================================
# 15. SECTION 12 CAVEATS: Update Gemini 3.7 Flash caveat
# ============================================================
old_37_caveat = '<td>Preview only \u2014 no SWE-V/Pro; limited independent verification</td><td>Aug 13, 2026</td></tr>\n        <tr><td>Gemini 3.1 Pro</td>'
new_37_caveat = '<td>Superseded by 3.8 Flash (Sep 2, 2026); no SWE-V/Pro; limited independent verification</td><td>Aug 13, 2026</td></tr>\n        <tr><td>Gemini 3.1 Pro</td>'
html = html.replace(old_37_caveat, new_37_caveat, 1)

# ============================================================
# 16. DASHBOARD: Update TB2.1 card
# ============================================================
old_dash_tb = """    <div class="dash-card">
      <div class="goal">\U0001f3c6 Best Terminal-Bench 2.1</div>
      <div class="pick">GLM-5.3 \u2014 88.2%*</div>
      <div class="alt">Kimi K3 \u2014 88.3%* (vendor)</div>
      <div class="why">GLM-5.3 shipped Aug 14; K3 vendor-reported</div>
    </div>"""
new_dash_tb = """    <div class="dash-card">
      <div class="goal">\U0001f3c6 Best Terminal-Bench 2.1</div>
      <div class="pick">Gemini 3.8 Flash \u2014 90.8% (direct)</div>
      <div class="alt">GLM-5.3 \u2014 88.2%* \u00b7 Kimi K3 \u2014 88.3%*</div>
      <div class="why">3.8 Flash direct provider; GLM-5.3/K3 Go platform</div>
    </div>"""
html = html.replace(old_dash_tb, new_dash_tb, 1)

# Write the updated HTML
with open(r'G:\Downloads\Documents\go-model-benchmarks.html', 'w', encoding='utf-8-sig') as f:
    f.write(html)

print("HTML updated successfully")
print(f"New file size: {len(html)} chars")
