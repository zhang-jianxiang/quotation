# GitHub 登录与操作指南

> 本文件总结了在当前项目中登录 GitHub、配置 Token、推送代码和启用 GitHub Pages 的完整流程，可复用于其他项目。

---

## 一、账号信息

| 项目 | 值 |
|------|-----|
| **GitHub 用户名** | `zhang-jianxiang` |
| **GitHub 邮箱** | `122053395@qq.com` |
| **GitHub 主页** | https://github.com/zhang-jianxiang |
| **GitHub Pages 域名** | `zhang-jianxiang.github.io` |

---

## 二、Token 创建

GitHub 支持两种 Personal Access Token，推荐使用 **Classic Token**（权限更宽泛、配置更简单）。

### 方案 A：Classic Token（推荐）

1. 打开链接（已预填参数）：
   ```
   https://github.com/settings/tokens/new?scopes=repo,workflow&description=push-manual
   ```
2. 确认 **Note** 为 `push-manual`
3. 确认 **Scopes** 已勾选 `repo`（包含所有子项）
4. 拉到最底部，点击绿色按钮 **Generate token**
5. 复制生成的 Token（格式：`ghp_` 开头 + 40 字符）
6. **注意**：Token 只在创建时显示一次，请立即保存

### 方案 B：Fine-grained Token

1. 打开 https://github.com/settings/tokens?type=beta
2. 点击 **Generate new token**
3. 配置如下：

| 配置项 | 值 |
|--------|-----|
| **Token name** | 自定义，如 `project-push` |
| **Expiration** | 90 天或自定义 |
| **Repository access** | Only select repositories → 勾选目标仓库 |
| **Contents 权限** | **Read and write** ✅（关键！） |
| **Metadata 权限** | Read（自动勾选） |

4. 点击 **Generate token**
5. 复制生成的 Token（格式：`github_pat_` 开头）

### ⚠️ 常见错误

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `403 Permission denied` | Token 缺少写入权限 | 重新生成 Token，确保勾选 `repo` 或 `Contents: Read and write` |
| `Repository not found` | 仓库名拼写错误或仓库不存在 | 检查仓库名称（注意 `_` 和 `-` 的区别） |
| `403 Resource not accessible` | Fine-grained Token 未选择目标仓库 | 编辑 Token，在 Repository access 中勾选目标仓库 |

---

## 三、Git 初始化与配置

### 1. 初始化 Git 仓库

```bash
cd /your/project/path
git init
git branch -m main
```

### 2. 配置用户信息

```bash
git config user.name "zhang-jianxiang"
git config user.email "122053395@qq.com"
```

> 如果是全局配置（所有项目通用）：
> ```bash
> git config --global user.name "zhang-jianxiang"
> git config --global user.email "122053395@qq.com"
> ```

### 3. 创建 .gitignore

```
# Uploads / 临时文件
.uploads/

# OS
.DS_Store
Thumbs.db
desktop.ini

# Editor
.vscode/
.idea/
*.swp
*.swo
*~
```

### 4. 创建 index.html（GitHub Pages 入口）

GitHub Pages 默认入口是根目录的 `index.html`。如果主页面在子目录中，需要创建一个跳转页面：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>项目名称</title>
  <meta http-equiv="refresh" content="0; url=子目录/主页面.html">
  <link rel="canonical" href="子目录/主页面.html">
</head>
<body>
  <p>正在跳转… Redirecting…</p>
  <p>若未自动跳转，请 <a href="子目录/主页面.html">点击此处</a>。</p>
