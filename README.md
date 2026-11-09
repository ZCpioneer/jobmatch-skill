# JobMatch Skill

把一份简历变成 5 个值得投的真实岗位——带匹配理由和原始链接。

[官网](https://zcpionner.cloud/skill?ref=github) · [SkillHub](https://skillhub.cn/skills/user_9757edcf/job-match) · [安装说明](https://zcpionner.cloud/install.md) · [免费注册](https://zcpionner.cloud/account/login?mode=signup&ref=github)

> 本仓库只含 Skill 客户端；服务端、岗位数据、部署配置与密钥不开源。

## 它做什么

- 输入：PDF / DOCX / TXT / Markdown 简历，或直接给文本。
- 输出：Top 5 岗位，含公司、职位、城市、匹配理由、原始 JD 链接。
- 没有简历时：`--list` 按关键词 / 城市免费搜岗位。
- 数据：2,300+ 条公开招聘岗位，6 家公司，每日更新（以官网实时数字为准）。
- 匹配分数是语义接近度，不是录用概率；不承诺面试或 offer。

## 安装

1. 下载并解压到客户端的 skills 目录。以 Claude Code 为例：

   ```bash
   unzip job-match-skill-v0.5.zip -d ~/.claude/skills/
   ```

   解压后应得到 `~/.claude/skills/job-match/SKILL.md`。

2. 到 <https://zcpionner.cloud/account/> 用邮箱注册，登录后在账号页创建个人 API Key（形如 `jm_live_...`，只显示一次）。

3. 把 Key 放进环境变量，不要写进这个目录：

   ```bash
   export JOBMATCH_API_KEY="jm_live_..."
   ```

4. 对助手说：

   ```text
   用 JobMatch 帮我匹配岗位。简历在 ~/resume.pdf，城市杭州，看 Top 5。
   ```

## 使用

```bash
# 有简历：完整匹配（免费 5 次/月，之后 1 credit/次）
python3 ~/.claude/skills/job-match/scripts/match_jobs.py --file ~/resume.pdf --city 杭州

# 有简历：快速匹配（0.1 credit/次，不占免费额度）
python3 ~/.claude/skills/job-match/scripts/match_jobs.py --file ~/resume.pdf --quick --city 杭州

# 没有简历：免费搜岗位
python3 ~/.claude/skills/job-match/scripts/match_jobs.py --list --q "后端" --city 杭州

# 查额度
python3 ~/.claude/skills/job-match/scripts/match_jobs.py --me
```

没有 Key 时接口返回 401；不要把 Key 写进 Skill 目录、聊天记录或 Git。

## 免费额度

- 免费 5 次完整匹配/月；快速匹配 0.1 credit/次；完整匹配 1 credit/次。
- 深度报告 9 credits，在网站上生成。
- 额度不足时到 <https://zcpionner.cloud/account/billing> 获取 credits；**具体价格以官网为准，本仓库不展示价格、不收款**。

## 隐私与数据

- 简历原文不落库；请求结束即丢弃。
- 免费匹配不保存；付费场景保留脱敏文本与解析结果 30 天，可删除；报告保留 30 天。
- 只有邮箱、Key 哈希、用量、订单和上述期限内脱敏内容会被保存。
- Key 只存哈希，可随时在账号页撤销。
- 不要把真实简历、手机号、邮箱、订单号或 Key 提交到 issue / PR。

## 数据口径

- 当前 2,300+ 条岗位 / 6 家公司；每日 04:00 更新。
- 岗位来自公开招聘页面；每个结果都带原始链接，可回源核对。
- 数字会随数据池变化，以官网为准；不要在二次传播中写死旧数字。

## 兼容性

- 适用于能读取 `SKILL.md`、并允许执行 Python 3（仅标准库）和访问 HTTPS 的 AI 助手。
- 只读提示词、不执行脚本的宿主：需要用户手动运行上面的命令。
- 扫描件 / 图片 PDF 暂不支持 OCR，会返回 422；请换文字版 PDF 或直接粘贴文本。

## 仓库边界

- 本仓库只含 Skill 客户端：`SKILL.md`、`README.md`、`VERSION`、`scripts/match_jobs.py`、`LICENSE`。
- 不开源：`server/`、`infra/`、岗位数据、部署脚本、Nginx / Cloudflare 配置、任何 Key。
- MIT 只覆盖本仓库；`JobMatch` 名称与品牌不随 MIT 授权。

## 版本

| 版本 | 日期 | 说明 |
|---|---|---|
| 0.5.0 | 2026-11-09 | 新增 `--list` 免费岗位搜索、`--quick` 0.1 credit 快速匹配；402 深链到账单页 |
| 0.4.0 | 2026-11-08 | API 改为 `https://zcpionner.cloud/api`；免费 5 次 / 402 语义；包内不含价格 |

Release 资产与官网 `job-match-skill-v0.5.zip` 相同；仓库 README 可能比包内 README 更详细。

## License

MIT。详见 [LICENSE](LICENSE)。
