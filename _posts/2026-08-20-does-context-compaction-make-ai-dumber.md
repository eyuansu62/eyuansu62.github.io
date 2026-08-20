---
layout: post
title: 上下文压缩之后，AI 编程助手会"变笨"吗？
date: 2026-08-20 12:00:00 +0800
description: 基于 40 万轮真实编码轨迹（TraceLab + 自有 Codex / Claude Code 日志）的实证分析：compact 后正确率基本不退化，但模型要交一笔"效率税"——用更多编辑与重读补救丢失的细节。
tags: [llm, coding-agent, context-compaction, evaluation, methodology]
---

<div style="font-family:Georgia,'Songti SC','Noto Serif SC',serif;max-width:760px;margin:0 auto;color:#222;line-height:1.9;">
  <p style="font-size:1.05em;color:#666;margin:0 0 28px;">——基于 40 万轮真实编码轨迹的分析</p>

  <p>长会话的 AI 编程助手迟早会撞上一堵墙：上下文窗口。当对话越来越长，系统会把历史"压缩"（compact）成一段摘要，腾出空间继续工作。这带来一个自然的问题：<strong>压缩之后，模型还记得自己在干什么吗？它会不会变笨？</strong></p>
  <p style="margin:24px 0 0;padding:20px 8px;border-top:1px solid #ddd;border-bottom:1px solid #ddd;text-align:center;font-size:1.12em;line-height:1.8;color:#111;"><span style="display:block;font-size:0.7em;letter-spacing:3px;color:#888;margin-bottom:6px;">结论先行</span>压缩没有让模型变笨——它只是让模型<strong>更费力地保持聪明</strong>。<br>而真正危险的，从来不是看得见的错误，而是<strong>看不见的遗失</strong>。</p>
  <p>我们分析了三份真实数据——一份来自 <a href="https://github.com/uw-syfi/TraceLab">TraceLab</a>（UW SYFI）的聚合编码轨迹集（约 35.7 万轮、4265 个会话），以及作者自己的 Codex（495 个会话）与 Claude Code（5856 个会话）原始日志。过程中我们踩了两个方法论的坑，也得到了一些反直觉的结论。</p>

  <h2 style="font-size:1.3em;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:36px;">〇、数据：三份互相印证的轨迹</h2>
  <table style="width:100%;border-collapse:collapse;font-size:0.88em;font-family:-apple-system,sans-serif;margin:16px 0;">
    <tr style="background:#f5f5f2;"><th style="padding:8px;text-align:left;border-bottom:2px solid #ddd;">数据源</th><th style="padding:8px;text-align:left;border-bottom:2px solid #ddd;">规模</th><th style="padding:8px;text-align:left;border-bottom:2px solid #ddd;">特点</th><th style="padding:8px;text-align:left;border-bottom:2px solid #ddd;">compact 检测</th></tr>
    <tr><td style="padding:8px;border-bottom:1px solid #eee;"><strong><a href="https://github.com/uw-syfi/TraceLab">TraceLab</a></strong>（UW SYFI 聚合轨迹集）</td><td style="padding:8px;border-bottom:1px solid #eee;">357,161 轮 / 4,265 会话 / 23 模型</td><td style="padding:8px;border-bottom:1px solid #eee;">覆盖 Claude 与 GPT；轮次级元数据，<strong>不含工具内容</strong></td><td style="padding:8px;border-bottom:1px solid #eee;">token 突降</td></tr>
    <tr><td style="padding:8px;border-bottom:1px solid #eee;">自有 <strong>Codex</strong> 日志</td><td style="padding:8px;border-bottom:1px solid #eee;">495 会话 / 10,810 轮</td><td style="padding:8px;border-bottom:1px solid #eee;">含原生 compacted 事件与完整命令内容</td><td style="padding:8px;border-bottom:1px solid #eee;">原生事件</td></tr>
    <tr><td style="padding:8px;">自有 <strong>Claude Code</strong> 日志</td><td style="padding:8px;">5,856 会话</td><td style="padding:8px;">含完整 tool_use 文件路径与 usage</td><td style="padding:8px;">token 突降</td></tr>
  </table>
  <p>TraceLab 提供<strong>跨模型的广度</strong>（对比 23 个模型），但只有元数据；两份自有日志提供<strong>内容深度</strong>（命令、文件路径），能直接观测"重读补救"等行为。三者互相印证，任何单一数据的结论都需另外两个确认。</p>

  <h2 style="font-size:1.3em;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:36px;">一、先定义"能力"：output token 是个陷阱</h2>
  <p>最直觉的做法是看 compact 前后模型"产出"的变化。我们一开始也这么做了，发现很多模型 compact 后 output token 大幅下降（claude-opus-4-8 降了 52%），于是差点得出"严重退化"的结论。<strong>这是错的。</strong></p>
  <p>compact 前，上下文正逼近窗口上限，输出被"撑"得虚高；压缩后输出变短可能只是更高效。用 output token 衡量能力，等于把"上下文压力"误认成"能力"。我们改用一组更贴近能力的指标，并每次都明确定义：</p>
  <ul>
    <li><strong>错误率</strong>：工具调用被框架标记为失败的比例（如 Bash 非零退出码）。这是"工具执行失败"，不等于"模型回答错误"。</li>
    <li><strong>恢复率</strong>：出错后 3 轮内不再出错的比例——自我纠错能力。</li>
    <li><strong>盲目重试</strong>：出错后重试同一工具、3 轮内仍持续出错——陷入失败循环，最强的退化信号。</li>
  </ul>

  <h2 style="font-size:1.3em;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:36px;">二、第二个坑：一个坏会话，制造了"严重退化"的假象</h2>
  <p>在 TraceLab 聚合数据里，claude-opus-4-8 各项指标都很难看：compact 后错误率 8.8% → 21.6%，盲目重试 14% → 40%。按任何标准都是"严重退化"。但我们做了一次 <strong>outlier 敏感性检查</strong>——移除贡献错误最多的单个会话，重新计算——结论瞬间翻转：</p>
  <table style="width:100%;border-collapse:collapse;font-size:0.9em;font-family:-apple-system,sans-serif;margin:16px 0;">
    <tr style="background:#f5f5f2;"><th style="padding:8px;text-align:left;border-bottom:2px solid #ddd;">指标</th><th style="padding:8px;text-align:right;border-bottom:2px solid #ddd;">含异常会话</th><th style="padding:8px;text-align:right;border-bottom:2px solid #ddd;">剔除后</th></tr>
    <tr><td style="padding:8px;border-bottom:1px solid #eee;">compact 后错误率</td><td style="padding:8px;text-align:right;border-bottom:1px solid #eee;">21.6%</td><td style="padding:8px;text-align:right;border-bottom:1px solid #eee;">7.7%</td></tr>
    <tr><td style="padding:8px;border-bottom:1px solid #eee;">错误率变化</td><td style="padding:8px;text-align:right;border-bottom:1px solid #eee;">+12.9pp</td><td style="padding:8px;text-align:right;border-bottom:1px solid #eee;">+0.1pp</td></tr>
    <tr><td style="padding:8px;">盲目重试</td><td style="padding:8px;text-align:right;">40%</td><td style="padding:8px;text-align:right;">0%</td></tr>
  </table>
  <p>那个会话贡献了该模型 26% 的错误，单轮最多 18/21 个工具调用失败，且错误在 compact 前后都爆发——它是一个本身就坏掉的环境，与压缩无关。<strong>教训：任何小样本结论，先做 leave-one-out 检查。一个会翻转的判定，不是发现，是假象。</strong></p>
  <p>全模型检查后，真正稳健的"compact 后正确性退化"只剩 claude-opus-4-7 和 gpt-5.4；样本最大的 gpt-5.5 始终稳定。</p>

  <h2 style="font-size:1.3em;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:36px;">三、自己的数据：正确率不退化，但更"费力"了</h2>
  <p><strong>结论一：正确率基本不退化。</strong>Codex 的错误率、恢复率、盲目重试 compact 前后稳定；Claude 的错误率甚至<strong>下降</strong>（haiku 13.5% → 1.3%）——退化其实发生在 compact 之前（上下文逼近上限的"压力"状态），压缩重置后反而更干净。compact 是减压，不是伤害。</p>
  <p><strong>结论二：但模型明显更费力了。</strong>Codex 工具调用/轮从 9.3 翻倍到 17.3，且几乎全是编辑操作（apply_patch 1432 → 3021）；Claude 读取量增加约 45%。</p>

  <h2 style="font-size:1.3em;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:36px;">四、它在"回忆"吗？不，它在重做与补救</h2>
  <p>自有数据的内容让我们能区分"回忆"与"普通多干活"。答案是：<strong>主要是更多编辑，辅以少量定向重读。</strong></p>
  <ul>
    <li>读操作占比很小（&lt;3%），但<strong>性质变了</strong>：compact 后的读操作中约 48.5% 是重读"之前已看过的文件"（compact 前仅 7.7%）——真实的"丢失细节 → 重读补救"信号。</li>
    <li>我们抓到了现行：compact 后模型重新 <code>sed -n</code> 读已读过的 <code>core.py</code>，重新 <code>rg "def generate_until"</code> 定位一个它忘了的函数。</li>
    <li>编辑方面重改旧文件比例只略升（59.8% → 63.5%），说明翻倍不是大规模"重做丢失工作"，而是对同一批热点文件做更多迭代收敛。</li>
  </ul>
  <pre style="background:#f5f5f2;border-left:3px solid #ccc;padding:14px;font-size:0.85em;overflow-x:auto;font-family:'SF Mono',Menlo,monospace;">compact 丢失部分细节
   → 模型察觉，重读旧文件 / 重定位函数（补救）
   → 在信息不全下更多次编辑收敛
   → 最终结果仍正确（正确率不降）
   → 但多花了约 2 倍的步骤（效率税）</pre>
  <p><strong>正确率之所以不降，恰恰是因为模型用额外努力补偿了细节遗失。</strong>成果质量没退化，时间成本退化了——就像笔记被压缩的人，靠翻回原资料重查、多改几稿，保住了产出质量，但花了更多时间。</p>

  <h2 style="font-size:1.3em;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:36px;">五、局限：看不见的才是最危险的</h2>
  <ul>
    <li><strong>重读只是"成功补救"的部分。</strong>若模型丢了细节却没察觉、直接基于摘要继续（静默遗失），telemetry 抓不到，却可能造成隐蔽错误。"正确率不降"是观测结果，不代表零风险。</li>
    <li><strong>TraceLab 聚合数据没有内容</strong>，无法观测细节遗失；三份数据中只有自有数据能直接证实。</li>
    <li><strong>因果不是铁证。</strong>compact 恰发生在密集编辑阶段，"努力量上升"里有一部分是任务节奏。</li>
    <li>结论不能推广到所有模型：TraceLab 里 opus-4-7、gpt-5.4 是真退化。</li>
  </ul>

  <h2 style="font-size:1.3em;border-bottom:2px solid #eee;padding-bottom:6px;margin-top:36px;">六、给实践者的启示</h2>
  <ol>
    <li><strong>别用 output token 衡量能力</strong>，用错误/恢复类指标，并明确定义每个指标。</li>
    <li><strong>小样本先做 outlier 检查</strong>，一个会翻转的判定不可信。</li>
    <li><strong>compact 的真实成本是效率，不是正确性</strong>。优化方向应是让摘要保留"热点"信息（常被重读的文件、关键决策），降低补救成本。</li>
    <li><strong>警惕静默遗失</strong>：可见的重读是冰山一角，压缩摘要的质量决定了看不见的风险。</li>
  </ol>

  <p style="margin:44px 0 0;padding:22px 8px;border-top:1px solid #ddd;border-bottom:1px solid #ddd;text-align:center;font-size:1.12em;line-height:1.8;color:#111;">压缩没有让模型变笨——它只是让模型<strong>更费力地保持聪明</strong>。<br>而真正危险的，从来不是看得见的错误，而是<strong>看不见的遗失</strong>。</p>

  <p style="margin-top:40px;padding-top:16px;border-top:1px solid #eee;font-size:0.8em;color:#999;">数据与方法详见第〇节：<a href="https://github.com/uw-syfi/TraceLab">TraceLab</a> 聚合轨迹集（UW SYFI，357,161 轮）、作者自有 Codex（495 会话，含原生 compacted 事件）与 Claude Code（5856 会话，token 突降检测）日志。</p>
</div>