</body>
</html>
```

### 5. 首次提交

```bash
git add -A
git commit -m "feat: 初始提交"
```

---

## 四、远程仓库配置与推送

### 1. 添加远程仓库

```bash
git remote add origin https://github.com/zhang-jianxiang/仓库名.git
```

### 2. 推送代码

#### 方式 A：Token 嵌入 URL（Classic Token）

```bash
git push https://zhang-jianxiang:ghp_你的TOKEN@github.com/zhang-jianxiang/仓库名.git main
```

#### 方式 B：x-access-token 方式（Fine-grained Token）

```bash
git remote set-url origin https://x-access-token:github_pat_你的TOKEN@github.com/zhang-jianxiang/仓库名.git
git push origin main
```

#### 方式 C：交互式输入（会提示输入用户名和密码，密码填 Token）

```bash
git push origin main
# Username: zhang-jianxiang
# Password: 粘贴你的 Token
```

### 3. 后续更新推送

```bash
git add -A
git commit -m "feat: 更新描述"
git push origin main
```

---

## 五、GitHub Pages 配置

### 1. 启用 Pages

1. 打开仓库页面：`https://github.com/zhang-jianxiang/仓库名`
2. 点击 **Settings** → 左侧菜单 **Pages**
3. **Source** 选择 `Deploy from a branch`
4. **Branch** 选择 `main`，文件夹选 `/ (root)`
5. 点击 **Save**

### 2. 访问地址

启用后等待 1-2 分钟，页面将通过以下地址访问：

```
https://zhang-jianxiang.github.io/仓库名/
```

如果主页面在子目录中：

```
https://zhang-jianxiang.github.io/仓库名/子目录/主页面.html
```

### 3. 本项目实际地址

```
https://zhang-jianxiang.github.io/social-media-manual/social-media-manual.html
```

---

## 六、常见问题

### Q: 嵌套 Git 仓库警告

```
warning: adding embedded git repository: social-media-manual
```

**原因**：子目录中存在 `.git` 目录。

**解决**：
```bash
git rm --cached -f 子目录名
Remove-Item -Recurse -Force 子目录名/.git
git add -A
```

### Q: LF / CRLF 换行符警告

```
warning: LF will be replaced by CRLF the next time Git touches it
```

**说明**：Windows 系统正常现象，不影响功能。如需消除警告：
```bash
git config core.autocrlf true
```

### Q: 推送大文件失败

GitHub 单文件限制 100MB，API 单次上传限制 100KB（Base64 编码后）。

**解决**：使用 Git LFS 或拆分文件。

### Q: GitHub Pages 404

1. 确认仓库为 **Public**（免费账户 Pages 仅支持公开仓库）
2. 确认 Pages 设置中 Branch 选择了 `main`
3. 等待 1-2 分钟让部署完成
4. 检查文件路径是否正确

---

## 七、PowerShell 环境注意事项

当前系统使用 PowerShell，与标准 Bash 有以下差异：

| 操作 | Bash | PowerShell |
|------|------|------------|
| 链接命令 | `cmd1 && cmd2` | `cmd1; cmd2` |
| 删除目录 | `rm -rf dir` | `Remove-Item -Recurse -Force dir` |
| 检查文件 | `test -f file` | `Test-Path file` |
| 输出 | `echo` | `Write-Output` |

---

## 八、快速部署清单

新项目部署到 GitHub Pages 的完整步骤：

- [ ] 1. `git init` + `git branch -m main`
- [ ] 2. 配置 `user.name` 和 `user.email`
- [ ] 3. 创建 `.gitignore`
- [ ] 4. 创建根目录 `index.html`（入口/跳转页）
- [ ] 5. `git add -A` + `git commit -m "feat: 初始提交"`
- [ ] 6. 在 GitHub 上创建仓库（或用 API 创建）
- [ ] 7. `git remote add origin https://github.com/zhang-jianxiang/仓库名.git`
- [ ] 8. 生成 Token（Classic Token，勾选 `repo` 权限）
- [ ] 9. `git push origin main`
- [ ] 10. 仓库 Settings → Pages → Branch: `main` → Save
- [ ] 11. 访问 `https://zhang-jianxiang.github.io/仓库名/` 验证

---

*最后更新：2026-07-11*
