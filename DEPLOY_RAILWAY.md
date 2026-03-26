# Railway 部署配置

1. **创建 GitHub 仓库**
   - 访问 https://github.com/new
   - 仓库名: `eurojobs`
   - 设为 Public
   - 不要勾选 README

2. **推送代码**
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/eurojobs.git
   git push -u origin master
   ```

3. **Railway 部署**
   - 访问 https://railway.app 注册
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择 `eurojobs` 仓库

4. **添加数据库**
   - 在 Railway 项目中点击 "New"
   - 选择 "PostgreSQL"
   - 等待创建完成

5. **配置环境变量**
   - 点击 Python 服务的 Settings
   - 在 Variables 中添加:
     - `DATABASE_URL`: 从 PostgreSQL 服务复制连接字符串
   - 点击 Deploy

6. **部署前端**
   - 访问 https://vercel.com 注册
   - 导入 GitHub 仓库 `eurojobs`
   - Build Command: `npm run build`
   - Output Directory: `frontend/.next`

完成后你的网站就可以通过公网访问了！