---
layout: post
title: 一条招募推文，意外成了中文 Agent Harness 生态的一次普查
date: 2026-08-04 04:05:00 +0000
notion_page_id: 3b28111ab86481e48f5be1c99e929d8a
notion_url: https://ruddy-engineer-594.notion.site/Agent-Harness-3b28111ab86481e48f5be1c99e929d8a
---

8 月 1 日，DeepSeek Harness 团队的 Tianyi 在 X 上发了一条很短的推文：如果你是 Agent Harness 相关开源项目的开发者，想参加 DeepSeek Harness 内测，回复我，附上 GitHub id 和开源代表作。（原推文链接待补）

三天后，这条推文有 83 万次浏览、1000 多条回复。

我原本自己抓了一遍评论区，拿到 637 条回复、446 个仓库——然后在评论区里发现有人已经把这件事做得比我彻底得多。有人建了一个叫 [deepseek-harness-applicants](https://github.com/Octo-o-o-o/deepseek-harness-applicants) 的社区档案库，走 X 官方 API 全量抓取，把整场活动整理成了可检索、可审计、可复现的结构化数据：**1081 条回复、769 位报名开发者、712 个不重复仓库**，其中 704 个还拉了 GitHub 的 star / 语言 / 上线时间 / 最后更新快照，分了 18 个赛道，附排行榜、CSV 导出和一个静态站。

所以下面的数据以那份档案为准，我自己那 637 条主要提供另一样东西——报名者的**自述原话**。两份数据加起来，能看到的东西比任何一份单独看都多。

> ⚠️ 有一件事需要提前说：**这份名单里的 star 数正在剧烈变动，部分项目疑似刷星后正在被回收**（第七节有实测对比表）。所以下文所有 star 数默认为档案库 8 月 3 日的快照值，我在 8 月 4 日对文中点名的仓库做了逐一实测，实测有明显出入的地方会单独标注。

### 一、最反直觉的一点：这个生态非常新

先看总榜前 40 名的"上线时间"这一列。

| 项目 | Stars（快照） | 语言 | 创建时间 |
| --- | --- | --- | --- |
| nexu-io/open-design | 83,268 ✓ | TypeScript | **2026-04-28** |
| Egonex-AI/Understand-Anything | 77,233 ↓ | TypeScript | **2026-03-15** |
| santifer/career-ops | 62,573 ✓ | JavaScript | **2026-04-04** |
| HKUDS/nanobot | 46,528 ↓ | Python | **2026-02-01** |
| Hmbown/CodeWhale | 40,383 ✓ | Rust | **2026-01-19** |
| stablyai/orca | 36,013 ↓ | TypeScript | **2026-03-17** |
| esengine/DeepSeek-Reasonix | 29,298 ↓ | Go | **2026-04-21** |

（✓ = 8 月 4 日实测与快照一致；↓ = 实测已回落，详见第七节。）

总榜 40 个项目里，**有 12 个是 2026 年内新建的，而且快照时已跨过 5000 star**。其中 open-design 从建仓到 8.3 万 star 只用了三个月——这个数字我在 8 月 4 日实测过，是真的。

这个分布说明的不是"某个项目很火"，而是**整个赛道的时间轴被压缩了**。传统认知里，一个基础设施项目要三年才能积累几万 star（vllm 2023 年 2 月建仓，88k；lobehub 2023 年 5 月，81k）。而 harness 这一层，2026 年上半年建的仓库和它们已经站在同一个量级上。即便把疑似刷星的水分挤掉（后面会讲），open-design、CodeWhale、career-ops 这几个实测无水分的头部项目，也足以支撑这个判断。

再看"最后更新"：704 个有快照的仓库里，**三分之二在最近一周内有提交，42% 在抓取前两天（8 月 2–3 日）还在 push**。这不是一堆躺着的仓库，是一个正在同时高速推进的战场。

### 二、赛道分布：前三名吃掉了近一半

档案库把 712 个项目分成 18 个赛道（此处按全部 712 个项目计）：

| 赛道 | 项目数 |
| --- | --- |
| agent-harness | 130 |
| coding-agent | 112 |
| skills | 83 |
| agent-orchestration | 58 |
| memory-context | 57 |
| agent-workspace | 47 |
| tooling-automation | 39 |
| agent-client | 36 |
| infrastructure / creative-tools | 27 / 27 |
| security-governance / research-evaluation | 24 / 24 |
| developer-tools | 18 |
| research-tools | 10 |
| education | 6 |
| 其他（unclassified / other / domain-application） | 14 |

前三名（harness 内核 + coding agent + skills）合计 325 个，占 46%。这是最卷的地方——自研 agent loop、工具调用、会话持久化、Skills、MCP、多 provider，这套配置在报名描述里几乎成了标点符号。

我抓到的原始回复能补上这一层的质感：这一类里相当多的回复只有"报名"两个字加一个链接，没有任何差异化叙述。在一个 769 人的池子里，这基本等于弃权。

### 三、Prefix cache 命中率已经变成公开的产品卖点

这是我读完两份数据之后最确定的一个判断。

`esengine/DeepSeek-Reasonix`，Go 写的，快照 29,298 star（实测 27.8k，依然是 DeepSeek-native 项目里最大的），仓库简介第一句就是："A DeepSeek-native AI coding agent for your terminal. Engineered around prefix-cache..."——把缓存工程直接写进了一句话定位里。

在我抓到的自述原话里，这条线更密集：`huiliyi37/Tianshu-Tui`（天枢）说针对 DeepSeek V4 做了前缀缓存工程优化，长会话实测稳态命中率 95–99%；`liliMozi/openhanako`（Hana）说群友在上面跑出过 99% 的缓存命中率，"对 DeepSeek 的优化也是最多的——识图、利用缓存压缩、官方人格补丁"；`ddlady342982/token-overload` 走的是另一条路，让强模型只做规划和验收、弱模型干所有读写代码的脏活，程序自动验证兜底，自述编程任务的强模型 token 省约 60%（该仓库 8 月 4 日核验时已 404，是档案库标记的 8 个失效仓库之一）。

与之并行的是**长程状态**这条线。`huangruiteng/loopx` 做长程任务的 state kernel，声称能让通用 agent 超长程执行 200+ 小时状态不漂移；`kyrielrving11/LoopForge` 的表述最精准——"context window 是为 attention 设计的，不是为 persistence 设计的"【核】，所以把跨轮次的认知状态当成一个运行时基础设施问题来解；`AttemorySystem/attemory` 更激进，把原始语料索引成可复用的 KV state，然后用 attention 本身做检索；`EverMind-AI/Raven` 是记忆 + 深度交叉检索 + 自进化。

把这两条线放一起：**harness 层的竞争焦点已经从"能不能跑通"迁移到"每一轮请求有多少 token 是白付的"**。这恰好是 DeepSeek 定价结构里最有竞争力也最需要真实压测的部分。这批报名者非常清楚自己要测什么。

### 四、双重空白：安全和评测，做的人少，看的人更少

**security-governance 只有 24 个项目**。剔掉明显的误分类（mindcraft、kube-ovn 这类高星但与 agent 安全无关的项目），真正在做 agent 安全治理的项目 star 数是这样的：

- `SponsioLabs/Sponsio` 467 —— 给概率性 AI agent 做确定性策略执行
- `xicilion/boxsh` 325 —— MCP 协议极速沙箱，单进程解决安全文件操作 + 进程沙箱 + CoW 文件系统
- `chainreactors/aiscan` 221 —— 安全方向 agent，单文件二进制做渗透测试
- `Ephemeral-AI-Lab/ephemeral-sandbox` 52
- `ythx-101/agent-sop` 46 —— human-gated 协作流，跨厂商独立审查 + 结构化 signoff
- `talesofai/cohub` **11** —— 多 agent harness，团队自己一周烧 34B token 压测过

**research-evaluation 也只有 24 个**，除了 `benchflow-ai/skillsbench`（1,622）和归在这个赛道的 AutoSci，其余大多两位数：

- `benchflow-ai/benchflow` 308
- `Jayden-X-L/forkprobe` **48** —— 同一任务并排试跑多个候选 skill，出 HTML 报告选 winner
- `shi275773124/Falsify` **4**（8 月 4 日实测只剩 1）—— 对抗审查 AI 产出，输出 PASS / PASS_WITH_DEBT / BLOCK

对照一下：一个三个月前建仓的 coding agent 能拿 8 万 star，一个专门解决"agent 谎报完成"的验证工具拿 4 个 star——实测甚至只剩 1 个。

这不只是"没人做"，而是**做了也没人看**。而这批项目要解决的恰恰是所有人都在抱怨的问题——agent 会声称自己完成了没有完成的工作。`rrrrrredy/beforedone` 的设计是把 verifier 的 PASS 结果绑定到当前相关文件的状态上，agent 宣布完成时用 Stop Hook 识别缺失或过期的验证证据，并保留可审计的 receipt、incident 和 replay。`Codegass/Setup-Agent` 已经把相关论文发在了 ICSE 2026 的 NIER track。

`education` 赛道 6 个项目，star 分别是 19、14、1、1、0、0，可以放在一起看。

顺带补几个别的空白点：系统级可观测性整个名单里基本只有 `eunomia-bpf/agentsight`（C 写的 eBPF profiler / debugger / OS 安全策略）一个；成本与 token 经济学除了 token-overload 只有 `dothinkerlab/AgentMeter`；Computer Use 方向虽然有 `hangwin/mcp-chrome`（11.8k，实测）、`browser-use/web-ui`（16k）、`web-infra-dev/midscene`（13.6k，实测）这些高星项目，但数量上仍然是个位数量级，且端侧方向只有 `OpenMinis/OpenMinis` 和一个做**物理操作 iPhone** 的 `physiclaw/PhysiClaw`。

### 五、语言：TypeScript 主导，Rust 是明显的新势力

总榜前 40 里 TypeScript 正好占一半。这符合预期——harness 的主战场是 CLI/TUI 和桌面壳。

值得单独说的是 Rust 的密度（以下均为快照值）。`Hmbown/CodeWhale`（40,383，实测无水分）、`ZSeven-W/openpencil`（4,557）、`xingkongliang/skills-manager`（3,469）、`yologdev/yoyo-evolve`（1,851）、`GCWing/BitFun`（1,397）、`openinfer-project/openinfer`（621，纯 Rust + CUDA 推理引擎不用 PyTorch）、`nowledge-co/con-terminal`（540）、`Ephemeral-AI-Lab/ephemeral-sandbox`、`aeroxy/ast-bro`、`noumena-labs/Sipp`——在 agent runtime、沙箱、AST 处理这几个对性能和内存安全敏感的位置，Rust 已经站住了。

Go 在网关和后端类项目里稳定出现（DeepSeek-Reasonix、gpt-load、yao、goclaw、ds2api、dynamicgo、cofy-x/axern）。

### 六、名单里有噪声，而且档案库自己标出来了

这份档案有个我很欣赏的地方：它在 README 里明确写着"高星不等于高相关"，并且专门维护了一份异常清单：10 个仓库被多人重复认领、8 个高星仓库与 harness 相关性弱、166 个组织仓库报名者未必是真正 owner、19 个是 fork。

确实有一批项目跟 Agent Harness 关系很弱，但因为高星排在了前面：`badges/shields`（27,011，2013 年建仓）和 `simple-icons`（25,546，2012 年）都是同一位报名者的项目；`drakeet/MultiType`（5,759，2016 年，最后更新 2022 年）的作者自己在回复里就说得很清楚——"曾经人类编程时代的开源代表作"。

还有跨数据源的署名分歧。`Hmbown/CodeWhale` 在档案库里同时被三个人认领，而在我抓到的原始回复里，@nightt5879 说的是"我是 deepseek tui 开发者现在叫做 CodeWhale，贡献第三"。档案库自己也留了 111 位"有项目但没显式给出 GitHub ID"的待确认清单，并且立了一条很克制的规则：**仓库 owner 绝不冒充报名者身份**。

这类噪声不影响趋势判断，但如果你要拿这份名单做尽调，需要自己回溯原始回复。

### 七、比噪声更严重的：star 正在被成批回收

上面那些是档案库自己标出来的噪声。下面这个是我做实测时撞见的，档案库没标，可能它建库时也不知道。

我在 8 月 4 日把本文点名的仓库逐一打开对了一遍实时 star 数，距离档案库快照只过了一天：

| 仓库 | 快照 8/3 | 实测 8/4 | 变化 |
| --- | --- | --- | --- |
| usewhale/whale | 965 | **100** | **-90%** |
| LING71671/open-reverselab | 965 | **9** | **-99%** |
| OpenMinis/OpenMinis | 3,032 | **211** | **-93%** |
| xuzhougeng/wisp-science | 834 | **36** | **-96%** |
| Cai-aa/CAE-Agent-Hub | 667 | 398 | -40% |
| liliMozi/openhanako | 5,706 | ~4,800 | -16% |
| HKUDS/nanobot | 46,528 | ~41,800 | -10% |
| Egonex-AI/Understand-Anything | 77,233 | ~73,500 | -5% |
| esengine/DeepSeek-Reasonix | 29,298 | ~27,800 | -5% |
| stablyai/orca | 36,013 | ~34,800 | -3% |
| open-design / CodeWhale / career-ops / AutoSci / boxsh / forkprobe | — | 与快照一致 | 稳定 |

star 数是不会自然下跌的，成批消失基本只有一种解释：**刷上去的星正在被 GitHub 清退**。一天之内，有项目掉了九成，头部项目也在以每天几个百分点的速度漏气；同时另一批项目（open-design、CodeWhale、career-ops）实测与快照分毫不差——真假在同一张榜单上泾渭分明。

最完整的一个样本是 `usewhale/whale`：快照时它 965 star，简介是英文的"blazingly fast, terminal-first AI coding agent for DeepSeek. ~98% prompt cache hit rate"；一天后它只剩 100 star，简介换成了中文，缓存命中率的口径也从 98% 调低到了"90% live prefix-cache hit"。星在回收，宣传口径在回撤，同步发生。

这件事和本文第四节是同一个主题的两面：agent 会谎报自己完成了工作，而**它们的作者，有一部分也在谎报自己的项目有多少人在用**。一场以"筛选可靠的 harness 开发者"为目的的报名，本身就成了一次可靠性测试——而且已经有人没通过。

所以：如果你拿这份名单做任何筛选，**不要单看 star**，看提交历史、看 issue 质量、看 star 增长曲线是不是自然的。这句话本来是句常识，现在它有了实测数据支撑。

### 八、开发者构成：门槛已经低到不像一个基础设施领域

769 位报名者，翻他们的自我介绍时，最打动我的不是技术，是身份。

有人说自己"技术起点是汽车车身控制器硬件工程师，熟悉 CAN 协议"【核】，现在在做多 agent 平台；有人是产品经理，说"我并不是程序员，但会着重从用户视角出发去理解并构建 harness 相关的工具"【核】；有人是"电子专业大二本科生"，维护着一个 mspm0 的 skill；有人自称"只会 matlab 但是几乎不用，现在重度依赖 agent 的非专业开发者"【核】；还有人说"我也不会推广，评论区的大部分作品我都下载试用学习过，大佬太多了，俺的项目只有自己在用，但好想学习啊啊啊啊"【核】。

垂类项目的分布印证了这一点：`Cai-aa/CAE-Agent-Hub` 把主流工程仿真软件封成 MCP server 和求解器脚本；`PaRr0tBoY/Pola-Agent` 把 SolidWorks 的 VBA 脚本内化成了 agent 的工具；`fanfan520zzq/hard-dsp-harness` 的作者是嵌入式方向的学生，在尝试让 agent 全自动读数据手册、调烧录工具、接示波器和逻辑分析仪；`xuzhougeng/wisp-science` 给科研场景提供持久化的 Python/R 执行环境和 SSH 远程计算；`skyllwt/AutoSci`（1,599 star，实测无水分）自述来自北大 DAIR Lab。

这些人不是 infra 工程师，是各自领域里被 coding agent 赋能之后，顺手把 harness 也做了的人。**一个基础设施领域出现大量非专业开发者，通常意味着上一层的抽象已经足够好用了。**

代价是质量方差极大。档案库老实记着：769 位报名者里有 130 位没贴任何项目（只表态、只给主页），8 个仓库已经 404，17 个项目连描述都没有。

### 九、一个次生现象

这件事最后长出了三层结构。

第一层是 769 位报名者。第二层是那个档案库——有人把整个评论区抓下来做成公开仓库和网站，理由写在提交说明里："感觉是中文环境的 Harness 大神团建，把所有的项目都抓了一遍，方便大家查看，时间截止北京时间 2026 年 8 月 3 日早上 11 点左右，如有遗漏勿怪。"【核】第三层是发现自己被漏抓的人：`lloydzhou` 专门二次报名，附了一句"我发现其他人抓取的回复里面没有我的记录，我得多报一次名"【核】。

还有人在评论区里直接问："话说都是来找内测机会的？没有来看 comment 里项目的嘛？哈哈哈哈哈哈"【核】

一个招募帖，72 小时内变成了社区资源、变成了被二次索引和交叉核对的公共数据集、变成了社交场——顺带还触发了一轮对刷星的公开清算。这件事本身比里面任何一个单独的项目都更能说明这个生态现在的温度。

### 十、如果你现在想入场：这份数据给新手的五条启发

前面九节是诊断，这一节是处方。如果你看完这份名单想动手做点什么，数据本身已经把路指得很清楚了。

**1. 别再写下一个通用 CLI 内核。**

agent-harness + coding-agent 两个赛道已经有 242 个项目，而且头部已经有了实测无水分的 4 万、8 万 star 项目。在这个赛道里，你的 agent loop 不会比前 242 个好多少——那些只能写出"报名"两个字的回复就是证据：当你在一个赛道里连一句差异化叙述都写不出来时，进去就等于弃权。

**2. 最快的路线是给底座当"配件商"，不是当"整机厂"。**

pi、Claude Code、Codex、Kimi Code、opencode、openclaw 这几个底座的生态位分化刚刚开始，skills 赛道 83 个项目里已经有人靠一个单点插件做到几千 star。做插件的好处是你不用自己解决 harness 最难的那部分（loop、缓存、会话持久化），一个人一两周就能出可用的东西，而且底座的用户就是你的分发渠道。

**3. 空白赛道是真空白，但要想清楚"没人看"的原因。**

评测和安全治理各 24 个项目、系统级可观测 1 个、token 经济学 2 个——位置确实很空。但 Falsify 只有 1 个 star 说明这类工具缺的不是功能，是分发：没人会为"验证"单独装一个工具。更可能跑通的做法是把验证、可观测、成本监控做成某个底座的插件或默认体验的一部分，借第 2 条的生态分发——把"最空的赛道"和"最现成的渠道"连起来，这个交叉点上现在一个人都没有。

**4. 把一个可验证的数字写进项目简介的第一句话。**

这次跑出来的 DeepSeek-native 项目，共同点是把 prefix cache 命中率直接写进了一句话定位（"Engineered around prefix-cache"）。在一个 769 人的池子里，能被记住的项目都是一句话里带数字的。但只写真的——第七节已经演示了谎报的下场：whale 把 98% 改口成 90% 的同时，star 掉了九成。刷星同理，现在清退是批量的、公开的、携带羞辱的。

**5. 垂类经验是你唯一不会被卷的护城河。**

这份名单里最有生命力的一批项目，作者都不是 infra 工程师：把仿真软件封成 MCP 的、把 SolidWorks VBA 内化成工具的、让 agent 接示波器的。通用 agent 能力会被底座和模型不断吞掉，但"知道 Abaqus 的求解器怎么调"这件事，模型短期内学不会，卷不进来的人也卷不走。如果你有一个领域，把它的工具链接进 agent 生态，就是你的项目。

时间窗口是真实的——这个生态三个月能长出 8 万 star 的项目。但留给"又一个 CLI"的窗口已经关了，开着的是另外几扇：生态配件、可靠性基础设施、垂类接入。

### 最后

如果要我用一句话总结这 712 个仓库：**中文 Agent Harness 生态正处在"功能极度过剩、可靠性极度稀缺"的转折点上。**

46% 的项目在做已经有一百个人做过的事；一个三个月前建仓的 coding agent 能拿货真价实的 8 万 star，而一个专门验证"agent 是不是真的做完了"的工具实测只有 1 个 star；与此同时，榜单上还有一批项目的 star 是刷出来的，正在被一颗一颗收回去。功能的边际收益已经很低了，可靠性的缺口却从模型层一直延伸到了社区层。

至于安全治理、评测基础设施、系统级可观测、token 经济学这几块——如果你正在想做点什么，那儿的位置还很空，而且空得有点反常。

---

报名者自述原话来自我自己对同一条推文评论区的独立抓取（637 条去重回复 / 446 个仓库），用于交叉核对与补充语料。

文中 star 数默认为 2026-08-03 快照值，非实时；文中点名的仓库已于 8 月 4 日逐一实测，标注"实测"或"✓"的为实测确认值，第七节的对比表列出了全部出入。"刷星被回收"是基于 star 成批下跌这一观测的推断，GitHub 未就个别仓库发布说明。报名者自述的评测分数、下载量、缓存命中率未做交叉核实。

### 附录：总榜 Top 100（快照 2026-08-03）

数据来自档案库 `exports/leaderboards.csv`。star 数为 8 月 3 日快照值；标 ✓ 的为 8 月 4 日实测与快照一致，标 ↓ 的为实测已回落（详见第七节），未标记的未做实测。

| # | 项目 | Stars（快照） | 赛道 | 语言 | 创建时间 |
| --- | --- | --- | --- | --- | --- |
| 1 | [vllm-project/vllm](https://github.com/vllm-project/vllm) | 88,004 | memory-context | Python | 2023-02-09 |
| 2 | [nexu-io/open-design](https://github.com/nexu-io/open-design) | 83,268 ✓ | coding-agent | TypeScript | 2026-04-28 |
| 3 | [lobehub/lobehub](https://github.com/lobehub/lobehub) | 81,142 | agent-workspace | TypeScript | 2023-05-21 |
| 4 | [bytedance/deer-flow](https://github.com/bytedance/deer-flow) | 79,024 | agent-harness | Python | 2025-05-07 |
| 5 | [Egonex-AI/Understand-Anything](https://github.com/Egonex-AI/Understand-Anything) | 77,233 ↓ | developer-tools | TypeScript | 2026-03-15 |
| 6 | [santifer/career-ops](https://github.com/santifer/career-ops) | 62,573 ✓ | coding-agent | JavaScript | 2026-04-04 |
| 7 | [HKUDS/nanobot](https://github.com/HKUDS/nanobot) | 46,528 ↓ | memory-context | Python | 2026-02-01 |
| 8 | [Hmbown/CodeWhale](https://github.com/Hmbown/CodeWhale) | 40,383 ✓ | agent-harness | Rust | 2026-01-19 |
| 9 | [chatchat-space/Langchain-Chatchat](https://github.com/chatchat-space/Langchain-Chatchat) | 38,498 | memory-context | Python | 2023-03-31 |
| 10 | [stablyai/orca](https://github.com/stablyai/orca) | 36,013 ↓ | agent-orchestration | TypeScript | 2026-03-17 |
| 11 | [esengine/DeepSeek-Reasonix](https://github.com/esengine/DeepSeek-Reasonix) | 29,298 ↓ | coding-agent | Go | 2026-04-21 |
| 12 | [badges/shields](https://github.com/badges/shields) | 27,011 | tooling-automation | JavaScript | 2013-01-30 |
| 13 | [QwenLM/qwen-code](https://github.com/QwenLM/qwen-code) | 26,530 | coding-agent | TypeScript | 2025-06-26 |
| 14 | [simple-icons/simple-icons](https://github.com/simple-icons/simple-icons) | 25,546 | tooling-automation | JavaScript | 2012-11-16 |
| 15 | [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin) | 23,713 | coding-agent | TypeScript | 2025-10-09 |
| 16 | [readest/readest](https://github.com/readest/readest) | 23,026 | other | TypeScript | 2024-10-12 |
| 17 | [can1357/oh-my-pi](https://github.com/can1357/oh-my-pi) | 21,376 | coding-agent | TypeScript | 2025-12-31 |
| 18 | [coze-dev/coze-studio](https://github.com/coze-dev/coze-studio) | 21,318 | infrastructure | TypeScript | 2025-06-26 |
| 19 | [Mikubill/sd-webui-controlnet](https://github.com/Mikubill/sd-webui-controlnet) | 17,852 | creative-tools | Python | 2023-02-12 |
| 20 | [camel-ai/camel](https://github.com/camel-ai/camel) | 17,530 | agent-orchestration | Python | 2023-03-17 |
| 21 | [browser-use/web-ui](https://github.com/browser-use/web-ui) | 16,257 | tooling-automation | Python | 2025-01-02 |
| 22 | [eigent-ai/eigent](https://github.com/eigent-ai/eigent) | 14,720 | coding-agent | TypeScript | 2025-07-29 |
| 23 | [electerm/electerm](https://github.com/electerm/electerm) | 14,645 | developer-tools | JavaScript | 2017-10-07 |
| 24 | [YishenTu/claudian](https://github.com/YishenTu/claudian) | 14,504 | agent-client | TypeScript | 2025-12-05 |
| 25 | [web-infra-dev/midscene](https://github.com/web-infra-dev/midscene) | 14,469 ↓ | infrastructure | TypeScript | 2024-07-23 |
| 26 | [plait-board/drawnix](https://github.com/plait-board/drawnix) | 14,367 | creative-tools | TypeScript | 2024-06-04 |
| 27 | [hangwin/mcp-chrome](https://github.com/hangwin/mcp-chrome) | 12,247 ↓ | tooling-automation | TypeScript | 2025-06-09 |
| 28 | [tt-a1i/archify](https://github.com/tt-a1i/archify) | 8,611 | skills | HTML | 2026-04-15 |
| 29 | [yaoapp/yao](https://github.com/yaoapp/yao) | 7,555 | agent-client | Go | 2021-09-06 |
| 30 | [l0o0/jasminum](https://github.com/l0o0/jasminum) | 7,115 | research-tools | TypeScript | 2020-06-16 |
| 31 | [open-multi-agent/open-multi-agent](https://github.com/open-multi-agent/open-multi-agent) | 6,705 | agent-orchestration | TypeScript | 2026-03-31 |
| 32 | [crisxuan/bestjavaer](https://github.com/crisxuan/bestjavaer) | 6,615 | agent-orchestration | JavaScript | 2020-06-03 |
| 33 | [DerekYRC/mini-spring](https://github.com/DerekYRC/mini-spring) | 6,371 | coding-agent | Java | 2020-11-17 |
| 34 | [op7418/CodePilot](https://github.com/op7418/CodePilot) | 6,325 | skills | TypeScript | 2026-02-06 |
| 35 | [tbphp/gpt-load](https://github.com/tbphp/gpt-load) | 6,260 | infrastructure | Go | 2025-06-06 |
| 36 | [ThinkInAIXYZ/deepchat](https://github.com/ThinkInAIXYZ/deepchat) | 6,186 | agent-client | TypeScript | 2025-02-14 |
| 37 | [drakeet/MultiType](https://github.com/drakeet/MultiType) | 5,759 | other | Kotlin | 2016-08-03 |
| 38 | [netease-youdao/LobsterAI](https://github.com/netease-youdao/LobsterAI) | 5,750 | agent-workspace | TypeScript | 2026-02-12 |
| 39 | [liliMozi/openhanako](https://github.com/liliMozi/openhanako) | 5,706 ↓ | agent-client | TypeScript | 2026-03-15 |
| 40 | [Mai-with-u/MaiBot](https://github.com/Mai-with-u/MaiBot) | 5,634 | agent-client | Python | 2025-02-25 |
| 41 | [KunAgent/Kun](https://github.com/KunAgent/Kun) | 5,615 | agent-workspace | TypeScript | 2026-05-21 |
| 42 | [mindcraft-bots/mindcraft](https://github.com/mindcraft-bots/mindcraft) | 5,593 | security-governance | JavaScript | 2023-08-16 |
| 43 | [looplj/axonhub](https://github.com/looplj/axonhub) | 4,854 | developer-tools | Go | 2025-09-09 |
| 44 | [CJackHwang/ds2api](https://github.com/CJackHwang/ds2api) | 4,761 | infrastructure | Go | 2026-01-21 |
| 45 | [l0o0/translators_CN](https://github.com/l0o0/translators_CN) | 4,698 | research-tools | JavaScript | 2019-11-21 |
| 46 | [MaaXYZ/MaaFramework](https://github.com/MaaXYZ/MaaFramework) | 4,574 | tooling-automation | C++ | 2023-04-24 |
| 47 | [ZSeven-W/openpencil](https://github.com/ZSeven-W/openpencil) | 4,557 | creative-tools | Rust | 2026-02-17 |
| 48 | [binaricat/Netcatty](https://github.com/binaricat/Netcatty) | 4,536 | developer-tools | TypeScript | 2025-12-06 |
| 49 | [phodal/auto-dev](https://github.com/phodal/auto-dev) | 4,521 | agent-orchestration | Kotlin | 2023-04-14 |
| 50 | [oomol-lab/open-connector](https://github.com/oomol-lab/open-connector) | 4,131 | tooling-automation | TypeScript | 2026-06-29 |
| 51 | [nextlevelbuilder/goclaw](https://github.com/nextlevelbuilder/goclaw) | 3,501 | agent-harness | Go | 2026-02-22 |
| 52 | [EverMind-AI/Raven](https://github.com/EverMind-AI/Raven) | 3,480 | memory-context | Python | 2026-05-21 |
| 53 | [xingkongliang/skills-manager](https://github.com/xingkongliang/skills-manager) | 3,469 | skills | Rust | 2026-03-02 |
| 54 | [strukto-ai/mirage](https://github.com/strukto-ai/mirage) | 3,377 | memory-context | TypeScript | 2026-05-06 |
| 55 | [VectifyAI/OpenKB](https://github.com/VectifyAI/OpenKB) | 3,241 | memory-context | Python | 2026-04-04 |
| 56 | [XiaoMi/xiaomi-miloco](https://github.com/XiaoMi/xiaomi-miloco) | 3,184 | memory-context | Python | 2025-11-06 |
| 57 | [jihe520/MathModelAgent](https://github.com/jihe520/MathModelAgent) | 3,126 | skills | Python | 2025-01-30 |
| 58 | [OpenMinis/OpenMinis](https://github.com/OpenMinis/OpenMinis) | 3,032 ↓ | agent-client | Swift | 2026-04-25 |
| 59 | [teaql/teaql-agent-kit](https://github.com/teaql/teaql-agent-kit) | 2,803 | agent-harness | — | 2018-12-17 |
| 60 | [BannyLon/DifyAIA](https://github.com/BannyLon/DifyAIA) | 2,624 | tooling-automation | HTML | 2024-10-14 |
| 61 | [metatool-ai/metamcp](https://github.com/metatool-ai/metamcp) | 2,575 | agent-orchestration | TypeScript | 2025-01-22 |
| 62 | [heshengtao/super-agent-party](https://github.com/heshengtao/super-agent-party) | 2,543 | agent-harness | JavaScript | 2025-03-08 |
| 63 | [spring-ai-alibaba/DataAgent](https://github.com/spring-ai-alibaba/DataAgent) | 2,390 | domain-application | Java | 2025-09-12 |
| 64 | [kubeovn/kube-ovn](https://github.com/kubeovn/kube-ovn) | 2,361 | security-governance | Go | 2019-03-22 |
| 65 | [oiov/wr.do](https://github.com/oiov/wr.do) | 2,271 | coding-agent | TypeScript | 2024-07-26 |
| 66 | [lioensky/VCPToolBox](https://github.com/lioensky/VCPToolBox) | 2,226 | memory-context | JavaScript | 2025-05-12 |
| 67 | [org2AI/ORG2](https://github.com/org2AI/ORG2) | 2,181 | agent-harness | TypeScript | 2026-06-01 |
| 68 | [openakita/openakita](https://github.com/openakita/openakita) | 1,895 | agent-harness | Python | 2026-01-30 |
| 69 | [proma-ai/Proma](https://github.com/proma-ai/Proma) | 1,881 | tooling-automation | TypeScript | 2026-01-31 |
| 70 | [yologdev/yoyo-evolve](https://github.com/yologdev/yoyo-evolve) | 1,851 | agent-harness | Rust | 2026-03-01 |
| 71 | [benchflow-ai/skillsbench](https://github.com/benchflow-ai/skillsbench) | 1,622 | research-evaluation | PDDL | 2025-12-29 |
| 72 | [skyllwt/AutoSci](https://github.com/skyllwt/AutoSci) | 1,599 ✓ | research-evaluation | Python | 2026-04-09 |
| 73 | [tddworks/baguette](https://github.com/tddworks/baguette) | 1,596 | tooling-automation | Swift | 2026-05-01 |
| 74 | [DeadWaveWave/opencove](https://github.com/DeadWaveWave/opencove) | 1,550 | coding-agent | TypeScript | 2026-03-09 |
| 75 | [kenryu42/cc-safety-net](https://github.com/kenryu42/cc-safety-net) | 1,466 | coding-agent | TypeScript | 2025-12-25 |
| 76 | [myshell-ai/AIlice](https://github.com/myshell-ai/AIlice) | 1,413 | tooling-automation | Python | 2023-10-16 |
| 77 | [GCWing/BitFun](https://github.com/GCWing/BitFun) | 1,397 | memory-context | Rust | 2026-02-02 |
| 78 | [nianhua99/PandoraHelper](https://github.com/nianhua99/PandoraHelper) | 1,354 | other | TypeScript | 2023-12-18 |
| 79 | [poco-ai/poco-claw](https://github.com/poco-ai/poco-claw) | 1,343 | agent-harness | Python | 2026-01-08 |
| 80 | [Lapis0x0/obsidian-yolo](https://github.com/Lapis0x0/obsidian-yolo) | 1,288 | agent-workspace | TypeScript | 2025-06-02 |
| 81 | [Team-Commonly/commonly](https://github.com/Team-Commonly/commonly) | 1,283 | agent-orchestration | TypeScript | 2025-02-03 |
| 82 | [via007/bilibili-rag](https://github.com/via007/bilibili-rag) | 1,277 | memory-context | Python | 2026-01-25 |
| 83 | [Vizards/deepseek-v4-for-copilot](https://github.com/Vizards/deepseek-v4-for-copilot) | 1,272 | coding-agent | TypeScript | 2026-04-24 |
| 84 | [mem9-ai/mem9](https://github.com/mem9-ai/mem9) | 1,174 | memory-context | TypeScript | 2026-03-08 |
| 85 | [clacky-ai/openclacky](https://github.com/clacky-ai/openclacky) | 1,159 | skills | Ruby | 2025-12-30 |
| 86 | [nevertoday/zhongguo-traditional-colors](https://github.com/nevertoday/zhongguo-traditional-colors) | 1,141 | skills | HTML | 2026-06-03 |
| 87 | [CreminiAI/skillpack](https://github.com/CreminiAI/skillpack) | 1,124 | skills | TypeScript | 2026-03-15 |
| 88 | [maka-agent/maka-agent](https://github.com/maka-agent/maka-agent) | 1,108 | agent-client | TypeScript | 2026-05-27 |
| 89 | [ChesterRa/cccc](https://github.com/ChesterRa/cccc) | 1,065 | agent-orchestration | Python | 2025-08-15 |
| 90 | [weiesky/cc-viewer](https://github.com/weiesky/cc-viewer) | 1,056 | coding-agent | JavaScript | 2026-02-17 |
| 91 | [QuantumBFS/Yao.jl](https://github.com/QuantumBFS/Yao.jl) | 1,037 | research-tools | Julia | 2018-04-13 |
| 92 | [LING71671/open-reverselab](https://github.com/LING71671/open-reverselab) | 965 ↓ | security-governance | Python | 2026-06-17 |
| 93 | [usewhale/whale](https://github.com/usewhale/whale) | 965 ↓ | coding-agent | Go | 2026-05-06 |
| 94 | [Orkas-AI/Orkas](https://github.com/Orkas-AI/Orkas) | 961 | skills | TypeScript | 2026-04-29 |
| 95 | [huifer/WellAlly-health](https://github.com/huifer/WellAlly-health) | 911 | domain-application | Shell | 2025-12-31 |
| 96 | [proxysoul/Empryo](https://github.com/proxysoul/Empryo) | 893 | agent-orchestration | TypeScript | 2026-03-01 |
| 97 | [xuzhougeng/wisp-science](https://github.com/xuzhougeng/wisp-science) | 834 ↓ | agent-workspace | HTML | 2026-07-01 |
| 98 | [xlang-ai/OpenCUA](https://github.com/xlang-ai/OpenCUA) | 808 | tooling-automation | Python | 2025-06-21 |
| 99 | [shenseanchen/waku-agent](https://github.com/shenseanchen/waku-agent) | 789 | memory-context | Python | 2026-07-10 |
| 100 | [vinhnx/VTCode](https://github.com/vinhnx/VTCode) | 783 | coding-agent | Rust | 2025-08-29 |
