# Redis Lock Laboratory

> 一个**用于验证分布式锁失败语义的工程级实验项目**，而不是“造一个锁”。
> 目标是**确定性认知**。

---

## 0. 项目定位

> **把“我感觉 Redis 锁不安全”变成“我可以精确描述它在什么条件下失效，以及为什么”**。

这正是工程岗位、尤其是后端/基础设施岗位要的能力。

---

## 1. 实验目标（第一性拆解）

从第一性原理拆开：

**分布式锁的本质不是互斥，而是：**
> 在不可靠世界中，对“谁有资格进入临界区”达成一个**短暂且可失效的共识**。

因此本项目只做三件事：
1. 明确定义锁协议（Protocol）
2. 系统性注入失败
3. 观察协议在失败下的**真实行为**


---

## 2. 实验环境假设（Frozen）


- Redis：**单实例**（强一致）
- 不使用 Redlock
- 不使用客户端时间作为真理
- TTL 是唯一可信的失效机制


---

## 3. 锁协议（Frozen Protocol）


### 3.1 数据模型

- Redis Key：`lock:{resource}`
- 类型：Hash

字段：
- `owner`：唯一持有者标识
- `count`：可重入计数

TTL：
- 直接绑定在 key 上（PEXPIRE）

---

### 3.2 owner_id 定义

```
owner_id = UUID + pid + thread_id
```

目的：
> **任何一次“续约 / 释放”都能被精确判定是否合法**。

---

### 3.3 Acquire（Lua 原子）

语义：
- key 不存在 → 创建锁（count=1，设置 TTL）
- key 存在 & owner == self → 可重入（count+1，刷新 TTL）
- 否则 → acquire 失败

刻意禁止：
- 自动重试
- sleep / backoff


---

### 3.4 Release（Lua 原子）

语义：
- key 不存在 → no-op
- owner != self → 非法释放（拒绝）
- owner == self → count--
  - count == 0 → 删除 key

---

### 3.5 Renew（Watchdog）

语义：
- key 不存在 → 续约失败
- owner != self → 立即放弃
- owner == self → 刷新 TTL

原则：
> Watchdog只是“延缓死亡”。

---

## 4. 失败模型（核心价值）

### 4.1 TTL Misjudge（时间误判）

定义：
- 业务执行时间 > TTL

可观测信号：
- 第二个 owner acquire 成功
- 第一个 owner 仍在 critical section

---

### 4.2 Watchdog 停止

实验脚本：
```
experiments/watchdog_pause_then_steal.py
```

**关键现象（已验证）：**
```
[A] acquire
[A] watchdog stop manually
[A] sleep 2s (TTL expire)
[B] acquire = True
[A] renew AFTER losing lock = False
[B] watchdog renew OK
```

结论：
> Watchdog只能在**没有被打断的前提下延长 TTL**。

---

### 4.3 Renew 竞态（失败）

现象：
- Lua 脚本被 Redis 清空（NOSCRIPT）
- renew 在 key 已过期后执行

观测到：
- renew 返回 false
- 或直接抛出脚本异常

这证明：
> **续约不是幂等安全操作**。

---

## 5. 实验设计规范

满足：

```
experiment(params) -> metrics
```

- params：明确的 TTL / 间隔 / 故障注入点
- metrics：结构化输出（dict / JSON）

禁止：
- print

---

## 6. 已完成

✔ Watchdog 暂停后锁被夺取
✔ Owner 在失锁后 renew 必然失败
✔ 第二个 owner 的 watchdog 能正常接管

---

## 7. 我原本以为……

> Watchdog 可以“保证”锁不会被别人拿走。

---

## 8. 但事实是……

> Watchdog 只是一个**概率性延寿机制**，
> 在任何暂停、阻塞、GC、网络异常下都会失效。

**锁的安全性来自协议设计。**

