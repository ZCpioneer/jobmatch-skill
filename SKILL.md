---
name: job-match
description: 上传 PDF/DOCX/TXT/Markdown 简历做岗位匹配（完整 1 credit/次、快速 0.1 credit/次），或免费按关键词/城市搜索每日更新的岗位池（不需要简历）。免费 5 次完整匹配/月。用户说“帮我找匹配的岗位”“这份简历适合投什么”“杭州有哪些后端岗位”“跑一下岗位匹配”时使用。
---

# JobMatch · 简历岗位匹配

## 解决什么问题

用户手里有一份简历，想知道当前岗位池里最值得投的 5 个岗位；不需要自己解析 PDF，也不需要自己写 prompt。

## 何时使用

- 用户上传/给出简历文件，问“适合什么岗位”“帮我匹配一下”。
- 用户给出岗位方向 + 城市，想快速看 Top 5。
- 用户没给简历，只想“看看杭州有哪些后端岗位”“最近有哪些 AI Agent 岗位”。
- 用户问“我还有多少次额度/多少 credits”。

## 输入

- `file`：PDF / DOCX / TXT / Markdown 简历路径（与 `--text`、`--me`、`--list` 四选一）；
- `--text`：直接传简历文本；
- `city`：可选，目标城市（如 `杭州`、`深圳`）。匹配时它是排序加权，不是硬过滤；`--list` 时它是硬过滤（`city`/`location_raw` 包含该城市）；

- `limit`：可选；匹配默认 5（最大 10），`--list` 默认 5（最大 20）；
- `--list`：免费岗位搜索，不需要简历；**只搜职位名/公司名，不扫 JD 正文**；配合 `--q`（关键词/公司）和 `--city`；没有结果时换更短的关键词，不要反复扩大同义词；

- `--quick`：快速匹配，只走向量召回，0.1 credit/次，不占用免费额度；
- `--me`：只查额度，不做匹配。

## 账号与 Key（每个用户自己的 Key）

1. 没有 Key 时，引导用户到 `https://zcpionner.cloud/account/login?mode=signup` 用邮箱注册；
2. 登录后在 `https://zcpionner.cloud/account/` 创建一个个人 Key（形如 `jm_live_...`，只显示一次）；
3. 把 Key 放进环境变量 `JOBMATCH_API_KEY`，或在客户端密钥管理里保存；**不要写进 Skill 包、脚本或聊天记录**；
4. 免费 **5 次完整匹配/月**、每分钟 6 次；快速匹配 **0.1 credit/次**，完整匹配 **1 credit/次**；免费岗位搜索不扣额度；
5. 查额度：运行 `python3 scripts/match_jobs.py --me`（或 `GET /api/v1/me`）。

### 额度

| 项目 | 规则 |
|---|---|
| 免费岗位搜索 | `--list`，不扣额度；每日更新，返回最新 20 条/页 |
| 免费完整匹配 | 5 次/月；每次 Top 5 + 链接 |
| 快速匹配 | 0.1 credit/次；向量召回，最快，适合反复筛 |
| 完整匹配 | 1 credit/次（免费额度用完后） |
| 深度报告 | 9 credits，在 JobMatch 网站生成（不在 Skill 内支付） |

额度用完时，告诉用户到 https://zcpionner.cloud/account/billing?sku=credits_10 获取 credits；**具体价格以网站为准，Skill 内不展示价格、不收款、不代付**。

没有 Key 时接口直接返回 401，不要猜测或复用别人的 Key。

## 工作流程

1. 先判断用户要什么：
   - 没有简历、只想看岗位 → `--list`（免费，不用上传简历）；
   - 有简历、想快速筛 → `--quick`（0.1 credit，最快）；
   - 有简历、要完整 Top 5 → 默认完整匹配（1 credit，免费额度内不扣）。
2. 确认用户简历路径；不要读取/回显简历正文，不要上传到其他服务。
3. 运行：

