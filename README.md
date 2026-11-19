# Orchestrate 皮肤库

在支持皮肤库的 Orchestrate 开发版或后续正式版中，打开“设置 → 风格与布局 → 管理皮肤”下载，再到配色下拉框切换。已安装皮肤可离线使用，支持标准和紧凑布局。

首款皮肤「曼巴紫 × 冠军金」的配色和侧栏插画源自 [Orchestrate PR #4](https://github.com/VelvetEvening/Orchestrate/pull/4)。

「冰湖五号 × 爱德华兹」取色自明尼苏达森林狼 2024–25 赛季城市版球衣。冰白和湖蓝构成工作区，炭黑用于主按钮。侧栏插画将爱德华兹的 5 号球衣、灰狼和冰湖融在一起。[球衣设计说明](https://www.nba.com/timberwolves/news/timberwolves-2024-25-city-edition-uniform-court-photos-games-giveaways)

## 制作皮肤

1. 参考[紫金主题包](themes/mamba/theme.json)，新建 `themes/<id>/theme.json`。保留格式版本，填写 ID 和名称，选择 `light` 或 `dark` 作为基础配色。
2. 在 `colors` 中覆盖需要的颜色，其余由应用补全。字段和颜色角色见 [JSON Schema](schema.json)。如需插画，在同一目录放入 `sidebar.png`，并设置 `"sidebarImage": "sidebar.png"`。图片最多 4 MiB，长边不超过 4096 像素，总像素不超过 4,194,304。
3. 将相同的 ID 和名称加入[目录清单](catalog.json)。下一次打开“管理皮肤”即可看到新条目。

提交前用 Python 运行格式与资源检查。CI 也执行同一检查。

```sh
python -m pip install jsonschema Pillow
python -m unittest discover -s tests
python verify.py
```
