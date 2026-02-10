# Redis Lock Laboratory

> A professional-grade experimental suite designed to **validate distributed lock failure semantics**, rather than merely "building another lock."
> **Goal:** Transitioning from "feeling" that Redis locks are unsafe to **accurately quantifying when, where, and why they fail.**

---

## 0. Project Positioning

This project aims to transform the vague intuition of "Redis locks are unreliable" into a **deterministic engineering map**. It is designed for backend and infrastructure engineers who prioritize **correctness over convenience**.

---

## 1. First-Principles Decomposition

From a first-principles perspective, the essence of a distributed lock is not just mutual exclusion, but:

> **Reaching a transient, revocable consensus** on "who is entitled to enter the critical section" within an unreliable distributed world.

Accordingly, this project focuses on three pillars:

1. **Defining a strict Lock Protocol.**
2. **Systematic Fault Injection.**
3. **Observing real-world protocol behavior under duress.**

---

## 2. Environmental Assumptions (Frozen)

* **Redis:** Single instance (Simulating strong consistency/linearizability for the lock store).
* **No Redlock:** Avoiding the complexity and clock-drift controversies of Redlock.
* **Clock Independence:** Client-side time is never treated as a source of truth.
* **TTL as Truth:** TTL is the only authoritative mechanism for lock expiration.

---

## 3. Frozen Protocol

### 3.1 Data Model

* **Redis Key:** `lock:{resource}`
* **Type:** Hash

**Fields:**

* `owner`: Unique identifier of the holder.
* `count`: Reentrancy counter.
* **TTL:** Bound directly to the key via `PEXPIRE`.

### 3.2 Owner Identification

```text
owner_id = UUID + pid + thread_id

```

**Rationale:** Ensures every "Renew" or "Release" operation can be **deterministically validated** for legitimacy.

### 3.3 Acquire (Atomic Lua)

* **Key exists + Owner matches:** Reentrant (Increment `count`, refresh TTL).
* **Key does not exist:** Create lock (Set `count=1`, set TTL).
* **Otherwise:** Acquisition failed.
* **Hard Constraint:** No automatic retries, sleep, or backoff logic (to isolate failure points).

### 3.4 Release (Atomic Lua)

* **Key does not exist:** No-op.
* **Owner mismatch:** Illegal release (Request rejected).
* **Owner matches:** Decrement `count`. If `count == 0`, delete the key.

### 3.5 Renew (Watchdog Mechanism)

* **Key does not exist:** Renewal failed.
* **Owner mismatch:** Immediate surrender (Stop renewal).
* **Owner matches:** Refresh TTL.
* **Core Principle:** The Watchdog is merely a **"deferred death"** mechanism.

---

## 4. Failure Models (The Core Value)

### 4.1 TTL Misjudgment

* **Definition:** Execution time exceeds the TTL.
* **Observable Signal:** A second owner successfully acquires the lock while the first owner is still in the critical section.

### 4.2 Watchdog Interruption

**Script:** `experiments/watchdog_pause_then_steal.py`

**Observed Phenomenon:**

1. [A] acquires lock.
2. [A]'s watchdog is manually paused (simulating GC/Network Hang).
3. [A] sleeps (TTL expires).
4. [B] acquires lock successfully.
5. [A] attempts `renew` after losing the lock -> **Returns False**.
6. [B]'s watchdog takes over successfully.

> **Conclusion:** A Watchdog only extends the TTL **if and only if** the environment remains uninterrupted.

### 4.3 Renewal Race Condition

**Observed Phenomenon:**

* Lua script cache is flushed (`NOSCRIPT`).
* `Renew` is triggered after the key has already expired.

**Result:** `Renew` returns `False` or throws a script exception, proving that **Renewal is not an idempotent safe operation.**

---

## 5. Experimental Design Specs

Every experiment follows a strict functional signature:
`experiment(params) -> metrics`

* **Params:** Explicit TTL, intervals, and fault injection points.
* **Metrics:** Structured output (JSON/Dict).
* **Constraint:** No arbitrary `print` statements; data must be structured for analysis.

---

## 6. Progress Report

* [x] Verified lock theft after Watchdog suspension.
* [x] Confirmed `Renew` failure for owners who have lost their lock.
* [x] Verified seamless Watchdog handover to the second owner.

---

## 7. The Myth...

> *"I thought a Watchdog could 'guarantee' that a lock would never be stolen while I was working."*

## 8. The Reality...

> **A Watchdog is a probabilistic life-extension mechanism.** It fails under any pause, block, GC event, or network anomaly.

**Lock safety is derived from protocol design, not from the "feeling" of a heartbeat.**