```bash
# 免费岗位搜索（不需要简历）
python3 scripts/match_jobs.py --list --q "后端" --city "杭州" --limit 10

# 快速匹配（0.1 credit）
python3 scripts/match_jobs.py --file "/path/to/resume.pdf" --quick --city "杭州"

# 完整匹配（免费 5 次/月，之后 1 credit）
python3 scripts/match_jobs.py --file "/path/to/resume.pdf" --city "杭州" --limit 5
```

4. 脚本把文件以 `multipart/form-data` 发到 `JOBMATCH_API_URL`（默认 `https://zcpionner.cloud/api`），服务器解析、embedding、pgvector 召回。
5. 把脚本输出原样整理给用户；不要编造岗位或链接。`--list` 的结果要说明“每日更新，可过几天再来搜”。
6. 用户想看原始 JSON 时加 `--json`；想看额度时用 `--me`。

## 输出格式

```text
找到 5 个匹配岗位（快速匹配，耗时 320 ms，本次 0.1 credit）：
1. 字节跳动｜后端研发工程师｜杭州｜0.83
   https://jobs.bytedance.com/...
   向量相似度 0.81；技能命中 java / mysql / redis；城市匹配（杭州）
2. 字节跳动｜服务端研发工程师｜杭州（4 城可选）｜0.79
   https://jobs.bytedance.com/...
   向量相似度 0.77；技能命中 python / kafka；城市匹配（杭州）
...
```

城市列怎么读：`city_matched` 是匹配时**实际命中的那个城市**；`cities` 是岗位开放的**全部城市**，`city` 只是主城市。约一成的岗位是多城市发布的（`珠海;杭州`），所以会出现「杭州（4 城可选）」——那不是岗位只在北京，而是同一职位在四个城市都招。

`--list` 的输出也带 `cities`：用户指定城市时，优先显示该城市并标 `（N 城可选）`；不要只报 `city` 第一项，否则杭州搜索会看起来像深圳/珠海结果。

## 错误处理

- 401 `unauthorized`：没有 Key 或 Key 无效/已撤销；提示去 `/account/keys` 重新创建，不要重试。旧版共享 Key 已停用，必须用个人 Key。
- 403 `suspended`：账号被停用，提示联系管理员。
- 403 `unverified`：邮箱未验证，提示到 `/account/` 重新发送验证邮件。
- 402 `insufficient_credits`：免费 5 次已用完，且 credit 余额不足。响应含 `balance`、`cost`、`report_cost`、`packs`；不要重试。告诉用户当前余额/本次需要多少，并到 `https://zcpionner.cloud/account/billing?sku=credits_10` 获取 credits；不要报价、不要代付。
- 422：简历无法解析（扫描件/旧 .doc/文件为空），提示换 PDF/DOCX 或粘贴文本。
- 429 `rate_limited`：等一分钟再试一次，不要连续重试。
- 429 `quota_exceeded`：旧版额度错误；按 402 的方式提示去网站获取 credits，不要重试。
- 503 `server_busy`：服务器并发保护，本次不扣额度；按响应 `Retry-After` 等 2 秒再试一次。
- 503 `database_unavailable` / `embedding_unavailable`：服务器依赖不可用，最多重试两次；仍失败则明确说“服务器暂不可用”，不伪造结果。

## 安全

- 本 Skill 不含 API Key、云厂商 AK/SK、cookie；`ARK_API_KEY` / `DEEPSEEK_API_KEY` 只在服务器。
- 用户 Key 从环境变量 `JOBMATCH_API_KEY` 读取，不写进 Skill 目录、不打印、不落日志。
- 简历只用于本次匹配；服务器无状态，不保存简历。
- 不引导用户离开当前平台去第三方；只指向 JobMatch 自己的账号/额度页。
- 不要把简历正文、手机号、邮箱写进日志或最终回答。
