# PaperDaily

每日自动获取论文的仓库，由 Cursor Automation 定时（每天 10AM GMT+8）更新。

## 邮件推送功能

每次仓库被更新（`push` 到 `main` 分支，即 Cursor 自动提交之后），GitHub Actions 会自动把本次新增/修改的论文 Markdown 内容渲染成 HTML 邮件，发送到你的邮箱。

- 工作流：`.github/workflows/notify-email.yml`
- 发送脚本：`scripts/send_email.py`

### 需要配置的 GitHub Secrets

在仓库页面 `Settings → Secrets and variables → Actions → New repository secret` 添加以下 5 个：

| Secret 名称       | 说明                                                         | 示例              |
| ----------------- | ------------------------------------------------------------ | ----------------- |
| `SENDER`          | 发件邮箱账号                                                  | `abc@qq.com`      |
| `SENDER_PASSWORD` | 发件邮箱的 **SMTP 授权码**（不是登录密码，向邮箱服务商申请） | `abcdefghijklmn`  |
| `RECEIVER`        | 收件邮箱（可多个，用英文逗号分隔）                            | `me@outlook.com`  |
| `SMTP_SERVER`     | 发件邮箱的 SMTP 服务器地址                                    | `smtp.qq.com`     |
| `SMTP_PORT`       | SMTP 端口（465 走 SSL，587 走 STARTTLS）                     | `465`             |

常见邮箱 SMTP：

- QQ 邮箱：`smtp.qq.com`，端口 `465`
- Gmail：`smtp.gmail.com`，端口 `465`（需使用应用专用密码）
- 163 邮箱：`smtp.163.com`，端口 `465`
- Outlook：`smtp.office365.com`，端口 `587`

### 手动测试

配置好 Secrets 后，到仓库 `Actions → Notify Email on Update → Run workflow` 手动触发一次。如果仓库还没有论文内容文件，会收到一封"配置成功"的测试邮件；有内容时会发送最新一篇的内容。

## 说明

- 默认分支：`main`
- 邮件只发送论文内容 Markdown，自动忽略 `README.md`、`scripts/` 和 `.github/`。
