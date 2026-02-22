# Carrion 的星露谷 Mod 管理器

一个基于 PyQt5 和 Fluent 风格界面的现代化 Mod 管理器，专为 **星露谷物语** 打造。

## 🌟 功能特色

- 🔄 一键启用/禁用 Mod
- 📁 游戏目录与配置目录自动同步
- 🧩 自动识别与分类 Mod
- 🌐 从 NexusMods 获取 Mod 信息与更新
- 📦 支持本地导入 Mod
- 🧼 简洁美观的 Fluent 风格界面


## 🚀 快速开始

无需安装 Python！只需下载 `.exe` 文件即可运行。

### ✅ 系统要求

- Windows 10 或更高版本
- 已安装星露谷物语
- 已安装SMAPI(不然怎么运行mod呀)

### 📦 安装步骤

1. 前往 [Releases](https://github.com/yourname/yourrepo/releases) 下载最新版
2. 解压 `.zip` 文件
3. 双击 `CarrionModManager.exe` 启动程序

## 📁 文件结构
CarrionModManager/  
├── App_entry.py  
├── main_UI.py  
├── assets/    
├── data/    
├── GUI/    
├── core/  
└── README_zh.md  

## 📸 界面截图

![截图](assets/Screenshots/profile_page.png)

## 🛠 技术栈

- [PyQt5](https://pypi.org/project/PyQt5/)
- [QFluentWidgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets)
- [Python 3.9+](https://www.python.org/)

## 📃 开源协议

本项目采用 MIT 协议开源。

---

---

## 🐷 开发者碎碎念

这个项目最初是因为我使用的 mod 管理器在星露谷游戏根目录文件结构十分混乱，甚至有的 mod 虽然显示导入了但是却未导入，让我的 mod 管理一团乱！  
我一怒之下怒写了一个决定自己干掉一个 mod 管理器，我的技术栈是 Python，因此这个软件全部使用 Python 来写。  
有懒蛋想着用自己的之前的打包环境来开发（因为需要的包都有），在打包的时候发现 2 个多 G，已老实，重新配了只含这个应用需要的包的环境。  

这个 mod 管理器的亮点大概就是管理器内和 Mods 文件夹内的 mod 顺序高度统一，mod 文件的结构原封不动地移入游戏的 Mods 文件夹内，和你自己打 mod 一模一样～  

因为是懒蛋，所以不想自己一个个手动添加 mod 进管理器，做了从 Mods 文件夹里直接扫描添加的功能；  
因为是懒蛋，所以在编辑 mod 和导入 mod 时不想多一个下载图贴的步骤，所以做了从剪贴板读取图片；  
因为是懒蛋，所以能自动化就自动化，能从 N 网读取到 mod 的信息绝不自己填；  
因为是懒蛋，所以搞做了多 profile 的接口了，但是孩子燃起来了，准备下次一定；  

虽然是懒蛋，但是穷鬼，所以没入 N 网 premium，更新 mod 只能自己去点一下「slow download」了，  
但是就这一下，剩下的压缩包移动替换文件程序会帮你搞定！  

这个 mod 管理器主要是为我自己服务的，因此我在开发过程中做了我觉得我会很喜欢的功能，  
希望能对你有用(❁´◡`❁)*✲ﾟ*  

在此致谢在我开发过程中帮了大忙的 ChatGPT 老师、Copilot 老师、Claude 老师们！  
不说了大家，我去星露谷 627 了！٩(๑❛ᴗ❛๑)۶  

—— Carrion


