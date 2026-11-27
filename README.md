# 巷拓 · 街区橱窗贴膜裁耗估计

为街区展览的异形橱窗确定裁切方向、卷宽、拼缝和每单放卷余量。实裁时段按签发顺序分配，核销实际占用毫米段，剩余预测余量退回库存。

## 使用场景

虚拟客户河埠街展陈维护组有一位场地监督、三位测量与裁膜人员。橱窗网点分别有顶部斜角、直窗以及横向招牌。团队过去在测绘表里手估边料，三处损耗常被漏算。卷材实际宽度要扣两侧伤边，竖纹有固定方向，能拼缝也有搭接损耗。旧测量单在改窗后仍可能被送去下料。

上游提供窗内净空、护边标记、所需表面和卷料盘点。巷拓提供布局、模型余量、签发和库存核销。门店展陈人员按裁切单领取已经实裁的卷段。

| 角色 | 权限 | 演示账号与密码 |
|---|---|---|
| 展陈监督 `admin` | 登记卷材、签发及作废、全部现场操作和审计 | `admin` / `admin-hexin-demo` |
| 裁膜员 `operator` | 录入窗格及修订、查询可裁性、申请估算、实裁核销 | `operator` / `operator-hexin-demo` |
| 门店联络人 `viewer` | 查窗格、卷材可用量、裁切单和收料凭据 | `viewer` / `viewer-hexin-demo` |

## 河埠拱角橱窗作业

1. 08:40 测绘 `WIN-ARC`，记录宽 1170 毫米、原高 1440 毫米、左斜角 95 毫米与右斜角 70 毫米。
2. 查竖纹及伤边。主卷 `ROLL-A12` 由 1220 毫米名义幅宽得出 1180 毫米可用幅宽。保留各侧 20 毫米工艺余边，需竖裁两片，各宽 615 毫米，中缝搭接 20 毫米。
3. 09:00 生成裁切草案并签发主卷。短余卷 `ROLL-END` 虽能通过幅宽检查，剩余长度不足以签发。
4. 09:20 现场发现实际高度应为 1470 毫米。旧版草案拒绝签发，旧版签发单拒绝实裁核销。监督作废并释放垫留量。
5. 新版拱窗单和书店直窗单先后签发，都从主卷预留长度。书店不能越过拱窗先出料。
6. 10:10 拱窗单核对下料，实裁进给比几何进给多 20 毫米。系统产生从卷头开始的实际段号并退回剩余垫留。
7. 10:35 书店下料从上一实际段的末点接续，两段持久化凭据进入领料和余料账，测得的损耗供下一版模型训练使用。

## 启动和 API

```sh
cp .env.example .env
docker compose up -d --build --wait
docker compose exec -T backend python -m scripts.seed_demo
curl -fsS http://127.0.0.1:18369/health
```

Nginx 网关在 `http://127.0.0.1:18369`，FastAPI 在 `http://127.0.0.1:19369`，接口描述为 `/openapi.json`。PostgreSQL 16 监听宿主机端口 17869，保存库存、裁切计划与实测。后台 worker 消费数据库任务，Redis 记录 worker 心跳。

```sh
curl -fsS -X POST http://127.0.0.1:18369/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"operator","password":"operator-hexin-demo"}'
```

获得 `access_token` 后在业务请求传入 `Authorization: Bearer <token>`。

| 动作 | API |
|---|---|
| 录入及修订图样 | `POST /windows`、`GET /windows/{code}`、`PUT /windows/{code}`（需携带 `expected_revision`） |
| 核实幅宽、纹向和搭接 | `GET /windows/{code}/fit?roll_code=ROLL-A12` |
| 建立库存与查放料顺序 | `POST /rolls`、`GET /rolls/{code}` |
| 请求损耗估算 | `POST /cut-estimates`（请求体含 `window_code`、`window_revision`、`roll_code`），用 `GET /jobs/{id}` 读取 `result.sheet_id` |
| 查草案、签发、撤销及核销 | `GET /cut-sheets/{id}`、`POST /cut-sheets/{id}/issue`、`POST /cut-sheets/{id}/void`、`POST /cut-sheets/{id}/complete` |

Compose 支持 `GATEWAY_PORT`、`BACKEND_PORT`、`DB_PORT`、`DB_PASSWORD`、`JWT_SECRET`、`SEED_DEMO` 和三个 `DEMO_*_PASSWORD`。本地调试可安装 `backend/requirements.txt`，设置可访问的 `DATABASE_URL`、`REDIS_URL`、`JWT_SECRET`，从 `backend/` 启动 `uvicorn main:app` 和 `python -m core.queue_worker`。正常停服执行 `docker compose down` 保留数据库卷。

## 拟合和库存口径

- 卷宽扣除两边的伤边；窗格净尺寸加两侧余边。竖纹沿卷长，方向无限制时可以转裁。单片不适配时，在允许拼缝的约束下补 20 毫米搭接并分为两片，每片至少 150 毫米。裁切单保存每片跨幅宽、进给长、拼缝及顶部两个斜角。
- scikit-learn 梯度提升树用 P80 pinball loss 拟合额外耗材长度。输入为进给长、有效幅宽、最宽片宽、斜角合计、厚度与裁片数量。按固定种子留出约 20%，报告损失和覆盖率。估计值截断为非负，每 5 毫米向上取整。
- 签发时将几何进给与预测损耗相加，存为已经占用的长度。核销要求当前窗格版次、卷内签发先后次序、实际进给不小于几何下限且不超过该单预留。核销或作废释放垫留；已裁卷段写入不可改的收料凭据。实测每次追加到历史记录。
- 初始历史是 216 条可重复生成的模拟实裁数据。现场部署需要用相同口径校准裁膜余量。布局覆盖顶部斜切和一条拼缝的窗格。

## 目录与许可

`backend/domain/` 有窗格净空、卷料余量、幅宽校核、损耗模型、签发和核销代码。`backend/migrations/` 保存领域表约束。纹向、卷纹和单据状态枚举位于 `domain/vocabulary.py` 以及 `010_windows.sql`、`020_rolls.sql`、`030_cut_sheets.sql`。许可为 MIT，见 [LICENSE](LICENSE)。
